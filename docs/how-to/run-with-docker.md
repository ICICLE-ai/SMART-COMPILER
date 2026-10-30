# Run with Docker

Docker packages the SMART server, Cetus, Java, and the C profiling tools together. Install Docker with Docker Compose, then run the commands below from the SMART-COMPILER checkout. Your host does not need Python, a JDK, or a separate Cetus checkout for this route.

## Start the server

```bash
docker compose up -d --build
docker compose ps
```

The default Compose configuration starts the `server` service. Cetus optimization and classical profiling work without a model. The optional Ollama and interactive client services belong to the `llm` profile; see [Connect a client](connect-a-client.md) when you want them.

The first build downloads the base image, system packages, Python dependencies, and Cetus source. Once the server is healthy, check it from the host:

```bash
curl --fail --silent --show-error http://127.0.0.1:8000/health
```

The response is `{"status":"ok"}`. Compose publishes port 8000 on the host's loopback address. The REST documentation is at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), and the MCP SSE endpoint is `http://127.0.0.1:8000/sse`.

If the server is still starting, inspect its status and logs:

```bash
docker compose ps
docker compose logs --tail=100 server
```

## Check the bundled compiler

The server image uses Python 3.12 on Debian Trixie. A build stage compiles PAROT's Cetus `release/3.0` with a Java 21 JDK, pinned to commit `cebcc57b22d7eaed01b9420f7a76140e13aeeee4`. The runtime includes the Java 21 JRE, GCC with OpenMP support, `gprof` from binutils, GDB, and curl.

```bash
docker compose exec server java -version
docker compose exec server /opt/cetus/bin/cetus -version
docker compose exec server gcc --version
docker compose exec server gprof --version
```

The image sets `CETUS=/opt/cetus/bin/cetus` and `CETUS_PROFILES_FILE=/app/config/profiles.json`. The whole built Cetus checkout stays at `/opt/cetus` because its generated launcher embeds absolute jar paths. The build checks for the compiled driver and jar entry and invokes the launcher before producing the runtime image.

To inspect the pinned revision label:

```bash
docker image inspect smart_server:latest \
  --format '{{ index .Config.Labels "io.smart-compiler.cetus.revision" }}'
```

The profiles come from this project's `config/profiles.json`, copied into the image. After editing that file, rebuild the service with `docker compose up -d --build server`. See [Optimization profiles](../reference/optimization-profiles.md) for their flags and [Configuration](../reference/configuration.md) for environment settings.

The upstream launcher may print a legacy online-update message mentioning Cetus 1.4.4. Use the pinned revision label above to identify this build instead of changing the compiler based on that message.

## Run an included example

The image contains the C inputs and runners under `/app/Testing_Examples`. Run a runner inside the server container so it uses the bundled GNU compiler and OpenMP runtime:

```bash
docker compose exec -e OMP_NUM_THREADS=2 server sh -lc \
  'cd /app/Testing_Examples && SMART_URL=http://127.0.0.1:8000 ./run_01_vector_scale.sh'
```

The runner uploads its input, waits for the optimization task, downloads the transformed C, compiles both versions, and compares their output. A successful run prints `PASS`. The server URL here uses the container's own loopback address. These runners otherwise default to port 18000, so keep the `SMART_URL` override for this Compose setup.

Other runners in that directory exercise reductions, tiling, loop interchange, reuse analysis, and a loop-carried dependency. See [First optimization](../tutorials/first-optimization.md) for the full case catalog and workflow.

Runner artifacts default to `/tmp/smart-compiler-example-results` inside the container. To keep them in the persistent files volume, set their output directory explicitly:

```bash
docker compose exec -e OMP_NUM_THREADS=2 server sh -lc \
  'cd /app/Testing_Examples && SMART_URL=http://127.0.0.1:8000 SMART_EXAMPLE_RESULTS_DIR=/app/files/example-results ./run_01_vector_scale.sh'
```

## Make host source files available

MCP file tools read paths on the server's filesystem. An absolute path on your host is usable only when that directory is also mounted into the server. The built-in examples are already available at `/app/Testing_Examples`.

For your own inputs, create an override file outside the checkout. Replace `/absolute/path/to/c-sources` with an existing directory on your host:

```bash
cat > /tmp/smart-inputs.compose.yaml <<'YAML'
services:
  server:
    volumes:
      - /absolute/path/to/c-sources:/workspace/input:ro
YAML

docker compose -f docker-compose.yml -f /tmp/smart-inputs.compose.yaml up -d --build
```

Compose adds this input mount to the service's existing named volumes for files and databases. Use the same two `-f` arguments when applying this override again.

Ask an MCP client to list `/workspace/input`, read a file such as `/workspace/input/main.c`, and optimize its source with `optimize_code_snippet`. The read-only mount is sufficient: that tool writes the supplied source text to a separate temporary directory. For example, a host file `/absolute/path/to/c-sources/main.c` is addressed by the MCP file tools as `/workspace/input/main.c`.

An external MCP client connects to `http://127.0.0.1:8000/sse` from the host. The Compose client uses `http://server:8000/sse`. In both cases, paths passed to the server's file tools refer to the server container. Mounting a directory only in a client container does not make it visible to the server.

REST uploads transfer the source bytes and need no source-directory mount. Run this from the host, where the local file exists:

```bash
curl --fail-with-body http://127.0.0.1:8000/tasks \
  -F 'task_type=optimize' \
  -F 'language=c' \
  -F 'optimization_profile=parallel' \
  -F 'file=@/absolute/path/to/c-sources/main.c'
```

The upload path after `@` is read by the host's curl process. SMART stores the upload inside the container and returns a task ID. Follow [First optimization](../tutorials/first-optimization.md) to poll the task and download its result, or consult the [API reference](../reference/api.md).

## Keep results and stop the stack

Compose creates these named volumes:

| Volume | Server path | Contents |
|---|---|---|
| `server_files` | `/app/files` | REST uploads and artifacts produced alongside those uploads, including transformed C |
| `server_db` | `/app/db` | Task records and scheduler database |

MCP `optimize_code_snippet` returns transformed source as text. Its temporary input and output directories are removed after the call, so save the returned text in your client if you want a file. Container paths under `/tmp`, including the example runners' default result directory, are also temporary and do not survive container replacement.

To stop services while keeping their containers and volumes:

```bash
docker compose stop
```

To remove the containers and network while retaining named volumes:

```bash
docker compose down
```

The next `docker compose up -d` reuses those volumes. Adding `-v` to `docker compose down` deletes the stack's named volumes and their data, including model data if you enabled Ollama. Use that option only when you intend to discard them.

## Advanced: use another Cetus build

The bundled build is sufficient for normal use. To test another source revision in a new image, supply a full commit SHA as a build argument:

```bash
docker compose build --build-arg CETUS_REF=REPLACE_WITH_FULL_COMMIT_SHA server
docker compose up -d server
```

To use an already-built external checkout without rebuilding the image, mount the whole checkout and override `CETUS`. The mount target must match the absolute checkout path embedded in its `bin/cetus` launcher. For example, if that launcher was generated under `/home/me/The-Cetus-Project`, add this to a separate Compose override:

```yaml
services:
  server:
    environment:
      CETUS: /home/me/The-Cetus-Project/bin/cetus
    volumes:
      - /home/me/The-Cetus-Project:/home/me/The-Cetus-Project:ro
```

Apply it with `docker compose -f docker-compose.yml -f /path/to/cetus-override.yaml up -d server`. Keep the jars and launcher together, and use classes compatible with the image's Java 21 runtime. Check the external launcher with `docker compose exec server /home/me/The-Cetus-Project/bin/cetus -version` after applying the override. `CETUS_PROFILES_FILE` can remain `/app/config/profiles.json`.

See [Run natively](run-native.md) for building and configuring Cetus outside Docker, [Troubleshooting](../troubleshooting.md) for startup and compiler errors, or return to [README](../../README.md).
