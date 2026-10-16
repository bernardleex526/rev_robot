#!/bin/bash
# Run a command on the M20 Pro dev host A over WiFi SSH (key-based auth).
# Usage: dog.sh "<remote command>"
set -o pipefail
HOST=10.21.41.1
USER=user
exec ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o ConnectTimeout=10 -o LogLevel=ERROR "$USER@$HOST" "$@"
