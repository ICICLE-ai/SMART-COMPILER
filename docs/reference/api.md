# REST and MCP task reference

The HTTP server exposes REST endpoints at `http://127.0.0.1:8000` and MCP at `http://127.0.0.1:8000/sse` in the local walkthrough. Container clients on the Compose network use `http://server:8000/sse`.

## REST optimization

From the SMART-COMPILER checkout on the machine running curl:

```bash
curl --fail-with-body -X POST http://127.0.0.1:8000/tasks \
  -F 'task_type=optimize' \
  -F 'language=c' \
  -F 'optimization_profile=parallel' \
  -F 'file=@Testing_Examples/01_vector_scale.c'
```

The API reads the uploaded bytes. It does not interpret `file=@...` as a path inside the server.

The response includes `task_id`, `task_status`, and `task_result`. Poll the returned ID:

```bash
curl --fail http://127.0.0.1:8000/tasks/REPLACE_WITH_TASK_ID
```

States are `pending`, `running`, `completed`, and `failed`. On completion, copy `task_result.file_path`:

```bash
FILE_PATH='REPLACE_WITH_TASK_RESULT_FILE_PATH'
curl --fail --get http://127.0.0.1:8000/files/download \
  --data-urlencode "file_path=$FILE_PATH" \
  --output optimized.c
```

On failure, inspect `task_result.error` and the server log. The [first optimization tutorial](../tutorials/first-optimization.md) uses a script that performs the entire submit/poll/download/check sequence.

Optimization is currently available for **C** files. The selected profile ID must exist in the server's [profiles JSON](optimization-profiles.md).

## REST profiling

For a self-contained C program:

```bash
curl --fail-with-body -X POST http://127.0.0.1:8000/tasks \
  -F 'task_type=profile' \
  -F 'language=c' \
  -F 'file=@Testing_Examples/01_vector_scale.c'
```

For Python, use `language=python` and upload a `.py` file. Profile tasks use the same polling and download workflow. C profiling uses GNU GCC/gprof; Python profiling uses cProfile. Program execution and required inputs occur on the server.

Optional `runtime_options` is a JSON multipart field for execution/compilation options. See the current schema at `http://127.0.0.1:8000/docs` before configuring arguments, working directories, or environment values.

## MCP tools

| Tool | Input | Result |
|---|---|---|
| `get_file_content` | `path`, visible on the server | File text or a diagnostic |
| `list_files_in_directory` | Server-visible directory `path` | File names or a diagnostic |
| `optimize_code_snippet` | C `code_snippet`; optional `optimization_profile`, default `parallel` | Generated C text |
| `profile_code_snippet` | Source `code_snippet` and `language` (`c` or `python`) | Profiling report text |

Example optimizer arguments:

```json
{
  "code_snippet": "#include <stdio.h>\nint main(void) { return 0; }\n",
  "optimization_profile": "parallel"
}
```

The optimizer expects C source, not a filename in `code_snippet`. A conversational path request should first call `get_file_content`, then pass its returned source to the optimizer.

MCP optimization returns text and removes its temporary work directory after reading the result. It does not create a persistent REST task or a downloadable task record. MCP profiling retains intermediate files under `tmp/<uuid>/` in the server working directory; REST inputs/results are stored under `files/<uuid>/`.

Current requests stage one file at a time; adjacent project headers are not collected automatically.

[Back to README](../../README.md)
