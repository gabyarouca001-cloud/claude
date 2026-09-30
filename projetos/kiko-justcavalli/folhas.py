"""Folhas de contato: 6 quadros por take, 8 takes por imagem (com tonemap HDR->SDR no iPhone)."""
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageDraw, ImageFont

HLG = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
       "zscale=t=bt709:m=bt709:r=tv,format=yuv420p,")
os.makedirs("folhas/q", exist_ok=True)
infos = {}
for linha in open("info.txt"):
    nome, dur = linha.split()[:2]
    h, m, s = dur.split(":")
    infos[nome] = int(h) * 3600 + int(m) * 60 + float(s)


def quadro(args):
    nome, i, t = args
    saida = f"folhas/q/{nome}_{i}.jpg"
    if os.path.exists(saida):
        return
    vf = (HLG if nome.startswith("IMG") else "") + "scale=180:320"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", f"bruto/{nome}",
                    "-frames:v", "1", "-vf", vf, "-q:v", "4", saida])


tarefas = []
for nome, dur in infos.items():
    if dur < 0.5:
        continue
    for i in range(6):
        tarefas.append((nome, i, dur * (i + 0.5) / 6))
with ThreadPoolExecutor(6) as ex:
    list(ex.map(quadro, tarefas))

fonte = ImageFont.truetype("/home/user/work/fonts/InterExtraBold.ttf", 18)
nomes = sorted(n for n, d in infos.items() if d >= 0.5)
for p in range(0, len(nomes), 8):
    folha = Image.new("RGB", (6 * 180 + 150, 8 * 320), "black")
    d = ImageDraw.Draw(folha)
    for r, nome in enumerate(nomes[p:p + 8]):
        d.text((6, r * 320 + 10), re.sub(r"\..*", "", nome), font=fonte, fill="yellow")
        d.text((6, r * 320 + 36), f"{infos[nome]:.1f}s", font=fonte, fill="white")
        for i in range(6):
            q = f"folhas/q/{nome}_{i}.jpg"
            if os.path.exists(q):
                folha.paste(Image.open(q), (150 + i * 180, r * 320))
    folha.save(f"folhas/folha_{p // 8:02d}.jpg", quality=80)
print(len(nomes), "takes")
