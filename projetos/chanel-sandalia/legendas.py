"""Legendas dinâmicas no padrão aprovado da editora + cartões de texto no formato curadoria, em ASS (libass).
Base: Rubik SemiBold branca 46 (palavra-chave Rubik Black amarela 52), 2–3 palavras, sombra leve, brilho só no amarelo.
Destaques: Rubik Black amarelo palavra a palavra | Playfair itálico branco+ouro palavra a palavra | Amatic SC letra a letra.
Cartões: Jost Light (caixa alta) + Cormorant itálico amarelo manteiga, entrada seca com fade curtíssimo.
Saída: legendas.ass, cartoes.ass e sfx.json (eventos de efeito). Usa edl.py. Rodar em /home/user/work/cur (fonts/ ao lado)."""
import json
import math
import os
import re

from PIL import ImageFont

import edl
from edl import PAL, achar, norm, DESTAQUES, CHAVE, FIX

S = int(os.environ.get("S", "1"))
W, H = 1080, 1920            # coordenadas lógicas do ASS (o libass escala para a resolução do vídeo)
BASE_Y, CX, LARG = 1221, 540, 800
BRANCO, OURO, MANTEIGA = "&H00FFFFFF&", "&H000BCEF1&", "&H00C1ECFB&"
EV, EV2, SFX = [], [], []

CAB = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Base,Rubik SemiBold,46,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Rubik,Rubik Black,112,&H00C1ECFB,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,-2,0,1,0,0,5,0,0,0,1
Style: Playfair,Playfair Display Medium,120,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,-1,0,0,100,100,-1,0,1,0,0,5,0,0,0,1
Style: Amatic,Amatic SC,140,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,4,0,1,0,0,5,0,0,0,1
Style: Sans,Jost Medium,100,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,10,0,1,0,0,5,0,0,0,1
Style: Serif,Playfair Display Medium,90,&H00C1ECFB,&H00FFFFFF,&H00000000,&H00000000,0,-1,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Numero,Jost Medium,300,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,-4,0,1,0,0,5,0,0,0,1
Style: Rotulo,Playfair Display Medium,50,&H00C1ECFB,&H00FFFFFF,&H00000000,&H00000000,0,-1,0,0,100,100,1,0,1,0,0,5,0,0,0,1
Style: Balao,Cormorant Garamond,54,&H00000000,&H00000000,&H00000000,&H00000000,0,-1,0,0,100,100,1,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ts(t):
    t = max(0, t)
    m, s = divmod(t, 60)
    return f"0:{int(m):02d}:{s:05.2f}"


def ev(lista, camada, a, b, estilo, texto):
    lista.append(f"Dialogue: {camada},{ts(a)},{ts(b)},{estilo},,0,0,0,,{texto}")


AMARELOS = (OURO, MANTEIGA)


def brilho(texto, estilo):
    """cópia só das palavras amarelas (o resto invisível), para o brilho ficar apenas no destaque amarelo"""
    if estilo in ("Amatic", "Sans", "Numero", "Rotulo"):
        return None

    def troca(m):
        c = "&H" + m.group(1) + "&"
        return m.group(0) + (r"\alpha&H90&" if c.upper() in [a.upper() for a in AMARELOS] else r"\alpha&HFF&")
    g = re.sub(r"\\1c&H([0-9A-Fa-f]+)&", troca, texto)
    if not re.search(r"\\1c&H([0-9A-Fa-f]+)&", texto) and estilo == "Base":
        return None
    ini = r"\alpha&H90&" if estilo in ("Rubik", "Serif") else r"\alpha&HFF&"
    g = g.replace(r"{\alpha&HFF&}", r"{\alpha&HFF&\1a&HFF&}")
    return ini, g


def com_sombra(lista, a, b, estilo, pos, texto, blur=9, desl=4, extra="", esc=100, brilhar=True, forte=False):
    """texto + sombra preta leve (só para dar leitura: \\bord3\\blur8, ~50%) + brilho apenas no amarelo"""
    x, y = pos
    sc = rf"\fscx{esc}\fscy{esc}" if esc != 100 else ""
    sombra = re.sub(r"\\1c&H[0-9A-Fa-f]+&", "", texto)
    sombra = sombra.replace(r"\alpha&HFF&", r"\alpha&HFF&\3a&HFF&")
    if forte:      # halo escuro maior e mais denso, só atrás das letras (sem caixa), para ler sobre a camiseta branca
        ev(lista, 0, a, b, estilo, rf"{{\an5\pos({x:.0f},{y + 2:.0f})\1c&H000000&\3c&H000000&\bord9\blur16\1a&H60&\3a&H60&{sc}{extra}}}{sombra}")
    ev(lista, 0, a, b, estilo, rf"{{\an5\pos({x + 1:.0f},{y + 3:.0f})\1c&H000000&\3c&H000000&\bord3\blur8\1a&H78&\3a&H78&{sc}{extra}}}{sombra}")
    gl = brilho(texto, estilo) if brilhar else None
    if gl:
        ini, g = gl
        ev(lista, 1, a, b, estilo, rf"{{\an5\pos({x:.0f},{y:.0f})\bord0\blur14{ini}{sc}{extra}}}{g}")
    ev(lista, 2, a, b, estilo, rf"{{\an5\pos({x:.0f},{y:.0f}){sc}{extra}}}{texto}")


FONTE = {"Rubik": ("Rubik_wght_900.ttf", 112), "Playfair": ("Playfair_Display_ital_wght_1_500.ttf", 120), "Amatic": ("Amatic_SC_wght_700.ttf", 140)}


def escala(estilo, linhas):
    f, tam = FONTE[estilo]
    fn = ImageFont.truetype("fonts/" + f, tam)
    larg = max(fn.getlength(l) for l in linhas)
    return min(100, int(LARG / larg * 100)) if larg else 100


def limpa(p):
    p = p.strip()
    base = re.sub(r"[^\wÀ-ú/-]", "", p)
    k = norm(base)
    if k in FIX:
        p = p.replace(base, FIX[k])
    return p


# ------------------------------------------------------------------------------------------------ destaques
ocupado = []
for frase, tipo, partes, perto in DESTAQUES:
    i0, i1 = achar(frase, perto)
    a = PAL[i0]["s"] - 0.05
    b = PAL[i1]["e"] + 0.5
    if i1 + 1 < len(PAL):
        b = min(b, PAL[i1 + 1]["s"] - 0.06)
    ocupado.append((i0, i1))
    textos = [" ".join(l) if tipo == "rubik" else (l if tipo == "amatic" else " ".join(p for p, _ in l)) for l in partes]
    esc = escala(tipo.capitalize(), textos)
    if tipo == "rubik":
        palavras_fala = iter(range(i0, i1 + 1))
        y0 = 1040 - (len(partes) - 1) * 46 * esc / 100
        for n, linha in enumerate(partes):
            y = y0 + n * 92 * esc / 100
            for k, palavra in enumerate(linha):
                j = next(palavras_fala, i1)
                t = max(a, PAL[min(j, i1)]["s"] - 0.04)
                vis = " ".join(linha[:k + 1])
                inv = " ".join(linha[k + 1:])
                txt = vis + (r"{\alpha&HFF&} " + inv if inv else "")
                fim = b if k == len(linha) - 1 else max(t + 0.05, PAL[min(j + 1, i1)]["s"] - 0.04)
                com_sombra(EV, t, fim, "Rubik", (CX, round(y)), txt, esc=esc, extra=r"\fad(0,140)" if k == len(linha) - 1 else "")
                SFX.append((t, "pop", n * 3 + k))
    elif tipo == "playfair":
        y0 = 1030 - (len(partes) - 1) * 50 * esc / 100
        ordem = list(range(i0, i1 + 1))
        pos = 0
        for n, linha in enumerate(partes):
            y = y0 + n * 100 * esc / 100
            for k in range(len(linha)):
                npal = len(linha[k][0].split())
                t = max(a, PAL[ordem[min(pos, len(ordem) - 1)]]["s"] - 0.04)
                pos += npal
                vis = " ".join(rf"{{\1c{c}}}{p}" for p, c in linha[:k + 1])
                inv = " ".join(p for p, _ in linha[k + 1:])
                txt = vis + (r"{\alpha&HFF&} " + inv if inv else "")
                fim = b if k == len(linha) - 1 else PAL[ordem[min(pos, len(ordem) - 1)]]["s"] - 0.04
                com_sombra(EV, t, max(fim, t + 0.05), "Playfair", (CX, round(y)), txt, esc=esc,
                           extra=r"\fad(120,140)" if k == len(linha) - 1 else r"\fad(120,0)")
                SFX.append((t, "brilho", n * 2 + k))
    elif tipo == "amatic":
        passo = 108 * esc / 100
        y0 = 1150 - (len(partes) - 1) * passo / 2
        total = sum(len(l.replace(" ", "")) for l in partes)
        dur = PAL[i1]["e"] - PAL[i0]["s"]
        m = 0
        for n, linha in enumerate(partes):
            y = y0 + n * passo
            visiveis = [k for k, c in enumerate(linha) if c != " "]
            for q, k in enumerate(visiveis):
                t = a + dur * m / total
                m += 1
                prox = a + dur * m / total if m < total else b
                ultimo = q == len(visiveis) - 1
                fim = b if ultimo else prox
                vis, inv = linha[:k + 1], linha[k + 1:]
                txt = vis + (r"{\alpha&HFF&}" + inv if inv else "")
                com_sombra(EV, t, fim, "Amatic", (CX, int(y)), txt, esc=esc, extra=r"\fad(0,140)" if ultimo else "")
                SFX.append((t, "tecla", m))

# ------------------------------------------------------------------------------------------------ legenda base
blocos, atual = [], []
dentro = {i for i0, i1 in ocupado for i in range(i0, i1 + 1)}
for i in range(len(PAL)):
    if i in dentro:
        if atual:
            blocos.append(atual)
            atual = []
        continue
    w = PAL[i]["w"].strip()
    atual.append(i)
    chars = sum(len(PAL[k]["w"].strip()) + 1 for k in atual)
    fim_frase = w[-1:] in ".?!,"
    prox_longe = i + 1 < len(PAL) and PAL[i + 1]["s"] - PAL[i]["e"] > 0.35
    curta = norm(w) in {norm(c) for c in CHAVE}
    if len(atual) >= 3 or chars >= 14 or fim_frase or prox_longe or (curta and len(atual) >= 2):
        blocos.append(atual)
        atual = []
if atual:
    blocos.append(atual)

for n, bl in enumerate(blocos):
    a = PAL[bl[0]]["s"] - 0.03
    b = PAL[bl[-1]]["e"] + 0.12
    if n + 1 < len(blocos):
        prox = PAL[blocos[n + 1][0]]["s"] - 0.03
        b = min(max(b, prox), PAL[bl[-1]]["e"] + 0.6, prox)
    if n + 1 < len(blocos) and blocos[n + 1][0] - bl[-1] > 1:
        b = min(b, PAL[blocos[n + 1][0]]["s"] - 0.03, PAL[bl[-1] + 1]["s"] - 0.08)
    elif bl[-1] + 1 < len(PAL) and (bl[-1] + 1) in dentro:
        b = min(b, PAL[bl[-1] + 1]["s"] - 0.08)
    partes = []
    for k in bl:
        p = limpa(PAL[k]["w"])
        if norm(p) in {norm(c) for c in CHAVE}:
            p = r"{\fnRubik Black\1c" + MANTEIGA + r"\fs52}" + p + r"{\fnRubik SemiBold\1c&HFFFFFF&\fs46}"
        partes.append(p)
    com_sombra(EV, a, b, "Base", (CX, BASE_Y), " ".join(partes), extra=r"\fscx112\fscy112\t(0,90,\fscx100\fscy100)")

# ------------------------------------------------------------------------------------------------ cartões, balões e rótulos
ev_ = edl.resolver()
for c in ev_["cart"]:
    for n, (txt, est, y, tam, cor) in enumerate(c["linhas"]):
        t = c["t"] + 0.16 * n
        texto = txt.upper() if est in ("sans",) else txt
        estilo = {"sans": "Sans", "serif": "Serif", "numero": "Numero"}[est]
        # largura útil 860 px: reduz se passar
        fnome = {"sans": "Jost_wght_500.ttf", "serif": "Playfair_Display_ital_wght_1_500.ttf", "numero": "Jost_wght_500.ttf"}[est]
        if est == "serif":
            tam = int(tam * 0.80)
        fn = ImageFont.truetype("fonts/" + fnome, tam)
        larg = fn.getlength(texto) + (10 * len(texto) if est == "sans" else 0)
        esc = min(100, int(860 / larg * 100)) if larg else 100
        extra = rf"\fs{tam}\fad(70,160)"
        com_sombra(EV2, t, c["fim"], estilo, (CX, y), rf"{{\1c{cor}}}{texto}", esc=esc, extra=extra, brilhar=False, forte=True)
    SFX.append((c["t"], "cartao", 0))
for b_ in ev_["bal"]:
    fn = ImageFont.truetype("fonts/Cormorant_Garamond_ital_400.ttf", 54)
    larg = int(fn.getlength(b_["txt"]) + 12 * len(b_["txt"]) * 0.0 + 56)
    alt = 90
    x, y = b_["x"], b_["y"]
    ev(EV2, 1, b_["t"], b_["fim"], "Balao", rf"{{\an7\pos({x},{y})\p1\bord0\shad0\1c&HFFFFFF&\fad(0,120)}}m 0 0 l {larg} 0 l {larg} {alt} l 0 {alt}{{\p0}}")
    ev(EV2, 2, b_["t"], b_["fim"], "Balao", rf"{{\an7\pos({x + 28},{y + 12})\fad(0,120)}}{b_['txt']}")
    SFX.append((b_["t"], "balao", 0))
for f in ev_["full"]:
    if f["rot"]:
        com_sombra(EV2, f["t"] + 0.12, f["fim"], "Rotulo", (CX, 1330), f["rot"], extra=r"\fad(80,120)", brilhar=False, forte=True)
    SFX.append((f["t"], "clique" if f["nome"] == "f_flashes" else "impacto", f["nome"]))
assets = json.load(open(f"ov_{S}.json")) if os.path.exists(f"ov_{S}.json") else {"pol": []}
for p in assets["pol"]:
    th = math.radians(p["ang"])
    dx, dy = 0, p["ch"] / 2 - p["bb"] / 2          # centro da faixa branca de baixo, relativo ao centro do cartão
    rx = dx * math.cos(th) + dy * math.sin(th)
    ry = -dx * math.sin(th) + dy * math.cos(th)
    cx = (p["x"] + p["w"] / 2 + rx) / S
    cy = (p["y"] + p["h"] / 2 + ry) / S
    ev(EV2, 3, p["t"] + 0.1, p["fim"], "Balao", rf"{{\an5\pos({cx:.0f},{cy:.0f})\frz{p['ang']}\fs34\fad(60,120)}}{p['rot']}")
    SFX.append((p["t"], "foto", p["nome"]))

open("legendas.ass", "w", encoding="utf-8").write(CAB + "\n".join(EV) + "\n")
open("cartoes.ass", "w", encoding="utf-8").write(CAB + "\n".join(EV2) + "\n")
json.dump(sorted(SFX, key=lambda e: e[0]), open("sfx.json", "w"))
print(len(blocos), "blocos de legenda;", len(DESTAQUES), "destaques;", len(ev_["cart"]), "cartões;", len(ev_["bal"]), "balões;", len(SFX), "efeitos")
