"""Check REST and both MCP transports against real child server processes.

Run in the server image:
    docker run --rm --entrypoint python smart-server:v2 tests/transport_smoke.py
No LLM service or API key is used.
"""

from __future__ import annotations

import asyncio
from contextlib import redirect_stderr
from datetime import timedelta
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER_SCRIPT = PROJECT_ROOT / "src/run_server.py"
EXAMPLE = PROJECT_ROOT / "Testing_Examples/01_vector_scale.c"
sys.path.insert(0, str(PROJECT_ROOT / "src"))

EXPECTED_TOOLS = {
    "get_file_content",
    "list_files_in_directory",
    "optimize_code_snippet",
    "profile_code_snippet",
}
TIMEOUT = 90
C_PROFILE_SOURCE = b"""#include <stdio.h>
int main(void) {
    int total = 0;
    for (int i = 0; i < 100; ++i) total += i;
    printf("%d\\n", total);
    return total == 4950 ? 0 : 1;
}
"""
PYTHON_PROFILE_SOURCE = b"total = sum(range(100))\nassert total == 4950\nprint(total)\n"


class SmokeFailure(RuntimeError):
    """A failed protocol or task check."""


def tail(text: str) -> str:
    return "\n".join(text.strip().splitlines()[-30:])[-5000:]


def describe_error(error: BaseException) -> str:
    if isinstance(error, BaseExceptionGroup):
        return "\n".join(describe_error(item) for item in error.exceptions)
    return f"{type(error).__name__}: {error}"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def assert_openmp(source: str, label: str) -> None:
    require(
        re.search(r"#\s*pragma\s+omp\s+parallel\s+for\b", source) is not None,
        f"{label} did not return C containing an OpenMP parallel loop",
    )


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def stop_server(process: subprocess.Popen[bytes]) -> None:
    # Cetus starts a separate process group. Include descendants when stopping
    # an interrupted test so a compiler timeout cannot leave Java behind.
    parents: dict[int, int] = {}
    for status in Path("/proc").glob("[0-9]*/status"):
        try:
            match = re.search(r"^PPid:\s+(\d+)", status.read_text(), re.M)
            if match:
                parents[int(status.parent.name)] = int(match.group(1))
        except (OSError, ValueError):
            continue
    descendants = {process.pid}
    while True:
        expanded = descendants | {pid for pid, parent in parents.items() if parent in descendants}
        if expanded == descendants:
            break
        descendants = expanded
    for pid in descendants:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    for pid in descendants:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=5)


async def wait_for_health(client: httpx.AsyncClient, process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + TIMEOUT
    while time.monotonic() < deadline:
        require(process.poll() is None, "HTTP server exited before becoming healthy")
        try:
            response = await client.get("/health")
            if response.status_code == 200 and response.json() == {"status": "ok"}:
                return
        except (httpx.HTTPError, ValueError):
            pass
        await asyncio.sleep(0.25)
    raise SmokeFailure("HTTP health check timed out after 90s")


async def rest_task(
    client: httpx.AsyncClient,
    task_type: str,
    language: str,
    filename: str,
    source: bytes,
) -> str:
    label = f"REST {task_type} {language}"
    response = await client.post(
        "/tasks",
        data={
            "task_type": task_type,
            "language": language,
            "optimization_profile": "parallel",
        },
        files={"file": (filename, source, "application/octet-stream")},
    )
    require(response.status_code == 201, f"{label} submission HTTP {response.status_code}: {tail(response.text)}")
    task_id = response.json().get("task_id")
    require(isinstance(task_id, str) and bool(task_id), f"{label} did not return a task id")
    deadline = time.monotonic() + TIMEOUT
    while time.monotonic() < deadline:
        response = await client.get(f"/tasks/{task_id}")
        response.raise_for_status()
        task = response.json()
        status = task.get("task_status")
        result = task.get("task_result") or {}
        if status == "completed":
            require(not result.get("error"), f"{label} completed with an error: {result.get('error')}")
            path = result.get("file_path")
            require(isinstance(path, str) and bool(path), f"{label} completed without an output path")
            download = await client.get("/files/download", params={"file_path": path})
            download.raise_for_status()
            require(bool(download.content.strip()), f"{label} returned an empty output file")
            return download.text
        require(status != "failed", f"{label} failed: {tail(str(result.get('error')))}")
        require(status in {"pending", "running"}, f"{label} returned unknown status {status!r}")
        await asyncio.sleep(0.25)
    raise SmokeFailure(f"{label} task timed out after 90s")


async def check_rest(client: httpx.AsyncClient) -> None:
    optimized, c_profile, python_profile = await asyncio.gather(
        rest_task(client, "optimize", "c", EXAMPLE.name, EXAMPLE.read_bytes()),
        rest_task(client, "profile", "c", "smoke_profile.c", C_PROFILE_SOURCE),
        rest_task(client, "profile", "python", "smoke_profile.py", PYTHON_PROFILE_SOURCE),
    )
    assert_openmp(optimized, "REST optimization")
    require("Flat profile" in c_profile, "REST C profiling did not return a GNU gprof report")
    require("function calls" in python_profile, "REST Python profiling did not return cProfile statistics")
    print("PASS REST optimize: upload, poll, download OpenMP C", flush=True)
    print("PASS REST C and Python profile: upload, poll, download reports", flush=True)


def tool_text(result: Any, label: str) -> str:
    text = "\n".join(item.text for item in result.content if item.type == "text")
    require(not getattr(result, "isError", False), f"{label} returned an MCP tool error: {tail(text)}")
    require(bool(text), f"{label} did not return text")
    return text


async def check_sse(log_path: Path) -> None:
    # This is the production client, but only its MCP connection is exercised.
    # The unused LLM endpoint is loopback and no query/API method is called.
    with log_path.open("w", buffering=1) as log, redirect_stderr(log):
        from client.openai.client import OpenAIResponsesMCPClient

        client = OpenAIResponsesMCPClient()
        async with asyncio.timeout(TIMEOUT):
            try:
                await client.connect_to_server()
                require(len(client.tools) == 4 and {tool["name"] for tool in client.tools} == EXPECTED_TOOLS, "MCP SSE tool inventory differs from the four supported tools")
                require(client.session is not None, "MCP SSE session did not initialize")
                original = EXAMPLE.read_text(encoding="utf-8")
                fetched = await client.session.call_tool("get_file_content", {"path": str(EXAMPLE)})
                require(tool_text(fetched, "MCP SSE file read") == original, "MCP SSE file content differs from the checked-in source")
                optimized = await client.session.call_tool(
                    "optimize_code_snippet",
                    {"code_snippet": original, "optimization_profile": "parallel"},
                )
                assert_openmp(tool_text(optimized, "MCP SSE optimization"), "MCP SSE optimization")
            finally:
                await client.cleanup()
    print("PASS MCP SSE: production client, four tools, file read, real Cetus optimization", flush=True)


async def check_stdio(environment: dict[str, str], log_path: Path) -> None:
    stdio_environment = dict(environment)
    stdio_environment.update(MCP_SERVER_TRANSPORT="stdio", ENABLE_REST_API="false")
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_SCRIPT), "stdio"],
        cwd=str(PROJECT_ROOT),
        env=stdio_environment,
    )
    # PORT deliberately remains occupied by the HTTP child. A string "false"
    # must disable REST rather than launch another listener on that port.
    async with asyncio.timeout(TIMEOUT):
        with log_path.open("w", buffering=1) as log:
            async with stdio_client(parameters, errlog=log) as (read, write):
                async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=TIMEOUT)) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    require(len(tools.tools) == 4 and {tool.name for tool in tools.tools} == EXPECTED_TOOLS, "MCP stdio tool inventory differs from the four supported tools")
                    await asyncio.sleep(0.2)
                    result = await session.call_tool("get_file_content", {"path": str(EXAMPLE)})
                    require(tool_text(result, "MCP stdio file read") == EXAMPLE.read_text(encoding="utf-8"), "MCP stdio file content differs from the checked-in source")
    require(bool(log_path.read_text().strip()), "MCP stdio did not emit diagnostics to stderr")
    print("PASS MCP stdio: initialization, four tools, clean protocol stdout, REST disabled", flush=True)


async def run_checks(
    url: str,
    environment: dict[str, str],
    process: subprocess.Popen[bytes],
    scratch: Path,
) -> None:
    async with httpx.AsyncClient(base_url=url, timeout=10, trust_env=False) as client:
        await wait_for_health(client, process)
        print("PASS HTTP child health on random loopback port", flush=True)
        await check_rest(client)
        await check_sse(scratch / "sse-client.log")
        await check_stdio(environment, scratch / "stdio-server.log")
        require(process.poll() is None, "HTTP server exited during MCP checks")
        response = await client.get("/health")
        require(response.status_code == 200, "HTTP server was not healthy after stdio checks")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="smart-transport-smoke-") as temporary:
        scratch = Path(temporary)
        (scratch / "db").mkdir()
        port = free_port()
        url = f"http://127.0.0.1:{port}"
        environment = dict(os.environ)
        environment.update(
            HOST="127.0.0.1",
            PORT=str(port),
            MCP_SERVER_TRANSPORT="sse",
            ENABLE_REST_API="true",
            LOG_LEVEL="INFO",
            PYTHONDONTWRITEBYTECODE="1",
            MCP_SERVER_URL=url + "/sse",
            ALLOWED_PATHS=EXAMPLE.parent.as_uri(),
            LLM_HOST="http://127.0.0.1:9/v1",
            LLM_MODEL="transport-smoke-no-llm",
            OPENAI_API_KEY="",
            OLLAMA_HOST="http://127.0.0.1:9",
            HTTP_PROXY="",
            HTTPS_PROXY="",
            ALL_PROXY="",
            NO_PROXY="127.0.0.1,localhost",
        )
        # The SSE client reads its settings from the current process.
        previous_environment = dict(os.environ)
        os.environ.update(environment)
        process: subprocess.Popen[bytes] | None = None
        try:
            with (scratch / "http-server.log").open("wb") as log:
                process = subprocess.Popen(
                    [sys.executable, str(SERVER_SCRIPT)],
                    cwd=scratch,
                    env=environment,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                asyncio.run(run_checks(url, environment, process, scratch))
            print("PASS transport smoke: REST, MCP SSE, MCP stdio; no LLM requests", flush=True)
            return 0
        except Exception as exc:
            print(f"FAIL {tail(describe_error(exc))}", file=sys.stderr, flush=True)
            for name in ("http-server.log", "sse-client.log", "stdio-server.log"):
                path = scratch / name
                if path.is_file():
                    print(f"{name} (tail):\n{tail(path.read_text(errors='replace'))}", file=sys.stderr)
            return 1
        finally:
            if process is not None:
                stop_server(process)
            os.environ.clear()
            os.environ.update(previous_environment)


if __name__ == "__main__":
    raise SystemExit(main())
