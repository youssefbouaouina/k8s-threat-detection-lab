#!/usr/bin/env bash
# S06 - start a privileged pod (T1611, container-escape preparation).
set -uo pipefail
source "$(dirname "$0")/_lib.sh"
trap 'cleanup_pod priv-pod' EXIT
cat <<'EOF' | kubectl apply -f - >/dev/null
apiVersion: v1
kind: Pod
metadata:
  name: priv-pod
  namespace: lab
spec:
  containers:
    - name: c
      image: alpine:3.20
      command: ["sleep", "30"]
      securityContext:
        privileged: true
EOF
kubectl -n "$NS" wait --for=condition=Ready pod/priv-pod --timeout=120s >/dev/null 2>&1 || true
sleep 2
