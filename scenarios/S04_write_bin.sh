#!/usr/bin/env bash
# S04 - write a file under /usr/bin (T1543).
set -uo pipefail
source "$(dirname "$0")/_lib.sh"
vexec sh -c 'touch /usr/bin/lab-marker' || true
