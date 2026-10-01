"""Reels 9:16 do EP2: legendas palavra a palavra + inserções do padrão DEEP adaptadas ao vertical, com
espaçamento entre linhas e entre letras o mais curto possível. Âncoras nas palavras da montagem do Reels."""
import json
import re
import unicodedata

import numpy as np

import insercoes as Y          # reaproveita INS e os sons (whoosh, tick, chime)

OFF = 9.6667                  # duração da abertura da editora (vinheta incluída)
W, H = 1080, 1920
CX = 510                      # centro levemente à esquerda (ícones do Reels à direita)
AMARELO, BRANCO = "&H00C0EDFC&", "&H00FFFFFF&"
PAL = [w for s in json.load(open("final_reels.json")) for w in s["words"]]
FIX = {"dip": "DEEP", "deep": "DEEP", "substacks": "Substack", "substeques": "Substack"}


def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if unicodedata.category(c) != "Mn"))


TOK = [norm(w["w"]) for w in PAL]
PY = json.load(open("plano_youtube.json"))["segmentos"]
PR = json.load(open("plano_reels.json"))["segmentos"]


def yt_para_reels(t):
    for s in PY:
        if s["t"] <= t < s["t"] + s["fim"] - s["ini"] + 1e-6:
            src = s["ini"] + t - s["t"]
            for q in PR:
                if q["fonte"] == s["fonte"] and q["ini"] - 0.3 <= src <= q["fim"] + 0.3:
                    return q["t"] + src - q["ini"]
            return None
    return None


def achar(frase, perto, apos=None):
    alvo = [norm(p) for p in frase.split()]
    occ = [(PAL[i]["s"], PAL[i + len(alvo) - 1]["e"]) for i in range(len(PAL))
           if TOK[i:i + len(alvo)] == alvo and (apos is None or PAL[i]["s"] > apos)]
    if not occ:
        return None
    return min(occ, key=lambda o: abs(o[0] - perto)) if apos is None else min(occ)


CAB = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Serif,Playfair Display,60,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,0,-1,0,0,100,100,-1,0,1,0,1.5,5,0,0,0,1
Style: Bold,Inter Black,112,&H00C0EDFC,&H00FFFFFF,&H00000000,&HA0000000,0,0,0,0,100,100,-4,0,1,0,2,5,0,0,0,1
Style: Label,Inter Medium,30,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,1,0,2,7,0,0,0,1
Style: Lista,Inter ExtraBold,50,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,0,0,0,0,100,100,-1,0,1,0,1.5,4,0,0,0,1
Style: Legenda,Inter ExtraBold,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,-1,0,1,0,3,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
EV, SFX, OCUP = [], [], []


def ts(t):
    t = max(0, t)
    m, s = divmod(t, 60)
    return f"0:{int(m):02d}:{s:05.2f}"


def ev(c, a, b, est, txt):
    EV.append(f"Dialogue: {c},{ts(a)},{ts(b)},{est},,0,0,0,,{txt}")


def tam(txt, base, larg=820, k=0.66):
    return min(base, int(larg / (k * max(len(txt), 1))))


def quebra(txt, maxc):
    if len(txt) <= maxc or " " not in txt:
        return [txt]
    p = txt.split()
    melhor = min(range(1, len(p)), key=lambda i: abs(len(" ".join(p[:i])) - len(" ".join(p[i:]))))
    return [" ".join(p[:melhor]), " ".join(p[melhor:])]


# ------------------------------------------------------------------ tipos (vertical, linhas encostadas)
def titulo(a, b, serif, bold, extra=None, y=1130):
    ls = quebra(serif, 24)
    lb = quebra(bold, 13)
    fb = min(tam(l, 112) for l in lb)
    alt_s, alt_b = 60 * 0.98, fb * 0.86                # altura de linha ≈ corpo da fonte (bem justo)
    y0 = y - (len(ls) * alt_s + len(lb) * alt_b) / 2
    yy = y0 + alt_s / 2
    for l in ls:
        ev(2, a, b, "Serif", rf"{{\an5\move({CX},{yy + 16:.0f},{CX},{yy:.0f},0,300)\fad(200,180)}}{l}")
        yy += alt_s
    yy += alt_b / 2 - alt_s / 2 + 4
    for l in lb:
        ev(2, a + 0.08, b, "Bold", rf"{{\an5\pos({CX},{yy:.0f})\fs{fb}\fscx116\fscy116\blur8\alpha&HFF&"
                                   r"\t(0,220,\fscx100\fscy100\blur0\alpha&H00&)\fad(0,180)}" + l)
        yy += alt_b
    if extra:
        ev(2, a + 0.3, b, "Serif", rf"{{\an5\pos({CX},{yy + 10:.0f})\fs44\fad(250,180)}}{extra}")
    SFX.append((a, "whoosh"))


def capitulo(a, b, texto):
    ev(1, a, b, "Label", r"{\an7\pos(60,262)\fad(300,300)\1c" + AMARELO + r"\bord0\shad0\p1}m 0 0 l 7 0 7 82 0 82{\p0}")
    ev(2, a, b, "Label", r"{\an7\move(72,262,84,262,0,350)\fad(300,300)\1c" + AMARELO + r"\fs26}CAPÍTULO")
    for n, l in enumerate(quebra(texto, 22)):
        ev(2, a + 0.12, b, "Label", rf"{{\an7\move(72,{292 + n * 44},84,{292 + n * 44},0,350)\fad(300,300)\fs42\b1}}{l}")
    SFX.append((a, "chime"))


def lista(a, b, tit, itens, fonte=None):
    y = 1040
    ev(2, a, b, "Serif", rf"{{\an4\move(60,{y},76,{y},0,300)\fad(250,220)\fs46}}{tit}")
    for n, (t, txt) in enumerate(itens):
        yy = y + 62 + n * 56
        ev(2, t, b, "Lista", rf"{{\an4\move(60,{yy},76,{yy},0,250)\fad(200,220)}}{{\1c{AMARELO}}}— {{\1c{BRANCO}}}{txt}")
        SFX.append((t, "tick"))
    if fonte:
        ev(2, a + 0.4, b, "Label", rf"{{\an4\pos(78,{y + 62 + len(itens) * 56})\fad(300,220)\fs22\alpha&H40&}}{fonte}")


def citacao(a, b, serif, bold):
    ls = quebra(serif, 26)
    lb = quebra(bold, 18)
    fb = min(tam(l, 76) for l in lb)
    y = 1130 - (len(ls) * 54 + len(lb) * fb * 0.9) / 2 + 27
    for l in ls:
        ev(2, a, b, "Serif", rf"{{\an5\move({CX},{y + 14:.0f},{CX},{y:.0f},0,350)\fs54\fad(300,250)}}{l}")
        y += 54
    y += fb * 0.45 - 27 + 6
    for l in lb:
        ev(2, a + 0.5, b, "Bold", rf"{{\an5\pos({CX},{y:.0f})\fs{fb}\fad(280,250)}}{l}")
        y += fb * 0.9
    SFX.append((a, "chime"))


def proximo(a, b):
    ev(1, a, b, "Label", r"{\an7\pos(60,262)\fad(300,300)\1c" + AMARELO + r"\bord0\shad0\p1}m 0 0 l 7 0 7 54 0 54{\p0}")
    ev(2, a, b, "Label", r"{\an7\move(72,266,84,266,0,350)\fad(300,300)\1c" + AMARELO + r"\fs44\b1}PRÓXIMO EPISÓDIO")
    SFX.append((a, "chime"))


# ------------------------------------------------------------------ inserções
dur = OFF + json.load(open("plano_reels.json"))["duracao"]
for tipo, frase, depois, fim, c in Y.INS:
    s_yt, e_yt = Y.achar(frase, depois)
    perto = yt_para_reels((s_yt + e_yt) / 2)
    if perto is None:
        continue                                   # trecho exclusivo do YouTube
    r = achar(frase, perto) or achar(frase.replace("estou", "tô"), perto)
    if r is None:
        print("sem âncora:", frase)
        continue
    a = r[0] - 0.05
    if fim == "fim":
        b = PAL[-1]["e"] + 0.4
    elif isinstance(fim, str):
        f2 = achar(fim, a, apos=a + 0.1)
        b = (f2[0] - 0.08) if f2 else a + 3
    else:
        b = a + fim
    a += OFF
    b = min(b + OFF, dur - 0.5)
    if tipo == "titulo":
        titulo(a, b, c["serif"], c["bold"], c.get("extra"))
    elif tipo == "capitulo":
        capitulo(a, b, c["texto"])
        continue                                   # capítulo fica no topo: legenda continua
    elif tipo in ("lista", "pesquisa"):
        its = []
        for f, d, txt in c["itens"]:
            q = achar(f, r[0])
            its.append(((q[0] - 0.05 + OFF) if q else a, txt))
        lista(a, b, c["titulo"], its, c.get("fonte"))
    elif tipo == "citacao":
        citacao(a, b, c["serif"], c["bold"])
    elif tipo == "proximo":
        proximo(a, b)
        continue
    else:
        continue
    OCUP.append((a, b))

# ------------------------------------------------------------------ legenda palavra a palavra (some durante inserções)
blocos, atual = [], []
for i, w in enumerate(PAL):
    atual.append(i)
    txt = " ".join(PAL[k]["w"].strip() for k in atual)
    fim_frase = w["w"].strip()[-1:] in ".?!,"
    longe = i + 1 < len(PAL) and PAL[i + 1]["s"] - w["e"] > 0.35
    if len(atual) >= 3 or len(txt) >= 16 or fim_frase or longe:
        blocos.append(atual)
        atual = []
if atual:
    blocos.append(atual)


def limpa(p):
    base = re.sub(r"[^\wÀ-ú-]", "", p)
    novo = FIX.get(norm(base))
    return p.replace(base, novo) if novo else p


for n, bl in enumerate(blocos):
    a = PAL[bl[0]]["s"] - 0.03 + OFF
    b = PAL[bl[-1]]["e"] + 0.15 + OFF
    if n + 1 < len(blocos):
        b = min(b + 0.45, PAL[blocos[n + 1][0]]["s"] - 0.03 + OFF)
    if any(a < y and b > x for x, y in OCUP):
        continue
    pal = [limpa(PAL[k]["w"].strip()) for k in bl]
    # palavra a palavra dentro do bloco: as já faladas em branco, a atual surge com leve pop
    for j, k in enumerate(bl):
        t0 = max(a, PAL[k]["s"] - 0.03 + OFF)
        t1 = b if j == len(bl) - 1 else PAL[bl[j + 1]]["s"] - 0.03 + OFF
        vis = " ".join(pal[:j + 1])
        inv = " ".join(pal[j + 1:])
        txt = vis + (r"{\alpha&HFF&} " + inv if inv else "")
        ev(3, t0, max(t1, t0 + 0.04), "Legenda", rf"{{\an5\pos({CX},1330)}}{txt}")

open("insercoes_reels.ass", "w", encoding="utf-8").write(CAB + "\n".join(EV) + "\n")
json.dump(SFX, open("sfx_reels.json", "w"))
print(len(OCUP), "inserções,", len(blocos), "blocos de legenda,", len(SFX), "efeitos")
