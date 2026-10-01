"""Legendas no padrão da editora (referência: reel "Me conta qual dessas mais te pegou").
Base: Rubik SemiBold branca, 2-3 palavras, ~64% da altura, sombra esfumada. Destaques variando fontes:
Rubik Black amarelo manteiga (palavra a palavra), Playfair Display itálico branco+ouro (palavra a palavra),
Amatic SC branco grande (letra a letra). Nada antes do fim de "Posso pesar o clima?"."""
import json
import re
import unicodedata

W, H = 1080, 1920
BASE_Y = 1221                  # ~63,6% da altura (medido no reel de referência)
BRANCO, OURO, MANTEIGA = "&H00FFFFFF&", "&H000BCEF1&", "&H00C1ECFB&"
PAL = [w for s in json.load(open("fala_v2.json")) for w in s["words"]]


def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if unicodedata.category(c) != "Mn"))


TOK = [norm(w["w"]) for w in PAL]


def achar(frase, perto=0):
    alvo = [norm(p) for p in frase.split()]
    occ = [i for i in range(len(PAL)) if TOK[i:i + len(alvo)] == alvo]
    i = min(occ, key=lambda k: abs(PAL[k]["s"] - perto))
    return i, i + len(alvo) - 1


# destaques: (frase falada, tipo, linhas/partes)
DESTAQUES = [
    ("e muito menos postar sobre todas elas", "rubik", [["E", "MUITO", "MENOS"], ["POSTAR"]], 3.4),
    ("é muito bom falar eu não sei", "playfair", [[("é muito bom falar,", BRANCO)], [("eu", BRANCO), ("não sei", OURO)]], 13.8),
    ("aliás eu considero um ato de coragem", "rubik", [["UM ATO"], ["DE CORAGEM"]], 34.6),
    ("nem toda situação ruim tem um lado bom", "amatic", ["NEM TODA SITUAÇÃO", "RUIM TEM", "UM LADO BOM"], 50.0),
    ("o óbvio precisa ser dito", "playfair", [[("O", BRANCO), ("óbvio", OURO)], [("precisa", OURO), ("ser dito", BRANCO)]], 61.8),
]

CAB = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Base,Rubik SemiBold,42,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Rubik,Rubik Black,132,&H00C1ECFB,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,-2,0,1,0,0,5,0,0,0,1
Style: Playfair,Playfair Display Medium,150,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,-1,0,0,100,100,-1,0,1,0,0,5,0,0,0,1
Style: Amatic,Amatic SC,165,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,4,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
EV = []


def ts(t):
    t = max(0, t)
    m, s = divmod(t, 60)
    return f"0:{int(m):02d}:{s:05.2f}"


def ev(camada, a, b, estilo, texto):
    EV.append(f"Dialogue: {camada},{ts(a)},{ts(b)},{estilo},,0,0,0,,{texto}")


def com_sombra(a, b, estilo, pos, texto, blur=9, alfa="&H70&", desl=4, extra=""):
    """texto + sombra esfumada (cópia preta desfocada um pouco abaixo)"""
    x, y = pos
    ev(0, a, b, estilo, rf"{{\an5\pos({x + desl * 0.4:.0f},{y + desl})\1c&H000000&\1a{alfa}\blur{blur}{extra}}}{texto}")
    ev(1, a, b, estilo, rf"{{\an5\pos({x},{y}){extra}}}{texto}")


# ------------------------------------------------------------------ destaques
ocupado = []
for frase, tipo, partes, perto in DESTAQUES:
    i0, i1 = achar(frase, perto)
    a = PAL[i0]["s"] - 0.05
    b = PAL[i1]["e"] + 0.45
    ocupado.append((a, b))
    if tipo == "rubik":
        # palavra a palavra, com leve "pop"
        palavras_fala = iter(range(i0, i1 + 1))
        y0 = 1020 - (len(partes) - 1) * 66
        for n, linha in enumerate(partes):
            y = y0 + n * 132
            texto_linha = " ".join(linha)
            # posição de cada palavra: reserva a linha inteira com as palavras ainda invisíveis
            for k, palavra in enumerate(linha):
                j = next(palavras_fala, i1)
                t = max(a, PAL[min(j, i1)]["s"] - 0.04)
                vis = " ".join(linha[:k + 1])
                inv = " ".join(linha[k + 1:])
                txt = vis + (r"{\alpha&HFF&} " + inv if inv else "")
                fim = b if k == len(linha) - 1 else max(t + 0.05, PAL[min(j + 1, i1)]["s"] - 0.04)
                com_sombra(t, fim, "Rubik", (540, y), txt, blur=12, alfa="&H60&", desl=6)
    elif tipo == "playfair":
        y0 = 1000 - (len(partes) - 1) * 72
        ordem = list(range(i0, i1 + 1))
        pos = 0
        for n, linha in enumerate(partes):
            y = y0 + n * 144
            for k in range(len(linha)):
                # quando aparece este pedaço: no início da sua primeira palavra
                npal = len(linha[k][0].split())
                t = max(a, PAL[ordem[min(pos, len(ordem) - 1)]]["s"] - 0.04)
                pos += npal
                vis = " ".join(rf"{{\1c{c}}}{p}" for p, c in linha[:k + 1])
                inv = " ".join(p for p, _ in linha[k + 1:])
                txt = vis + (r"{\alpha&HFF&} " + inv if inv else "")
                fim = b if k == len(linha) - 1 else PAL[ordem[min(pos, len(ordem) - 1)]]["s"] - 0.04
                com_sombra(t, max(fim, t + 0.05), "Playfair", (540, y), txt, blur=14, alfa="&H38&", desl=5,
                           extra=r"\fad(120,0)")
    elif tipo == "amatic":
        # letra a letra, distribuído ao longo da fala
        texto = "\\N".join(partes)
        letras = [c for c in texto.replace("\\N", "\n")]
        n_vis = [k for k, c in enumerate(letras) if c not in " \n"]
        dur = PAL[i1]["e"] - PAL[i0]["s"]
        for m, k in enumerate(n_vis):
            t = a + dur * m / len(n_vis)
            t2 = a + dur * (m + 1) / len(n_vis) if m + 1 < len(n_vis) else b
            vis = "".join(letras[:k + 1]).replace("\n", "\\N")
            inv = "".join(letras[k + 1:]).replace("\n", "\\N")
            txt = vis + (r"{\alpha&HFF&}" + inv if inv else "")
            com_sombra(t, t2, "Amatic", (540, 1180), txt, blur=14, alfa="&H48&", desl=6)

# ------------------------------------------------------------------ legenda base
inicio = achar("posso pesar o clima")[1] + 1          # nada sobre "Posso pesar o clima?"
blocos, atual = [], []
for i in range(inicio, len(PAL)):
    w = PAL[i]["w"].strip()
    atual.append(i)
    chars = sum(len(PAL[k]["w"].strip()) + 1 for k in atual)
    fim_frase = w[-1:] in ".?!,"
    prox_longe = i + 1 < len(PAL) and PAL[i + 1]["s"] - PAL[i]["e"] > 0.35
    if len(atual) >= 3 or chars >= 15 or fim_frase or prox_longe:
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
    if any(a < y and b > x for x, y in ocupado):        # some enquanto há destaque
        continue
    txt = " ".join(PAL[k]["w"].strip() for k in bl)
    txt = txt[0].lower() + txt[1:] if txt[:1].isupper() and txt.split()[0] not in ("Você", "Eu", "E", "O") else txt
    com_sombra(a, b, "Base", (540, BASE_Y), txt, blur=7, alfa="&H5A&", desl=3)

open("legendas.ass", "w", encoding="utf-8").write(CAB + "\n".join(EV) + "\n")
print(len(blocos), "blocos de legenda,", len(DESTAQUES), "destaques")
