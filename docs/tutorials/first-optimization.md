# Complete your first C optimization

This tutorial uses the Docker server and one checked-in, self-contained C file. It needs Docker with Compose and curl on the host. No model service or API key is used.

## Start the server

From the SMART-COMPILER checkout:

```bash
docker compose up -d --build
docker compose ps
curl --fail http://127.0.0.1:8000/health
```

Wait for the server to become healthy before continuing. If it fails, inspect `docker compose logs --tail=100 server`.

The image contains Python, the pinned Cetus compiler at `/opt/cetus`, Java 21, GCC, and GNU profiling tools. Confirm that the compiler can start:

```bash
docker compose exec server java -version
docker compose exec server sh -lc '"$CETUS" -version'
```

## Optimize and check the vector example

```bash
docker compose exec -e OMP_NUM_THREADS=2 server sh -lc \
  'cd /app/Testing_Examples && SMART_URL=http://127.0.0.1:8000 ./run_01_vector_scale.sh'
```

The script uses the REST API. It submits `01_vector_scale.c` with the `parallel` profile, polls the task, downloads the generated C, compiles both programs, and compares their stdout and exit codes.

Expected success:

```text
PASS 01_vector_scale.c [parallel]: checksum=14999950000
```

The task ID and generated source path are printed afterward. To inspect the generated OpenMP directives:

```bash
docker compose exec server grep -n '#pragma omp' \
  /tmp/smart-compiler-example-results/01_vector_scale.parallel.optimized.c
```

`PASS` establishes output equivalence for this input. It does not by itself prove a particular loop changed or that execution became faster.

## Run the remaining cases, one by one

Enter a shell inside the server:

```bash
docker compose exec -e OMP_NUM_THREADS=2 server bash
cd /app/Testing_Examples
export SMART_URL=http://127.0.0.1:8000
```

Then run:

```bash
./run_02_reduction_sum.sh
./run_03_matrix_multiply.sh
./run_04_prefix_sum.sh
./run_05_loop_interchange.sh
./run_06_matrix_tiling_nt.sh
./run_07_matrix_tiling_lrw.sh
./run_08_reuse_analysis.sh
exit
```

There are five source files and eight runs: seven optimization runs plus the prefix-sum dependency-preservation case.

| Run | Profile | Expected program output |
|---|---|---|
| 01 vector scale | parallel | `checksum=14999950000` |
| 02 reduction | parallel | `sum=495000` |
| 03 matrix multiply | paw_tiling_fixed32 | `checksum=1572475` |
| 04 prefix sum | parallel | `prefix_checksum=167167000` |
| 05 interchange | loop_interchange | `checksum=4161536` |
| 06 matrix multiply | paw_tiling_nt | `checksum=1572475` |
| 07 matrix multiply | paw_tiling_lrw | `checksum=1572475` |
| 08 vector scale | reuse_analysis | `checksum=14999950000` |

The container already has GNU GCC with OpenMP support, avoiding the difference between Apple's default compiler and GNU GCC.

## Keep the downloaded test results

Runner outputs are under `/tmp/smart-compiler-example-results` inside the server container. Copy them out before recreating that container:

```bash
docker compose cp server:/tmp/smart-compiler-example-results /tmp/smart-example-results
```

The filename includes the source name and profile. Repeating the same source/profile pair overwrites its previous runner outputs. To retain a separate run, set `SMART_EXAMPLE_RESULTS_DIR` to a new directory when invoking the script.

REST task inputs, generated files, and task records are separately retained by the Compose `server_files` and `server_db` volumes. MCP optimization returns C text rather than creating a persistent task result.

See [API requests](../reference/api.md), [custom profiles](../reference/optimization-profiles.md), and [client connections](../how-to/connect-a-client.md) for the next steps.
