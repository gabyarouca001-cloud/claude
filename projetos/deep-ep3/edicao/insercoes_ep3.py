"""EP3 (9:16): gera insercoes_ep3.ass + eventos de SFX a partir do mapa_insercoes.py.
Padrão DEEP: amarelo manteiga #FCEDC0, Playfair Italic + Inter Black, sombra preta leve, brilho só no amarelo,
centro x=540, largura útil <= 800 px, faixa y 1000-1420 (área segura do Instagram), nunca sobre o rosto."""
import json

from PIL import ImageFont

import mapa_insercoes as M

W, H = 1080, 1920
BRANCO, AMARELO, ESCURO = "&H00FFFFFF&", "&H00C0EDFC&", "&H00262626&"
FONTES = "/home/user/work/ep3/fonts"
F900 = ImageFont.truetype(f"{FONTES}/Inter900.ttf", 100)
F800 = ImageFont.truetype(f"{FONTES}/Inter800.ttf", 100)

CAB = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Serif,Playfair Display,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,0,-1,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Bold,Inter Black,120,&H00C0EDFC,&H00FFFFFF,&H00000000,&HB4000000,0,0,0,0,100,100,-2,0,1,0,0,5,0,0,0,1
Style: Eco,Inter Black,560,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,-8,0,1,0,0,5,0,0,0,1
Style: Label,Inter Medium,32,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,0,0,0,0,100,100,6,0,1,0,0,7,0,0,0,1
Style: Lista,Inter ExtraBold,62,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,0,0,0,0,100,100,0,0,1,0,0,4,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ts(t):
    t = max(0, t)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def larg(txt, fonte, fs, esp=0):
    return fonte.getlength(txt) * fs / 100 + esp * len(txt)


def ajusta(txt, fonte, base, maxw=800, esp=0):
    """maior tamanho (<= base) em que o texto cabe em maxw"""
    return int(min(base, base * maxw / max(larg(txt, fonte, base, esp), 1)))


def quebra(txt, fonte, base, minimo=78, maxw=800, esp=-2):
    """uma linha se couber com tamanho decente; senão duas linhas equilibradas"""
    if ajusta(txt, fonte, base, maxw, esp) >= minimo or " " not in txt:
        return [txt]
    p = txt.split()
    melhor = min(range(1, len(p)), key=lambda k: abs(larg(" ".join(p[:k]), fonte, 100) - larg(" ".join(p[k:]), fonte, 100)))
    return [" ".join(p[:melhor]), " ".join(p[melhor:])]


def _tags(texto, alfa00, alfa70, blur, tira_cor):
    t = texto
    if tira_cor:
        t = t.replace(r"\1c&H00FFFFFF&", "").replace(r"\1c&H00C0EDFC&", "")
    t = t.replace(r"\alpha&H00&", rf"\alpha&H{alfa00}&").replace(r"\alpha&H70&", rf"\alpha&H{alfa70}&")
    import re
    return re.sub(r"\\blur\d+", rf"\\blur{blur}", t)


def sombra(texto):
    """sombra preta leve atrás das letras (pedido da editora): \\bord3\\blur8, ~50% de opacidade"""
    t = _tags(texto, "78", "C0", 8, True)
    pre = r"\1c&H000000&\3c&H000000&\bord3\blur8\alpha&H78&"
    return "{" + pre + t[1:]


def brilho(texto):
    """brilho suave só nas letras amarelas"""
    t = _tags(texto, "A0", "D0", 16, False)
    return "{" + r"\bord0\blur16\alpha&HA0&" + t[1:]


class Trilha:
    def __init__(self):
        self.ev, self.sfx = [], []

    def e(self, camada, ini, fim, estilo, texto, sombrear=True):
        self.ev.append(f"Dialogue: {camada + 2},{ts(ini)},{ts(fim)},{estilo},,0,0,0,,{texto}")
        desenho = r"\p1" in texto
        if sombrear and not desenho and estilo != "Eco" and ESCURO not in texto:
            self.ev.append(f"Dialogue: {camada},{ts(ini)},{ts(fim)},{estilo},,0,0,0,,{sombra(texto)}")
            if AMARELO in texto:
                self.ev.append(f"Dialogue: {camada + 1},{ts(ini)},{ts(fim)},{estilo},,0,0,0,,{brilho(texto)}")


def ret(w, h, r):
    k = r * 0.45
    return (f"m {r} 0 l {w - r} 0 b {w - k} 0 {w} {k} {w} {r} l {w} {h - r} b {w} {h - k} {w - k} {h} {w - r} {h} "
            f"l {r} {h} b {k} {h} 0 {h - k} 0 {h - r} l 0 {r} b 0 {k} {k} 0 {r} 0")


# ------------------------------------------------------------------ componentes
def titulo(T, a, b, serif, bold, eco=None):
    d = int((b - a) * 1000)
    linhas = quebra(bold, F900, 120)
    fs = min(ajusta(l, F900, 120, 800, -2) for l in linhas)
    if eco:
        fe = ajusta(eco, F900, 560, 1000, -8)
        T.e(0, a, b, "Eco", rf"{{\an5\pos(540,1190)\fs{fe}\alpha&HC0&\fad(250,300)\fscx96\fscy96\t(0,{d},\fscx106\fscy106)}}{eco}", False)
    y0 = 1085
    T.e(2, a, b, "Serif", rf"{{\an5\move(540,{y0 + 20},540,{y0},0,300)\fad(220,200)}}{serif}")
    for k, l in enumerate(linhas):
        y = y0 + 90 + k * int(fs * 1.02)
        T.e(2, a + 0.08, b, "Bold", rf"{{\an5\pos(540,{y})\fs{fs}\fscx118\fscy118\blur10\alpha&HFF&"
                                    r"\t(0,240,\fscx100\fscy100\blur0\alpha&H00&)\fad(0,200)}" + l)
    T.sfx.append((a, "whoosh"))


def capitulo(T, a, b, n, texto):
    y = 1290
    T.e(1, a, b, "Label", rf"{{\an7\pos(70,{y})\fad(300,300)\1c{AMARELO}\bord0\shad0\p1}}m 0 0 l 8 0 8 104 0 104{{\p0}}", False)
    T.e(2, a, b, "Label", rf"{{\an7\move(90,{y},108,{y},0,350)\fad(300,300)\1c{AMARELO}\fs30}}CAPÍTULO {n}")
    T.e(2, a + 0.12, b, "Label", rf"{{\an7\move(90,{y + 44},108,{y + 44},0,350)\fad(300,300)\fs54\b1}}{texto}")
    T.sfx.append((a, "chime"))


def lista(T, a, b, itens):
    n = len(itens)
    for k, (t, txt, destaque) in enumerate(itens):
        y = int(1200 + (k - (n - 1) / 2) * 100)
        fs = ajusta(txt, F800, 62, 700)
        cor = AMARELO if destaque else BRANCO
        T.e(1, t, b, "Lista", rf"{{\an7\pos(96,{y - 3})\fad(150,250)\1c{AMARELO}\bord0\shad0\p1}}m 0 0 l 40 0 40 7 0 7{{\p0}}", False)
        T.e(2, t, b, "Lista", rf"{{\an4\move(146,{y},158,{y},0,250)\fad(180,250)\fs{fs}\1c{cor}}}{txt}")
        T.sfx.append((t, "tick"))


def cadeia(T, a, b, itens):
    """ASSISTIR ↓ ACREDITAR ↓ COMPRAR: cada palavra entra na fala; as anteriores esmaecem"""
    ys = [1085, 1215, 1345]
    for k, (t, txt) in enumerate(itens):
        fim_dim = int(((itens[k + 1][0] if k + 1 < len(itens) else b) - t) * 1000)
        ultimo = k == len(itens) - 1
        fs = ajusta(txt, F900, 104 if ultimo else 88, 760, -2)
        cor = AMARELO if ultimo else BRANCO
        dim = "" if ultimo else rf"\t({fim_dim},{fim_dim + 250},\alpha&H70&)"
        T.e(2, t, b, "Bold", rf"{{\an5\pos(540,{ys[k]})\fs{fs}\1c{cor}\fscx115\fscy115\blur8\alpha&HFF&"
                             rf"\t(0,220,\fscx100\fscy100\blur0\alpha&H00&)\fad(0,220){dim}}}{txt}")
        if k:
            T.e(1, t - 0.1, b, "Label", rf"{{\an5\pos(540,{ys[k] - 66})\fad(150,250)\1c{AMARELO}\bord0\shad0\alpha&H30&\p1}}m -16 -9 l 0 9 l 16 -9 l 11 -11 l 0 1 l -11 -11{{\p0}}", False)
        T.sfx.append((t, "tick"))


def duas_caixas(T, a, t2, tv, b):
    """TESTOU O PRODUTO / OU SÓ REPETIU? — a 2ª caixa vira amarela na virada"""
    w, h = 760, 130
    x0 = 540 - w // 2
    T.e(1, a, b, "Label", rf"{{\an7\pos({x0},1060)\fad(200,250)\1a&HFF&\3c{BRANCO}\3a&H30&\bord3\shad0\p1}}{ret(w, h, 30)}{{\p0}}", False)
    T.e(2, a, b, "Lista", rf"{{\an5\pos(540,1125)\fad(200,250)\fs56}}TESTOU O PRODUTO")
    T.sfx.append((a, "whoosh"))
    ms = int((tv - t2) * 1000)
    T.e(1, t2, b, "Label", rf"{{\an7\pos({x0},1230)\fad(200,250)\1a&HFF&\3c{BRANCO}\3a&H30&\bord3\shad0"
                           rf"\t({ms},{ms + 220},\1a&H00&\1c{AMARELO}\3c{AMARELO}\3a&H00&)\p1}}{ret(w, h, 30)}{{\p0}}", False)
    T.e(2, t2, tv, "Lista", rf"{{\an5\pos(540,1295)\fad(200,120)\fs56}}OU SÓ REPETIU?")
    T.e(2, tv, b, "Lista", rf"{{\an5\pos(540,1295)\fs56\fscx112\fscy112\t(0,200,\fscx100\fscy100)\fad(0,250)\1c{ESCURO}}}OU SÓ REPETIU?")
    T.sfx.append((t2, "tick")); T.sfx.append((tv, "bloco"))


def caixa_app(T, a, tv, b):
    """caixa 'DENTRO DO APLICATIVO': contorno; na virada ('comprar na mesma hora') vira amarela"""
    w, h = 780, 200
    x0, y0 = 540 - w // 2, 1060
    ms = int((tv - a) * 1000)
    T.e(1, a, b, "Label", rf"{{\an7\pos({x0},{y0})\fad(250,300)\1a&HFF&\3c{BRANCO}\3a&H30&\bord3\shad0"
                          rf"\t({ms},{ms + 250},\1a&H00&\1c{AMARELO}\3c{AMARELO}\3a&H00&)\p1}}{ret(w, h, 36)}{{\p0}}", False)
    T.e(2, a, tv, "Label", rf"{{\an5\pos(540,{y0 + 44})\fad(250,150)\1c{AMARELO}\fs30\fsp5}}DENTRO DO APLICATIVO")
    T.e(2, a + 0.1, tv, "Lista", rf"{{\an5\pos(540,{y0 + 125})\fad(250,150)\fs52}}ENTRA PARA SE DISTRAIR")
    T.e(2, tv, b, "Lista", rf"{{\an5\pos(540,{y0 + 100})\fs58\fscx112\fscy112\t(0,200,\fscx100\fscy100)\fad(0,300)\1c{ESCURO}}}COMPRA NA MESMA HORA")
    T.sfx.append((a, "whoosh")); T.sfx.append((tv, "bloco"))


# ------------------------------------------------------------------ montagem a partir do mapa
def t(o):
    return M.saida(o)


def gerar():
    T = Trilha()
    S = M.saida
    L = M.INS
    ini = lambda i, k=0: max(S(L[i][2][k]) - 0.15, 11.7)
    fim = lambda i: S(L[i][3])
    titulo(T, ini(0), fim(0), "a história participa", "DA SUA ESCOLHA")
    cadeia(T, ini(1), fim(1), [(S(o) - 0.05, x) for o, x in zip(L[1][2], ["ASSISTIR", "ACREDITAR", "COMPRAR"])])
    capitulo(T, ini(2), fim(2), 1, "Produção")
    lista(T, ini(3), fim(3), [(S(o) - 0.05, x, False) for o, x in zip(L[3][2], ["ESCREVER", "EDITAR", "CRIAR IMAGENS E VÍDEOS"])])
    titulo(T, ini(4), fim(4), "a qualidade da apresentação", "NÃO COMPROVA A INFORMAÇÃO")
    duas_caixas(T, ini(5), S(L[5][2][1]) - 0.1, S(L[5][2][1]) + 0.55, fim(5))
    titulo(T, ini(6), fim(6), "conseguir", "DEMONSTRAR O QUE SUSTENTA")
    capitulo(T, ini(7), fim(7), 2, "Compra")
    caixa_app(T, ini(8), S(L[8][2][1]) - 0.05, fim(8))
    lista(T, ini(9), fim(9), [(S(o) - 0.05, x, d) for o, x, d in zip(L[9][2], ["DIVERTIR", "ENSINAR", "GERAR COMISSÃO"], [False, False, True])])
    titulo(T, ini(10), fim(10), "saber que existe", "INTERESSE COMERCIAL")
    capitulo(T, ini(11), fim(11), 3, "O tamanho do negócio")
    lista(T, ini(12), fim(12), [(S(o) - 0.05, x, False) for o, x in zip(L[12][2], ["EQUIPES", "PROGRAMAS", "PRODUTOS", "ASSINATURAS"])])
    titulo(T, ini(13), fim(13), "construindo", "EMPRESAS", eco="EMPRESAS")
    # L[14] = b-roll (feed / podcast / loja): sem camada de texto
    lista(T, ini(15), fim(15), [(S(o) - 0.05, x, False) for o, x in zip(L[15][2], ["RECEBER", "ACOMPANHAR", "PAGAR"])])
    titulo(T, ini(16), fim(16), "uma questão central", "CONFIANÇA")
    lista(T, ini(17), fim(17), [(S(o) - 0.05, x, False) for o, x in zip(L[17][2], ["SE SUSTENTA?", "É CUMPRIDA?", "É ASSUMIDO?"])])
    titulo(T, ini(18), fim(18), "perguntar, discordar e", "MUDAR DE OPINIÃO")
    titulo(T, ini(19), fim(19), "quem é influenciado:", "TODOS NÓS", eco="NÓS")
    titulo(T, ini(20), fim(20), "o que faz alguém merecer", "A SUA CONFIANÇA?")
    titulo(T, ini(21), fim(21), "e o que faria você", "MUDAR DE IDEIA?")
    open("/home/user/work/ep3/insercoes_ep3.ass", "w").write(CAB + "\n".join(T.ev) + "\n")
    json.dump(T.sfx, open("/home/user/work/ep3/sfx_insercoes.json", "w"))
    print(len(T.ev), "eventos ASS;", len(T.sfx), "efeitos sonoros")


if __name__ == "__main__":
    gerar()
