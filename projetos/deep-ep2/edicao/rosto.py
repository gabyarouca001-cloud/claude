"""Centro do rosto da Samara em cada segmento do plano (para os zooms ficarem sempre nela).
Modelo selfie_multiclass (LiteRT): classe 3 = pele do rosto. Mede em 3 quadros do segmento (no take original,
sem zoom) e guarda a média em coordenadas relativas (0–1) -> rosto_<versao>.json"""
import json
import subprocess
import sys

import numpy as np
from ai_edge_litert.interpreter import Interpreter
from PIL import Image

from audio import FONTES

it = Interpreter(model_path="/home/user/work/modelos/selfie_multiclass.tflite")
it.allocate_tensors()
ent, sai = it.get_input_details()[0], it.get_output_details()[0]


def quadro(fonte, t):
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", FONTES[fonte], "-frames:v", "1",
                        "-vf", "scale=512:288", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombytes("RGB", (512, 288), b)


def rosto(img):
    it.set_tensor(ent["index"], np.asarray(img.resize((256, 256)), np.float32)[None] / 255.0)
    it.invoke()
    y = it.get_tensor(sai["index"])[0]
    m = y.argmax(-1) == 3
    if m.sum() < 30:
        return None
    ys, xs = np.nonzero(m)
    return float(xs.mean() / 256), float(ys.mean() / 256)


versao = sys.argv[1] if len(sys.argv) > 1 else "youtube2"
segs = json.load(open(f"plano_{versao}.json"))["segmentos"]
cache, out = {}, []
for i, s in enumerate(segs):
    pts = []
    for f in (0.2, 0.5, 0.8):
        t = round(s["ini"] + (s["fim"] - s["ini"]) * f, 1)
        k = (s["fonte"], t)
        if k not in cache:
            cache[k] = rosto(quadro(s["fonte"], t))
        if cache[k]:
            pts.append(cache[k])
    out.append(list(np.mean(pts, 0)) if pts else None)
    if i % 25 == 0:
        print(i, len(segs), out[-1], flush=True)
# segmentos sem detecção herdam o vizinho
for i in range(len(out)):
    if out[i] is None:
        out[i] = next((out[j] for j in list(range(i - 1, -1, -1)) + list(range(i + 1, len(out))) if out[j]), [0.5, 0.3])
json.dump(out, open(f"rosto_{versao}.json", "w"))
print("FIM")
