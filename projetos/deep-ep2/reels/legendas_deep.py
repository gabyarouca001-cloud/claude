"""Legendas no padrão da editora (referência: reel "Me conta qual dessas mais te pegou").
Base: Rubik SemiBold branca, 2-3 palavras, ~64% da altura, sombra esfumada. Destaques variando fontes:
Rubik Black amarelo manteiga (palavra a palavra), Playfair Display itálico branco+ouro (palavra a palavra),
Amatic SC branco grande (letra a letra). Nada antes do fim de "Posso pesar o clima?"."""
import json
import re
import unicodedata

W, H = 1080, 1920
BASE_Y = 1221                  # ~63,6% da altura (medido no reel de referência)
CX = 510                       # centro da área segura do Instagram (direita 140 px livres)
LARG = 800                     # largura útil dos destaques
BRANCO, OURO, MANTEIGA = "&H00FFFFFF&", "&H000BCEF1&", "&H00C1ECFB&"
OFF = 9.8                     # abertura da editora (vinheta incluída)
PAL = [dict(w, s=w["s"] + OFF, e=w["e"] + OFF) for s in json.load(open("final_reels.json")) for w in s["words"]]
FIX = {"dip": "DEEP", "deep": "DEEP", "substacks": "Substack", "substeques": "Substack"}
CHAVE = {"deep", "instagram", "substack", "substacks", "podcast", "podcasts", "newsletter", "faturamento", "fatura",
         "constroi", "construir", "construindo", "construcao", "dependencia", "feed", "atencao", "rotina", "confiar",
         "milhoes", "profundidade", "referencias", "comunidade", "campanha", "carreira", "motivo", "reputacao",
         "nome", "algoritmo", "aplicativo", "plataformas", "conversa", "entrou", "concreto", "reconhecivel"}


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
DESTAQUES = [   # (frase falada, estilo, linhas, perto de (s, tempo do Reels sem a abertura))
    ("guarda esse nome", "rubik", [["GUARDA"], ["ESSE NOME"]], 2),
    ("alguma coisa tinha ficado", "amatic", ["ALGUMA COISA", "TINHA FICADO"], 33),
    ("questão de ir procurar", "rubik", [["QUESTÃO DE"], ["IR PROCURAR"]], 61),
    ("essas duas vontades estão se encontrando", "playfair", [[("essas duas vontades", BRANCO)], [("estão se", BRANCO), ("encontrando", OURO)]], 106),
    ("com quem se aprofundar", "amatic", ["COM QUEM", "SE APROFUNDAR"], 141),
    ("o que você fatura e o que você constrói", "playfair", [[("o que você", BRANCO), ("fatura", OURO)], [("e o que você", BRANCO), ("constrói", OURO)]], 157),
    ("4 milhões de criadores", "rubik", [["4 MILHÕES"], ["DE CRIADORES"]], 165),
    ("o próximo mês", "rubik", [["O PRÓXIMO"], ["MÊS"]], 193),
    ("continuar escolhendo acompanhar você", "playfair", [[("continuar", BRANCO), ("escolhendo", OURO)], [("acompanhar você", BRANCO)]], 202),
    ("não elimina a sua dependência dele", "amatic", ["NÃO ELIMINA", "A SUA DEPENDÊNCIA", "DELE"], 275),
    ("não resolve", "rubik", [["NÃO"], ["RESOLVE"]], 317),
    ("merece fazer parte da rotina de alguém", "playfair", [[("merece fazer parte", BRANCO)], [("da", BRANCO), ("rotina", OURO), ("de alguém", BRANCO)]], 347),
    ("proposta reconhecível", "amatic", ["PROPOSTA", "RECONHECÍVEL"], 359),
    ("lembra do nome", "rubik", [["LEMBRA"], ["DO NOME?"]], 373),
    ("quanto entrou", "amatic", ["QUANTO", "ENTROU"], 398),
    ("em quem confiar", "playfair", [[("em quem", BRANCO), ("confiar?", OURO)]], 434),
]
DESTAQUES = [(f, t, p, x + OFF) for f, t, p, x in DESTAQUES]
SFX = []   # (tempo, tipo, variação)

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


AMARELOS = (OURO, MANTEIGA)


def brilho(texto, estilo):
    """cópia só das palavras amarelas (o resto invisível), para o brilho ficar apenas no destaque amarelo"""
    if estilo == "Amatic":
        return None
    def troca(m):
        c = "&H" + m.group(1) + "&"
        return m.group(0) + (r"\alpha&H90&" if c.upper() in [a.upper() for a in AMARELOS] else r"\alpha&HFF&")
    g = re.sub(r"\\1c&H([0-9A-Fa-f]+)&", troca, texto)
    if not re.search(r"\\1c&H([0-9A-Fa-f]+)&", texto) and estilo == "Base":
        return None
    ini = r"\alpha&H90&" if estilo == "Rubik" else r"\alpha&HFF&"
    # trechos invisíveis (palavras que ainda vão entrar) continuam invisíveis
    g = g.replace(r"{\alpha&HFF&}", r"{\alpha&HFF&\1a&HFF&}")
    return ini, g


def com_sombra(a, b, estilo, pos, texto, blur=9, alfa="&H70&", desl=4, extra="", esc=100):
    """texto + sombra preta leve (só para dar leitura) + brilho apenas no amarelo"""
    x, y = pos
    sc = rf"\fscx{esc}\fscy{esc}" if esc != 100 else ""
    sombra = re.sub(r"\\1c&H[0-9A-Fa-f]+&", "", texto)
    sombra = sombra.replace(r"\alpha&HFF&", r"\alpha&HFF&\3a&HFF&")
    ev(0, a, b, estilo, rf"{{\an5\pos({x + 1:.0f},{y + 3})\1c&H000000&\3c&H000000&\bord3\blur8\1a&H78&\3a&H78&{sc}{extra}}}{sombra}")
    gl = brilho(texto, estilo)
    if gl:
        ini, g = gl
        ev(1, a, b, estilo, rf"{{\an5\pos({x},{y})\bord0\blur14{ini}{sc}{extra}}}{g}")
    ev(2, a, b, estilo, rf"{{\an5\pos({x},{y}){sc}{extra}}}{texto}")


from PIL import ImageFont
FONTE = {"Rubik": ("Rubik_wght_900.ttf", 112), "Playfair": ("Playfair_Display_ital_wght_1_500.ttf", 120),
         "Amatic": ("Amatic_SC_wght_700.ttf", 140)}


def escala(estilo, linhas):
    """reduz o destaque se alguma linha passar da largura útil da área segura"""
    f, tam = FONTE[estilo]
    fn = ImageFont.truetype("fonts/" + f, tam)
    larg = max(fn.getlength(l) for l in linhas)
    return min(100, int(LARG / larg * 100)) if larg else 100


# ------------------------------------------------------------------ destaques
ocupado = []
for frase, tipo, partes, perto in DESTAQUES:
    i0, i1 = achar(frase, perto)
    a = PAL[i0]["s"] - 0.05
    b = PAL[i1]["e"] + 0.5
    if i1 + 1 < len(PAL):
        b = min(b, PAL[i1 + 1]["s"] - 0.06)
    ocupado.append((i0, i1))
    SFX.append((b - 0.12, "saida_" + tipo, len(SFX)))
    textos = [" ".join(l) if tipo == "rubik" else (l if tipo == "amatic" else " ".join(p for p, _ in l)) for l in partes]
    esc = escala(tipo.capitalize(), textos)
    if tipo == "rubik":
        # palavra a palavra, com leve "pop"
        palavras_fala = iter(range(i0, i1 + 1))
        y0 = 1040 - (len(partes) - 1) * 46 * esc / 100
        for n, linha in enumerate(partes):
            y = y0 + n * 92 * esc / 100
            texto_linha = " ".join(linha)
            # posição de cada palavra: reserva a linha inteira com as palavras ainda invisíveis
            for k, palavra in enumerate(linha):
                j = next(palavras_fala, i1)
                t = max(a, PAL[min(j, i1)]["s"] - 0.04)
                vis = " ".join(linha[:k + 1])
                inv = " ".join(linha[k + 1:])
                txt = vis + (r"{\alpha&HFF&} " + inv if inv else "")
                fim = b if k == len(linha) - 1 else max(t + 0.05, PAL[min(j + 1, i1)]["s"] - 0.04)
                ultimo = n == len(partes) - 1 and k == len(linha) - 1
                com_sombra(t, fim, "Rubik", (CX, round(y)), txt, esc=esc,
                           extra=r"\fad(0,140)" if k == len(linha) - 1 else "")
                SFX.append((t, "pop", n * 3 + k))
    elif tipo == "playfair":
        y0 = 1030 - (len(partes) - 1) * 50 * esc / 100
        ordem = list(range(i0, i1 + 1))
        pos = 0
        for n, linha in enumerate(partes):
            y = y0 + n * 100 * esc / 100
            for k in range(len(linha)):
                # quando aparece este pedaço: no início da sua primeira palavra
                npal = len(linha[k][0].split())
                t = max(a, PAL[ordem[min(pos, len(ordem) - 1)]]["s"] - 0.04)
                pos += npal
                vis = " ".join(rf"{{\1c{c}}}{p}" for p, c in linha[:k + 1])
                inv = " ".join(p for p, _ in linha[k + 1:])
                txt = vis + (r"{\alpha&HFF&} " + inv if inv else "")
                fim = b if k == len(linha) - 1 else PAL[ordem[min(pos, len(ordem) - 1)]]["s"] - 0.04
                com_sombra(t, max(fim, t + 0.05), "Playfair", (CX, round(y)), txt, esc=esc,
                           extra=r"\fad(120,140)" if k == len(linha) - 1 else r"\fad(120,0)")
                SFX.append((t, "brilho", n * 2 + k))
    elif tipo == "amatic":
        # letra a letra, uma linha por evento (controle do espaçamento), distribuído ao longo da fala
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
                ultimo_da_linha = q == len(visiveis) - 1
                fim = b if ultimo_da_linha else prox
                vis, inv = linha[:k + 1], linha[k + 1:]
                txt = vis + (r"{\alpha&HFF&}" + inv if inv else "")
                com_sombra(t, fim, "Amatic", (CX, int(y)), txt, esc=esc,
                           extra=r"\fad(0,140)" if ultimo_da_linha else "")
                SFX.append((t, "tecla", m))

# ------------------------------------------------------------------ legenda base
inicio = 0
blocos, atual = [], []
dentro = {i for i0, i1 in ocupado for i in range(i0, i1 + 1)}
for i in range(inicio, len(PAL)):
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
    curta = norm(w) in CHAVE                      # palavra-chave fecha o bloco (fica no fim, com destaque)
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
    if n + 1 < len(blocos) and blocos[n + 1][0] - bl[-1] > 1:   # destaque logo depois: sai antes dele
        b = min(b, PAL[blocos[n + 1][0]]["s"] - 0.03, PAL[bl[-1] + 1]["s"] - 0.08)
    elif bl[-1] + 1 < len(PAL) and (bl[-1] + 1) in dentro:
        b = min(b, PAL[bl[-1] + 1]["s"] - 0.08)
    partes = []
    for k in bl:
        p = PAL[k]["w"].strip()
        base = re.sub(r"[^\wÀ-ú-]", "", p)
        p = p.replace(base, FIX.get(norm(base), base)) if norm(base) in FIX else p
        if norm(base) in CHAVE:
            p = r"{\fnRubik Black\1c" + MANTEIGA + r"\fs52}" + p + r"{\fnRubik SemiBold\1c&HFFFFFF&\fs46}"
        partes.append(p)
    txt = " ".join(partes)
    pop = r"\fscx112\fscy112\t(0,90,\fscx100\fscy100)"
    com_sombra(a, b, "Base", (CX, BASE_Y), txt, extra=pop)

open("legendas_deep.ass", "w", encoding="utf-8").write(CAB + "\n".join(EV) + "\n")
json.dump(sorted(SFX), open("sfx_deep.json", "w"))
print(len(blocos), "blocos de legenda,", len(DESTAQUES), "destaques")
