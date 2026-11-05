#!/usr/bin/env bash
# S02 - read /etc/shadow inside a container (T1003.008).
set -uo pipefail
source "$(dirname "$0")/_lib.sh"
vexec sh -c 'head -1 /etc/shadow' || true
