#!/usr/bin/env bash
# Benign workload: nginx + CronJob + rolling update + normal debugging exec.
# Records its own window so evaluate.py can count alerts per hour.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MINUTES=${BENIGN_MINUTES:-15}
cd "$ROOT"
mkdir -p results

kubectl -n lab apply -f k8s/benign.yaml >/dev/null
kubectl -n lab rollout status deploy/web --timeout=180s >/dev/null
kubectl -n lab wait --for=condition=Ready pod -l app=web --timeout=180s >/dev/null 2>&1 || true

start=$(date +%s.%N)
echo "benign workload for $MINUTES minutes"

deadline=$(( $(date +%s) + MINUTES * 60 ))
i=0
while [ "$(date +%s)" -lt "$deadline" ]; do
  i=$((i + 1))
  # normal operator activity
  kubectl -n lab exec deploy/web -- nginx -t >/dev/null 2>&1 || true
  kubectl -n lab exec deploy/web -- cat /etc/nginx/nginx.conf >/dev/null 2>&1 || true
  kubectl -n lab logs deploy/web --tail=20 >/dev/null 2>&1 || true
  kubectl -n lab get pods >/dev/null 2>&1 || true
  if [ $((i % 3)) -eq 0 ]; then
    kubectl -n lab rollout restart deploy/web >/dev/null 2>&1 || true
    kubectl -n lab rollout status deploy/web --timeout=120s >/dev/null 2>&1 || true
  fi
  sleep 30
done

end=$(date +%s.%N)
printf "%s\t%s\n" "$start" "$end" > results/benign_window.tsv

kubectl -n lab delete -f k8s/benign.yaml --ignore-not-found >/dev/null 2>&1 || true
echo "benign workload done"
