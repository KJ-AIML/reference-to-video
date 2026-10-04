#!/usr/bin/env bash
# Master one raw Remotion render: audio to -14 LUFS (static gain + look-ahead limiter, ceiling -2.3 dBFS ≈ TP ≤ -1.5 dBTP),
# and ONE video re-encode to tagged tv/bt709 (bt601 matrix -> bt709; range auto-detected). No -shortest.
# Usage: scripts/master.sh out/film-16x9.raw.mp4 out/film-16x9.mp4   (env CRF=16 PRESET=slow by default)
set -euo pipefail
IN=$1; OUT=$2; TMP=$(mktemp -d)
# png frames (remotion.config.ts) give LIMITED-range yuv420p (untagged, bt601 matrix); jpeg frames give full-range yuvj420p.
# Detect it, so a limited-range raw is not squeezed a second time (that turns cream #FBF8F3 into grey #E8E3E0).
PF=$(ffprobe -v error -select_streams v:0 -show_entries stream=pix_fmt,color_range -of csv=p=0 "$IN")
case "$PF" in *yuvj*|*,pc*) INR=pc;; *) INR=tv;; esac; echo "raw video: $PF -> in_range=$INR"
I=$(ffmpeg -nostats -i "$IN" -map 0:a -af ebur128 -f null - 2>&1 | awk '/I:/{v=$2} END{print v}')
G=$(python3 -c "print(round(-14-($I),2))")
echo "raw I=$I LUFS -> gain $G dB"
# up to four passes: the limiter eats some loudness on VO peaks, so correct the gain once by the measured shortfall
for pass in 1 2 3 4; do
  ffmpeg -v error -y -i "$IN" -map 0:a -af "volume=${G}dB,alimiter=limit=0.767:attack=5:release=80:level=disabled" -ar 48000 -c:a pcm_s24le "$TMP/a.wav"
  I2=$(ffmpeg -nostats -i "$TMP/a.wav" -af ebur128 -f null - 2>&1 | awk '/I:/{v=$2} END{print v}')
  G=$(python3 -c "print(round($G+(-14-($I2)),2))"); echo "  pass $pass I=$I2 -> next gain $G dB"
  python3 -c "import sys; sys.exit(0 if abs(-14-($I2))>0.3 else 1)" || break
done
ffmpeg -nostats -i "$TMP/a.wav" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|LRA|Peak):" | sed 's/^/  mastered /'
ffmpeg -v error -y -i "$IN" -i "$TMP/a.wav" -map 0:v -map 1:a \
  -vf "scale=in_range=$INR:out_range=tv:in_color_matrix=bt601:out_color_matrix=bt709:flags=accurate_rnd+full_chroma_int+bitexact,format=yuv420p" \
  -c:v libx264 -preset ${PRESET:-slow} -crf ${CRF:-16} -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a aac -b:a 320k -ar 48000 -movflags +faststart "$OUT"
rm -rf "$TMP"; echo "wrote $OUT"
