#!/usr/bin/env bash
# Phase-10 checks for one final file. Usage: scripts/verify.sh out/film-16x9.mp4 169|916 [#BRANDHEX]
# Expects src/vo.json (fps/total) in the current Remotion project.
set -euo pipefail
F=$1; COMP=$2; TAG=$(basename "$F" .mp4)
EXP=$(python3 -c "import json;print(json.load(open('src/vo.json'))['total'])")
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=width,height,r_frame_rate,pix_fmt,color_range,color_space,nb_read_frames -of compact "$F"
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate -of compact "$F"
echo "expected frames: $EXP"
ffmpeg -nostats -i "$F" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|LRA|Peak):"
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$F")
SC=$([[ "$COMP" == *169* ]] && echo 480:270 || echo 360:640); WANT=${3:-#FBF8F3}
ffmpeg -v error -y -i "$F" -vf "fps=14/$D,scale=$SC,tile=7x2" -frames:v 1 "out/contact-$TAG.jpg" && echo "contact sheet out/contact-$TAG.jpg"
ffmpeg -v error -y -ss 0.5 -i "$F" -frames:v 1 /tmp/px.png
python3 -c "from PIL import Image;im=Image.open('/tmp/px.png').convert('RGB');print('bg pixel', '#%02X%02X%02X'%im.getpixel((8,im.size[1]//2)), 'want $WANT ±4 (sample a full-bleed brand area)')"
