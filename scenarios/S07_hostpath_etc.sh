#!/usr/bin/env bash
# S07 - mount the host /etc into a pod (T1611).
set -uo pipefail
source "$(dirname "$0")/_lib.sh"
trap 'cleanup_pod hostpath-pod' EXIT
cat <<'EOF' | kubectl apply -f - >/dev/null
apiVersion: v1
kind: Pod
metadata:
  name: hostpath-pod
  namespace: lab
spec:
  containers:
    - name: c
      image: alpine:3.20
      command: ["sleep", "30"]
      volumeMounts:
        - name: host-etc
          mountPath: /etc
  volumes:
    - name: host-etc
      hostPath:
        path: /etc
        type: Directory
EOF
kubectl -n "$NS" wait --for=condition=Ready pod/hostpath-pod --timeout=120s >/dev/null 2>&1 || true
sleep 2
