#!/usr/bin/env bash
# Run the attack scenarios in order and record their time windows.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p results
: > results/timeline.tsv
: > results/errors.log

for f in scenarios/S*.sh; do
  id=$(basename "$f" .sh)
  start=$(date +%s.%N)
  if ! bash "$f"; then
    echo "$id failed" | tee -a results/errors.log
  fi
  sleep 12
  end=$(date +%s.%N)
  printf "%s\t%s\t%s\n" "$id" "$start" "$end" >> results/timeline.tsv
  echo "ran $id"
done

echo "timeline:"
cat results/timeline.tsv
