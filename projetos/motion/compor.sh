#!/bin/bash
# Põe o overlay transparente (webm) sobre o vídeo. Precisa do decoder libvpx-vp9 NA ENTRADA do overlay,
# senão o ffmpeg ignora o canal alfa e o fundo do overlay aparece.
#   ./compor.sh video.mp4 overlay.webm saida.mp4 [inicio_s]
set -euo pipefail
V="$1"; O="$2"; S="$3"; T="${4:-0}"
ffmpeg -v error -y -i "$V" -itsoffset "$T" -c:v libvpx-vp9 -i "$O" \
  -filter_complex "[0:v][1:v]overlay=0:0:format=auto:eof_action=pass" \
  -c:v libx264 -preset faster -crf 19 -pix_fmt yuv420p -c:a copy -movflags +faststart "$S"
