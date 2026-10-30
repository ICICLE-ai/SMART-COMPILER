# Run SMART natively

Use this guide to run the SMART server directly on Linux, WSL, or macOS. SMART
requires Python 3.11 or newer. The commands below use Python 3.11 and JDK 21,
the Java version used by the [Docker image](../../Dockerfile).

For native C profiling and the verified C example runners, use Linux or WSL
with GNU GCC and GNU `gprof`. The macOS commands below configure a native
server, with the preprocessing limitation described below. Use
[Docker](run-with-docker.md) for C profiling and the example runners on macOS.
Apple's `gcc` command normally invokes Clang and does not provide the GNU
OpenMP/profiling toolchain used by these workflows.

### macOS preprocessing limitation

In the tested macOS setup with Apple SDK 26.2 and the pinned Cetus build,
optimizing the checked-in vector example that includes `<stdio.h>` failed
while preprocessing Apple SDK headers. The reported errors included:

```text
AvailabilityInternal.h: error: missing '(' after '__has_builtin'
error: _Pragma takes a parenthesized string literal
cetus: preprocessor terminated with exit code 1
```

The server's `/health` endpoint still succeeded. This compiler failure occurs
before transformation; it does not indicate a missing Java runtime. A separate
headerless C input was optimized successfully, so the limitation does not
affect every native input.

Use the [Docker setup](run-with-docker.md) for inputs affected by these errors.
It supplies a Linux C preprocessor and headers together with Cetus and Java 21.

## 1. Install the system tools

On Debian or Ubuntu with JDK 21 available in the configured repositories:

```bash
sudo apt-get update
sudo apt-get install -y \
  binutils ca-certificates curl diffutils gcc git libc6-dev \
  openjdk-21-jdk-headless
```

GNU GCC supplies the C preprocessor Cetus invokes as `cpp`. The `binutils`
package supplies GNU `gprof` for C profiling. Check the installed tools:

```bash
java -version
javac -version
cpp --version
gcc --version
gprof --version
```

On macOS, install the Command Line Tools if needed, then install JDK 21 with
Homebrew:

```bash
xcode-select --install
brew install openjdk@21
export JAVA_HOME="$(brew --prefix openjdk@21)/libexec/openjdk.jdk/Contents/Home"
export PATH="$JAVA_HOME/bin:$PATH"
java -version
javac -version
cpp --version
```

Keep the `JAVA_HOME` and `PATH` settings in the terminal running SMART. Add them
to your shell configuration if you want them in future terminals. Native Cetus
optimization needs Java and a working C preprocessor; compiling and profiling
the transformed program additionally needs the appropriate C toolchain.

## 2. Set up the Python environment

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if it is not
already available. Open a terminal in your SMART-COMPILER checkout:

```bash
cd /absolute/path/to/SMART-COMPILER
SMART_ROOT="$(pwd -P)"
uv python install 3.11
uv venv --python 3.11 .venv
uv sync --locked --python 3.11
uv run python --version
```

Use this `.venv` for both the server and the optional built-in client. `uv run`
selects the project environment automatically; activating another virtual
environment is unnecessary. The commands in the rest of this guide assume the
SMART project root as the working directory unless they explicitly change it.

`SMART_ROOT` and `CETUS_ROOT` below are shell variables for constructing paths.
SMART reads the `CETUS` and `CETUS_PROFILES_FILE` application settings described
in step 4.

## 3. Build the pinned Cetus checkout

Build the same Cetus `release/3.0` revision as the Docker image. The following
commands create a sibling directory named `The-Cetus-Project`; choose another
stable location if that directory already contains a checkout you use.

Choose an absolute `CETUS_ROOT` with **no spaces in any path component**.
Upstream's build scripts and generated `bin/cetus` launcher do not support
spaces in that installation path, even when the outer shell commands are
quoted. If the sibling path below contains spaces, replace its first
assignment with a separate absolute path without spaces before cloning.
SMART's project, input, profile, and result paths can contain spaces when
quoted.

```bash
CETUS_ROOT="$(dirname "$SMART_ROOT")/The-Cetus-Project"
git clone --branch release/3.0 \
  https://github.com/PAROT-Udel/The-Cetus-Project.git "$CETUS_ROOT"
cd "$CETUS_ROOT"
git checkout --detach cebcc57b22d7eaed01b9420f7a76140e13aeeee4
git rev-parse HEAD
./build.sh clean && ./build.sh compile && ./build.sh bin
"$CETUS_ROOT/bin/cetus" -version
cd "$SMART_ROOT"
```

The printed commit must be
`cebcc57b22d7eaed01b9420f7a76140e13aeeee4`. The pinned build script compiles
Cetus with Java source/target level 1.8; using JDK 21 to build and run it does
not require changing that target.

The explicit `compile` step propagates a Java compilation failure before the
packaging step. Upstream's nested `bin` command alone can continue after one.

Keep the entire built checkout at this path. The generated `bin/cetus` launcher
embeds its checkout's absolute classpath and uses `lib/cetus.jar`; copying the
launcher alone or moving the checkout breaks that reference. If you move the
checkout, rerun the clean/build commands at the new location and update `CETUS`.

## 4. Configure the server

Create a private root-level `.env` from the server template on first setup:

```bash
cd "$SMART_ROOT"
if [ ! -e .env ]; then
  cp envs/.server.example.env .env
fi
```

If `.env` already exists, merge the server settings into it. Edit these entries,
replacing both paths with the absolute paths from the previous steps:

```dotenv
HOST=127.0.0.1
PORT=8000
MCP_SERVER_TRANSPORT=sse
ENABLE_REST_API=true
LOG_LEVEL=INFO
CETUS=/absolute/path/to/The-Cetus-Project/bin/cetus
CETUS_PROFILES_FILE=/absolute/path/to/SMART-COMPILER/config/profiles.json
CETUS_TIMEOUT_SECONDS=300
```

To print the two path settings with your shell variables expanded:

```bash
printf 'CETUS="%s/bin/cetus"\nCETUS_PROFILES_FILE="%s/config/profiles.json"\n' \
  "$CETUS_ROOT" "$SMART_ROOT"
```

Copy those printed values into `.env`. Use SMART's own
[`config/profiles.json`](../../config/profiles.json), which includes all six
supported [optimization profiles](../reference/optimization-profiles.md).
Keep credentials in your private `.env` or shell, and leave the checked-in
example files without secrets. The server's optional `OLLAMA_HOST` and
`OLLAMA_MODEL` settings are needed only for tasks requesting the Ollama
profiler.

## 5. Start the server and verify an optimization

Start the server from the SMART project root and leave this terminal running:

```bash
cd "$SMART_ROOT"
uv run --env-file .env python src/run_server.py
```

In a second terminal, change to the same checkout and check the REST endpoint:

```bash
cd /absolute/path/to/SMART-COMPILER
curl --fail --silent --show-error http://127.0.0.1:8000/health
```

The response should be `{"status":"ok"}`. The MCP SSE endpoint is
`http://127.0.0.1:8000/sse`. On Linux or WSL with GNU GCC/OpenMP available, run
the first end-to-end example:

```bash
export SMART_URL=http://127.0.0.1:8000
uv run bash Testing_Examples/run_01_vector_scale.sh
```

The runner uploads the source to REST, waits for Cetus, downloads the transformed
C, compiles the original and transformed programs with `gcc -fopenmp`, and
compares their outputs. It prints `PASS` and the transformed file location.
`SMART_URL` is explicit because the scripts otherwise default to port 18000.
The `uv run bash` wrapper also puts the project environment's `python3` on
`PATH` for the shell runner; no virtual-environment activation is needed.

The remaining examples use the same running server and `SMART_URL`:

```bash
uv run bash Testing_Examples/run_02_reduction_sum.sh
uv run bash Testing_Examples/run_03_matrix_multiply.sh
uv run bash Testing_Examples/run_04_prefix_sum.sh
uv run bash Testing_Examples/run_05_loop_interchange.sh
uv run bash Testing_Examples/run_06_matrix_tiling_nt.sh
uv run bash Testing_Examples/run_07_matrix_tiling_lrw.sh
uv run bash Testing_Examples/run_08_reuse_analysis.sh
```

See the [first optimization tutorial](../tutorials/first-optimization.md) for the
individual REST requests, and [troubleshooting](../troubleshooting.md) if a tool
or endpoint fails.

## 6. Optionally connect a client

The server and REST examples above work without an LLM. To use the built-in
interactive client, merge the settings from
[`envs/.client.example.env`](../../envs/.client.example.env) into your existing
private `.env`. For an already configured local Ollama model, the settings are:

```dotenv
LLM_HOST=http://localhost:11434
LLM_MODEL=llama3.1-smart-compiler:latest
MCP_SERVER_URL=http://127.0.0.1:8000/sse
ALLOWED_PATHS=file:///absolute/path/to/SMART-COMPILER/Testing_Examples
```

`ALLOWED_PATHS` is a `file://` URI for the client root. To generate a correctly
escaped URI for this checkout's examples, run from the project root:

```bash
uv run python -c 'from pathlib import Path; print((Path.cwd() / "Testing_Examples").as_uri())'
```

Then start the client in the second terminal:

```bash
uv run --env-file .env python src/run_client.py
```

Use [Connect a client](connect-a-client.md) for provider setup, external MCP
clients, and the stdio launch configuration. For stdio, configure
`MCP_SERVER_TRANSPORT=stdio` and `ENABLE_REST_API=false` in that client's launch
environment; `UV_ENV_FILE` can supply the absolute path of your private dotenv
file. The [configuration reference](../reference/configuration.md) explains
these settings and environment precedence.
