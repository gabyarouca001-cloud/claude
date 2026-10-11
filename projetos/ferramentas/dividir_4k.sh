#!/bin/bash
# Divide um vídeo em partes de 29 MB (limite do chat) e gera o juntar_<nome>.bat para o Windows
# (copy /b + conferência SHA256 com certutil). Uso: dividir_4k.sh video.mp4 pasta_saida
set -e
arq="$1"; saida="$2"; nome=$(basename "$arq")
mkdir -p "$saida"
split -b 29000000 -d -a 2 --numeric-suffixes=1 "$arq" "$saida/$nome.part"
hash=$(sha256sum "$arq" | cut -d' ' -f1)
partes=$(cd "$saida" && ls "$nome".part* | sort | paste -sd+)
bat="$saida/juntar_${nome%.*}.bat"
{
  echo "@echo off"
  echo "cd /d \"%~dp0\""
  echo "echo Juntando as partes de $nome ..."
  echo "copy /b $partes \"$nome\" >nul"
  echo "echo Conferindo o arquivo..."
  echo "certutil -hashfile \"$nome\" SHA256 | findstr /i \"$hash\" >nul && (echo OK: $nome completo e identico ao original.) || (echo ERRO: o arquivo nao confere. Confira se baixou todas as partes.)"
  echo "pause"
} | sed 's/$/\r/' > "$bat"
echo "$(ls "$saida"/"$nome".part* | wc -l) partes + $(basename "$bat")  sha256 $hash"
