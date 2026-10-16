#!/bin/bash
# Read-only SSH to any M20 Pro host using the device password.
# Usage: dogssh.sh <ip> "<remote command>"
set -o pipefail
IP="$1"; shift
exec sshpass -p "'" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o ConnectTimeout=8 -o LogLevel=ERROR \
  -o PreferredAuthentications=password -o PubkeyAuthentication=no \
  "user@$IP" "$@"
