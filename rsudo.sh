#!/bin/bash
# Generic remote sudo runner for the M20 Pro hosts.
# Usage: rsudo.sh <ip> "<remote command>"
set -o pipefail
IP="$1"; shift
PASS="'"
REMOTE="$1"
B64=$(printf '%s' "$REMOTE" | base64 -w0)
PWB64=$(printf '%s\n' "$PASS" | base64 -w0)
exec ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o ConnectTimeout=10 -o LogLevel=ERROR "user@$IP" \
  "PW=\$(echo $PWB64 | base64 -d); echo \"\$PW\" | sudo -S -p '' bash -c \"\$(echo $B64 | base64 -d)\""
