"""Acha inserções de vídeo (B-roll em tela cheia) no vídeo da editora: trechos em que o rosto da Samara some
(modelo selfie_multiclass, classe 3 = pele do rosto) ou muda muito de tamanho. Uso: python3 ... video.mp4"""
import subprocess
import sys

import numpy as np
from ai_edge_litert.interpreter import Interpreter

it = Interpreter(model_path="/home/user/work/modelos/selfie_multiclass.tflite")
it.allocate_tensors()
e, s = it.get_input_details()[0], it.get_output_details()[0]
FPS, W, H = 4, 144, 256
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", sys.argv[1], "-vf", f"fps={FPS},scale={W}:{H}", "-f", "rawvideo",
                      "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
area, n = [], 0
while True:
    b = p.stdout.read(W * H * 3)
    if len(b) < W * H * 3:
        break
    img = np.frombuffer(b, np.uint8).reshape(H, W, 3)
    # o modelo é quadrado 256x256: centraliza o quadro vertical num canvas
    tela = np.zeros((256, 256, 3), np.uint8)
    tela[:, 56:200] = img
    it.set_tensor(e["index"], tela[None].astype(np.float32) / 255)
    it.invoke()
    cls = it.get_tensor(s["index"])[0].argmax(-1)
    area.append(float((cls == 3).mean()))
    n += 1
a = np.array(area)
ref = np.median(a)
fora = a < ref * 0.35
ints, i = [], 0
while i < len(fora):
    if fora[i]:
        j = i
        while j < len(fora) and fora[j]:
            j += 1
        if j - i >= 2:
            ints.append((i / FPS, j / FPS))
        i = j
    else:
        i += 1
print("área mediana do rosto", round(ref, 4))
for a0, a1 in ints:
    print(f"vídeo inserido (sem o rosto dela): {a0:6.2f} -> {a1:6.2f}")
