#!/bin/bash
# Read-only chunked disk imaging of an M20 Pro host over SSH.
# Resumable: each 512MiB chunk is gzipped separately (concatenable gzip members).
# Usage: image_host.sh <ip> <label>
set -uo pipefail
IP="$1"; LABEL="$2"
OUTDIR="/media/lee/数据/rea_images/${LABEL}"
mkdir -p "$OUTDIR"
CHUNK_MB=512
DISK_BYTES=123748745216
TOTAL_MB=$(( (DISK_BYTES + 1048576 - 1) / 1048576 ))
NCHUNK=$(( (TOTAL_MB + CHUNK_MB - 1) / CHUNK_MB ))
PASS="'"
PWB64=$(printf '%s\n' "$PASS" | base64 -w0)
SSHOPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ServerAliveInterval=20 -o ServerAliveCountMax=6 -o LogLevel=ERROR"

run_remote_sudo() {
  local b64
  b64=$(printf '%s' "$1" | base64 -w0)
  ssh $SSHOPTS "user@$IP" "PW=\$(echo $PWB64 | base64 -d); echo \"\$PW\" | sudo -S -p '' bash -c \"\$(echo $b64 | base64 -d)\""
}

echo "[$LABEL] starting imaging -> $OUTDIR ($NCHUNK chunks of ${CHUNK_MB}MiB)"
for ((i=0;i<NCHUNK;i++)); do
  f="$OUTDIR/mmcblk0.part$(printf '%04d' $i).gz"
  if [ -s "$f" ] && gzip -t "$f" 2>/dev/null; then
    continue
  fi
  skip=$((i*CHUNK_MB))
  REMOTE="set -o pipefail; nice -n 19 ionice -c3 dd if=/dev/mmcblk0 bs=1M skip=$skip count=$CHUNK_MB 2>/dev/null | nice -n 19 pigz -6 -p 3"
  ok=0
  for attempt in 1 2 3 4 5 6; do
    if run_remote_sudo "$REMOTE" > "$f.tmp" 2>/dev/null && gzip -t "$f.tmp" 2>/dev/null; then
      mv "$f.tmp" "$f"; ok=1
      echo "[$LABEL] chunk $i/$((NCHUNK-1)) ok $(du -h "$f" | cut -f1)"
      break
    fi
    echo "[$LABEL] chunk $i attempt $attempt failed, retry in 5s"
    sleep 5
  done
  if [ "$ok" -ne 1 ]; then echo "[$LABEL] chunk $i FAILED permanently"; fi
done

echo "[$LABEL] concatenating chunks"
cat "$OUTDIR"/mmcblk0.part*.gz > "$OUTDIR/mmcblk0.img.gz.tmp" && mv "$OUTDIR/mmcblk0.img.gz.tmp" "$OUTDIR/mmcblk0.img.gz"
if gzip -t "$OUTDIR/mmcblk0.img.gz" 2>/dev/null; then
  echo "[$LABEL] CONCAT OK size=$(du -h "$OUTDIR/mmcblk0.img.gz" | cut -f1)"
else
  echo "[$LABEL] CONCAT FAILED"
fi

for b in boot0 boot1; do
  bf="$OUTDIR/mmcblk0${b}.gz"
  [ -s "$bf" ] && continue
  run_remote_sudo "set -o pipefail; nice -n 19 ionice -c3 dd if=/dev/mmcblk0${b} bs=4M 2>/dev/null | pigz -6 -p 2" > "$bf.tmp" 2>/dev/null \
    && gzip -t "$bf.tmp" 2>/dev/null && mv "$bf.tmp" "$bf" && echo "[$LABEL] $b ok"
done
echo "[$LABEL] DONE"
