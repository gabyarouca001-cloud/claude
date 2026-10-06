"""Thumb do DEEP EP2 (padrão do EP1): Samara à direita, gradiente escuro à esquerda, texto em 3 níveis.
Uso: python3 thumb.py take1.mp4 18.2 x0,y0,largura saida.jpg"""
import subprocess
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1280, 720


def suavizar_pele(img, forca=0.75):
    """limpeza de pele: filtro bilateral só nas áreas de pele (modelo selfie_multiclass: pele do rosto/corpo),
    com máscara esfumada; olhos, sobrancelhas, boca e cabelo ficam nítidos"""
    import cv2
    import numpy as np
    from ai_edge_litert.interpreter import Interpreter
    it = Interpreter(model_path="/home/user/work/modelos/selfie_multiclass.tflite")
    it.allocate_tensors()
    e, s_ = it.get_input_details()[0], it.get_output_details()[0]
    it.set_tensor(e["index"], np.asarray(img.resize((256, 256)), np.float32)[None] / 255.0)
    it.invoke()
    cls = it.get_tensor(s_["index"])[0].argmax(-1)
    m = np.isin(cls, (2, 3)).astype(np.float32)
    m = cv2.resize(m, img.size, interpolation=cv2.INTER_LINEAR)
    m = cv2.erode(m, np.ones((5, 5), np.uint8))
    m = cv2.GaussianBlur(m, (0, 0), 6)[..., None] * forca
    a = np.asarray(img).astype(np.float32)
    liso = cv2.bilateralFilter(a.astype(np.uint8), 0, 30, 9).astype(np.float32)
    liso = cv2.GaussianBlur(liso, (0, 0), 1.2) * 0.5 + liso * 0.5
    # devolve um pouco de textura fina para não ficar "plástico"
    detalhe = a - cv2.GaussianBlur(a, (0, 0), 0.8)
    out = a * (1 - m) + (liso + detalhe * 0.35) * m
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))
AMARELO = (252, 237, 192)
FONTES = "/home/user/work/ep2/fonts/"
arq, t, crop, saida = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4]
b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", arq, "-frames:v", "1", "-f", "rawvideo",
                    "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
img = Image.frombytes("RGB", (3840, 2160), b)
x0, y0, cw = (int(v) for v in crop.split(","))
img = img.crop((x0, y0, x0 + cw, y0 + int(cw * 9 / 16))).resize((W, H), Image.LANCZOS)
img = suavizar_pele(img)
img = ImageEnhance.Contrast(img).enhance(1.10)
img = ImageEnhance.Color(img).enhance(1.06)
img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
grad = Image.new("L", (W, H))
for x in range(W):
    grad.paste(int(max(0, 1 - x / (W * 0.62)) ** 1.3 * 215), (x, 0, x + 1, H))
img = Image.composite(Image.new("RGB", (W, H), (18, 14, 12)), img, grad)

serif = ImageFont.truetype(FONTES + "PlayfairItalic.ttf", 54)
bold = ImageFont.truetype(FONTES + "InterBlack.ttf", 84)
grande = ImageFont.truetype(FONTES + "InterBlack.ttf", 128)
marca = ImageFont.truetype(FONTES + "InterMedium.ttf", 22)


def texto(xy, t, fonte, cor, sombra=6):
    camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(camada).text((xy[0] + 3, xy[1] + 5), t, font=fonte, fill=(0, 0, 0, 170))
    camada = camada.filter(ImageFilter.GaussianBlur(sombra))
    img.paste(camada, (0, 0), camada)
    ImageDraw.Draw(img).text(xy, t, font=fonte, fill=cor)


LARG = 590                       # o texto não passa da mão dela


def caber(caminho, tam, t):
    f = ImageFont.truetype(caminho, tam)
    while f.getlength(t) > LARG and tam > 20:
        tam -= 2
        f = ImageFont.truetype(caminho, tam)
    return f


L1, L2, L3 = (sys.argv[5:8] + ["pensou em alguém?", "GUARDA ESSE", "NOME."][len(sys.argv[5:8]):])[:3]
x = 64
f1 = caber(FONTES + "PlayfairItalic.ttf", 54, L1)
f2 = caber(FONTES + "InterBlack.ttf", 84, L2)
f3 = caber(FONTES + "InterBlack.ttf", 128, L3)
y3 = 600 - f3.size * 1.05
y2 = y3 - f2.size * 1.02
y1 = y2 - f1.size * 1.25
texto((x, y1), L1, f1, (255, 255, 255))
texto((x, y2), L2, f2, (255, 255, 255))
texto((x, y3), L3, f3, AMARELO)
ImageDraw.Draw(img).rectangle([x, 70, x + 5, 102], fill=AMARELO)
texto((x + 18, 72), "D E E P   ·   S A M A R A   C H E C O N", marca, (255, 255, 255), sombra=3)
img.save(saida, quality=92)
print(saida, img.size)
