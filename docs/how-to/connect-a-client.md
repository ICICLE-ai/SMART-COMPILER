# Connect a conversational or MCP client

Start and verify the SMART server before connecting a client. You can use the bundled CLI **or** another MCP client; starting the bundled CLI is not a prerequisite for an editor's MCP connection.

For the local HTTP server:

```text
REST/health: http://127.0.0.1:8000/health
MCP SSE:     http://127.0.0.1:8000/sse
```

An MCP client running on the Compose network uses `http://server:8000/sse`. A remote client needs the reachable server address. Inside a container, `localhost` refers to that container.

## Docker client with optional Ollama

The default Compose deployment starts only SMART's server. Enable the `llm` profile to start Ollama, initialize the custom model, and start the interactive client:

```bash
LLM_HOST=http://ollama:11434/v1 \
LLM_MODEL=llama3.1-smart-compiler:latest \
OPENAI_API_KEY= \
docker compose --profile llm up -d --build

docker compose --profile llm logs --tail=50 ollama_init
docker compose attach --sig-proxy=false client
```

The first initialization downloads the base Llama model if the custom model is absent. The explicit values above override native-client settings that may be present in the host's `.env`.

At `You:`, enter:

```text
Please optimize the C file at /app/Testing_Examples/01_vector_scale.c using the parallel profile.
```

Use **Ctrl-p, Ctrl-q** to detach from the client while leaving it running. Typing `quit` stops the client; start the existing container again with `docker compose --profile llm start client` so its configured model endpoint is preserved.

No client port publication is needed: the client makes outbound connections to SMART and the model host.

## Docker client with an existing model service

Start the server and build the client:

```bash
docker compose up -d --build server
docker compose --profile llm build client
```

Then launch only the client, without starting its optional Ollama dependencies:

```bash
docker compose --profile llm run --rm --no-deps \
  -e LLM_HOST=https://provider.example/v1 \
  -e LLM_MODEL=your-tool-capable-model-id \
  client
```

Supply `OPENAI_API_KEY` privately in your shell or Compose environment when that provider requires it. Local services and proxies that perform authentication themselves may need no client key.

For an OpenAI-compatible reverse proxy on the same **Docker Desktop** host, a configuration example is:

```bash
docker compose --profile llm run --rm --no-deps \
  -e LLM_HOST=http://host.docker.internal:6188/v1 \
  -e LLM_MODEL=openai/gpt-oss-20b \
  -e OPENAI_API_KEY= \
  client
```

Start your proxy separately with its own authentication configuration. These example IDs and endpoints must match the service you actually run. `host.docker.internal` is a Docker Desktop host address; on other engines, use a host address reachable from the container or configure a host-gateway mapping.

## Native CLI with local Ollama

Follow [native server setup](run-native.md), then keep the server running in its own terminal.

Install Ollama using its [official instructions](https://ollama.com/download). Start its service if it is not already running, then create the model from the SMART checkout:

```bash
ollama pull llama3.1
ollama create llama3.1-smart-compiler -f ollama-smart-compiler-Modelfile
```

In the terminal used for the SMART client:

```bash
cd /absolute/path/to/SMART-COMPILER
export MCP_SERVER_URL=http://127.0.0.1:8000/sse
export LLM_HOST=http://localhost:11434
export LLM_MODEL=llama3.1-smart-compiler:latest
export ALLOWED_PATHS="file://$PWD/Testing_Examples"
uv run python src/run_client.py
```

Use the native server's actual absolute source path in a request:

```text
Please optimize the C file at /absolute/path/to/SMART-COMPILER/Testing_Examples/01_vector_scale.c using the parallel profile.
```

If the server runs on a different machine, that path must exist on the server.

## Native CLI with an OpenAI-compatible host

Set the existing client variables before starting the same CLI:

```dotenv
MCP_SERVER_URL=http://127.0.0.1:8000/sse
LLM_HOST=https://provider.example/v1
LLM_MODEL=your-tool-capable-model-id
ALLOWED_PATHS=file:///absolute/path/to/server/source-directory
```

Set `OPENAI_API_KEY` only if the provider requires a credential. For OpenAI itself, use `LLM_HOST=https://api.openai.com/v1` and an available tool-capable model ID. The client uses OpenAI's Responses API for that host and Chat Completions for other hosts.

## External HTTP MCP clients

Configure an SSE-capable MCP client to connect to the **server's** `/sse` endpoint. The server must use:

```dotenv
MCP_SERVER_TRANSPORT=sse
ENABLE_REST_API=true
```

The external client's model configuration belongs to that client. SMART's bundled CLI does not need to run alongside it.

The screenshots below show earlier editor sessions. Interface labels and model names may differ in your installation; use your running SMART server's address. Paths and timings shown in a profiling report belong to that example session.

### VS Code / GitHub Copilot example

1. Open the Command Palette and choose **MCP: Add Server…**.

   ![VS Code Command Palette showing MCP: Add Server](../images/addServer.png)

2. Choose the HTTP connection option and enter SMART's SSE endpoint, such as `http://127.0.0.1:8000/sse` for an editor on the same machine as the server.

   ![VS Code MCP transport menu showing the HTTP or Server-Sent Events option](../images/httpMCP.png)

3. Open Copilot Chat and select **Agent** mode so the client can call SMART's tools.

   ![Copilot Chat menu with Agent mode selected](../images/Agent.png)

4. Type a request into Copilot Chat, for example:

   ```text
   Create a small Python matrix multiplication example, profile it using SMART's profile_code_snippet tool, and explain the profiling report.
   ```

   ![Copilot response after invoking SMART's profiling tool for a Python matrix multiplication example](../images/usecaseCopilot.png)

### Cursor profiling example

Configure Cursor's MCP connection with the running SMART server's SSE URL. This example follows a Python matrix multiplication snippet from generation through profiling; enter requests in Cursor's chat.

1. Check that Cursor lists the SMART MCP connection and its enabled tools.

   ![Cursor showing the enabled smart_compiler MCP connection](../images/use_case_1_1.png)

2. Ask Cursor to generate a small Python matrix multiplication example.

   ![Cursor generating a small Python matrix multiplication snippet](../images/use_case_1_2.png)

3. Ask it to profile the snippet using SMART's `profile_code_snippet` tool and inspect the returned report.

   ![Cursor invoking profile_code_snippet and summarizing the small example's profiling output](../images/use_case_1_3.png)

4. Expand the example to larger matrices when you want to investigate how the workload changes.

   ![Cursor expanding the example to multiply two 1000 by 1000 matrices](../images/use_case_1_4.png)

5. Profile the larger example with the same tool.

   ![Cursor invoking profile_code_snippet for the larger matrix example and displaying its output](../images/use_case_1_5.png)

6. Review the client's interpretation of the profiling report. Suggestions and comparisons with other implementations are model commentary, rather than additional benchmark measurements.

   ![Cursor interpreting the profiling results and suggesting performance improvements](../images/use_case_1_6.png)

## Clients that launch a stdio MCP server

A stdio client launches its own SMART process. Set `MCP_SERVER_TRANSPORT=stdio` and `ENABLE_REST_API=false`; do not give that client an SSE URL for this process.

For a client using a command/args/env MCP configuration, the entry can be:

```json
{
  "mcpServers": {
    "smart-compiler": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/SMART-COMPILER",
        "run",
        "python",
        "src/run_server.py",
        "stdio"
      ],
      "env": {
        "MCP_SERVER_TRANSPORT": "stdio",
        "ENABLE_REST_API": "false",
        "CETUS": "/absolute/path/to/The-Cetus-Project/bin/cetus",
        "CETUS_PROFILES_FILE": "/absolute/path/to/SMART-COMPILER/config/profiles.json",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

Use a complete native installation and adjust paths to that server machine. Application logs go to stderr so stdout remains available for MCP messages.

See [configuration](../reference/configuration.md) and [troubleshooting](../troubleshooting.md).

[Back to README](../../README.md)
