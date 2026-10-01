"""Centro horizontal da Samara (máscara de pessoa) por bloco do plano do Reels, para o recorte 9:16."""
import json
import subprocess

import numpy as np
from ai_edge_litert.interpreter import Interpreter
from PIL import Image

from audio import FONTES

it = Interpreter(model_path="/home/user/work/modelos/selfie_multiclass.tflite")
it.allocate_tensors()
ent, sai = it.get_input_details()[0], it.get_output_details()[0]


def centro(arq, t):
    fr = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", arq, "-frames:v", "1", "-vf", "scale=256:256",
                         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(fr, np.uint8).reshape(256, 256, 3).astype(np.float32)[None] / 255
    it.set_tensor(ent["index"], x)
    it.invoke()
    y = it.get_tensor(sai["index"])[0]
    p = 1 - (np.exp(y) / np.exp(y).sum(-1, keepdims=True))[..., 0]
    p = p[:150]                                  # cabeça e tronco (ignora pernas/mãos baixas)
    col = p.sum(0)
    return float((col * np.arange(256)).sum() / (col.sum() + 1e-6) / 256)


if __name__ == "__main__":
    segs = json.load(open("plano_reels.json"))["segmentos"]
    blocos = {}
    for i, s in enumerate(segs):
        blocos.setdefault(tuple(s["ns"]), []).append(i)
    cx = {}
    for k, idx in blocos.items():
        amostras = [centro(FONTES[segs[i]["fonte"]], (segs[i]["ini"] + segs[i]["fim"]) / 2) for i in idx[::max(1, len(idx) // 3)][:3]]
        for i in idx:
            cx[i] = float(np.median(amostras))
    abertura = {"0": centro("inicio_editora.mp4", 2.0), "1": centro("inicio_editora.mp4", 5.5)}
    json.dump({"segmentos": cx, "abertura": abertura}, open("centros_reels.json", "w"))
    print(len(blocos), "blocos;", "faixa", min(cx.values()), max(cx.values()), "abertura", abertura)
