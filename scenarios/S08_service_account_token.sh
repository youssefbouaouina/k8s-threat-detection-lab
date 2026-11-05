#!/usr/bin/env bash
# S08 - read the pod's Kubernetes service-account token (T1552.007).
set -uo pipefail
source "$(dirname "$0")/_lib.sh"
vexec sh -c 'cat /var/run/secrets/kubernetes.io/serviceaccount/token >/dev/null' || true
