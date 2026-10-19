# SMART Compiler Testing Examples

These standalone C programs are small inputs for testing the SMART compiler without PolyBench or NPB. Each file can be uploaded individually through the SMART REST API; none depends on benchmark headers.

## Tiling and loop interchange

SMART exposes these Cetus transformations as separate optimization profiles. The exact Cetus flags are maintained in `SMART-COMPILER/config/profiles.json`.

| SMART profile | Cetus option(s) | Behavior |
|---|---|---|
| `paw_tiling_nt` | `-paw_tiling=1 -selection=NT` | Parallel-aware tiling with NT tile-size selection. |
| `paw_tiling_lrw` | `-paw_tiling=1 -selection=LRW` | Parallel-aware tiling with the LRW (FindB) tile-size selection algorithm. |
| `paw_tiling_fixed32` | `-paw_tiling=1 -selection=FIXED -tileSizes=32` | Parallel-aware tiling with fixed tile size 32. |
| `loop_interchange` | `-loop_interchange` | Reorders eligible nested loops to improve data reuse and locality. This profile disables loop parallelization and OpenMP generation. |

The three tiling profiles also run dependence, privatization, and reduction analyses, enable loop parallelization and OpenMP generation, and use the profile's hardware settings (4 cores, a 25,600 KiB cache estimate, and a 64-byte cache line). For direct Cetus invocation, `-selection` accepts `NT`, `LRW`, or `FIXED`; `-tileSizes` accepts comma-separated sizes for successive loop levels. Cetus also supports serial tiling with `-paw_tiling=0`; the SMART profiles listed above use parallel-aware tiling.

Loop interchange is constrained by legality and the form of the loop nest. Cetus may leave a nest unchanged when it cannot safely interchange it, including imperfectly nested loops, negative increments, complex bounds, or nests containing function calls. Check Cetus output for whether a loop was interchanged; selecting the profile does not guarantee that every loop changes or that runtime improves.

For implementation details, see `The-Cetus-Project/docs/Parallel-Aware-Tiling.md` and `The-Cetus-Project/src/cetus/transforms/LoopInterchange.java`.


## Start SMART

Replace each example path with the actual checkout location on the machine you will use.

In Terminal 1, from the SMART-COMPILER checkout:

```bash
cd /path/to/SMART-COMPILER

# Only needed the first time, or after dependencies change:
uv sync

export CETUS=/path/to/The-Cetus-Project/bin/cetus
export CETUS_PROFILES_FILE=/path/to/SMART-COMPILER/config/profiles.json
export CETUS_TIMEOUT_SECONDS=300
export HOST=127.0.0.1 PORT=18000 MCP_SERVER_TRANSPORT=sse ENABLE_REST_API=true

test -x "$CETUS" || { echo "Cetus is missing or not executable: $CETUS"; exit 1; }
test -r "$CETUS_PROFILES_FILE" || { echo "Profiles file is missing or unreadable: $CETUS_PROFILES_FILE"; exit 1; }

# If this reports healthy, leave the existing server running.
# Otherwise, start the server and leave this terminal open.
if curl --fail --silent http://127.0.0.1:18000/health >/dev/null; then
  echo "SMART API is already running at http://127.0.0.1:18000"
else
  uv run python src/run_server.py
fi
```

## Run the seven optimization cases

In Terminal 2, run these scripts from the examples directory. Keep the server running in Terminal 1:

```bash
cd /path/to/SMART-COMPILER/Testing_Examples

./run_01_vector_scale.sh       # parallelization
./run_02_reduction_sum.sh      # parallel reduction
./run_03_matrix_multiply.sh    # fixed-size tiling
./run_05_loop_interchange.sh   # loop interchange
./run_06_matrix_tiling_nt.sh   # NT tiling
./run_07_matrix_tiling_lrw.sh  # LRW/FindB tiling
./run_08_reuse_analysis.sh     # reuse analysis plus parallelization
```

There are seven optimization runs above. The separate run_04_prefix_sum.sh checks that Cetus preserves a loop-carried dependency; it is a correctness/safety case, not an optimization profile.

## Submit examples

For direct API submission without output validation, run these from the SMART-COMPILER checkout in another terminal. Submit one file per request:

```bash
curl --fail-with-body -X POST http://127.0.0.1:18000/tasks \
  -F 'task_type=optimize' \
  -F 'language=c' \
  -F 'optimization_profile=parallel' \
  -F 'file=@Testing_Examples/01_vector_scale.c'

curl --fail-with-body -X POST http://127.0.0.1:18000/tasks \
  -F 'task_type=optimize' \
  -F 'language=c' \
  -F 'optimization_profile=parallel' \
  -F 'file=@Testing_Examples/02_reduction_sum.c'

curl --fail-with-body -X POST http://127.0.0.1:18000/tasks \
  -F 'task_type=optimize' \
  -F 'language=c' \
  -F 'optimization_profile=paw_tiling_fixed32' \
  -F 'file=@Testing_Examples/03_matrix_multiply.c'

curl --fail-with-body -X POST http://127.0.0.1:18000/tasks \
  -F 'task_type=optimize' \
  -F 'language=c' \
  -F 'optimization_profile=parallel' \
  -F 'file=@Testing_Examples/04_prefix_sum.c'

curl --fail-with-body -X POST http://127.0.0.1:18000/tasks \
  -F 'task_type=optimize' \
  -F 'language=c' \
  -F 'optimization_profile=loop_interchange' \
  -F 'file=@Testing_Examples/05_loop_interchange.c'

curl --fail-with-body -X POST http://127.0.0.1:18000/tasks \
  -F 'task_type=optimize' \
  -F 'language=c' \
  -F 'optimization_profile=paw_tiling_nt' \
  -F 'file=@Testing_Examples/03_matrix_multiply.c'

curl --fail-with-body -X POST http://127.0.0.1:18000/tasks \
  -F 'task_type=optimize' \
  -F 'language=c' \
  -F 'optimization_profile=paw_tiling_lrw' \
  -F 'file=@Testing_Examples/03_matrix_multiply.c'

curl --fail-with-body -X POST http://127.0.0.1:18000/tasks \
  -F 'task_type=optimize' \
  -F 'language=c' \
  -F 'optimization_profile=reuse_analysis' \
  -F 'file=@Testing_Examples/01_vector_scale.c'
```

The examples exercise different compiler behavior:

| File | Intended check | Baseline output |
|---|---|---|
| `01_vector_scale.c` | Independent loop iterations should be candidates for parallelization. | `checksum=14999950000` |
| `02_reduction_sum.c` | Tests recognition of a sum reduction. | `sum=495000` |
| `03_matrix_multiply.c` | Tests nested-loop analysis and the fixed-32 tiling profile. | `checksum=1572475` |
| `04_prefix_sum.c` | A loop-carried dependency must preserve sequential semantics. | `prefix_checksum=167167000` |
| `05_loop_interchange.c` | Applies Cetus loop interchange to improve contiguous memory access; checks output equivalence. | `checksum=4161536` |

## Additional optimization profiles

The fixed-32 profile is covered by `run_03_matrix_multiply.sh`. These extra runners use the same correctness-checked inputs with the other available profiles:

| Runner | Input | Profile | Optimization exercised |
|---|---|---|---|
| `run_06_matrix_tiling_nt.sh` | `03_matrix_multiply.c` | `paw_tiling_nt` | Cache-aware NT tile selection, with OpenMP parallelization |
| `run_07_matrix_tiling_lrw.sh` | `03_matrix_multiply.c` | `paw_tiling_lrw` | LRW/FindB tile selection, with OpenMP parallelization |
| `run_08_reuse_analysis.sh` | `01_vector_scale.c` | `reuse_analysis` | Reuse-vector analysis plus OpenMP parallelization |

The NT, LRW, and fixed-32 profiles provide three ways to exercise Cetus PAW tiling. Tiling profiles also enable loop parallelization and OpenMP generation as configured in `config/profiles.json`.

## Check the unoptimized C programs

This compiles and runs each input with the system C compiler. It checks the examples themselves; it does not test the SMART transformation output.

```bash
mkdir -p /tmp/smart-example-baseline
for source in Testing_Examples/*.c; do
  name=$(basename "$source" .c)
  cc -std=c11 -O0 -Wall -Wextra "$source" -o "/tmp/smart-example-baseline/$name" || exit 1
  "/tmp/smart-example-baseline/$name" || exit 1
done
```

## Run one example with a script

Start the SMART API server using the startup commands above. The scripts must run on the same machine as the server because the API listens on `127.0.0.1`. On a cluster, use the same compute or login node for the server and the scripts.

From this directory, run one script at a time:

```bash
./run_01_vector_scale.sh
./run_02_reduction_sum.sh
./run_03_matrix_multiply.sh
./run_04_prefix_sum.sh
./run_05_loop_interchange.sh
./run_06_matrix_tiling_nt.sh
./run_07_matrix_tiling_lrw.sh
./run_08_reuse_analysis.sh
```

Each script submits its C file and profile to SMART, waits for the task, downloads the transformed C, compiles the original and transformed files, and compares their output. A successful check prints `PASS`. Transformed C files, binaries, and output captures are kept in `/tmp/smart-compiler-example-results/`; filenames include both the example and profile so repeated runs do not overwrite one another. The scripts require `curl`, `python3`, and `gcc` with OpenMP support. `SMART_URL` and `SMART_TASK_TIMEOUT_SECONDS` can be set to override the API URL and task timeout.
