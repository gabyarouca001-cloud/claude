import sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

S = sys.argv[1]
W, H = 1280, 720
AMARELO = (252, 237, 192)
img = Image.open(f"{S}/base.png").convert("RGB")
x0, y0, cw = 250, 150, 2380
img = img.crop((x0, y0, x0 + cw, y0 + int(cw * 9 / 16))).resize((W, H), Image.LANCZOS)
img = ImageEnhance.Contrast(img).enhance(1.10)
img = ImageEnhance.Color(img).enhance(1.08)
img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))

# gradiente escuro à esquerda para o texto
grad = Image.new("L", (W, H))
for x in range(W):
    grad.paste(int(max(0, 1 - x / (W * 0.60)) ** 1.3 * 205), (x, 0, x + 1, H))
img = Image.composite(Image.new("RGB", (W, H), (18, 14, 12)), img, grad)

d = ImageDraw.Draw(img)
serif = ImageFont.truetype("fonts/PlayfairItalic.ttf", 50)
bold = ImageFont.truetype("fonts/InterBlack.ttf", 76)
grande = ImageFont.truetype("fonts/InterBlack.ttf", 132)
marca = ImageFont.truetype("fonts/InterMedium.ttf", 22)


def texto(xy, t, fonte, cor, sombra=6):
    camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(camada).text((xy[0] + 3, xy[1] + 5), t, font=fonte, fill=(0, 0, 0, 170))
    camada = camada.filter(ImageFilter.GaussianBlur(sombra))
    img.paste(camada, (0, 0), camada)
    ImageDraw.Draw(img).text(xy, t, font=fonte, fill=cor)


x = 64
texto((x, 318), "4 milhões de influencers.", serif, (255, 255, 255))
texto((x, 386), "VOCÊ QUER SER", bold, (255, 255, 255))
texto((x, 452), "MAIS UM?", grande, AMARELO)
# assinatura discreta
d = ImageDraw.Draw(img)
d.rectangle([x, 70, x + 5, 102], fill=AMARELO)
texto((x + 18, 72), "D E E P   ·   S A M A R A   C H E C O N", marca, (255, 255, 255), sombra=3)
img.save("thumb_DEEP.png", optimize=True)
img.save("thumb_DEEP.jpg", quality=92)
print(img.size)
