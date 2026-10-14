#!/bin/bash
# Baixa as fontes do padrão DEEP pela API CSS do Google Fonts (o GitHub raw fica bloqueado) para demo/assets/fonts.
set -euo pipefail
DEST="$(cd "$(dirname "$0")" && pwd)/demo/assets/fonts"; mkdir -p "$DEST"; cd "$DEST"
baixar() {  # família, nome do arquivo
  curl -sL -A "Old Android 4.4" "https://fonts.googleapis.com/css2?family=$1" -o "$2.css"
  python3 - "$2" <<'PY'
import re, subprocess, sys
nome = sys.argv[1]
for w, url in re.findall(r"font-weight: (\d+);\s*src: url\((\S+?)\)", open(nome + ".css").read()):
    subprocess.run(["curl", "-sL", "-o", f"{nome}-{w}.ttf", url], check=True)
PY
  rm -f "$2.css"
}
baixar "Playfair+Display:ital,wght@1,500;1,700" PlayfairItalic
baixar "Inter:wght@500;800;900" Inter
baixar "Rubik:wght@600;900" Rubik
ls -1 *.ttf
