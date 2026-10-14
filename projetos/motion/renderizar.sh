#!/bin/bash
# Renderiza uma composição HyperFrames (HTML/GSAP) usando o Chromium já instalado no ambiente.
#   ./renderizar.sh demo previa         -> demo/renders/previa.mp4 (fundo escuro, para aprovar)
#   ./renderizar.sh demo overlay        -> demo/renders/overlay.webm (fundo TRANSPARENTE, para pôr sobre o vídeo)
# Antes: ./baixar_fontes.sh  e  (cd demo && npx --yes hyperframes@0.8.155 check)
set -euo pipefail
PROJ="${1:?pasta do projeto}"; MODO="${2:-previa}"; FPS="${FPS:-25}"
export PUPPETEER_SKIP_DOWNLOAD=1
export PRODUCER_HEADLESS_SHELL_PATH="${PRODUCER_HEADLESS_SHELL_PATH:-$(ls /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell | head -1)}"
cd "$PROJ"; ABS="$(pwd)"
if [[ "$MODO" == "overlay" ]]; then
  # variante sem fundo: tira o .bg e deixa body transparente (o original não é alterado)
  TMP="$(dirname "$ABS")/.overlay_tmp"; rm -rf "$TMP" && mkdir "$TMP" && cp -r . "$TMP/" && cd "$TMP" && rm -rf renders .hyperframes
  sed -i 's|<div class="bg"></div>||; s|background: #0c0c0e; }|background: transparent; }|' index.html
  npx --yes hyperframes@0.8.155 render --format webm --fps "$FPS" -o renders/overlay.webm
  mkdir -p "$ABS/renders" && cp renders/overlay.webm "$ABS/renders/overlay.webm"
else
  npx --yes hyperframes@0.8.155 render --fps "$FPS" -o "renders/$MODO.mp4"
fi
