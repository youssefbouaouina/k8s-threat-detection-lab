#!/usr/bin/env bash
# S10 - outbound connection to a crypto-mining pool port (T1496).
# 192.0.2.1 is TEST-NET-1: the connect() happens, no real host is contacted.
set -uo pipefail
source "$(dirname "$0")/_lib.sh"
vexec sh -c 'timeout 3 wget -q -O- http://192.0.2.1:4444/ >/dev/null 2>&1' || true
