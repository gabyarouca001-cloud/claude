"""Confere as inserções sobre os quadros reais do vídeo. Uso (em /home/user/work/ep): python3 teste_quadros.py nome t1 t2 ... -> teste_<nome>.png"""
import json, subprocess, sys, os
from PIL import Image
S = int(os.environ.get("S", "1"))
man = json.load(open(f"ov_{S}/manifesto.json"))
nome = sys.argv[1]
ts = [float(x) for x in sys.argv[2:]]
ins = next(m for m in man["inserts"] if m["nome"] == nome)
tiles = []
for t in ts:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", "original.mp4", "-frames:v", "1", "-vf", "scale=1080:1920", "q.png"], check=True)
    base = Image.open("q.png").convert("RGBA")
    k = int(round((t - ins["t0"]) * 30))
    if 0 <= k < ins["n"]:
        ov = Image.open(f"ov_{S}/{nome}/{k:04d}.png").convert("RGBA")
        if ov.size != base.size: ov = ov.resize(base.size)
        base.alpha_composite(ov)
    tiles.append(base.convert("RGB").resize((432, 768)))
sh = Image.new("RGB", (432 * len(tiles), 768))
for i, t in enumerate(tiles): sh.paste(t, (i * 432, 0))
sh.save(f"teste_{nome}.png")
