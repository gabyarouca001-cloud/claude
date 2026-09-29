"""Etapa 4: textos (ASS), gráfico animado (PNG) e efeitos sonoros, no tempo da timeline final."""
import json
import os
import re
import subprocess
import unicodedata

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SR = 48000
FPS = 25
plano = json.load(open("plano.json"))
palavras = [w for s in json.load(open("transcricao.json")) for w in s["words"]]


def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if unicodedata.category(c) != "Mn"))


TOKENS = [norm(w["w"]) for w in palavras]


def achar(frase, depois):
    """Início (tempo de origem) da frase, procurando a partir de `depois`."""
    alvo = [norm(p) for p in frase.split()]
    for i, w in enumerate(palavras):
        if w["s"] < depois:
            continue
        if TOKENS[i:i + len(alvo)] == alvo:
            return w["s"], palavras[i + len(alvo) - 1]["e"]
    raise ValueError(f"não achei {frase!r} depois de {depois}")


def mapa(t):
    """Tempo de origem -> tempo na timeline final."""
    saida = 0.0
    for s in plano["segmentos"]:
        if t < s["ini"]:
            return saida
        if t <= s["fim"]:
            return saida + t - s["ini"]
        saida += s["fim"] - s["ini"]
    return saida


# ----------------------------------------------------------------------------- inserções
# tipo, frase-âncora, procurar depois de, duração (ou frase final), conteúdo
INS = [
    ("titulo", "30", 72, 3.4, dict(serif="30% dos criadores", bold="NÃO MONETIZAM")),
    ("titulo", "não tem negócio", 96, "tem um cachê", dict(serif="a maioria que vive de publi", bold="NÃO TEM NEGÓCIO")),
    ("titulo", "tem um cachê", 99, 2.8, dict(serif="tem", bold="CACHÊ", eco="CACHÊ")),
    ("lista", "algoritmo mudar", 111, "agora negócio", dict(titulo="o cachê acaba quando…", itens=[
        ("algoritmo mudar", 111, "o algoritmo muda"),
        ("marca mudar", 116, "a marca muda de estratégia"),
        ("alguém mais novo", 119, "chega alguém mais novo")])),
    ("titulo", "outra coisa", 124, 2.2, dict(serif="negócio é", bold="OUTRA COISA")),
    ("capitulo", "mas por que tanta", 132, 3.6, dict(texto="POR QUE TODO MUNDO QUER ENTRAR")),
    ("titulo", "o resultado", 145, 2.3, dict(serif="a gente vê o resultado,", bold="NÃO O PROCESSO")),
    ("titulo", "18 meses", 148, 3.6, dict(serif="postando sem retorno", bold="18 MESES", eco="18")),
    ("titulo", "ilusão de controle", 160, 2.6, dict(serif="a ilusão de", bold="CONTROLE", eco="CONTROLE")),
    ("grafico", "o alcance orgânico", 181, "e aí aquela liberdade", dict(serif="alcance orgânico no Instagram", bold="-35%")),
    ("titulo", "dependência total", 192, 2.4, dict(serif="a liberdade vira", bold="DEPENDÊNCIA TOTAL")),
    ("capitulo", "e as marcas", 201, 3.6, dict(texto="O QUE O MERCADO COMPRA HOJE")),
    ("titulo", "quase 10 anos", 206, 2.8, dict(serif="no mercado há quase", bold="10 ANOS")),
    ("titulo", "era alcance", 218, 3.0, dict(serif="antes, as marcas compravam", bold="ALCANCE")),
    ("titulo", "comprando confiança", 237, 3.0, dict(serif="hoje, elas compram", bold="CONFIANÇA", eco="CONFIANÇA")),
    ("versus", "vale mais do que", 262, "porque vitrine", dict()),
    ("capitulo", "então qual é a diferença", 284, 3.8, dict(texto="QUEM SOBREVIVE × QUEM CONSTRÓI")),
    ("titulo", "três coisas", 301, 2.0, dict(serif="são", bold="3 COISAS", eco="3")),
    ("titulo", "ponto de vista próprio", 303, "nixo é categoria", dict(serif="1 · ter um", bold="PONTO DE VISTA PRÓPRIO")),
    ("titulo", "nixo é categoria", 306, 3.2, dict(serif="nicho é categoria. olhar é só seu.", bold="NICHO ≠ OLHAR")),
    ("titulo", "não depender de uma única plataforma", 335, "e daí a importância",
     dict(serif="2 · não depender de", bold="UMA ÚNICA PLATAFORMA")),
    ("titulo", "criar uma comunidade", 344, 2.6, dict(serif="a importância de criar uma", bold="COMUNIDADE", eco="COMUNIDADE")),
    ("titulo", "é só sua e isso", 379, "e a terceira", dict(serif="uma audiência que é", bold="SÓ SUA")),
    ("titulo", "publi é uma fonte de renda", 402, "modelo de negócio gente",
     dict(serif="3 · publi é fonte de renda,", bold="NÃO MODELO DE NEGÓCIO")),
    ("citacao", "o que eu estou construindo", 486, "dito isso", dict(
        serif="o que eu estou construindo que vai continuar existindo", bold="INDEPENDENTE DO ALGORITMO DE AMANHÃ?")),
    ("titulo", "4 milhões", 495, "você quer ser", dict(serif="quase", bold="4 MILHÕES", eco="4 MILHÕES",
                                                        extra="de criadores, só no Instagram")),
    ("titulo", "você quer ser mais um", 500, 0.84, dict(serif="você quer ser", bold="MAIS UM?")),
    ("proximo", "a diferença entre", 503, "agora sim", dict(serif="o que você fatura", bold="× O QUE VOCÊ CONSTRÓI")),
]

# ----------------------------------------------------------------------------- ASS
BRANCO, DESTAQUE = "&H00FFFFFF&", "&H00C0EDFC&"  # amarelo manteiga #FCEDC0 (o mesmo do "MAS")
CAB = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Serif,Playfair Display,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,0,-1,0,0,100,100,0,0,1,0,1.5,5,0,0,0,1
Style: Bold,Inter Black,190,&H00C0EDFC,&H00FFFFFF,&H00000000,&HB4000000,0,0,0,0,100,100,-3,0,1,0,2,5,0,0,0,1
Style: Eco,Inter Black,640,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,-10,0,1,0,0,5,0,0,0,1
Style: Label,Inter Medium,30,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,0,0,0,0,100,100,6,0,1,0,2,1,0,0,0,1
Style: Lista,Inter ExtraBold,62,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,0,0,0,0,100,100,0,0,1,0,1.5,4,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ts(t):
    t = max(0, t)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


eventos = []
sfx = []  # (tempo_saida, tipo)


def ev(camada, ini, fim, estilo, texto):
    eventos.append(f"Dialogue: {camada},{ts(ini)},{ts(fim)},{estilo},,0,0,0,,{texto}")


def tamanho_bold(texto, base=190, largura=1700):
    # Inter Black ~0.68 em por caractere em caixa-alta
    return min(base, int(largura / (0.68 * max(len(texto), 1))))


def titulo(a, b, serif, bold, eco=None, extra=None, y_serif=636, y_bold=750):
    d = int((b - a) * 1000)
    if eco:
        ev(0, a, b, "Eco", r"{\an5\pos(960,700)\alpha&HC4&\fad(250,300)\fscx96\fscy96"
                           rf"\t(0,{d},\fscx106\fscy106)}}{eco}")
    ev(2, a, b, "Serif", rf"{{\an5\move(960,{y_serif + 22},960,{y_serif},0,300)\fad(220,200)}}{serif}")
    fs = tamanho_bold(bold)
    ev(2, a + 0.08, b, "Bold", rf"{{\an5\pos(960,{y_bold})\fs{fs}\fscx118\fscy118\blur10\alpha&HFF&"
                               r"\t(0,240,\fscx100\fscy100\blur0\alpha&H00&)\fad(0,200)}" + bold)
    if extra:
        ev(2, a + 0.3, b, "Serif", rf"{{\an5\pos(960,{y_bold + 105})\fs62\fad(250,200)}}{extra}")
    sfx.append((a, "whoosh"))


def capitulo(a, b, texto):
    ev(1, a, b, "Label", r"{\an7\pos(110,915)\fad(300,300)\1c" + DESTAQUE + r"\bord0\shad0\p1}m 0 0 l 8 0 8 112 0 112{\p0}")
    ev(2, a, b, "Label", r"{\an7\move(120,915,140,915,0,350)\fad(300,300)\1c" + DESTAQUE + r"\fs32}CAPÍTULO")
    ev(2, a + 0.12, b, "Label", r"{\an7\move(120,958,140,958,0,350)\fad(300,300)\fs60\b1\fsp3}" + texto)
    sfx.append((a, "chime"))


def lista(a, b, titulo_txt, itens):
    ev(2, a, b, "Serif", rf"{{\an4\move(100,400,120,400,0,300)\fad(250,250)\fs54}}{titulo_txt}")
    for n, (t, texto) in enumerate(itens):
        y = 490 + n * 95
        ev(2, t, b, "Lista", rf"{{\an4\move(100,{y},120,{y},0,250)\fad(200,250)}}{{\1c{DESTAQUE}}}— {{\1c{BRANCO}}}{texto}")
        sfx.append((t, "tick"))


def versus(a, b):
    d = int((b - a) * 1000)
    ev(2, a, b, "Serif", r"{\an5\move(960,607,960,585,0,300)\fad(220,200)}vale mais do que")
    ev(2, a + 0.1, b, "Bold", r"{\an6\pos(880,700)\fs170\fad(200,200)}RELAÇÃO")
    ev(2, a + 0.1, b, "Bold", r"{\an5\pos(960,700)\fs120\fad(200,200)\1c" + BRANCO + "}>")
    ev(2, a + 0.5, b, "Bold", r"{\an4\pos(1040,700)\fs170\fad(250,200)\alpha&H60&" + rf"\t(0,{d},\alpha&H90&)" + "}VITRINE")
    sfx.append((a, "whoosh"))
    sfx.append((a + 0.5, "tick"))


def citacao(a, b, serif, bold):
    ev(2, a, b, "Serif", rf"{{\an5\move(960,790,960,770,0,400)\fs72\fad(350,300)}}{serif}")
    ev(2, a + 0.6, b, "Bold", rf"{{\an5\pos(960,845)\fs{tamanho_bold(bold, 84)}\fad(300,300)}}{bold}")
    sfx.append((a, "chime"))


def proximo(a, b):
    ev(1, a, b, "Label", r"{\an7\pos(110,100)\fad(300,300)\1c" + DESTAQUE + r"\bord0\shad0\p1}m 0 0 l 8 0 8 66 0 66{\p0}")
    ev(2, a, b, "Label", r"{\an7\move(120,104,140,104,0,350)\fad(300,300)\1c" + DESTAQUE + r"\fs56\b1\fsp6}PRÓXIMO EPISÓDIO")
    sfx.append((a, "chime"))


# gráfico: sequência de PNGs com a linha desenhando
def grafico(frames_total, pasta="grafico"):
    os.makedirs(pasta, exist_ok=True)
    W, H = 760, 420
    pts = [(40, 70), (170, 95), (300, 80), (430, 160), (560, 230), (700, 330)]
    for f in range(frames_total):
        prog = min(1, f / 22)
        alpha = min(1, f / 6, (frames_total - f) / 6)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dr = ImageDraw.Draw(img)
        # grade discreta
        for y in (80, 180, 280, 380):
            dr.line([(30, y), (W - 30, y)], fill=(255, 255, 255, 40), width=2)
        # linha até o progresso
        total = len(pts) - 1
        alvo = prog * total
        caminho = [pts[0]]
        for i in range(1, len(pts)):
            if i <= alvo:
                caminho.append(pts[i])
            else:
                fr = alvo - (i - 1)
                if fr > 0:
                    x0, y0 = pts[i - 1]
                    x1, y1 = pts[i]
                    caminho.append((x0 + (x1 - x0) * fr, y0 + (y1 - y0) * fr))
                break
        brilho = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(brilho).line(caminho, fill=(252, 237, 192, 150), width=22, joint="curve")
        brilho = brilho.filter(ImageFilter.GaussianBlur(12))
        img = Image.alpha_composite(img, brilho)
        dr = ImageDraw.Draw(img)
        dr.line(caminho, fill=(252, 237, 192, 255), width=8, joint="curve")
        for p in pts[: int(alvo) + 1]:
            dr.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], fill=(255, 255, 255, 255))
        if alpha < 1:
            a = img.getchannel("A").point(lambda v: int(v * alpha))
            img.putalpha(a)
        img.save(f"{pasta}/{f:04d}.png")


grafico_info = None
for tipo, frase, depois, dur, c in INS:
    s0, _ = achar(frase, depois)
    a = mapa(s0) - 0.05
    if isinstance(dur, str):
        s1, _ = achar(dur, s0 + 0.1)
        b = mapa(s1) - 0.08
    else:
        b = a + dur
    if tipo == "titulo":
        titulo(a, b, c["serif"], c["bold"], c.get("eco"), c.get("extra"))
    elif tipo == "capitulo":
        capitulo(a, b, c["texto"])
    elif tipo == "lista":
        itens = [(mapa(achar(f, d)[0]) - 0.05, txt) for f, d, txt in c["itens"]]
        lista(a, b, c["titulo"], itens)
    elif tipo == "versus":
        versus(a, b)
    elif tipo == "citacao":
        citacao(a, b, c["serif"], c["bold"])
    elif tipo == "proximo":
        proximo(a, b)
    elif tipo == "grafico":
        # gráfico à esquerda, número à direita
        ev(2, a + 0.3, b, "Bold", r"{\an4\pos(1260,470)\fs230\fscx118\fscy118\blur10\alpha&HFF&"
                                  r"\t(0,260,\fscx100\fscy100\blur0\alpha&H00&)\fad(0,200)}" + c["bold"])
        ev(2, a + 0.4, b, "Serif", r"{\an4\move(1270,625,1270,605,0,300)\fs56\fad(250,200)}" + c["serif"])
        n = int(round((b - a) * FPS))
        grafico(n)
        grafico_info = {"ini": round(a * FPS) / FPS, "frames": n}
        sfx.append((a, "queda"))
    print(f"{tipo:9} {ts(a)} -> {ts(b)}  {c.get('bold') or c.get('texto') or c.get('titulo') or 'RELAÇÃO > VITRINE'}")

open("insercoes.ass", "w", encoding="utf-8").write(CAB + "\n".join(eventos) + "\n")
json.dump({"grafico": grafico_info, "sfx": sfx}, open("insercoes.json", "w"), indent=1)


# ----------------------------------------------------------------------------- SFX
def env(n, ataque, queda):
    t = np.arange(n) / SR
    return np.minimum(1, t / ataque) * np.exp(-t / queda)


def som(tipo, rng=np.random.default_rng(7)):
    if tipo == "whoosh":
        n = int(0.55 * SR)
        ruido = rng.standard_normal(n)
        # filtro passa-banda com varredura (1 polo, simples)
        t = np.arange(n) / SR
        fc = 400 + 3200 * np.sin(np.pi * t / t[-1]) ** 2
        y = np.zeros(n)
        lp = hp = 0.0
        for i in range(n):
            a = 1 - np.exp(-2 * np.pi * fc[i] / SR)
            lp += a * (ruido[i] - lp)
            hp += 0.02 * (lp - hp)
            y[i] = lp - hp
        y *= np.sin(np.pi * t / t[-1]) ** 2
        return y / np.abs(y).max() * 10 ** (-27 / 20)
    if tipo == "tick":
        n = int(0.12 * SR)
        t = np.arange(n) / SR
        y = np.sin(2 * np.pi * 1850 * t) * env(n, 0.001, 0.018) + 0.4 * np.sin(2 * np.pi * 3700 * t) * env(n, 0.001, 0.008)
        return y / np.abs(y).max() * 10 ** (-30 / 20)
    if tipo == "chime":
        n = int(1.2 * SR)
        t = np.arange(n) / SR
        y = (np.sin(2 * np.pi * 880 * t) + 0.5 * np.sin(2 * np.pi * 1320 * t) + 0.25 * np.sin(2 * np.pi * 1760 * t)) * env(n, 0.004, 0.35)
        return y / np.abs(y).max() * 10 ** (-31 / 20)
    if tipo == "queda":
        n = int(0.7 * SR)
        t = np.arange(n) / SR
        f = 700 * np.exp(-t * 2.2)
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.01, 0.3)
        return y / np.abs(y).max() * 10 ** (-29 / 20)
    raise ValueError(tipo)


voz = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", "voz_cortada.wav", "-f", "f32le", "-"],
                                   capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()
cache = {}
for t, tipo in sfx:
    if tipo not in cache:
        cache[tipo] = som(tipo).astype(np.float32)
    y = cache[tipo]
    i = int(t * SR)
    j = min(len(voz), i + len(y))
    voz[i:j] += y[: j - i, None]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-c:a", "pcm_f32le", "mix.wav"], input=voz.tobytes(), check=True)
print(f"{len(eventos)} eventos ASS, {len(sfx)} efeitos sonoros")
