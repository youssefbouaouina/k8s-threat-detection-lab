#!/usr/bin/env bash
# S15 - launch an SSH client from a container (T1021.004).
set -uo pipefail
source "$(dirname "$0")/_lib.sh"
vexec sh -c 'timeout 4 ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=2 -p 2222 root@192.0.2.1' || true
