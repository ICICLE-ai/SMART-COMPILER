# Configuration reference

Run native commands from the SMART-COMPILER project root. The entry points load a private root `.env` file through python-dotenv. Existing shell environment values take precedence. Copy a template only when creating a new file; edit an existing `.env` instead of overwriting it.

Docker does not load a native `.env` into the image. `.dockerignore` excludes private environment files from builds. Compose may still read a host `.env` for interpolation, so use the explicit container endpoint values in the [client guide](../how-to/connect-a-client.md).

## Server settings

| Variable | Meaning | Native default | Docker/Compose value |
|---|---|---|---|
| `HOST` | Address on which the server listens | `0.0.0.0`; use `127.0.0.1` for a local native server | `0.0.0.0` inside the container |
| `PORT` | HTTP port inside the server environment | `8000` | `8000`; Compose publishes it at host `127.0.0.1:8000` |
| `MCP_SERVER_TRANSPORT` | MCP transport: `sse` or `stdio` | `sse` | `sse` |
| `ENABLE_REST_API` | Enable the HTTP application; also required to mount SSE | `false` | `true` |
| `LOG_LEVEL` | Application log level | `INFO` | `INFO` |
| `CETUS` | Executable compiler launcher | Required for optimization | `/opt/cetus/bin/cetus` |
| `CETUS_PROFILES_FILE` | Active profile JSON on the server | Required for optimization | `/app/config/profiles.json` |
| `CETUS_TIMEOUT_SECONDS` | Positive Cetus subprocess timeout, in seconds | `300` | `300` when unset |

`ENABLE_REST_API` accepts `true/1/yes/on` as true, ignoring case and surrounding whitespace. `false/0/off`, an empty value, and other values are false. For an HTTP MCP endpoint, use **both** `MCP_SERVER_TRANSPORT=sse` and `ENABLE_REST_API=true`.

The server reads `HOST` and `PORT`. The older `MCP_SERVER_HOST` and `MCP_SERVER_PORT` names do not configure its listener.

## Client settings

| Variable | Meaning | Example |
|---|---|---|
| `MCP_SERVER_URL` | Reachable HTTP MCP endpoint, including `/sse` | Native: `http://127.0.0.1:8000/sse`; Compose client: `http://server:8000/sse` |
| `LLM_HOST` | Model service base URL | Native Ollama: `http://localhost:11434`; OpenAI-compatible service: `https://provider.example/v1` |
| `LLM_MODEL` | Exact deployed model ID | `llama3.1-smart-compiler:latest` or an ID advertised by your provider |
| `OPENAI_API_KEY` | Optional provider credential; required for OpenAI's API | Leave empty for local Ollama or a proxy that handles authentication |
| `ALLOWED_PATHS` | Single advertised MCP root, as a file URL | `file:///app/Testing_Examples` |
| `LOG_LEVEL` | Client logging level | `INFO` |

For OpenAI, the client uses the Responses API at `https://api.openai.com/v1`. Other hosts use Chat Completions. The endpoint/model must support tool calling for conversational compiler requests.

The native Ollama client is selected for a loopback host on port 11434 without a `/v1` suffix. For Ollama reached by a container service name, use its compatible endpoint `http://ollama:11434/v1`, as configured in Compose. A bearer credential, when supplied, is sent to the configured non-loopback model host; use the credential for that service.

`ALLOWED_PATHS` advertises a root to MCP. It does not mount a directory, transfer client-local files, or enforce a server-side filesystem allowlist in the current file tools.

## Legacy and internal Ollama settings

`OLLAMA_HOST` and `OLLAMA_MODEL` remain in compatibility/internal profiler paths. Use `LLM_HOST` and `LLM_MODEL` for the conversational client. The direct Cetus optimizer and classical C/Python profiling do not require an Ollama service.

## Example runner settings

| Variable | Meaning | Default |
|---|---|---|
| `SMART_URL` | REST server URL used by the shell runners | `http://127.0.0.1:18000` |
| `SMART_TASK_TIMEOUT_SECONDS` | Maximum time the runner polls a task | `360` |
| `SMART_EXAMPLE_RESULTS_DIR` | Runner's downloaded C, binaries, and output captures | `/tmp/smart-compiler-example-results` |
| `OMP_NUM_THREADS` | OpenMP runtime thread count for compiled examples | Chosen by the OpenMP runtime if unset |

The new Docker/native walkthroughs use port 8000, so they explicitly set `SMART_URL=http://127.0.0.1:8000`. This polling timeout is separate from the server's Cetus subprocess timeout.

## When do edits take effect?

- Restart a native process after changing its environment.
- Recreate a Compose service after changing its environment or mount configuration.
- The active profile JSON is read on every optimization request. For an edited bind-mounted file, recreating the server also handles editors that replace the file inode.
- Rebuild an image to change source/configuration copied into it, unless that path is overridden by a runtime mount.

[Back to README](../../README.md)
