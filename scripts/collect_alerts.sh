#!/usr/bin/env bash
# Stream the Falco pod log (JSON alert lines) into a file.
set -euo pipefail
OUT=${1:-results/alerts.jsonl}
mkdir -p "$(dirname "$OUT")"
: > "$OUT"

POD=$(kubectl -n falco get pods -l app.kubernetes.io/name=falco -o jsonpath='{.items[0].metadata.name}')
if [ -z "$POD" ]; then
  echo "no falco pod found" >&2
  exit 1
fi
echo "collecting Falco alerts from pod $POD into $OUT" >&2
exec kubectl -n falco logs -f "$POD" -c falco --tail=-1 >> "$OUT" 2>&1
