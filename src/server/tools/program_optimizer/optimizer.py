"""Run Cetus with a named optimization profile from Regression-Test."""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_TIMEOUT_SECONDS = 300.0


class CetusOptimizationError(ValueError):
    """Raised when Cetus cannot transform a source file."""


@dataclass(frozen=True)
class CetusOptimizationResult:
    """Result of one Cetus source transformation."""

    input_path: Path
    output_path: Path
    profile: str
    returncode: int
    stdout: str
    stderr: str
    command: tuple[str, ...]


class CetusOptimizer:
    """Invoke the Cetus binary with profile flags from profiles.json.

    CETUS selects the Cetus executable, CETUS_PROFILES_FILE selects the
    SMART-COMPILER profile JSON, and CETUS_TIMEOUT_SECONDS sets the process
    timeout. Explicit constructor values take precedence over environment
    variables.
    """

    def __init__(
        self,
        cetus_path: str | Path | None = None,
        profiles_file: str | Path | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.cetus_path = self._resolve_cetus_path(cetus_path)
        self.profiles_file = self._resolve_profiles_file(profiles_file)
        self.timeout_seconds = self._resolve_timeout(timeout_seconds)

    @staticmethod
    def _resolve_cetus_path(value: str | Path | None) -> Path:
        configured = value or os.environ.get("CETUS")
        if not configured:
            raise CetusOptimizationError(
                "CETUS is not set. Export CETUS with the path to "
                "The-Cetus-Project/bin/cetus before starting SMART."
            )
        path = Path(configured).expanduser()
        if not path.is_file():
            raise CetusOptimizationError(
                f"Cetus executable not found: {path}. Set CETUS to the Cetus bin/cetus path."
            )
        if not os.access(path, os.X_OK):
            raise CetusOptimizationError(f"Cetus executable is not executable: {path}")
        return path.resolve()

    @staticmethod
    def _resolve_profiles_file(value: str | Path | None) -> Path:
        configured = value or os.environ.get("CETUS_PROFILES_FILE")
        if not configured:
            raise CetusOptimizationError(
                "CETUS_PROFILES_FILE is not set. Export it with the path to "
                "config/profiles.json in your SMART-COMPILER checkout before starting SMART."
            )
        path = Path(configured).expanduser()
        if not path.is_file():
            raise CetusOptimizationError(
                f"Cetus profile configuration not found: {path}. "
                "Set CETUS_PROFILES_FILE to config/profiles.json in your SMART-COMPILER checkout."
            )
        return path.resolve()

    @staticmethod
    def _resolve_timeout(value: float | None) -> float:
        if value is not None:
            timeout = float(value)
        else:
            raw = os.environ.get("CETUS_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
            try:
                timeout = float(raw)
            except ValueError as exc:
                raise CetusOptimizationError(
                    f"CETUS_TIMEOUT_SECONDS must be a positive number, got {raw!r}."
                ) from exc
        if timeout <= 0:
            raise CetusOptimizationError("Cetus timeout must be greater than zero.")
        return timeout

    def _load_profile_flags(self, profile: str) -> list[str]:
        try:
            content: Any = json.loads(self.profiles_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CetusOptimizationError(
                f"Could not read Cetus profiles from {self.profiles_file}: {exc}"
            ) from exc
        if not isinstance(content, dict):
            raise CetusOptimizationError(
                f"Invalid Cetus profile configuration in {self.profiles_file}: expected a JSON object."
            )

        entry = content.get(profile)
        if entry is None:
            choices = ", ".join(sorted(str(name) for name in content))
            raise CetusOptimizationError(
                f"Unknown Cetus profile {profile!r}. Available profiles: {choices or '(none)'}."
            )
        if not isinstance(entry, dict) or not isinstance(entry.get("flags"), list):
            raise CetusOptimizationError(
                f"Invalid Cetus profile {profile!r}: expected an object with a flags array."
            )
        flags = entry["flags"]
        if any(not isinstance(flag, str) or not flag for flag in flags):
            raise CetusOptimizationError(
                f"Invalid Cetus profile {profile!r}: every flag must be a non-empty string."
            )
        return list(flags)

    def optimize_file(
        self,
        file_path: str | Path,
        profile: str,
        output_dir: str | Path | None = None,
    ) -> CetusOptimizationResult:
        """Transform one C source file, preserving the original file.

        The input is copied into a unique work directory under a simple filename.
        This avoids word-splitting in the upstream bin/cetus shell wrapper when
        an uploaded source path contains spaces. The transformed file remains in
        that work directory (or below output_dir when one is provided).
        """
        source = Path(file_path).expanduser()
        if not source.is_file():
            raise CetusOptimizationError(f"C source file not found: {source}")
        source = source.resolve()
        if not profile:
            raise CetusOptimizationError("A Cetus optimization profile is required.")

        flags = self._load_profile_flags(profile)
        base = Path(output_dir).expanduser().resolve() if output_dir else None
        try:
            # Keep the work directory beside the source, so Cetus's default
            # cpp -I. can still resolve headers from the source directory.
            work_dir = Path(
                tempfile.mkdtemp(prefix=".cetus-optimizer-", dir=source.parent)
            )
        except OSError as exc:
            raise CetusOptimizationError(
                f"Could not create a temporary Cetus work directory beside "
                f"{source}: {exc}"
            ) from exc

        suffix = source.suffix
        if not suffix or not re.fullmatch(r"\.[A-Za-z0-9_-]+", suffix):
            suffix = ".c"
        staged_source = work_dir / f"input{suffix}"
        transformed_dir = work_dir / "transformed"
        try:
            source_bytes = source.read_bytes()
            if not source_bytes.endswith(b"\n"):
                source_bytes += b"\n"
            staged_source.write_bytes(source_bytes)
            # The wrapper expands positional arguments without quoting them.
            # Relative paths from source.parent contain no spaces, while
            # running there preserves the compiler's normal include lookup.
            staged_source_arg = staged_source.relative_to(source.parent).as_posix()
            transformed_dir_arg = transformed_dir.relative_to(source.parent).as_posix()
            command = (
                str(self.cetus_path),
                *flags,
                f"-outdir={transformed_dir_arg}",
                staged_source_arg,
            )
            try:
                process = subprocess.Popen(
                    list(command),
                    cwd=source.parent,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    start_new_session=(os.name == "posix"),
                )
                try:
                    stdout, stderr = process.communicate(timeout=self.timeout_seconds)
                except subprocess.TimeoutExpired as exc:
                    if os.name == "posix":
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    else:
                        process.kill()
                    stdout, stderr = process.communicate()
                    stdout = stdout or _decode_output(exc.stdout)
                    stderr = stderr or _decode_output(exc.stderr)
                    raise CetusOptimizationError(
                        f"Cetus profile {profile!r} timed out after "
                        f"{self.timeout_seconds:g} seconds. stdout: {stdout} stderr: {stderr}"
                    ) from exc
            except OSError as exc:
                raise CetusOptimizationError(f"Could not run Cetus: {exc}") from exc

            if process.returncode != 0:
                raise CetusOptimizationError(
                    f"Cetus profile {profile!r} failed with exit code "
                    f"{process.returncode}. stdout: {stdout} stderr: {stderr}"
                )

            transformed_file = transformed_dir / staged_source.name
            if not transformed_file.is_file():
                raise CetusOptimizationError(
                    f"Cetus exited successfully but did not create the expected output "
                    f"file {transformed_file}. stdout: {stdout} "
                    f"stderr: {stderr}"
                )

            if base is None:
                output_path = transformed_file.resolve()
            else:
                try:
                    base.mkdir(parents=True, exist_ok=True)
                    result_dir = Path(tempfile.mkdtemp(prefix="cetus-", dir=base))
                    output_path = result_dir / transformed_file.name
                    shutil.copy2(transformed_file, output_path)
                except OSError as exc:
                    raise CetusOptimizationError(
                        f"Could not place transformed output under {base}: {exc}"
                    ) from exc

            return CetusOptimizationResult(
                input_path=source,
                output_path=output_path.resolve(),
                profile=profile,
                returncode=process.returncode,
                stdout=stdout,
                stderr=stderr,
                command=command,
            )
        except BaseException:
            # Keep the successful default output directory, but do not leave
            # half-written work after a failed run or after copying to output_dir.
            shutil.rmtree(work_dir, ignore_errors=True)
            raise
        finally:
            if base is not None:
                shutil.rmtree(work_dir, ignore_errors=True)


def _decode_output(output: str | bytes | None) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode(errors="replace")
    return output
