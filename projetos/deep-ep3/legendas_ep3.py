"""DEEP EP3 (versão da editora, 9:16 4K): legenda de tudo depois da vinheta DEEP, no padrão aprovado do Reels DEEP
(Rubik SemiBold 46 branca, palavra-chave em Rubik Black 52 amarelo manteiga, sombra preta leve, pop na entrada),
sem nunca encostar nas inserções de texto dela: enquanto uma inserção está na tela (mapa por OCR,
mapear_insercoes.py), a legenda desce para baixo dela ou sobe para cima dela; se não houver espaço livre
(entre o queixo e a área segura de baixo), o bloco fica escondido.
Uso (em /home/user/work/deep3): python3 legendas_ep3.py  -> legendas_ep3.ass + legendas_ep3_log.txt"""
import json
import re
import unicodedata

from PIL import ImageFont

W, H = 1080, 1920
CX, BASE_Y = 540, 1221           # centro / altura padrão (~63,6%)
INICIO = 11.5                    # fim da vinheta DEEP
LIM_CIMA = 860                   # nunca acima disso (rosto)
LIM_BAIXO = H - 480              # área segura do Instagram (base)
MARGEM = 50                      # folga entre a legenda e a inserção (as caixas passam ~40 px do texto)
FOLGA_A, FOLGA_B = 1.0, 0.5      # folga de tempo: o OCR só enxerga o texto ~1 s depois do início do fade de entrada
MANTEIGA = "&H00C1ECFB&"
# palavras-eco translúcidas (o OCR não enxerga): (início, fim, x0, x1, y0, y1) relativos
ECOS = [(193.2, 199.2, 0.0, 1.0, 0.55, 0.66), (299.0, 300.2, 0.0, 1.0, 0.55, 0.725)]
CHAVE = {"confianca", "recomendacao", "indicacao", "comprar", "compra", "produto", "produtos", "producao",
         "inteligencia", "qualidade", "informacao", "convincente", "comercial", "comissao", "negocio", "empresas",
         "audiencia", "rotina", "expectativa", "entrega", "receita", "responsavel", "opiniao", "influenciado",
         "influenciador", "mercado", "deep", "escolha", "venda", "equipes", "assinaturas", "impecavel", "erro",
         "errada", "recursos", "valor", "interesse", "confianca?", "ideia"}
FSEMI = ImageFont.truetype("fonts/Rubik_wght_600.ttf", 46)
FBLACK = ImageFont.truetype("fonts/Rubik_wght_900.ttf", 52)


def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if unicodedata.category(c) != "Mn"))


def palavras():
    """transcrição em janela longa (texto fiel) + o que ela fala de fato ("pra", "tá") pela transcrição em pedaços"""
    L = json.load(open("palavras_longo.json"))
    C = json.load(open("palavras.json"))
    for w in L:
        n = norm(w["w"])
        if n in ("para", "esta"):
            curto = {"para": "pra", "esta": "ta"}[n]
            if any(norm(c["w"]) == curto and c["s"] < w["e"] + 0.3 and c["e"] > w["s"] - 0.3 for c in C):
                novo = {"para": "pra", "esta": "tá"}[n]
                w["w"] = re.sub(r"(?i)para|está|esta", novo.capitalize() if w["w"][0].isupper() else novo, w["w"], 1)
        if n in ("dip", "deep"):
            w["w"] = re.sub(r"(?i)dip|deep", "DEEP", w["w"])
    # "pra quem tá recebendo, assistindo aí do outro lado" (a transcrição longa engoliu o "recebendo")
    i = next(k for k, w in enumerate(L) if norm(w["w"]) == "assistindo" and 172 < w["s"] < 178)
    rec = next(c for c in C if norm(c["w"]) == "recebendo" and 174 < c["s"] < 176)
    L.insert(i, dict(w="recebendo,", s=rec["s"], e=min(rec["e"], L[i]["s"] - 0.02)))
    troca = {(255, "sustenta,"): "sustenta?", (258, "cumprida."): "cumprida?", (261, "assumido,"): "assumido?",
             (263, "paga."): "paga", (265, "Pode"): "pode,", (266, "sim"): "sim,"}
    for w in L:
        for (t, velho), novo in troca.items():
            if w["w"] == velho and abs(w["s"] - t) < 2.5:
                w["w"] = novo
    L = [w for w in L if not (w["w"] == "e" and 265.3 < w["s"] < 266.2)]       # "pode, e sim" -> "pode, sim"
    for k, w in enumerate(L):                                                  # "uma recomendação" depois de "?"
        if k and L[k - 1]["w"].endswith("?") and w["w"] == "uma":
            w["w"] = "Uma"
    return L


def insercoes():
    ins = [d for d in json.load(open("insercoes_editora.json")) if d["fim"] - d["ini"] >= 0.5 and d["fim"] > INICIO]
    return [dict(a=d["ini"] - FOLGA_A, b=d["fim"] + FOLGA_B, x0=d["x0"] * W, x1=d["x1"] * W, y0=d["y0"] * H,
                 y1=d["y1"] * H, txt=" / ".join(dict.fromkeys(d["textos"]))[:60]) for d in ins] + [
        dict(a=a - FOLGA_A, b=b + FOLGA_B, x0=x0 * W, x1=x1 * W, y0=y0 * H, y1=y1 * H, txt="eco") for a, b, x0, x1, y0, y1 in ECOS]


def caixa(texto, y):
    """caixa ocupada pela legenda (com o pop de 112%)"""
    larg = 0
    for p in texto.split():
        f = FBLACK if norm(p) in CHAVE else FSEMI
        larg += f.getlength(p + " ")
    larg = larg * 1.12 + 20
    meia = 36
    return (CX - larg / 2, y - meia, CX + larg / 2, y + meia)


def bate(c, i):
    return not (c[2] < i["x0"] - MARGEM or c[0] > i["x1"] + MARGEM or c[3] < i["y0"] - MARGEM or c[1] > i["y1"] + MARGEM)


def posicao(texto, a, b, ins):
    ativas = [i for i in ins if i["a"] < b and i["b"] > a]
    cands = [BASE_Y]
    for i in ativas:
        cands += [i["y1"] + MARGEM + 37, i["y0"] - MARGEM - 37]
    for i in ativas:                      # também logo acima/abaixo de duas inserções juntas
        for j in ativas:
            cands += [max(i["y1"], j["y1"]) + MARGEM + 37, min(i["y0"], j["y0"]) - MARGEM - 37]
    cands = sorted(set(round(y) for y in cands), key=lambda y: (y != BASE_Y, abs(y - BASE_Y)))
    for y in cands:
        c = caixa(texto, y)
        if c[1] >= LIM_CIMA and c[3] <= LIM_BAIXO and not any(bate(c, i) for i in ativas):
            return y, ativas
    return None, ativas


def ts(t):
    m, s = divmod(max(0, t), 60)
    return f"0:{int(m):02d}:{s:05.2f}"


CAB = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Base,Rubik SemiBold,46,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def main():
    PAL = palavras()
    ins = insercoes()
    inicio = next(k for k, w in enumerate(PAL) if w["s"] >= INICIO - 0.05)
    blocos, atual = [], []
    for i in range(inicio, len(PAL)):
        w = PAL[i]["w"]
        atual.append(i)
        chars = sum(len(PAL[k]["w"]) + 1 for k in atual)
        fim_frase = w[-1:] in ".?!,"
        prox_longe = i + 1 < len(PAL) and PAL[i + 1]["s"] - PAL[i]["e"] > 0.35
        chave = norm(w) in CHAVE
        if len(atual) >= 3 or chars >= 14 or fim_frase or prox_longe or (chave and len(atual) >= 2):
            blocos.append(atual)
            atual = []
    if atual:
        blocos.append(atual)

    ev, log = [], []
    for n, bl in enumerate(blocos):
        a = max(PAL[bl[0]]["s"] - 0.03, INICIO)
        b = PAL[bl[-1]]["e"] + 0.12
        if n + 1 < len(blocos):
            prox = PAL[blocos[n + 1][0]]["s"] - 0.03
            b = min(max(b, prox), PAL[bl[-1]]["e"] + 0.6, prox)
        cru = " ".join(PAL[k]["w"] for k in bl)
        y, ativas = posicao(cru, a, b, ins)
        if ativas:
            onde = "ESCONDIDA" if y is None else ("y padrão" if y == BASE_Y else f"y={y}")
            log.append(f"{ts(a)}  {cru:<28} {onde:<10} (inserção: {ativas[0]['txt']})")
        if y is None:
            continue
        partes = []
        for k in bl:
            p = PAL[k]["w"]
            if norm(p) in CHAVE:
                p = r"{\fnRubik Black\1c" + MANTEIGA + r"\fs52}" + p + r"{\fnRubik SemiBold\1c&HFFFFFF&\fs46}"
            partes.append(p)
        txt = " ".join(partes)
        pop = r"\fscx112\fscy112\t(0,90,\fscx100\fscy100)"
        sombra = re.sub(r"\\1c&H[0-9A-Fa-f]+&", "", txt)
        ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Base,,0,0,0,,{{\\an5\\pos({CX + 1},{y + 3})\\1c&H000000&\\3c&H000000&"
                  f"\\bord3\\blur8\\1a&H78&\\3a&H78&{pop}}}{sombra}")
        ev.append(f"Dialogue: 2,{ts(a)},{ts(b)},Base,,0,0,0,,{{\\an5\\pos({CX},{y}){pop}}}{txt}")
    open("legendas_ep3.ass", "w", encoding="utf-8").write(CAB + "\n".join(ev) + "\n")
    open("legendas_ep3_log.txt", "w", encoding="utf-8").write("\n".join(log) + "\n")
    json.dump(PAL, open("palavras_ep3.json", "w"), ensure_ascii=False)
    print(len(blocos), "blocos;", sum(1 for x in log if "ESCONDIDA" in x), "escondidos;",
          sum(1 for x in log if "y=" in x), "reposicionados")


if __name__ == "__main__":
    main()
