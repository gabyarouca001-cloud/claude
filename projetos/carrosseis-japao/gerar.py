"""Gera os carrosséis do Japão (1080x1350) a partir das fotos da pasta Japao-fotos.

Uso:  python gerar.py [roteiro|diario|criancas|todos]
Toda foto passa antes por retoque de pele (só o rosto da Samara; filhos e terceiros não) -> lib_foto.retocar.
Fontes: Instrument Serif (títulos), Inter (rótulos), Caveat (manuscrito) — baixadas do Google Fonts em /home/user/work/japao_fotos/fontes.
"""
import os, sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_foto as L

FONTES = "/home/user/work/japao_fotos/fontes"
RET = "/home/user/work/carrosseis/ret"
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saidas")
W, H = 1080, 1350

CREAM = (247, 240, 228); INK = (27, 35, 46); RED = (178, 60, 43); WHITE = (255, 255, 255)
SAND = (232, 218, 192)

def F(nome, tam):
    return ImageFont.truetype(f"{FONTES}/{nome}.ttf", tam)
SERIF = lambda t: F("InstrumentSerif-Regular", t)
SERIF_I = lambda t: F("InstrumentSerif-Italic", t)
SANS = lambda t: F("Inter-SemiBold", t)
SANS_B = lambda t: F("Inter-ExtraBold", t)
HAND = lambda t: F("Caveat-Bold", t)

# índices (esq→dir, como em lib_foto.detectar) dos rostos da Samara a retocar em cada foto
RETOQUE = {4435: "maior", 3642: [0], 4037: [0], 4138: [0], 5039: [0], 5611: [0], 6087: [2], 2554: [0], 3966: [0],
           4123: [0], 5857: [1], 2953: [1], 6045: [0], 5471: [1], 3795: [0]}

# ---------------------------------------------------------------- fotos
def foto(num):
    """Original -> retoque de pele -> cache (altura 2400)."""
    os.makedirs(RET, exist_ok=True)
    out = f"{RET}/{num}.jpg"
    if os.path.exists(out):
        return Image.open(out).convert("RGB")
    im = L.abrir(num)
    quais = RETOQUE.get(num)
    if quais:
        im, k = L.retocar(im, quais)
        print(f"  retoque {num}: {k} rosto(s)")
    s = 2400 / im.height
    im = im.resize((int(im.width * s), 2400), Image.LANCZOS)
    im.save(out, quality=95)
    return im

def recorte(im, fx=0.5, fy=0.5, zoom=1.0, tam=(W, H)):
    """Janela 4:5 (ou da proporção de tam) com âncora fx/fy (0..1) e zoom."""
    ar = tam[0] / tam[1]
    w, h = im.size
    cw = w / zoom; ch = cw / ar
    if ch > h / zoom:
        ch = h / zoom; cw = ch * ar
    x0 = (w - cw) * fx; y0 = (h - ch) * fy
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize(tam, Image.LANCZOS)

# ---------------------------------------------------------------- desenho
def largura(txt, f, esp=0):
    return sum(f.getlength(c) + esp for c in txt) - (esp if txt else 0) if esp else f.getlength(txt)

def texto(img, xy, txt, f, cor=WHITE, esp=0, sombra=0, anchor="l", alpha=1.0):
    """Texto com espaçamento entre letras e sombra suave opcional. anchor: l|m|r (horizontal)."""
    x, y = xy
    tw = largura(txt, f, esp)
    if anchor == "m": x -= tw / 2
    elif anchor == "r": x -= tw
    def pintar(d, dx, dy, c):
        if esp:
            cx = x + dx
            for ch in txt:
                d.text((cx, y + dy), ch, font=f, fill=c); cx += f.getlength(ch) + esp
        else:
            d.text((x + dx, y + dy), txt, font=f, fill=c)
    if sombra:
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        pintar(d, 0, sombra * 0.5, (0, 0, 0, int(150 * alpha)))
        lay = lay.filter(ImageFilter.GaussianBlur(sombra))
        img.alpha_composite(lay)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    pintar(d, 0, 0, tuple(cor) + (int(255 * alpha),))
    img.alpha_composite(lay)
    return tw

def gradiente(img, de="baixo", altura=0.6, forca=0.72, cor=(8, 10, 14)):
    h = int(H * altura)
    a = np.linspace(0, 1, h) ** 1.6 * forca * 255
    a = a[::-1] if de == "cima" else a
    cam = np.zeros((h, W, 4), np.uint8); cam[..., :3] = cor; cam[..., 3] = a[:, None].astype(np.uint8)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lay.paste(Image.fromarray(cam, "RGBA"), (0, 0 if de == "cima" else H - h))
    img.alpha_composite(lay)

def pilula(img, xy, txt, f, fundo=CREAM, cor=INK, pad=(34, 18), esp=2, raio=None):
    x, y = xy
    tw = largura(txt, f, esp); th = f.size
    w = int(tw + pad[0] * 2); h = int(th * 1.25 + pad[1] * 2 - th * 0.25)
    if x is None: x = (W - w) // 2
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([x, y, x + w, y + h], radius=raio or h // 2, fill=tuple(fundo) + (255,))
    img.alpha_composite(lay)
    texto(img, (x + pad[0], y + pad[1] - th * 0.04), txt, f, cor, esp=esp)
    return w, h

def seta(img, cor=WHITE, sombra=6):
    texto(img, (W - 64, H - 96), "→", SANS_B(54), cor, sombra=sombra, anchor="r")

def papel(seed=1):
    rnd = np.random.default_rng(seed)
    base = np.zeros((H, W, 3), np.float32) + np.array(CREAM, np.float32)
    base += rnd.normal(0, 3.2, (H, W, 1))
    yy, xx = np.mgrid[0:H, 0:W]
    v = ((xx - W / 2) ** 2 / (W / 2) ** 2 + (yy - H / 2) ** 2 / (H / 2) ** 2)
    base -= (v * 7)[..., None]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")

def salvar(img, pasta, n):
    os.makedirs(f"{SAIDA}/{pasta}", exist_ok=True)
    p = f"{SAIDA}/{pasta}/{n:02d}.jpg"
    img.convert("RGB").save(p, quality=93, subsampling=0)
    return p

# ================================================================ 1) ROTEIRO
def roteiro():
    pasta = "1_roteiro"; N = 9
    # 1 capa
    im = recorte(foto(4514), 0.5, 0.0, 1.0).convert("RGBA")
    gradiente(im, "cima", 0.62, 0.80)
    texto(im, (72, 92), "CIDADE POR CIDADE", SANS_B(27), CREAM, esp=7, sombra=5)
    texto(im, (66, 120), "O roteiro", SERIF(172), WHITE, sombra=14)
    texto(im, (66, 290), "do Japão", SERIF_I(172), CREAM, sombra=14)
    pilula(im, (72, H - 150), "salva pra sua viagem", SANS_B(30), CREAM, INK, esp=1)
    seta(im)
    salvar(im, pasta, 1)
    # 2 rota
    im = papel(2)
    texto(im, (72, 84), "A ROTA", SANS_B(27), RED, esp=7)
    texto(im, (68, 118), "6 destinos,", SERIF(150), INK)
    texto(im, (68, 262), "uma viagem.", SERIF_I(150), RED)
    paradas = [("Tóquio", "a cidade que nunca para"), ("Hakone", "natureza e ryokan"), ("Kyoto", "templos e tradição"),
               ("Nara", "cervos e Grande Buda"), ("Osaka", "comida e diversão"), ("Okinawa", "mar e descanso")]
    y0 = 520; passo = 118
    d = ImageDraw.Draw(im)
    for i, (c, leg) in enumerate(paradas):
        y = y0 + i * passo
        if i < len(paradas) - 1:
            for k in range(7):  # traço pontilhado vertical
                yy = y + 30 + k * 12
                d.line([(104, yy), (104, yy + 6)], fill=INK + (120,), width=3)
        d.ellipse([90, y + 6, 118, y + 34], fill=RED + (255,))
        texto(im, (150, y - 16), c, SERIF(78), INK)
        texto(im, (150 + largura(c, SERIF(78)) + 26, y + 6), leg, SANS(30), (27, 35, 46), alpha=0.62)
    texto(im, (150, y0 + 6 * passo - 10), "e volta pra Tóquio no final", HAND(54), RED)
    seta(im, INK, 0)
    salvar(im, pasta, 2)
    # 3..8 cidades
    cidades = [
        (3, 2457, (0.5, 0.15, 1.0), "01", "Tóquio", ["Shibuya à noite", "Asakusa e o templo Senso-ji", "Tokyo Skytree e Akihabara", "Harajuku e Meiji Jingu", "Ginza: compras e beleza"]),
        (4, 3642, (0.5, 0.25, 1.0), "02", "Hakone", ["Vale de Owakudani e o ovo preto", "Teleférico com vista", "Ryokan com jantar e yukata", "Hakone Open-Air Museum"]),
        (5, 4435, (0.5, 0.25, 1.0), "03", "Kyoto", ["Fushimi Inari de yukata", "Floresta de bambu de Arashiyama", "Kinkaku-ji, o templo dourado", "Nishiki Market", "Gion e o pagode Yasaka"]),
        (6, 4138, (0.5, 0.2, 1.0), "04", "Nara", ["Cervos soltos pelo parque", "Templo Todai-ji e o Grande Buda"]),
        (7, 5039, (0.5, 0.92, 1.0), "05", "Osaka", ["Dotonbori e o letreiro do Glico", "Castelo de Osaka e Tsutenkaku", "Universal e Super Nintendo World", "Katsuo-ji, o templo dos daruma"]),
        (8, 5611, (0.5, 0.55, 1.0), "06", "Okinawa", ["Miyakojima, a ilha das águas azuis", "Ponte Irabu Ohashi", "Dias de resort e praia", "Pôr do sol de tirar o fôlego"]),
    ]
    for n, num, (fx, fy, z), idx, cid, itens in cidades:
        im = recorte(foto(num), fx, fy, z).convert("RGBA")
        gradiente(im, "baixo", 0.62, 0.86)
        gradiente(im, "cima", 0.14, 0.40)
        base = H - 70
        y = base - len(itens) * 54
        for t in itens:
            texto(im, (72, y), "—  " + t, SANS(36), CREAM, sombra=6)
            y += 54
        ytit = base - len(itens) * 54 - 215
        texto(im, (72, ytit - 6), f"{idx} · DESTINO", SANS_B(24), CREAM, esp=6, sombra=5)
        texto(im, (66, ytit + 22), cid, SERIF(165), WHITE, sombra=12)
        seta(im)
        salvar(im, pasta, n)
    # 9 CTA
    im = recorte(foto(6087), 0.5, 0.18, 1.0).convert("RGBA")
    gradiente(im, "baixo", 0.55, 0.84)
    texto(im, (66, 805), "Quer o roteiro", SERIF(120), WHITE, sombra=12)
    texto(im, (66, 925), "completo?", SERIF_I(120), CREAM, sombra=12)
    texto(im, (72, 1075), "Comenta a palavra e conheça o guia", SANS(36), CREAM, sombra=6)
    texto(im, (72, 1120), "completo do Japão.", SANS(36), CREAM, sombra=6)
    pilula(im, (72, H - 140), "COMENTA  GUIA", SANS_B(36), CREAM, INK, esp=4, pad=(44, 24))
    salvar(im, pasta, 9)

# ================================================================ 2) DIÁRIO DE BORDO (polaroids)
def polaroid(foto_im, legenda=None, data=None, larg=860, rot=0.0, fx=0.5, fy=0.4, zoom=1.0, borda=36, rodape=190):
    ph = int((larg - 2 * borda) * 1.18)
    h = ph + borda + rodape
    cartao = Image.new("RGBA", (larg, h), (252, 250, 245, 255))
    cartao.paste(recorte(foto_im, fx, fy, zoom, (larg - 2 * borda, ph)), (borda, borda))
    if legenda:
        texto(cartao, (borda + 6, ph + borda + 22), legenda, HAND(70), INK)
    if data:
        texto(cartao, (larg - borda - 6, ph + borda + 110), data, SANS_B(25), RED, esp=5, anchor="r")
    return cartao

def colar(im, cartao, centro, rot, sombra=22, fita=True):
    rot_im = cartao.rotate(rot, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", rot_im.size, (0, 0, 0, 0))
    sh.putalpha(rot_im.getchannel("A").point(lambda v: int(v * 0.30)))
    sh = Image.merge("RGBA", (Image.new("L", sh.size, 0),) * 3 + (sh.getchannel("A"),)).filter(ImageFilter.GaussianBlur(sombra))
    x = int(centro[0] - rot_im.width / 2); y = int(centro[1] - rot_im.height / 2)
    im.alpha_composite(sh, (x + 8, y + 18)); im.alpha_composite(rot_im, (x, y))
    if fita:
        t = Image.new("RGBA", (200, 62), (222, 198, 150, 175)).rotate(rot * 2 - 4, expand=True, resample=Image.BICUBIC)
        im.alpha_composite(t, (int(centro[0] - t.width / 2), int(centro[1] - rot_im.height / 2 - 10)))

def diario():
    pasta = "2_diario"; N = 9
    # 1 capa: colagem de 3 polaroids
    im = papel(11)
    texto(im, (72, 84), "JAPÃO  ·  15.07 → 01.08", SANS_B(27), RED, esp=6)
    texto(im, (66, 112), "diário", SERIF_I(190), INK)
    texto(im, (66, 292), "de bordo", SERIF(190), INK)
    colar(im, polaroid(foto(4037), None, None, 520, fx=0.5, fy=0.2, rodape=90), (330, 960), -7)
    colar(im, polaroid(foto(2554), None, None, 520, fx=0.5, fy=0.4, rodape=90), (770, 900), 6)
    colar(im, polaroid(foto(5611), None, None, 520, fx=0.5, fy=0.5, rodape=90), (560, 1130), -1.5)
    texto(im, (W - 120, H - 92), "arrasta", HAND(54), RED, anchor="r"); texto(im, (W - 100, H - 90), "→", SANS_B(44), RED, anchor="r")
    salvar(im, pasta, 1)
    # 2..8 polaroids
    itens = [
        (2457, "15.07", "noite em Shibuya", (0.5, 0.2), 2.0),
        (2554, "16.07", "sorvete antes do templo", (0.5, 0.3), -2.2),
        (3966, "22.07", "bambu até o céu", (0.5, 0.3), 1.6),
        (4123, "23.07", "Nara: os cervos mandam", (0.5, 0.25), -1.8),
        (4505, "24.07", "Kinkaku-ji, dourado de verdade", (0.5, 0.4), 2.2),
        (5611, "30.07", "dia de não fazer nada", (0.5, 0.55), -2.0),
        (5857, "30.07", "o sol pediu pra ficar", (0.5, 0.35), 1.7),
    ]
    for i, (num, data, leg, (fx, fy), rot) in enumerate(itens):
        im = papel(20 + i)
        card = polaroid(foto(num), leg, data, 880, fx=fx, fy=fy)
        colar(im, card, (W // 2, H // 2 - 6), rot)
        salvar(im, pasta, i + 2)
    # 9 CTA
    im = papel(40)
    texto(im, (W / 2, 78), "gostou do diário?", HAND(112), RED, anchor="m")
    colar(im, polaroid(foto(6045), None, None, 560, fx=0.5, fy=0.3, rodape=90), (W // 2, 590), -3)
    texto(im, (W / 2, 975), "Quer ver tudo isso no", SERIF(84), INK, anchor="m")
    texto(im, (W / 2, 1062), "guia completo do Japão?", SERIF_I(84), RED, anchor="m")
    pilula(im, (None, 1196), "COMENTA  GUIA", SANS_B(36), INK, CREAM, esp=4, pad=(60, 24))
    salvar(im, pasta, 9)

# ================================================================ 3) JAPÃO COM CRIANÇAS (lista numerada)
def cartao_item(im, num, cidade, titulo, info):
    x0, x1, base = 56, W - 56, 1292
    xt = x0 + 40 + 215; maxw = x1 - 36 - xt
    ft = SERIF(74); fi = SANS(29)
    lt = quebrar(titulo, ft, maxw); li = quebrar(info, fi, maxw)
    altura = 34 + 34 + len(lt) * 78 + 12 + len(li) * 40 + 34
    y0 = base - altura
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    ds.rounded_rectangle([x0, y0 + 10, x1, base + 10], 26, fill=(0, 0, 0, 90)); sh = sh.filter(ImageFilter.GaussianBlur(18))
    im.alpha_composite(sh)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([x0, y0, x1, base], 26, fill=CREAM + (250,))
    im.alpha_composite(lay)
    texto(im, (x0 + 40, y0 + 10), num, SERIF_I(190), RED)
    y = y0 + 30
    texto(im, (xt, y), cidade, SANS_B(22), RED, esp=5)
    y += 34
    for ln in lt:
        texto(im, (xt, y), ln, ft, INK); y += 78
    y += 12
    for ln in li:
        texto(im, (xt, y), ln, fi, INK, alpha=0.75); y += 40

def quebrar(txt, f, maxw):
    palavras = txt.split(); linhas = []; cur = ""
    for p in palavras:
        t = (cur + " " + p).strip()
        if f.getlength(t) <= maxw: cur = t
        else: linhas.append(cur); cur = p
    if cur: linhas.append(cur)
    return linhas

def criancas():
    pasta = "3_criancas"; N = 9
    # 1 capa
    im = recorte(foto(3477), 0.5, 0.0, 1.0).convert("RGBA")
    gradiente(im, "baixo", 0.58, 0.85)
    gradiente(im, "cima", 0.14, 0.45)
    texto(im, (72, 84), "7 PROGRAMAS EM FAMÍLIA", SANS_B(27), CREAM, esp=7, sombra=5)
    texto(im, (66, 835), "Japão", SERIF(190), WHITE, sombra=14)
    texto(im, (66, 1010), "com crianças", SERIF_I(165), CREAM, sombra=14)
    pilula(im, (72, H - 112), "salva pra próxima viagem", SANS_B(30), CREAM, INK, esp=1)
    seta(im)
    salvar(im, pasta, 1)
    itens = [
        (4762, (0.5, 0.3, 1.0), "01", "OSAKA · UNIVERSAL STUDIOS JAPAN", "Super Nintendo World", "A pulseira Power-Up Band transforma o parque num jogo: dá pra coletar moedas."),
        (2860, (0.5, 0.35, 1.0), "02", "TÓQUIO", "Sumô de pertinho", "Apresentação ao vivo, com direito a foto ao lado dos lutadores no final."),
        (2989, (0.5, 0.25, 1.0), "03", "TÓQUIO", "Café com bichinhos", "Hamsters, porquinhos, corujas e pintinhos pertinho das crianças."),
        (4363, (0.25, 0.48, 1.35), "04", "EXPERIÊNCIA CULTURAL", "Aula de samurai", "Traje tradicional, espada e um mestre ensinando os movimentos."),
        (4186, (0.5, 0.4, 1.0), "05", "NARA", "Cervos de Nara", "Os biscoitinhos são vendidos no parque: os cervos vêm até você."),
        (3750, (0.5, 0.3, 1.0), "06", "KYOTO", "Yukata em Fushimi Inari", "Dá pra alugar o yukata e passear entre os milhares de portais vermelhos."),
        (3453, (0.5, 0.4, 1.0), "07", "HAKONE", "Noite de ryokan", "Hospedagem tradicional japonesa, com jantar servido e todo mundo de yukata."),
    ]
    for i, (num, (fx, fy, z), idx, cid, tit, info) in enumerate(itens):
        im = recorte(foto(num), fx, fy, z).convert("RGBA")
        gradiente(im, "baixo", 0.35, 0.5)
        gradiente(im, "cima", 0.14, 0.40)
        cartao_item(im, idx, cid, tit, info)
        salvar(im, pasta, i + 2)
    # 9 CTA
    im = recorte(foto(5471), 0.5, 0.45, 1.0).convert("RGBA")
    gradiente(im, "cima", 0.45, 0.72)
    texto(im, (66, 96), "Quer montar esse", SERIF(110), WHITE, sombra=12)
    texto(im, (66, 214), "roteiro em família?", SERIF_I(110), CREAM, sombra=12)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([56, 1040, W - 56, 1292], 26, fill=CREAM + (250,)); im.alpha_composite(lay)
    texto(im, (96, 1068), "Comenta a palavra e conheça o", SANS(34), INK)
    texto(im, (96, 1114), "guia completo do Japão.", SANS(34), INK)
    pilula(im, (96, 1190), "COMENTA  GUIA", SANS_B(34), RED, WHITE, esp=4, pad=(40, 20))
    salvar(im, pasta, 9)

if __name__ == "__main__":
    alvo = sys.argv[1] if len(sys.argv) > 1 else "todos"
    if alvo in ("roteiro", "todos"): roteiro()
    if alvo in ("diario", "todos"): diario()
    if alvo in ("criancas", "todos"): criancas()
    print("ok")
