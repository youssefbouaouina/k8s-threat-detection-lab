#!/usr/bin/env bash
# S01 - spawn an interactive shell in a running container (T1609).
set -uo pipefail
source "$(dirname "$0")/_lib.sh"
vexec_tty sh -c 'id' || true
