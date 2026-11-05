#!/usr/bin/env bash
# Shared helpers for the attack scenarios.
set -uo pipefail

NS=${NS:-lab}

victim_pod() {
  kubectl -n "$NS" get pods -l app=victim -o jsonpath='{.items[0].metadata.name}'
}

vexec() {
  kubectl -n "$NS" exec "$(victim_pod)" -- "$@"
}

# Allocated tty: needed for Falco's "Terminal shell in container" rule.
vexec_tty() {
  kubectl -n "$NS" exec -t "$(victim_pod)" -- "$@"
}

cleanup_pod() {
  kubectl -n "$NS" delete pod "$1" --ignore-not-found --wait=false >/dev/null 2>&1 || true
}
