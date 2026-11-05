#!/usr/bin/env bash
# S14 - connect to the Kubernetes API server from a container (T1613).
set -uo pipefail
source "$(dirname "$0")/_lib.sh"
vexec sh -c 'timeout 10 wget -q -O- --no-check-certificate https://kubernetes.default.svc/version >/dev/null 2>&1' || true
