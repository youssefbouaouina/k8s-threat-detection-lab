#!/usr/bin/env bash
# Install the pinned Falco chart with the custom rules mounted.
set -euo pipefail

FALCO_CHART_VERSION=${FALCO_CHART_VERSION:-9.2.2}
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

helm version --short
helm repo add falcosecurity https://falcosecurity.github.io/charts >/dev/null 2>&1 || true
helm repo update >/dev/null

kubectl create namespace falco --dry-run=client -o yaml | kubectl apply -f - >/dev/null
kubectl -n falco create configmap lab-rules \
  --from-file=lab-rules.yaml="$ROOT/rules/custom_rules.yaml" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null

helm upgrade --install falco falcosecurity/falco \
  --namespace falco \
  --version "$FALCO_CHART_VERSION" \
  -f "$ROOT/helm/falco-values.yaml" \
  --wait --timeout 10m

kubectl -n falco rollout status ds/falco --timeout=300s
kubectl -n falco get pods

# Record the exact Falco build and the loaded rule count for RESULTS.md.
FALCO_POD=$(kubectl -n falco get pods -l app.kubernetes.io/name=falco -o jsonpath='{.items[0].metadata.name}')
kubectl -n falco exec "$FALCO_POD" -c falco -- falco --version > "$ROOT/results/falco_version.txt" 2>&1 || true
kubectl -n falco exec "$FALCO_POD" -c falco -- falco --list > "$ROOT/results/falco_rules_loaded.txt" 2>&1 || true
