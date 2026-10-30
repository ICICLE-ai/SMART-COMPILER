# Troubleshooting

Identify the stage that failed before changing the model, compiler, or deployment.

## Check the server and compiler separately

```bash
docker compose ps
docker compose logs --tail=100 server
curl --fail http://127.0.0.1:8000/health
docker compose exec server java -version
docker compose exec server sh -lc '"$CETUS" -version'
```

A successful HTTP health check confirms the application is reachable; it does not establish that Cetus can transform the requested input.

## Java cannot be found during a native build

Cetus's build needs a **JDK**, including `java`, `javac`, and `jar`. Recommend JDK 21 to match the Docker runtime. The Docker setup already provides its own Java toolchain.

On macOS with Homebrew OpenJDK 21:

```bash
export JAVA_HOME="$(brew --prefix openjdk@21)/libexec/openjdk.jdk/Contents/Home"
export PATH="$JAVA_HOME/bin:$PATH"
java -version
javac -version
jar --version
```

See [native setup](how-to/run-native.md) if the package is not installed. A Java installation inside another container does not provide a JDK to a native Mac terminal.

## UnsupportedClassVersionError

The JVM is present but cannot load the compiled Cetus class version. Class version `71` corresponds to Java 27; Java 21 supports versions through `65`.

The bundled image builds and runs Cetus with Java 21. For an external native/mounted checkout, select JDK 21 and rebuild the **actual checkout used by the server**:

```bash
cd /absolute/path/to/The-Cetus-Project
./build.sh clean && ./build.sh compile && ./build.sh bin
./bin/cetus -version
```

Ensure `java -version` and `javac -version` identify the selected toolchain first. Upstream's build can print wrapper-generation messages even after a compilation error, so executable presence alone is not a success check.

## Client connection fails or returns HTTP 404

- A connection error occurs before the MCP session starts: check the address, port, running server, and container network.
- A 404 may mean the URL lacks `/sse`, or the server is not running an SSE transport.
- Inside the Compose client, use `http://server:8000/sse`; `localhost` points to that client container.
- Use `MCP_SERVER_TRANSPORT=sse` and `ENABLE_REST_API=true` for HTTP MCP.

From the host, this bounded probe should establish a stream and then time out because SSE stays open:

```bash
curl -iN --max-time 3 http://127.0.0.1:8000/sse
```

If port 8000 is occupied, choose a different host port in a Compose override, leaving the container's port 8000 unchanged. For Compose versions supporting `!override`, for example:

```bash
cat > /tmp/smart-port.compose.yaml <<'YAML'
services:
  server:
    ports: !override
      - "127.0.0.1:18000:8000"
YAML
docker compose -f docker-compose.yml -f /tmp/smart-port.compose.yaml up -d
```

Use host URL `http://127.0.0.1:18000` afterward. Continue supplying both Compose files when managing that deployment.

## Source file or directory does not exist

MCP file tools read the **server's filesystem**:

```bash
docker compose exec server pwd
docker compose exec server ls -l /app/Testing_Examples/01_vector_scale.c
```

Use that container path in a prompt. A host directory becomes available through a server-side bind mount with an explicit destination. `/examples` does not exist automatically, and a client-only mount does not share files with the server. See [source mounting](how-to/run-with-docker.md#make-host-source-files-available).

REST `file=@...` is different: curl reads a file on its own machine and uploads its bytes.

## Missing or unknown optimization profile

```bash
docker compose exec server printenv CETUS_PROFILES_FILE
docker compose exec server python -m json.tool /app/config/profiles.json
```

If you changed `CETUS_PROFILES_FILE`, inspect that effective path instead. Request an exact top-level ID from the active JSON. A valid JSON file can still contain an invalid profile shape or unsupported Cetus arguments. See the [profile reference](reference/optimization-profiles.md).

## Cetus parser or header errors

If tool calling succeeded, Java started, and Cetus reports an ANTLR parsing error, the failure is in compiler input processing.

An observed older Alpine/musl deployment failed on `_Noreturn` in `stdlib.h`. The new image uses Debian/glibc and includes a standard-library-header smoke case. This does not imply support for every C dialect or header extension.

For that **specific** keyword failure, Cetus's preprocessing option `-macro=_Noreturn=` can remove the annotation from parser input. Test it in a separate compatibility profile and validate the resulting program. If a profile already uses `-macro`, combine definitions into its comma-separated value rather than adding a competing option. This workaround does not add general C11 support.

For missing `#include "local.h"`, remember that snippet/upload optimization stages one source file and does not automatically collect neighboring headers.

## What does PASS mean?

The example script compiled and ran both versions, obtained successful exit codes, and compared stdout. Inspect the downloaded C for the intended transformation. Unchanged code may still pass correctness checks, and correctness is separate from runtime performance.

Runner files default to `/tmp/smart-compiler-example-results` in the environment running the script. Repeating the same source/profile pair overwrites those runner files. REST task artifacts have separate UUID directories and persist in the Compose data volumes.

[Back to README](../README.md)
