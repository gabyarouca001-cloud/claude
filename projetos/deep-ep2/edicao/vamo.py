"""'Vamo de DEEP?' atravessando a tela atrás da cabeça dela (como no EP1): texto amarelo em Playfair Black,
inclinado, com a máscara de pessoa (selfie_multiclass, LiteRT) recortando o texto. Gera PNGs 4K com alfa."""
import json
import os
import subprocess
import sys

import numpy as np
from ai_edge_litert.interpreter import Interpreter
from PIL import Image, ImageDraw, ImageFilter, ImageFont

PREVIA = os.environ.get("PREVIA") == "1"
FPS = 30
W, H, PASTA, SAIDA = (1280, 720, "seg720", "vamo720") if PREVIA else (3840, 2160, "seg", "vamo")
AMARELO = (252, 237, 192)
versao = sys.argv[1] if len(sys.argv) > 1 else "youtube"
plano = json.load(open(f"plano_{versao}.json"))["segmentos"]
pal = [w for s in json.load(open("final_youtube.json")) for w in s["words"]]

# janela: do fim de "lugar?" até a vinheta
vin = next(s for s in plano if s["fonte"] == "vinheta")
t1 = vin["t"]
vamos = next(w for w in pal if w["w"].strip().lower().startswith("vamos") and w["s"] < t1)
t0 = max(0.0, vamos["s"] - 0.45)
n = int(round((t1 - t0) * FPS))

# quadros da timeline nesse intervalo (a partir dos segmentos renderizados)
os.makedirs(SAIDA, exist_ok=True)
lista = [l.split("'")[1] for l in open(f"{PASTA}/lista_{versao}.txt") if l.strip()]
quadros = []
for k in range(n):
    t = t0 + k / FPS
    for s, arq in zip(plano, lista):
        d = s["fim"] - s["ini"]
        if s["t"] <= t < s["t"] + d:
            quadros.append((arq, min(t - s["t"], d - 1.5 / FPS)))
            break

it = Interpreter(model_path="/home/user/work/modelos/selfie_multiclass.tflite")
it.allocate_tensors()
ent, sai = it.get_input_details()[0], it.get_output_details()[0]


def mascara(img):
    x = np.asarray(img.resize((256, 256)), np.float32)[None] / 255.0
    it.set_tensor(ent["index"], x)
    it.invoke()
    y = it.get_tensor(sai["index"])[0]
    p = 1 - (np.exp(y) / np.exp(y).sum(-1, keepdims=True))[..., 0]
    p = np.clip((p - 0.2) / 0.6, 0, 1)
    m = Image.fromarray((p * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(6 * W / 3840)), np.float32) / 255


# texto (desenhado uma vez, grande, inclinado)
fonte = ImageFont.truetype("fonts/PlayfairDisplay-Black.ttf", int(420 * W / 3840))
txt = "Vamo de DEEP?"
l, t_, r, b = fonte.getbbox(txt)
m_ = int(80 * W / 3840)
base = Image.new("RGBA", (r - l + m_, b - t_ + m_), (0, 0, 0, 0))
ImageDraw.Draw(base).text((m_ // 2 - l, m_ // 2 - t_), txt, font=fonte, fill=AMARELO + (255,))
base = base.rotate(8, resample=Image.BICUBIC, expand=True)
tw, th = base.size

for k, (arq, off) in enumerate(quadros):
    fr = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{off:.4f}", "-i", f"{PASTA}/{arq}", "-frames:v", "1",
                         "-vf", "scale=1920:1080", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                        capture_output=True, check=True).stdout
    img = Image.frombytes("RGB", (1920, 1080), fr)
    m = mascara(img)
    prog = k / max(1, n - 1)
    ease = 1 - (1 - prog) ** 2                       # desacelera no fim
    x = int(-tw * 0.55 + ease * (W * 0.5 - tw * 0.5 + tw * 0.55))
    y = int(H * 0.06)
    camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    camada.alpha_composite(base, (max(x, -tw + 1), y)) if x >= 0 else camada.paste(base, (x, y), base)
    a = np.asarray(camada, np.float32)
    a[..., 3] *= (1 - m)                             # ela fica na frente do texto
    alfa_fade = min(1.0, k / 4, (n - 1 - k) / 3 + 0.35)
    a[..., 3] *= alfa_fade
    Image.fromarray(a.astype(np.uint8)).save(f"{SAIDA}/{k:04d}.png")
json.dump(dict(ini=round(t0 * FPS) / FPS, quadros=n), open(f"{SAIDA}_{versao}.json", "w"))
print("vamo", versao, t0, t1, n)
