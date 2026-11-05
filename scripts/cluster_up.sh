#!/usr/bin/env bash
# Bring up the local cluster and the victim workload.
# Requires: minikube (docker driver), kubectl.
set -euo pipefail

MINIKUBE_VERSION=${MINIKUBE_VERSION:-v1.34.0}
K8S_VERSION=${K8S_VERSION:-v1.30.0}
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "minikube: $(minikube version --short 2>/dev/null || echo not-installed)"
minikube start \
  --driver=docker \
  --kubernetes-version="$K8S_VERSION" \
  --cpus=2 \
  --memory=4096 \
  --wait=all
kubectl wait --for=condition=Ready nodes --all --timeout=180s

kubectl apply -f "$ROOT/k8s/victim.yaml"
kubectl -n lab rollout status deploy/victim --timeout=180s

# openssh-client is only needed by S15; install it outside the measured windows.
kubectl -n lab exec deploy/victim -- apk add --no-cache openssh-client >/dev/null 2>&1 || true

echo "cluster ready"
kubectl version 2>/dev/null | head -2 || true
