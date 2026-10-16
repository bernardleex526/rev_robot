#!/bin/bash
# Run a command on the M20 Pro dev host A with sudo.
# The sudo password on the dog is a single quote character.
# Usage: dogsudo.sh "<remote command>"
set -o pipefail
HOST=10.21.41.1
USER=user
PASS="'"
REMOTE="$1"
B64=$(printf '%s' "$REMOTE" | base64 -w0)
PWB64=$(printf '%s\n' "$PASS" | base64 -w0)
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o ConnectTimeout=10 -o LogLevel=ERROR "$USER@$HOST" \
  "PW=\$(echo $PWB64 | base64 -d); echo \"\$PW\" | sudo -S -p '' bash -c \"\$(echo $B64 | base64 -d)\""
