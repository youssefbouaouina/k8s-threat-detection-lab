#!/usr/bin/env bash
# S12 - drop a binary in /tmp, make it executable and run it (T1105).
set -uo pipefail
source "$(dirname "$0")/_lib.sh"
vexec sh -c 'printf "#!/bin/sh\necho lab\n" > /tmp/lab-bin; chmod +x /tmp/lab-bin; /tmp/lab-bin' || true
