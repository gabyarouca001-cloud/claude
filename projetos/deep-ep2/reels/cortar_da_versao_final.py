"""Cortes para Reels / TikTok / Shorts a partir da VERSÃO FINAL VERTICAL da editora (4K 2160x3840, legendas e música dela já
na imagem). Não refaz legenda nem trilha: só corta no trecho, põe o gancho no topo (título Playfair amarelo com olho de peixe,
primeiros ~3,5 s) e o "EPISÓDIO COMPLETO / NO YOUTUBE" no fim. 1080x1920, 30 fps, cada corte < 30 MB (2 passes).

Uso: python3 cortar_da_versao_final.py PASTA cortes.json
  PASTA com original.mp4 + transcricao.json (faster-whisper com word_timestamps); saída em PASTA/cortes/.
  cortes.json: [{"nome": "01_...", "ini": "frase de início", "fim": "frase final", "gancho": ["linha 1", "linha 2"]}]
  (ou "t0"/"t1" em segundos no lugar de ini/fim)
"""
import json
import math
import os
import re
import subprocess
import sys
import unicodedata

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "deep-influencer", "edicao"))
from titulo_olho_peixe import titulo as titulo_olho_peixe  # noqa: E402

W, H, FPS = 1080, 1920, 30
FONTES = os.environ.get("DEEP_FONTES", "/home/user/work/fonts")
AMARELO = (252, 237, 192)
LIMITE_MB = 28.5
ANTES, DEPOIS = 0.30, 0.45        # folga antes da 1ª sílaba e depois da última (nunca invade a palavra vizinha)
FIM_CARD = 2.4                    # duração do "episódio completo" no fim


def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if unicodedata.category(c) != "Mn"))


def palavras(pasta):
    return [w for s in json.load(open(f"{pasta}/transcricao.json")) for w in s["words"]]


def achar(pal, frase, depois=0):
    alvo = [norm(p) for p in frase.split()]
    tok = [norm(w["w"]) for w in pal]
    for i in range(depois, len(pal)):
        if tok[i:i + len(alvo)] == alvo:
            return i, i + len(alvo) - 1
    raise ValueError(f"frase não encontrada: {frase}")


def tempos(pal, c):
    if "t0" in c:
        return c["t0"], c["t1"]
    i, _ = achar(pal, c["ini"])
    _, j = achar(pal, c["fim"], i)
    ini = pal[i]["s"] - ANTES
    if i > 0:
        ini = max(ini, pal[i - 1]["e"] + 0.02)
    fim = pal[j]["e"] + DEPOIS
    if j + 1 < len(pal):
        fim = min(fim, pal[j + 1]["s"] - 0.04)
    return max(0, ini), fim


def cartao_final(saida):
    """barra amarela + 'EPISÓDIO COMPLETO / NO YOUTUBE' (canto superior esquerdo, fora da área do app)."""
    f = ImageFont.truetype(f"{FONTES}/InterExtraBold.ttf", 34)
    img = Image.new("RGBA", (620, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for dx, dy, a in ((3, 4, 110),):
        for k, t in enumerate(("EPISÓDIO COMPLETO", "NO YOUTUBE")):
            x = 28
            for ch in t:
                d.text((x + dx, 22 + k * 52 + dy), ch, font=f, fill=(0, 0, 0, a))
                x += f.getlength(ch) + 5
    d.rectangle((0, 18, 8, 128), fill=AMARELO + (255,))
    for k, t in enumerate(("EPISÓDIO COMPLETO", "NO YOUTUBE")):
        x = 28
        for ch in t:
            d.text((x, 22 + k * 52), ch, font=f, fill=AMARELO + (255,))
            x += f.getlength(ch) + 5
    img.save(saida)


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def main(pasta, arq):
    pal = palavras(pasta) if os.path.exists(f"{pasta}/transcricao.json") else []
    cortes = json.load(open(arq))
    os.makedirs(f"{pasta}/cortes", exist_ok=True)
    os.makedirs(f"{pasta}/tmp", exist_ok=True)
    cartao_final(f"{pasta}/tmp/fim.png")
    rel = []
    for c in cortes:
        t0, t1 = tempos(pal, c)
        dur = round(t1 - t0, 3)
        n = c["nome"]
        hook = f"{pasta}/tmp/{n}_gancho.png"
        titulo_olho_peixe(c["gancho"], hook, fonte=f"{FONTES}/PlayfairMedium.ttf")
        kbps = int((LIMITE_MB * 8192) / dur - 128)
        kbps = min(kbps, 9000)
        fc = (f"[0:v]scale={W}:{H}:flags=lanczos,setsar=1,fps={FPS}[v];"
              f"[1:v]format=rgba,fade=t=in:st=0.15:d=0.35:alpha=1,fade=t=out:st=3.3:d=0.4:alpha=1[h];"
              f"[2:v]format=rgba,fade=t=in:st={dur - FIM_CARD:.2f}:d=0.3:alpha=1[e];"
              f"[v][h]overlay=(W-w)/2:175[a];[a][e]overlay=70:270,format=yuv420p[o]")
        fa = f";[0:a]afade=t=in:d=0.04,afade=t=out:st={dur - 0.15:.2f}:d=0.15,aresample=48000[au]"
        ent = ["-ss", t0, "-t", dur, "-i", f"{pasta}/original.mp4", "-loop", "1", "-t", dur, "-i", hook,
               "-loop", "1", "-t", dur, "-i", f"{pasta}/tmp/fim.png", "-filter_complex"]
        log = f"{pasta}/tmp/{n}"
        v = ["-c:v", "libx264", "-preset", "medium", "-b:v", f"{kbps}k", "-maxrate", f"{int(kbps * 1.4)}k",
             "-bufsize", f"{kbps * 2}k", "-pix_fmt", "yuv420p", "-r", FPS, "-passlogfile", log]
        ff(*ent, fc, "-map", "[o]", *v, "-pass", 1, "-an", "-f", "null", "/dev/null")
        saida = f"{pasta}/cortes/{n}.mp4"
        ff(*ent, fc + fa, "-map", "[o]", "-map", "[au]", *v, "-pass", 2, "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", saida)
        mb = os.path.getsize(saida) / 1e6
        rel.append((n, round(t0, 2), round(t1, 2), round(dur, 1), round(mb, 1)))
        print(n, f"{t0:.2f}-{t1:.2f}", f"{dur:.1f}s", f"{mb:.1f} MB", flush=True)
    json.dump(rel, open(f"{pasta}/cortes/relatorio.json", "w"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
