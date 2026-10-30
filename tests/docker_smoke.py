"""Exercise the bundled Java/Cetus/GCC toolchain without an LLM or server.

Run from the built server image:
    docker run --rm --entrypoint python smart-server:v2 tests/docker_smoke.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from server.tools.program_optimizer.optimizer import (  # noqa: E402
    CetusOptimizationError,
    CetusOptimizer,
)


@dataclass(frozen=True)
class Case:
    name: str
    filename: str
    profile: str
    expected_stdout: str
    check_openmp: bool = False
    check_prefix: bool = False


# These are the eight commands documented in README.md.
CASES = (
    Case("01_parallel", "01_vector_scale.c", "parallel", "checksum=14999950000\n", True),
    Case("02_reduction", "02_reduction_sum.c", "parallel", "sum=495000\n"),
    Case("03_fixed32", "03_matrix_multiply.c", "paw_tiling_fixed32", "checksum=1572475\n"),
    Case("04_prefix", "04_prefix_sum.c", "parallel", "prefix_checksum=167167000\n", check_prefix=True),
    Case("05_interchange", "05_loop_interchange.c", "loop_interchange", "checksum=4161536\n"),
    Case("06_nt", "03_matrix_multiply.c", "paw_tiling_nt", "checksum=1572475\n"),
    Case("07_lrw", "03_matrix_multiply.c", "paw_tiling_lrw", "checksum=1572475\n"),
    Case("08_reuse", "01_vector_scale.c", "reuse_analysis", "checksum=14999950000\n"),
)

HEADERS_SOURCE = """#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(void) {
    int *values;
    long checksum = 0;
    time_t epoch = 0;
    struct tm *calendar;

    values = (int *)malloc(64 * sizeof(int));
    if (values == NULL) return 2;
    for (int i = 0; i < 64; ++i) values[i] = 3 * i + 1;
    for (int i = 0; i < 64; ++i) checksum += values[i];
    free(values);

    calendar = gmtime(&epoch);
    if (calendar == NULL || calendar->tm_year != 70) return 3;
    printf("stdlib_checksum=%ld\\n", checksum);
    return checksum == 6112L ? 0 : 1;
}
"""


class SmokeFailure(RuntimeError):
    """A failed integration check with bounded compiler diagnostics."""


def tail(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        value = value.decode(errors="replace")
    lines = (value or "").strip().splitlines()
    return "\n".join(lines[-30:])[-5000:]


def run_command(
    argv: list[str],
    label: str,
    *,
    env: dict[str, str] | None = None,
    timeout: float = 60,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            errors="replace",
            env=env,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise SmokeFailure(
            f"{label} timed out after {timeout:g}s\n"
            f"{tail(exc.stdout)}\n{tail(exc.stderr)}"
        ) from exc
    except OSError as exc:
        raise SmokeFailure(f"{label} could not start: {exc}") from exc
    if result.returncode != 0:
        raise SmokeFailure(
            f"{label} exited {result.returncode}\n"
            f"{tail(result.stdout)}\n{tail(result.stderr)}"
        )
    return result


def compile_source(source: Path, executable: Path, label: str) -> None:
    run_command(
        ["gcc", "-std=c11", "-O0", "-fopenmp", str(source), "-o", str(executable)],
        f"{label} compile",
    )


def check_program(
    executable: Path,
    expected_stdout: str,
    label: str,
    *,
    check_prefix: bool = False,
) -> None:
    # One and four threads exercise both serialized and parallel OpenMP paths.
    # Repeat the dependency-sensitive prefix case at four threads as well.
    threads = (1, 2, 4, 4, 4) if check_prefix else (1, 4)
    for count in threads:
        environment = dict(os.environ)
        environment.update(
            OMP_NUM_THREADS=str(count),
            OMP_DYNAMIC="false",
            OMP_WAIT_POLICY="PASSIVE",
        )
        result = run_command(
            [str(executable)],
            f"{label} run ({count} threads)",
            env=environment,
            timeout=20,
        )
        if result.stdout != expected_stdout:
            raise SmokeFailure(
                f"{label} produced incorrect output with {count} threads: "
                f"expected {expected_stdout!r}, got {tail(result.stdout)!r}"
            )


def run_case(optimizer: CetusOptimizer, root: Path, case: Case, source_bytes: bytes) -> None:
    # Uploaded names may contain spaces. Keep all optimizer work outside /app.
    case_dir = root / f"{case.name} source with spaces"
    case_dir.mkdir()
    source = case_dir / "original source.c"
    source.write_bytes(source_bytes)
    baseline = case_dir / "baseline"
    compile_source(source, baseline, f"{case.name} original")
    check_program(baseline, case.expected_stdout, f"{case.name} original")

    try:
        transformed = optimizer.optimize_file(
            source, case.profile, output_dir=case_dir / "transformed output"
        )
    except CetusOptimizationError as exc:
        raise SmokeFailure(f"{case.name} Cetus {case.profile}:\n{tail(str(exc))}") from exc
    if source.read_bytes() != source_bytes:
        raise SmokeFailure(f"{case.name} modified its original source")
    transformed_text = transformed.output_path.read_text(encoding="utf-8")
    if case.check_openmp and not re.search(
        r"#\s*pragma\s+omp\s+parallel\s+for\b", transformed_text
    ):
        raise SmokeFailure(f"{case.name} did not emit an OpenMP parallel loop")

    optimized = case_dir / "optimized"
    compile_source(transformed.output_path, optimized, f"{case.name} transformed")
    check_program(
        optimized,
        case.expected_stdout,
        f"{case.name} transformed",
        check_prefix=case.check_prefix,
    )
    print(f"PASS {case.name}: {case.profile}, original/transformed output matches", flush=True)


def main() -> int:
    try:
        java = run_command(["java", "-version"], "Java runtime")
        version = re.search(r'version\s+"(\d+)', java.stdout + java.stderr)
        if version is None or version.group(1) != "21":
            raise SmokeFailure(f"Expected Java 21; got:\n{tail(java.stdout + java.stderr)}")
        print("PASS Java 21 runtime", flush=True)

        # Constructor defaults must resolve the image's bundled configuration.
        optimizer = CetusOptimizer()
        launch = run_command([str(optimizer.cetus_path), "-version"], "Cetus launcher")
        if "cetus" not in (launch.stdout + launch.stderr).lower():
            raise SmokeFailure("Cetus launcher did not identify itself")
        print("PASS bundled Cetus launcher", flush=True)

        configured = json.loads(optimizer.profiles_file.read_text(encoding="utf-8"))
        exercised = {case.profile for case in CASES}
        if not isinstance(configured, dict) or set(configured) != exercised:
            raise SmokeFailure("Smoke cases must cover every configured profile")

        with tempfile.TemporaryDirectory(prefix="smart-docker-smoke-") as temporary:
            root = Path(temporary)
            for case in CASES:
                source = PROJECT_ROOT / "Testing_Examples" / case.filename
                run_case(optimizer, root, case, source.read_bytes())
            headers = Case("09_stdlib_headers", "stdlib_headers.c", "parallel", "stdlib_checksum=6112\n")
            run_case(optimizer, root, headers, HEADERS_SOURCE.encode("utf-8"))
        print("PASS Docker smoke: 9 programs, all 6 profiles", flush=True)
        return 0
    except (SmokeFailure, CetusOptimizationError, OSError, ValueError) as exc:
        print(f"FAIL {tail(str(exc))}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
