#!/usr/bin/env bash
# S03 - write a file under /etc (T1222.002).
set -uo pipefail
source "$(dirname "$0")/_lib.sh"
vexec sh -c 'echo lab >> /etc/motd' || true
