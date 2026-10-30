# SMART Compiler 3.0

SMART Compiler lets you request **C optimization** and **C/Python profiling** in natural language. Its conversational client connects a tool-capable language model to SMART's Model Context Protocol (MCP) tools, which run Cetus and the profilers. You can also call the server directly through its REST API for automation and testing.

This release adds Cetus profiles for OpenMP parallelization, parallel-aware tiling, loop interchange, and reuse-vector analysis. The Docker server image includes a pinned Cetus `release/3.0` build and **Java 21**. Native installations build Cetus separately.

**Tags:** Software, CI4AI

### License

[![License: BSD 3-Clause](https://img.shields.io/badge/License-BSD--3--Clause-blue.svg)](LICENSE)

SMART Compiler uses the [BSD 3-Clause license](LICENSE). Cetus retains its upstream licensing and notices in the bundled checkout.

## References

- [Cetus compiler source and documentation](https://github.com/PAROT-Udel/The-Cetus-Project)
- [Docker Compose documentation](https://docs.docker.com/compose/)
- [uv installation and dependency management](https://docs.astral.sh/uv/)
- [Ollama documentation](https://docs.ollama.com/) for the optional local model service
- [Model Context Protocol documentation](https://modelcontextprotocol.io/)
- [IMT integration diagram 1](https://drive.google.com/file/d/1S5gRxw_vizR1XnmbiZnAH1yZnkB8Ep0_/view?usp=drive_link)
- [IMT integration diagram 2](https://drive.google.com/file/d/1tgCcINlzBUe6A1PCNX6R_ftAnb9WidcA/view?usp=sharing)
- [Diátaxis](https://diataxis.fr/), the framework used to separate tutorials, task guides, explanation, and technical reference

## Acknowledgements

*National Science Foundation (NSF) funded AI institute for Intelligent Cyberinfrastructure with Computational Learning in the Environment (ICICLE) (OAC 2112606)*

## Issue reporting

Report bugs, setup failures, and documentation problems through [SMART Compiler GitHub Issues](https://github.com/ICICLE-ai/SMART-COMPILER/issues). Include:

- The SMART revision, Docker or native setup, operating system, and architecture.
- The command or prompt, optimization profile, and a minimal input that reproduces the issue.
- Relevant error output and, for compiler failures, the Java and Cetus versions. Redact API keys and tokens from logs.

Check [troubleshooting](docs/troubleshooting.md) for known Java, networking, source-path, and parser errors before reporting a new issue.

---

# Tutorials

## Optimize code with a natural-language request

**Goal:** type a request into SMART's conversational client and receive optimized C code.

The example below uses Docker and a local Ollama model. **Prerequisites:** Docker Engine/Desktop with Compose and a SMART-COMPILER checkout. Docker supplies the server, Cetus, Java 21, the model service, and the client; this local-model route needs no API key.

If you already have a native SMART server or another model host, use the [native client instructions below](#use-a-native-client-or-another-model-host) or the [client connection guide](docs/how-to/connect-a-client.md).

For a better natural-language experience, we recommend a model with strong instruction-following and tool-calling capabilities. More capable models can help SMART interpret your requests and use the optimization and profiling tools more reliably.

### 1. Start SMART, the model service, and the client

Run this from your SMART-COMPILER checkout:

```bash
LLM_HOST=http://ollama:11434/v1 \
LLM_MODEL=llama3.1-smart-compiler:latest \
OPENAI_API_KEY= \
docker compose --profile llm up -d --build

docker compose --profile llm ps -a
docker compose --profile llm logs --tail=50 ollama_init
```

The first initialization downloads the base Llama model and creates `llama3.1-smart-compiler`. Wait for the server to become healthy and `ollama_init` to finish successfully before continuing. The explicit model settings above keep this Docker example independent of native-client settings in a host `.env`.

### 2. Open the chat terminal

Attach to the running interactive client:

```bash
docker compose attach --sig-proxy=false client
```

Enter natural-language requests in this attached terminal at the client's **`You:`** prompt. The client may already be waiting for input when you attach, so the prompt may have been printed before attachment. If the terminal is blank, type your request and press Enter; subsequent turns will display `You:`.

### 3. Type your optimization request at `You:`

The client prints the `You:` prefix; type the message after it, or start typing if the initial prompt is not visible:

```text
You: Please optimize the C file at /app/Testing_Examples/01_vector_scale.c using the parallel profile.
```

The model can read the file through SMART's MCP tools and call the optimization tool. Cetus runs inside the SMART server, and the client displays the returned C code in the conversation. Save that returned text if you want a file; MCP optimization does not create a persistent REST task result.

**Your prompt → language model → MCP tools → Cetus → optimized code in the client.**

The `/app/Testing_Examples` path is inside the Docker server. For your own C files, [mount their directory into the server](docs/how-to/run-with-docker.md#make-host-source-files-available) and use the server-visible path in your prompt. See [available profiles](#available-optimization-profiles) for other optimization choices.

Use **Ctrl-p, Ctrl-q** to detach and return to your shell while leaving the client running, or type `quit` to stop the client. The [client guide](docs/how-to/connect-a-client.md) explains how to restart it. The REST and shell-script examples below are separate automated runs you can perform from your shell.

### Use a native client or another model host

Complete the [native setup](docs/how-to/run-native.md) and [client configuration](docs/how-to/connect-a-client.md) first. Keep the SMART server and chosen model service running. Configure `MCP_SERVER_URL`, `LLM_HOST`, and `LLM_MODEL` for those services; set `OPENAI_API_KEY` only when the provider requires it.

In another terminal, from the SMART-COMPILER project root, start the client:

```bash
uv run --env-file .env python src/run_client.py
```

At its **`You:`** prompt, use the file's actual absolute path on the server. Replace the placeholder prefix in this example:

```text
You: Please optimize the C file at /absolute/path/to/SMART-COMPILER/Testing_Examples/01_vector_scale.c using the parallel profile.
```

For a Docker client using an existing model service instead of the bundled Ollama service, follow [Docker client with an existing model service](docs/how-to/connect-a-client.md#docker-client-with-an-existing-model-service). Requests are entered at the same `You:` prompt.

## REST API and automated validation

Use this route for direct API access and repeatable checks. These requests and `.sh` scripts call SMART's REST API without an LLM or a natural-language prompt.

Run the following commands at your **shell prompt**, after detaching from or quitting the conversational client. They assume the SMART-COMPILER checkout as the working directory and require curl on the host.

If you completed the Docker conversation above, the server is already running. Otherwise, start the server-only deployment:

```bash
docker compose up -d --build
```

Check the REST endpoint and bundled compiler:

```bash
curl --fail http://127.0.0.1:8000/health

docker compose exec server java -version
docker compose exec server sh -lc '"$CETUS" -version'
```

If the health check runs before startup finishes, wait for `docker compose ps` to show a healthy server and retry it.

### Submit a REST request

This uploads a source file from the checkout on the machine running curl:

```bash
curl --fail-with-body -X POST http://127.0.0.1:8000/tasks \
  -F 'task_type=optimize' \
  -F 'language=c' \
  -F 'optimization_profile=parallel' \
  -F 'file=@Testing_Examples/01_vector_scale.c'
```

The response contains a task ID. Follow the [API reference](docs/reference/api.md) to poll its status and download the result.

### Run the automated `.sh` examples

The included runner makes its own REST optimization request, downloads the generated C, compiles the original and transformed programs, and compares their output:

```bash
docker compose exec -e OMP_NUM_THREADS=2 server sh -lc \
  'cd /app/Testing_Examples && SMART_URL=http://127.0.0.1:8000 ./run_01_vector_scale.sh'
```

Success includes:

```text
PASS 01_vector_scale.c [parallel]: checksum=14999950000
```

This verifies the example's output equivalence. Inspect the transformed C to confirm the intended transformation; measure timings separately when evaluating performance.

Continue with the [complete REST validation tutorial](docs/tutorials/first-optimization.md), including output retrieval and all eight runs.

---

# How-To Guides

## Choose a setup

| Setup | What you install on the server machine | Start here |
|---|---|---|
| Docker, recommended for a first conversation | Docker Engine/Desktop with Compose | [Natural-language tutorial](#optimize-code-with-a-natural-language-request) |
| Native Linux/WSL | Python 3.11+, uv, a C toolchain, and JDK 21 | [Native setup](docs/how-to/run-native.md) |
| Existing model host or external MCP client | A reachable model supporting tool calling, plus the running SMART server | [Connect a client](docs/how-to/connect-a-client.md) |

The Docker route needs **no host Java installation, host Cetus checkout, Ollama service, or API key** for direct REST optimization and classical profiling. Docker builds Cetus with JDK 21 and runs it with a Java 21 runtime.

Keep the native Cetus installation path free of spaces, including all parent directories. Its upstream build scripts and generated launcher do not support spaces in that path. SMART's project, input, profile, and result paths can contain spaces when quoted; see the [native build instructions](docs/how-to/run-native.md#3-build-the-pinned-cetus-checkout).

For native Linux/WSL, complete the [native setup](docs/how-to/run-native.md) first. With the server running on port 8000, run shell examples through `uv` so they can find the project's Python interpreter:

```bash
SMART_URL=http://127.0.0.1:8000 uv run bash Testing_Examples/run_01_vector_scale.sh
```

On macOS, native Cetus optimization can fail while preprocessing Apple SDK system headers, including inputs that use `<stdio.h>`. A successful `/health` response does not verify this compiler step. Use the [Docker setup](docs/how-to/run-with-docker.md) for affected inputs; see the [native macOS preprocessing limitation](docs/how-to/run-native.md#macos-preprocessing-limitation) for the observed errors.

## Complete a specific task

| Task | Guide |
|---|---|
| Build images, mount source files, or manage persistent results | [Run with Docker](docs/how-to/run-with-docker.md) |
| Install and run without Docker | [Run natively](docs/how-to/run-native.md) |
| Use the CLI, Ollama, another model host, or an external MCP client | [Connect a client](docs/how-to/connect-a-client.md) |
| Submit a profiling task, check its status, and retrieve its report in Postman | [Profile with Postman](docs/how-to/profile-with-postman.md) |
| Add a custom optimization profile | [Customize profiles](docs/reference/optimization-profiles.md#add-a-custom-profile) |
| Diagnose Java, networking, path, profile, or parsing errors | [Troubleshooting](docs/troubleshooting.md) |

## Where are my source files?

MCP file tools run **inside the SMART server**, so paths in prompts must be visible to that server.

| Source | Path used by the server |
|---|---|
| Checked-in examples in the Docker image | `/app/Testing_Examples/01_vector_scale.c` |
| Your directory mounted into the server | The mount destination you choose, such as `/workspace/input/main.c` |
| Native server | An absolute path on the machine running the server |

`/examples` is not a built-in alias. Mounting files only into a client container does not make them available to the server.

For REST requests, `curl -F 'file=@main.c'` reads `main.c` where curl runs and uploads its contents; a source mount is unnecessary. See [Docker source mounts](docs/how-to/run-with-docker.md#make-host-source-files-available).

---

# Explanation

The SMART server exposes compiler tools and owns the files those tools read. Cetus runs on that server and transforms C source according to its selected profile. A model host and conversational client are optional: direct REST optimization and classical profiling can call the tools without a model.

## Architecture diagram

![SMART Compiler architecture showing the conversational client, model service, MCP and REST APIs, compiler tools, and an external system](diagrams/architecture.png)

The diagram illustrates a local Ollama deployment. Other compatible model hosts can fill the model-service role; Cetus and the profilers run through the SMART server's tools. The [IMT integration diagrams](#references) show the connection with ICICLE Middleware and Tools.

The Docker image builds Cetus and supplies its Java 21 runtime together, keeping the compiler's embedded paths and Java compatibility consistent. A native installation supplies that compiler checkout and toolchain separately.

The bundled CLI and external MCP clients are alternative ways to connect to the server; an editor does not require the bundled CLI to run alongside it. See the [architecture explanation](docs/explanation/architecture.md) for component roles, request flow, input/header limitations, and the difference between correctness checks and performance measurement.

---

# Reference

| Technical reference | Contents |
|---|---|
| [Configuration](docs/reference/configuration.md) | Client/server environment variables, defaults, runtime paths, and update behavior |
| [Optimization profiles](docs/reference/optimization-profiles.md) | `profiles.json` fields, available profiles, custom entries, and tuning assumptions |
| [REST and MCP APIs](docs/reference/api.md) | Tool arguments, file uploads, task polling, downloads, and output persistence |

## Available optimization profiles

| Profile | Purpose |
|---|---|
| `parallel` | OpenMP parallelization, including dependence, privatization, and reduction analyses |
| `paw_tiling_nt` | Parallel-aware tiling using NT tile selection |
| `paw_tiling_lrw` | Parallel-aware tiling using LRW/FindB tile selection |
| `paw_tiling_fixed32` | Parallel-aware tiling with fixed tile size 32 |
| `reuse_analysis` | Parallelization with explicit reuse-vector analysis |
| `loop_interchange` | Loop interchange with OpenMP generation disabled |

These entries are editable in SMART's own `config/profiles.json`. Read the [profile schema and customization guide](docs/reference/optimization-profiles.md) before changing them. Upstream Cetus also supports subscripted-subscript analysis; SMART does not currently ship a dedicated profile or example for that analysis.
