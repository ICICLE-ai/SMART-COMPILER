# Optimization profiles

SMART selects Cetus arguments by an exact profile ID in [config/profiles.json](../../config/profiles.json). Use that ID as `optimization_profile` in a REST upload or an MCP optimization call. `parallel` is the default when the request omits it. See the [setup and usage guide](../../README.md) for working requests.

## Included profiles

| Exact ID | Requested behavior | Distinguishing arguments |
| --- | --- | --- |
| `parallel` | Analyze loops and generate OpenMP where Cetus accepts parallelization. | `-parallelize-loops=1 -ompGen=1` with the shared analysis flags below. |
| `paw_tiling_nt` | Parallel-aware tiling with the NT tile-size selector. | `-paw_tiling=1 -selection=NT` with the shared analysis and tiling flags below. |
| `paw_tiling_lrw` | Parallel-aware tiling with the LRW (FindB) tile-size selector. | `-paw_tiling=1 -selection=LRW` with the shared analysis and tiling flags below. |
| `paw_tiling_fixed32` | Parallel-aware tiling with a fixed tile size of 32. | `-paw_tiling=1 -selection=FIXED -tileSizes=32` with the shared analysis and tiling flags below. |
| `reuse_analysis` | OpenMP parallelization with explicit reuse-vector analysis. | The `parallel` flags plus `-reuse-vector-analysis=1`. |
| `loop_interchange` | Loop interchange with OpenMP loop parallelization and generation disabled. | Exactly `-loop_interchange -parallelize-loops=0 -ompGen=0`. |

The first five profiles include these analysis and OpenMP settings:

```text
-alias=3 -verbosity=0 -profitable-omp=0 -ddt=2
-privatize=2 -reduction=2 -parallelize-loops=1 -ompGen=1
```

`parallel` changes two stock Cetus defaults: `-alias=3` replaces the default of 1, and `-profitable-omp=0` disables the default profitability filter. The three `paw_tiling_*` profiles also include:

```text
-tile-profitability=1 -cores=4 -cacheSize=25600 -cacheLine=64 -tilingLevel=0
```

The JSON file contains a complete, ordered argument list for each profile. These shared groups explain repeated settings; SMART does not inherit or combine them at runtime. In `paw_tiling_fixed32`, `-tileSizes=32` forces the fixed selector.

`-cores=4`, `-cacheSize=25600`, and `-cacheLine=64` are configurable assumptions for Cetus's tiling analysis. They do not set the number of threads used when the transformed program runs. Set the OpenMP runtime, such as `OMP_NUM_THREADS`, separately when compiling and running generated OpenMP code.

A selected profile requests a transformation. Whether Cetus changes a particular loop depends on the input and its analyses. A successful request does not establish correctness or a speedup; inspect the output, rebuild it, and compare results and performance with the original program. `reuse_analysis` enables reuse-vector analysis; it does not enable subscripted-subscript analysis. The included file has no `subsub` profile.

## JSON format

The top-level value must be a JSON object. Each top-level key is an exact, case-sensitive profile ID. The selected value must be an object containing `flags`:

| Field | Format and behavior |
| --- | --- |
| Profile ID | Top-level JSON key, used verbatim in the request. Names such as `parallel_verbose` are allowed. |
| `description` | Optional documentation for people reading the file. SMART does not use it to select arguments. |
| `flags` | Required ordered array of non-empty strings. Each string is passed as one Cetus argument. Null values, empty strings, and non-string entries are rejected. An empty array is accepted, but explicitly listing intended flags is recommended. |

SMART checks JSON structure and the selected entry's argument types. Cetus determines whether the arguments are supported and meaningful. SMART does not check flag compatibility, resolve conflicting flags, expand a shell command, or merge one profile with another. A profile ID absent from the active file produces an unknown-profile error listing the available keys.

The file is read again for each optimization request, so a valid edit is used on the next request. Changes to server environment variables require restarting the process or recreating its container. For a Docker bind mount, recreating the container also makes sure it sees files saved through an editor that replaces the original file.

## Server configuration

These are global server environment variables, outside the profile JSON:

| Variable | Purpose | Native setup | Bundled Docker setup |
| --- | --- | --- | --- |
| `CETUS` | Executable Cetus launcher. The file must exist and be executable. | Set it to the absolute path to your built `The-Cetus-Project/bin/cetus`. | `/opt/cetus/bin/cetus` |
| `CETUS_PROFILES_FILE` | JSON file containing all profile IDs available to requests. | Set it to the absolute path to `config/profiles.json` in this checkout, or your custom file. | `/app/config/profiles.json` |
| `CETUS_TIMEOUT_SECONDS` | Maximum Cetus process time, in seconds. Must be a number greater than zero. | Defaults to `300` if unset. | Defaults to `300` if unset. |

For example, start a native server after exporting these paths from the repository root:

```bash
export CETUS=/absolute/path/to/The-Cetus-Project/bin/cetus
export CETUS_PROFILES_FILE="$PWD/config/profiles.json"
export CETUS_TIMEOUT_SECONDS=300
export HOST=127.0.0.1 PORT=8000 MCP_SERVER_TRANSPORT=sse ENABLE_REST_API=true
uv run python src/run_server.py
```

Keep the complete built Cetus checkout with its launcher and libraries together. Moving only `bin/cetus` can break the launcher's embedded classpath. Follow the [native setup instructions](../how-to/run-native.md) to install prerequisites before running this command.

## Add a custom profile

Start with a copy of the included file so the six existing profile IDs remain available:

```bash
cp config/profiles.json /tmp/smart-profiles.json
```

Open `/tmp/smart-profiles.json` and add a `parallel_verbose` entry beside the existing entries. Copy the `parallel` argument list and change only `-verbosity=0` to `-verbosity=1`. Preserve its analysis and OpenMP arguments.

The following is a complete, valid JSON document illustrating that custom entry. It contains only `parallel_verbose`; replacing the whole copied file with it would remove the six included IDs. To retain them, add the entry to the copied object instead.

```json
{
  "parallel_verbose": {
    "description": "OpenMP parallelization with Cetus verbosity set to 1.",
    "flags": [
      "-alias=3",
      "-verbosity=1",
      "-profitable-omp=0",
      "-ddt=2",
      "-privatize=2",
      "-reduction=2",
      "-parallelize-loops=1",
      "-ompGen=1"
    ]
  }
}
```

For native use, export `CETUS_PROFILES_FILE=/tmp/smart-profiles.json` before starting the server. Select `parallel_verbose` in a subsequent optimization request.

For Docker, mount the host file over the image's existing configuration path. From the repository root, create a separate Compose override file:

```bash
cat > /tmp/smart-profiles.compose.yaml <<'YAML'
services:
  server:
    volumes:
      - type: bind
        source: /tmp/smart-profiles.json
        target: /app/config/profiles.json
        read_only: true
YAML

docker compose -f docker-compose.yml -f /tmp/smart-profiles.compose.yaml \
  up -d --force-recreate server
```

The mount source is on the host. The target is the server's existing `CETUS_PROFILES_FILE` path, `/app/config/profiles.json`. The image's bundled Cetus executable and the other Compose volumes remain in use. No image rebuild is needed for changes to this mounted JSON file. After saving an edit on the host, rerun the same Compose command to ensure the mount uses the current file. Include both `-f` arguments when managing this custom deployment.

## Input requirements

Profiles configure Cetus; they do not supply missing source files or headers. SMART optimizes one source file per request. A REST upload contains that file only, so local headers from its original project are not uploaded automatically. Source paths used by an MCP client must exist on the server, including inside its container when using Docker. Start with the self-contained example in [your first optimization](../tutorials/first-optimization.md), and see [troubleshooting](../troubleshooting.md) for header, parser, profile, and launcher errors.
