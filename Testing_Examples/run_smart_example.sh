#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <example.c> <optimization-profile>" >&2
  exit 2
fi

example="$1"
profile="$2"
case "$example" in
  01_vector_scale.c|02_reduction_sum.c|03_matrix_multiply.c|04_prefix_sum.c|05_loop_interchange.c) ;;
  *) echo "Unknown example: $example" >&2; exit 2 ;;
esac

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_file="$script_dir/$example"
smart_url="${SMART_URL:-http://127.0.0.1:18000}"
timeout_seconds="${SMART_TASK_TIMEOUT_SECONDS:-360}"
result_dir="${SMART_EXAMPLE_RESULTS_DIR:-/tmp/smart-compiler-example-results}"
stem="${example%.c}"

for command_name in curl python3 gcc; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Required command not found: $command_name" >&2
    exit 1
  fi
done

if [[ ! -f "$source_file" ]]; then
  echo "Example source not found: $source_file" >&2
  exit 1
fi

if ! curl --fail --silent --show-error "$smart_url/health" >/dev/null 2>&1; then
  echo "SMART API is not reachable at $smart_url." >&2
  echo "Start the SMART server on this DARWIN host first; see README.md." >&2
  exit 1
fi

mkdir -p "$result_dir"
response="$(curl --fail-with-body --silent --show-error \
  -X POST "$smart_url/tasks" \
  -F 'task_type=optimize' \
  -F 'language=c' \
  -F "optimization_profile=$profile" \
  -F "file=@$source_file")"
task_id="$(printf '%s' "$response" | python3 -c 'import json,sys; print(json.load(sys.stdin)["task_id"])')"
printf 'Submitted %s using profile %s (task %s).\n' "$example" "$profile" "$task_id"

start_time=$SECONDS
while true; do
  response="$(curl --fail-with-body --silent --show-error "$smart_url/tasks/$task_id")"
  status="$(printf '%s' "$response" | python3 -c 'import json,sys; print(json.load(sys.stdin)["task_status"])')"
  case "$status" in
    completed)
      break
      ;;
    failed)
      echo "SMART optimization failed:" >&2
      printf '%s\n' "$response" >&2
      exit 1
      ;;
    pending|running)
      if (( SECONDS - start_time >= timeout_seconds )); then
        echo "Timed out waiting for SMART task $task_id (last status: $status)." >&2
        exit 1
      fi
      sleep 2
      ;;
    *)
      echo "Unexpected task status '$status':" >&2
      printf '%s\n' "$response" >&2
      exit 1
      ;;
  esac
done

output_path="$(printf '%s' "$response" | python3 -c 'import json,sys; result=json.load(sys.stdin).get("task_result") or {}; print(result.get("file_path") or "")')"
if [[ -z "$output_path" ]]; then
  echo "Task completed without a transformed file path:" >&2
  printf '%s\n' "$response" >&2
  exit 1
fi

result_key="$stem.$profile"
optimized_source="$result_dir/$result_key.optimized.c"
curl --fail-with-body --silent --show-error --get "$smart_url/files/download" \
  --data-urlencode "file_path=$output_path" \
  -o "$optimized_source"

baseline_binary="$result_dir/$result_key.baseline"
optimized_binary="$result_dir/$result_key.optimized"
gcc -std=c11 -O0 -fopenmp "$source_file" -o "$baseline_binary"
gcc -std=c11 -O0 -fopenmp "$optimized_source" -o "$optimized_binary"
"$baseline_binary" > "$result_dir/$result_key.baseline.txt"
"$optimized_binary" > "$result_dir/$result_key.optimized.txt"

if ! cmp -s "$result_dir/$result_key.baseline.txt" "$result_dir/$result_key.optimized.txt"; then
  echo "FAIL: baseline and SMART outputs differ for $example with profile $profile." >&2
  diff -u "$result_dir/$result_key.baseline.txt" "$result_dir/$result_key.optimized.txt" || true
  exit 1
fi

printf 'PASS %s [%s]: ' "$example" "$profile"
cat "$result_dir/$result_key.optimized.txt"
printf 'Task ID: %s\nTransformed C: %s\n' "$task_id" "$optimized_source"
