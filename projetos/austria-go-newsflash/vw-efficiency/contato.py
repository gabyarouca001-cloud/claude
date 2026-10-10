"""Folha de contato para conferir cada plano (3 quadros, já com o recorte aplicado). Uso (em /home/user/work/gn): python3 contato.py de ate saida.png"""
import subprocess, sys, os, tempfile
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl as E, resolver as R
FILM = {35: "films/V2026NR0035.mp4", 36: "films/V2026NR0036.mp4"}
def vf(f):
    if f == 36:
        z = E.ZOOM36
        return f"crop=iw/{z}:ih/{z}:(iw-iw/{z})/2:ih*0.01,scale=480:270"
    return "scale=480:270"
de, ate, saida = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
ev = [e for e in R.resolver() if de <= e["i"] <= ate]
tw, th = 480, 270
folha = Image.new("RGB", (tw * 3, (th + 0) * len(ev)))
with tempfile.TemporaryDirectory() as tmp:
    for r, e in enumerate(ev):
        for c, k in enumerate((0.05, 0.5, 0.95)):
            t = e["ss"] + e["dur"] * k
            arq = f"{tmp}/{r}_{c}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", FILM[e["f"]], "-frames:v", "1", "-vf", vf(e["f"]), arq], check=True)
            folha.paste(Image.open(arq), (c * tw, r * th))
        ImageDraw.Draw(folha).text((6, r * th + 4), f"#{e['i']} f{e['f']} {e['obs']}", fill=(255, 255, 0))
folha.save(saida)
