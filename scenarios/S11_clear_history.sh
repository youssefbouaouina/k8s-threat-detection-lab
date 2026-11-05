#!/usr/bin/env bash
# S11 - delete the shell history (T1070.003).
set -uo pipefail
source "$(dirname "$0")/_lib.sh"
vexec sh -c 'echo marker > /root/.bash_history; rm -f /root/.bash_history' || true
