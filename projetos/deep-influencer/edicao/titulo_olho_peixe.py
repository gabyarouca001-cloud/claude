"""Gera o título do gancho com efeito olho de peixe (lente convexa), em amarelo manteiga."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AMARELO = (252, 237, 192)
W, H = 1000, 340          # tamanho da camada do título
FORCA = 0.38              # intensidade da lente (0 = sem efeito)


def olho_de_peixe(img, forca=FORCA):
    """Distorção radial convexa: amplia o centro e curva as bordas."""
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    raio = np.hypot(cx, cy)
    nx, ny = (xx - cx) / raio, (yy - cy) / raio
    r = np.hypot(nx, ny)
    # raio de origem < raio de destino no centro -> centro ampliado
    fator = np.where(r > 0, (1 - forca) + forca * r, 1 - forca)
    sx = cx + nx * fator * raio
    sy = cy + ny * fator * raio
    # amostragem bilinear
    x0, y0 = np.floor(sx).astype(int), np.floor(sy).astype(int)
    fx, fy = (sx - x0)[..., None], (sy - y0)[..., None]
    x0c, x1c = np.clip(x0, 0, w - 1), np.clip(x0 + 1, 0, w - 1)
    y0c, y1c = np.clip(y0, 0, h - 1), np.clip(y0 + 1, 0, h - 1)
    out = (a[y0c, x0c] * (1 - fx) * (1 - fy) + a[y0c, x1c] * fx * (1 - fy)
           + a[y1c, x0c] * (1 - fx) * fy + a[y1c, x1c] * fx * fy)
    fora = ((sx < 0) | (sx > w - 1) | (sy < 0) | (sy > h - 1))[..., None]
    out = np.where(fora, 0, out)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA")


def titulo(linhas, saida, fonte="fonts/PlayfairMedium.ttf"):
    tam = 84
    f = ImageFont.truetype(fonte, tam)
    # reduz a fonte até a linha mais longa caber com folga
    while max(f.getlength(l) for l in linhas) > W * 0.74 and tam > 50:
        tam -= 2
        f = ImageFont.truetype(fonte, tam)
    texto = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(texto)
    alt = tam * 1.02
    y = (H - alt * len(linhas)) / 2
    for l in linhas:
        d.text((W / 2, y + alt / 2), l, font=f, fill=AMARELO + (255,), anchor="mm")
        y += alt
    texto = olho_de_peixe(texto)
    # sombra suave para ler sobre cabelo/parede
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sombra.putalpha(texto.getchannel("A").point(lambda v: int(v * 0.55)))
    sombra = sombra.filter(ImageFilter.GaussianBlur(7))
    final = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    final.alpha_composite(sombra, (3, 5))
    final.alpha_composite(texto)
    final.save(saida)


if __name__ == "__main__":
    titulo(["Como ser influencer:", "o sonho vs. a realidade"], "teste_titulo.png")
