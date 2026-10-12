"""Mapeia as inserções de texto já gravadas no vídeo da editora (DEEP EP3 Reels): detecta texto quadro a quadro
(RapidOCR), junta em intervalos e guarda a caixa ocupada -> insercoes_editora.json. Também detecta os cortes.
Uso: python3 mapear_insercoes.py video.mp4 saida.json"""
import json
import subprocess
import sys

import numpy as np
from rapidocr_onnxruntime import RapidOCR

FPS, W, H = 5, 540, 960
arq, saida = sys.argv[1], sys.argv[2]
ocr = RapidOCR()
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", arq, "-vf", f"fps={FPS},scale={W}:{H}", "-f", "rawvideo",
                      "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
quadros, n = [], 0
while True:
    b = p.stdout.read(W * H * 3)
    if len(b) < W * H * 3:
        break
    img = np.frombuffer(b, np.uint8).reshape(H, W, 3)
    res, _ = ocr(img, use_det=True, use_cls=False, use_rec=True)
    caixas = []
    for box, txt, conf in res or []:
        xs, ys = [q[0] for q in box], [q[1] for q in box]
        if float(conf) < 0.5 or len(txt.strip()) < 2:
            continue
        caixas.append(dict(t=round(n / FPS, 2), x0=min(xs) / W, x1=max(xs) / W, y0=min(ys) / H, y1=max(ys) / H, txt=txt))
    quadros.append(caixas)
    n += 1
    if n % 150 == 0:
        print(n / FPS, "s", flush=True)
# intervalos: quadros consecutivos com texto (tolerância de 1 quadro)
ints, cur = [], None
for i, cx in enumerate(quadros):
    t = i / FPS
    if cx:
        if cur and t - cur["fim"] <= 2 / FPS:
            cur["fim"] = t
            cur["caixas"] += cx
        else:
            cur = dict(ini=t, fim=t, caixas=list(cx))
            ints.append(cur)
out = []
for it in ints:
    c = it["caixas"]
    txts = []
    for k in c:
        if k["txt"] not in txts:
            txts.append(k["txt"])
    out.append(dict(ini=round(it["ini"], 2), fim=round(it["fim"] + 1 / FPS, 2), y0=round(min(k["y0"] for k in c), 3),
                    y1=round(max(k["y1"] for k in c), 3), x0=round(min(k["x0"] for k in c), 3),
                    x1=round(max(k["x1"] for k in c), 3), textos=txts[:8]))
json.dump(out, open(saida, "w"), ensure_ascii=False, indent=1)
for o in out:
    print(f"{o['ini']:7.2f}-{o['fim']:7.2f}  y {o['y0']:.2f}-{o['y1']:.2f}  x {o['x0']:.2f}-{o['x1']:.2f}  {' | '.join(o['textos'])}")
