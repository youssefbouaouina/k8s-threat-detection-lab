#!/usr/bin/env bash
# S05 - run the package manager inside a container (T1505).
set -uo pipefail
source "$(dirname "$0")/_lib.sh"
vexec apk info >/dev/null 2>&1 || true
