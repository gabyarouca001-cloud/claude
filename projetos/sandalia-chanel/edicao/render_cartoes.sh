#!/usr/bin/env bash
# Renderiza cada composição curta (hf_cards/kNN) em WebM com transparência. Uso: render_cartoes.sh <pasta_hf_cards> [paralelo] [qualidade]
set -u
PASTA="${1:?pasta}"; PAR="${2:-3}"; Q="${3:-draft}"
export PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers
render_um() {
  d="$1"; q="$2"
  [ -s "$d/cartao.webm" ] && { echo "pronto $d (já existia)"; return; }
  (cd "$d" && npx --yes hyperframes render --quality "$q" --format webm --output cartao.webm > render.log 2>&1) \
    && echo "pronto $d" || echo "FALHOU $d"
}
export -f render_um
ls -d "$PASTA"/k* | xargs -P "$PAR" -I{} bash -c 'render_um "$@"' _ {} "$Q"
echo "TODOS_TERMINADOS"
