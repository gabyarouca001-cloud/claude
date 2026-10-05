"""EP2 — textos (ASS), efeitos sonoros e mix, no padrão aprovado do EP1. Âncoras nas palavras da montagem
final do YouTube (final_youtube.json); a versão Instagram recebe as mesmas inserções remapeadas (as que caem
em trecho exclusivo do YouTube saem)."""
import difflib
import json
import os
import re
import subprocess
import sys
import unicodedata

import numpy as np

SR = 48000
# BASE=youtube2: versão final do YouTube com a abertura da editora (inicio_editora.mp4) e os cortes de erro de fala;
# âncoras na retranscrição dessa montagem e tempos "perto" convertidos da montagem antiga do YouTube
BASE = os.environ.get("BASE", "youtube")
OFF = 9.68 if BASE == "youtube2" else 0.0
if BASE == "youtube2":
    PAL = json.load(open("checar_youtube2.json"))
else:
    PAL = [w for s in json.load(open("final_youtube.json")) for w in s["words"]]


def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if unicodedata.category(c) != "Mn"))


TOK = [norm(w["w"]) for w in PAL]


SINONIMOS = {"para": "pra", "estou": "to", "esta": "ta", "substeques": "substacks", "substack": "substacks", "dip": "deep"}


def parecido(a, b):
    """tokens iguais, com grafias equivalentes ou quase iguais (o Whisper varia "pra/para", "substeques"...)"""
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        x, y = SINONIMOS.get(x, x), SINONIMOS.get(y, y)
        if x != y and not (min(len(x), len(y)) >= 5 and difflib.SequenceMatcher(None, x, y).ratio() >= 0.8):
            return False
    return True


def antigo_para_novo(t):
    """tempo da montagem antiga do YouTube -> montagem youtube2 (pela fonte; usa o segmento mais próximo)"""
    if BASE != "youtube2":
        return t
    velho = json.load(open("plano_youtube.json"))["segmentos"]
    novo = json.load(open("plano_youtube2.json"))["segmentos"]
    s = min(velho, key=lambda s: 0 if s["t"] <= t <= s["t"] + s["fim"] - s["ini"] else min(abs(t - s["t"]), abs(t - s["t"] - s["fim"] + s["ini"])))
    src = s["ini"] + min(max(t - s["t"], 0), s["fim"] - s["ini"])
    q = min((q for q in novo if q["fonte"] == s["fonte"]),
            key=lambda q: 0 if q["ini"] <= src <= q["fim"] else min(abs(src - q["ini"]), abs(src - q["fim"])))
    return q["t"] + min(max(src - q["ini"], 0), q["fim"] - q["ini"])


def achar(frase, perto, apos=None, novo=False):
    """ocorrência da frase mais próxima de `perto` (s); com `apos`, só depois desse instante"""
    if apos is None and not novo:
        perto = antigo_para_novo(perto)
    alvo = [norm(p) for p in frase.split()]
    occ = [(w["s"], PAL[i + len(alvo) - 1]["e"]) for i, w in enumerate(PAL)
           if parecido(TOK[i:i + len(alvo)], alvo) and (apos is None or w["s"] > apos)]
    if not occ:
        raise ValueError(f"não achei {frase!r} perto de {perto}")
    return min(occ, key=lambda o: abs(o[0] - perto)) if apos is None else min(occ)


# ------------------------------------------------------------------ mapa YouTube -> Instagram
PY = json.load(open(f"plano_{BASE}.json"))["segmentos"]
PI = json.load(open("plano_instagram.json"))["segmentos"]


def para_ig(t):
    for s in PY:
        if s["t"] <= t < s["t"] + s["fim"] - s["ini"] + 1e-6:
            src = s["ini"] + t - s["t"]
            for q in PI:
                if q["fonte"] == s["fonte"] and q["ini"] - 1e-6 <= src <= q["fim"] + 1e-6:
                    return q["t"] + src - q["ini"]
            return None
    return None


# ------------------------------------------------------------------ inserções
# tipo, frase-âncora, procurar depois de (s, timeline YT), duração ou frase final, conteúdo
INS = [
    ("titulo", "pensou em alguém", 6, "comecei a pensar", dict(serif="pensou em alguém?", bold="GUARDA ESSE NOME")),
    ("capitulo", "comecei a pensar", 10, 3.6, dict(texto="O QUE A GENTE ESTÁ PROCURANDO")),
    ("titulo", "substacks", 20, 2.8, dict(serif="procurar em outros lugares:", bold="SUBSTACK, PODCASTS")),
    ("lista", "porque eu queria ter tempo", 28, "e essa busca", dict(titulo="eu queria…", itens=[
        ("acompanhar uma ideia", 28, "acompanhar uma ideia"),
        ("raciocínio de alguém", 33, "entender um raciocínio"),
        ("terminar um conteúdo", 36, "sentir que algo ficou")])),
    ("titulo", "outras eu fazia", 78, 3.2, dict(serif="outras, eu fazia questão de", bold="PROCURAR", eco="PROCURAR")),
    ("lista", "tem muita gente também", 100, "e tem criador", dict(titulo="tem muita gente procurando…", itens=[
        ("espaço para aprender", 100, "espaço pra aprender"),
        ("conteúdo com profundidade", 105, "profundidade"),
        ("encontrar referências", 110, "referências"),
        ("se abastecer", 112, "se abastecer")])),
    ("titulo", "essas duas vontades", 125, 3.4, dict(serif="essas duas vontades estão", bold="SE ENCONTRANDO")),
    ("formatos", "num vídeo curto", 135, "a gente também quer", dict(itens=[
        ("num vídeo curto", 135, "video", "vídeo curto"), ("num podcast", 140, "podcast", "podcast"),
        ("num texto", 141, "texto", "texto"), ("numa comunidade", 142, "comunidade", "comunidade")],
        papeis=[("despertar o interesse", 148, 0, "DESPERTA"), ("dar espaço para desenvolver", 150, 2, "DESENVOLVEM")])),
    ("titulo", "com quem se aprofundar", 165, 2.6, dict(serif="escolher com quem", bold="APROFUNDAR", eco="DEEP")),
    # --- trecho exclusivo do YouTube 1
    ("capitulo", "e tem uma diferença", 170, 3.6, dict(texto="DESCOBRIR × COMPREENDER")),
    ("titulo", "10 opiniões", 183, 3.0, dict(serif="10 vídeos,", bold="10 OPINIÕES", eco="10")),
    ("titulo", "o que falta é contexto", 194, 2.8, dict(serif="o que falta é", bold="CONTEXTO", eco="CONTEXTO")),
    ("pesquisa", "e eu encontrei uma", 210, "mas isso não significa", dict(
        titulo="por que as pessoas ouvem podcasts de notícias", itens=[
            ("profundidade", 219, "profundidade"), ("aprendizado", 224, "aprendizado"),
            ("compreensão", 225, "compreensão")], fonte="FONTE: REUTERS INSTITUTE")),
    ("titulo", "longo para ser bom", 234, 2.8, dict(serif="não precisa ser longo", bold="PRA SER BOM")),
    ("versus", "um corte pode apresentar", 259, "e a mesma pessoa", dict(
        serif="um corte mostra a conclusão;", esq="CONCLUSÃO", dir="RACIOCÍNIO", dir_ancora=("uma conversa completa", 262))),
    ("lista", "tem hora de descobrir", 284, 7.5, dict(titulo="tem hora de…", itens=[
        ("descobrir", 285, "descobrir"), ("se divertir", 287, "se divertir"), ("permanecer", 289, "permanecer num assunto")])),
    # --- faturar x construir
    ("capitulo", "e foi dessa vontade", 293, 3.6, dict(texto="FATURAR × CONSTRUIR")),
    ("titulo", "o que você fatura", 305, "lembra que no", dict(serif="o que você fatura", bold="× O QUE VOCÊ CONSTRÓI")),
    ("titulo", "4 milhões", 312, 3.4, dict(serif="mais de", bold="4 MILHÕES", eco="4 MILHÕES", extra="de criadores, só no Instagram", contador=4000000)),
    ("titulo", "como fazer esse trabalho", 333, 2.6, dict(serif="como fazer esse trabalho", bold="CONTINUAR?")),
    ("titulo", "não garante necessariamente", 340, 3.2, dict(serif="o faturamento de hoje não garante", bold="O PRÓXIMO MÊS")),
    ("tijolos", "porque envolve o trabalho", 360, "lembrando que uma", dict(titulo="construir envolve…", itens=[
        ("o trabalho que você", 360, "TRABALHO"), ("a relação que você", 365, "RELAÇÃO"),
        ("e o motivo que você", 368, "MOTIVO")])),
    ("lista", "uma campanha envolve", 374, "e sim com certeza", dict(titulo="uma campanha tem…", itens=[
        ("entrega", 376, "entrega"), ("prazo", 378, "prazo"), ("pagamento", 379, "pagamento")])),
    ("titulo", "entre uma campanha e outra", 389, 3.6, dict(serif="entre uma campanha e outra,", bold="POR QUE FICAR?")),
    ("citacao", "que tipo de conversa", 406, "hoje existem", dict(serif="que tipo de conversa eu quero ter?", bold="POR QUE ALGUÉM ESCOLHERIA VOLTAR?")),
    # --- mais caminhos, mesma dependência
    ("capitulo", "hoje existem mais caminhos", 414, 3.6, dict(texto="MAIS CAMINHOS, A MESMA DEPENDÊNCIA")),
    ("app", "como programas", 420, "e eu realmente não", dict(itens=[
        ("como programas", 421, "programas"), ("produtos", 422, "produtos"), ("assinaturas", 423, "assinaturas"),
        ("comunidades", 424, "comunidades"), ("vender", 427, "vendas"), ("receber comissões", 428, "comissões"),
        ("fechar parcerias", 429, "parcerias")], virada=("não elimina a sua", 437))),
    ("titulo", "no feed de alguém", 455, 2.6, dict(serif="não depender de", bold="APARECER NO FEED")),
    ("titulo", "criei uma newsletter", 462, 3.0, dict(serif="outro caminho:", bold="NEWSLETTER")),
    ("titulo", "mudar de lugar sozinho", 476, 3.2, dict(serif="mudar de lugar, sozinho,", bold="NÃO RESOLVE")),
    ("lista", "porque até num", 481, "e estar em vários", dict(titulo="em todo lugar…", itens=[
        ("até num", 481, "e-mail: disputa atenção"), ("num podcast", 486, "podcast: fica na metade"),
        ("uma assinatura", 491, "assinatura: cancelada")])),
    # --- trecho exclusivo do YouTube 2
    ("titulo", "também tem um custo", 495, 2.8, dict(serif="estar em vários lugares", bold="TEM UM CUSTO")),
    ("citacao", "o que a pessoa vai encontrar", 518, "um podcast pode", dict(
        serif="o que a pessoa vai encontrar ali que justifique", bold="ACOMPANHAR POR ESSE CAMINHO?")),
    ("titulo", "cada formato precisa", 540, 3.2, dict(serif="cada formato precisa ter uma", bold="FUNÇÃO")),
    ("titulo", "ter um perfil em outro", 548, 4.2, dict(serif="perfil em outro app", bold="≠ CANAL DE CONTATO")),
    ("titulo", "a atenção continua", 580, 3.6, dict(serif="a atenção continua sendo", bold="ESCOLHA DO OUTRO")),
    # --- o que é construir
    ("capitulo", "a pessoa precisa encontrar", 595, 3.6, dict(texto="O QUE É CONSTRUIR")),
    ("citacao", "o que eu estou entregando", 605, "para mim é aí", dict(
        serif="o que eu estou entregando que merece fazer parte da", bold="ROTINA DE ALGUÉM?")),
    ("titulo", "proposta reconhecível", 622, 3.2, dict(serif="uma proposta", bold="RECONHECÍVEL")),
    ("titulo", "lembra do nome", 652, 2.8, dict(serif="lembra do", bold="NOME?")),
    ("lista", "pelo conhecimento", 658, "e é esse motivo", dict(titulo="você procuraria essa pessoa…", itens=[
        ("pelo conhecimento", 658, "pelo conhecimento"), ("pelo humor", 662, "pelo humor"),
        ("pelo jeito", 663, "pelo jeito de contar")])),
    ("titulo", "quanto entrou", 678, "mas o que você constrói", dict(serif="o faturamento mostra", bold="QUANTO ENTROU")),
    ("tijolos", "mas o que você constrói", 682, "só que essa relação", dict(titulo="o que você constrói aparece…", itens=[
        ("no trabalho que consegue", 686, "TRABALHO"), ("na reputação", 689, "REPUTAÇÃO"),
        ("e nos motivos", 692, "MOTIVOS")])),
    ("titulo", "em quem confiar", 715, 2.8, dict(serif="como decidir", bold="EM QUEM CONFIAR?", eco="CONFIAR")),
    ("proximo", "e é sobre isso", 718, "fim", dict()),
]

BRANCO, DESTAQUE = "&H00FFFFFF&", "&H00C0EDFC&"
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
Style: Lista,Inter ExtraBold,56,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,0,0,0,0,100,100,0,0,1,0,1.5,4,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ts(t):
    t = max(0, t)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


class Trilha:
    def __init__(self):
        self.ev, self.sfx = [], []

    def e(self, camada, ini, fim, estilo, texto):
        self.ev.append(f"Dialogue: {camada},{ts(ini)},{ts(fim)},{estilo},,0,0,0,,{texto}")
        if estilo != "Eco" and r"\p1" not in texto and r"\1c&H262626&" not in texto:
            self.ev.append(f"Dialogue: {max(camada - 1, 0)},{ts(ini)},{ts(fim)},{estilo},,0,0,0,,{sombra(texto)}")


def sombra(texto):
    """sombra preta leve atrás das letras, só para dar leitura sobre fundo claro (pedido da editora no Reels)"""
    t = re.sub(r"\\1c&H[0-9A-Fa-f]+&", "", texto)
    t = t.replace(r"\alpha&H00&", r"\alpha&H78&").replace(r"\blur0", r"\blur8")
    pre = r"\1c&H000000&\3c&H000000&\bord3\blur8"
    if not re.match(r"\{[^}]*\\alpha", t):
        pre += r"\alpha&H78&"
    return "{" + pre + t[1:] if t.startswith("{") else "{" + pre + "}" + t


def tamanho_bold(texto, base=190, largura=1700):
    return min(base, int(largura / (0.68 * max(len(texto), 1))))


def titulo(T, a, b, serif, bold, eco=None, extra=None, y_serif=636, y_bold=750, contador=None):
    d = int((b - a) * 1000)
    if contador:   # número contando até o valor e virando a palavra final
        n = 24
        for k in range(n):
            v = contador * (1 - (1 - (k + 1) / n) ** 3)
            T.e(2, a + 0.08 + k / 30, a + 0.08 + (k + 1) / 30, "Bold", rf"{{\an5\pos(960,{y_bold})\fs{tamanho_bold(bold)}}}{numero_br(v)}")
        T.e(2, a + 0.08 + n / 30, b, "Bold", rf"{{\an5\pos(960,{y_bold})\fs{tamanho_bold(bold)}\fscx112\fscy112\t(0,160,\fscx100\fscy100)\fad(0,200)}}{bold}")
        T.e(2, a, b, "Serif", rf"{{\an5\move(960,{y_serif + 22},960,{y_serif},0,300)\fad(220,200)}}{serif}")
        if extra:
            T.e(2, a + 0.3, b, "Serif", rf"{{\an5\pos(960,{y_bold + 105})\fs62\fad(250,200)}}{extra}")
        T.sfx.append((a, "whoosh"))
        return
    if eco:
        fs = min(640, int(1900 / (0.62 * max(len(eco), 1))))
        T.e(0, a, b, "Eco", rf"{{\an5\pos(960,700)\fs{fs}\alpha&HC4&\fad(250,300)\fscx96\fscy96\t(0,{d},\fscx106\fscy106)}}{eco}")
    T.e(2, a, b, "Serif", rf"{{\an5\move(960,{y_serif + 22},960,{y_serif},0,300)\fad(220,200)}}{serif}")
    T.e(2, a + 0.08, b, "Bold", rf"{{\an5\pos(960,{y_bold})\fs{tamanho_bold(bold)}\fscx118\fscy118\blur10\alpha&HFF&"
                                r"\t(0,240,\fscx100\fscy100\blur0\alpha&H00&)\fad(0,200)}" + bold)
    if extra:
        T.e(2, a + 0.3, b, "Serif", rf"{{\an5\pos(960,{y_bold + 105})\fs62\fad(250,200)}}{extra}")
    T.sfx.append((a, "whoosh"))


def capitulo(T, a, b, texto):
    T.e(1, a, b, "Label", r"{\an7\pos(110,915)\fad(300,300)\1c" + DESTAQUE + r"\bord0\shad0\p1}m 0 0 l 8 0 8 112 0 112{\p0}")
    T.e(2, a, b, "Label", r"{\an7\move(120,915,140,915,0,350)\fad(300,300)\1c" + DESTAQUE + r"\fs32}CAPÍTULO")
    T.e(2, a + 0.12, b, "Label", r"{\an7\move(120,958,140,958,0,350)\fad(300,300)\fs60\b1\fsp3}" + texto)
    T.sfx.append((a, "chime"))


def lista(T, a, b, titulo_txt, itens, fonte=None):
    T.e(2, a, b, "Serif", rf"{{\an4\move(100,400,120,400,0,300)\fad(250,250)\fs54}}{titulo_txt}")
    for n, (t, texto) in enumerate(itens):
        y = 490 + n * 95
        T.e(2, t, b, "Lista", rf"{{\an4\move(100,{y},120,{y},0,250)\fad(200,250)}}{{\1c{DESTAQUE}}}— {{\1c{BRANCO}}}{texto}")
        T.sfx.append((t, "tick"))
    if fonte:
        T.e(2, a + 0.4, b, "Label", rf"{{\an4\pos(122,{490 + len(itens) * 95 + 10})\fad(300,250)\fs26\alpha&H40&}}{fonte}")


def versus(T, a, b, serif, esq, dir, t_dir):
    T.e(2, a, b, "Serif", rf"{{\an5\move(960,607,960,585,0,300)\fad(220,200)}}{serif}")
    T.e(2, a + 0.1, b, "Bold", rf"{{\an6\pos(880,700)\fs150\fad(200,200)\1c{BRANCO}\alpha&H50&}}{esq}")
    T.e(2, a + 0.1, b, "Bold", rf"{{\an5\pos(960,700)\fs110\fad(200,200)\1c{BRANCO}}}→")
    T.e(2, t_dir, b, "Bold", rf"{{\an4\pos(1040,700)\fs150\fscx118\fscy118\blur10\alpha&HFF&"
                             r"\t(0,240,\fscx100\fscy100\blur0\alpha&H00&)\fad(0,200)}" + dir)
    T.sfx.append((a, "whoosh"))
    T.sfx.append((t_dir, "tick"))


def citacao(T, a, b, serif, bold):
    T.e(2, a, b, "Serif", rf"{{\an5\move(960,790,960,770,0,400)\fs72\fad(350,300)}}{serif}")
    T.e(2, a + 0.6, b, "Bold", rf"{{\an5\pos(960,860)\fs{tamanho_bold(bold, 84)}\fad(300,300)}}{bold}")
    T.sfx.append((a, "chime"))


def proximo(T, a, b):
    T.e(1, a, b, "Label", r"{\an7\pos(110,100)\fad(300,300)\1c" + DESTAQUE + r"\bord0\shad0\p1}m 0 0 l 8 0 8 66 0 66{\p0}")
    T.e(2, a, b, "Label", r"{\an7\move(120,104,140,104,0,350)\fad(300,300)\1c" + DESTAQUE + r"\fs56\b1\fsp6}PRÓXIMO EPISÓDIO")
    T.sfx.append((a, "chime"))


# ------------------------------------------------------------------ motion graphics (explicam a fala)
def ret(w, h, r):
    """retângulo de cantos arredondados (desenho ASS, origem no canto superior esquerdo)"""
    k = r * 0.45
    return (f"m {r} 0 l {w - r} 0 b {w - k} 0 {w} {k} {w} {r} l {w} {h - r} b {w} {h - k} {w - k} {h} {w - r} {h} "
            f"l {r} {h} b {k} {h} 0 {h - k} 0 {h - r} l 0 {r} b 0 {k} {k} 0 {r} 0")


ICONES = {
    # play (vídeo curto), microfone (podcast), linhas (texto), três pessoas (comunidade)
    "video": "m 22 14 l 52 32 l 22 50",
    "podcast": "m 26 10 b 26 2 46 2 46 10 l 46 32 b 46 40 26 40 26 32 l 26 10 m 18 30 l 22 30 b 22 44 50 44 50 30 l 54 30 "
               "b 54 46 40 49 38 49 l 38 56 l 34 56 l 34 49 b 32 49 18 46 18 30",
    "texto": "m 14 16 l 58 16 l 58 21 l 14 21 m 14 29 l 58 29 l 58 34 l 14 34 m 14 42 l 44 42 l 44 47 l 14 47",
    "comunidade": "m 36 14 b 42 14 42 26 36 26 b 30 26 30 14 36 14 m 26 46 b 26 32 46 32 46 46 "
                  "m 18 22 b 23 22 23 31 18 31 b 13 31 13 22 18 22 m 9 46 b 9 36 24 34 26 40 "
                  "m 54 22 b 59 22 59 31 54 31 b 49 31 49 22 54 22 m 63 46 b 63 36 48 34 46 40",
}


def formatos(T, a, b, itens, papeis=None):
    """cadeia de formatos (vídeo curto → podcast → texto → comunidade), à esquerda, entrando conforme a fala"""
    x0, y0, passo = 120, 300, 128
    for n, (t, icone, texto) in enumerate(itens):
        y = y0 + n * passo
        T.e(1, t, b, "Label", rf"{{\an7\pos({x0},{y})\fad(200,250)\1c{DESTAQUE}\bord0\shad0\alpha&H30&"
                              rf"\fscx80\fscy80\t(0,220,\fscx100\fscy100)\p1}}" + ret(72, 72, 16) + r"{\p0}")
        T.e(2, t, b, "Label", rf"{{\an7\pos({x0},{y})\fad(200,250)\1c&H202020&\bord0\shad0\p1}}" + ICONES[icone] + r"{\p0}")
        T.e(2, t + 0.05, b, "Lista", rf"{{\an4\move({x0 + 92},{y + 36},{x0 + 108},{y + 36},0,250)\fad(200,250)}}{texto}")
        if n:
            # linha amarela "descendo" até o próximo formato
            T.e(1, t - 0.25, b, "Label", rf"{{\an7\pos({x0 + 34},{y - passo + 78})\1c{DESTAQUE}\bord0\shad0\fscy0"
                                         rf"\t(0,250,\fscy100)\fad(0,250)\p1}}m 0 0 l 4 0 l 4 {passo - 84} l 0 {passo - 84}{{\p0}}")
        T.sfx.append((t, "tick"))
    for t, idx, texto in papeis or []:
        y = y0 + idx * passo + 36
        T.e(2, t, b, "Label", rf"{{\an4\move(560,{y},540,{y},0,250)\fad(200,250)\1c{DESTAQUE}\fs34\b1\fsp4}}← {texto}")
        T.sfx.append((t, "tick"))


def caixa_app(T, a, b, itens, virada):
    """tudo o que é 'novo caminho' cabe dentro do mesmo aplicativo -> a dependência continua"""
    x0, y0, w, h = 110, 250, 700, 590
    t_v = virada
    T.e(1, a, b, "Label", rf"{{\an7\pos({x0},{y0})\fad(250,300)\1a&HFF&\3c{BRANCO}\3a&H30&\bord3\shad0"
                          rf"\t({int((t_v - a) * 1000)},{int((t_v - a) * 1000) + 250},\3c{DESTAQUE}\3a&H00&\bord5)\p1}}"
                          + ret(w, h, 34) + r"{\p0}")
    # cabeçalho muda na virada
    T.e(2, a, t_v, "Label", rf"{{\an7\pos({x0 + 36},{y0 + 30})\fad(250,150)\1c{DESTAQUE}\fs32\b1\fsp5}}DENTRO DO APLICATIVO")
    T.e(2, t_v, b, "Bold", rf"{{\an7\pos({x0 + 36},{y0 + 20})\fs58\fscx112\fscy112\t(0,200,\fscx100\fscy100)\fad(0,300)"
                           rf"\1c{DESTAQUE}}}A DEPENDÊNCIA CONTINUA")
    for n, (t, texto) in enumerate(itens):
        col, lin = n % 2, n // 2
        x, y = x0 + 36 + col * 322, y0 + 110 + lin * 112
        T.e(1, t, b, "Label", rf"{{\an7\pos({x},{y})\fad(180,250)\1a&HFF&\3c{DESTAQUE}\3a&H20&\bord2.5\shad0\fscx85\fscy85"
                              rf"\t(0,200,\fscx100\fscy100)\p1}}" + ret(300, 84, 42) + r"{\p0}")
        T.e(2, t, b, "Lista", rf"{{\an5\pos({x + 150},{y + 42})\fs46\fad(180,250)}}{texto}")
        T.sfx.append((t, "tick"))
    T.sfx.append((t_v, "bloco"))


def tijolos(T, a, b, titulo_txt, itens):
    """a construção como tijolos: cada parte cai e encaixa sobre a anterior"""
    x0, base, w, h = 120, 830, 520, 104
    T.e(2, a, b, "Serif", rf"{{\an7\move(110,{base - len(itens) * (h + 14) - 112},130,{base - len(itens) * (h + 14) - 112},0,300)"
                          rf"\fad(250,250)\fs58}}{titulo_txt}")
    for n, (t, texto) in enumerate(itens):
        y = base - (n + 1) * (h + 14)
        T.e(1, t, b, "Label", rf"{{\an7\move({x0},{y - 140},{x0},{y},0,260)\fad(120,250)\1c{DESTAQUE}\bord0\shad0\p1}}"
                              + ret(w, h, 14) + r"{\p0}")
        T.e(2, t, b, "Lista", rf"{{\an5\move({x0 + w // 2},{y - 140 + h // 2},{x0 + w // 2},{y + h // 2},0,260)\fad(120,250)"
                              rf"\1c&H262626&\fs52\b1}}{texto}")
        T.sfx.append((t + 0.24, "bloco"))


def numero_br(v):
    return f"{int(v):,}".replace(",", ".")


def gerar(versao):
    dur = json.load(open(f"plano_{versao}.json"))["duracao"] + OFF
    mp = (lambda t: t + OFF) if versao in ("youtube", "youtube2") else para_ig
    T = Trilha()
    for tipo, frase, depois, fim, c in INS:
        s0, e0 = achar(frase, depois)
        a_y = s0 - 0.05
        if fim == "fim":
            b_y = PY[-1]["t"] + PY[-1]["fim"] - PY[-1]["ini"] - (0.0 if BASE == "youtube2" else 0.7)
        elif isinstance(fim, str):
            b_y = achar(fim, s0, apos=s0 + 0.1)[0] - 0.08
        else:
            b_y = a_y + fim
        # a checagem de trecho exclusivo usa o meio da palavra (a borda pode cair no trecho anterior)
        if mp((s0 + e0) / 2) is None:
            continue
        a = mp(s0 + 0.05) - 0.10
        b = mp(b_y)
        if b is None or b <= a:
            b = a + (b_y - a_y)
        b = min(b, dur - (0.05 if BASE == "youtube2" else 0.65))
        if tipo == "titulo":
            titulo(T, a, b, c["serif"], c["bold"], c.get("eco"), c.get("extra"), contador=c.get("contador"))
        elif tipo == "formatos":
            itens = [(mp(achar(f, d)[0] - 0.05), ic, txt) for f, d, ic, txt in c["itens"]]
            papeis = [(mp(achar(f, d)[0] - 0.05), i, txt) for f, d, i, txt in c.get("papeis", [])]
            formatos(T, a, b, itens, papeis)
        elif tipo == "app":
            itens = [(mp(achar(f, d)[0] - 0.05), txt) for f, d, txt in c["itens"]]
            caixa_app(T, a, b, itens, mp(achar(*c["virada"])[0] - 0.05))
        elif tipo == "tijolos":
            itens = [(mp(achar(f, d)[0] - 0.05), txt) for f, d, txt in c["itens"]]
            tijolos(T, a, b, c["titulo"], itens)
        elif tipo == "capitulo":
            capitulo(T, a, b, c["texto"])
        elif tipo in ("lista", "pesquisa"):
            itens = [(mp(achar(f, d)[0] - 0.05), txt) for f, d, txt in c["itens"]]
            itens = [(t if t is not None else a, txt) for t, txt in itens]
            lista(T, a, b, c["titulo"], itens, c.get("fonte"))
        elif tipo == "versus":
            versus(T, a, b, c["serif"], c["esq"], c["dir"], mp(achar(*c["dir_ancora"])[0] - 0.05))
        elif tipo == "citacao":
            citacao(T, a, b, c["serif"], c["bold"])
        elif tipo == "proximo":
            proximo(T, a, b)
        print(f"{versao[:2]} {tipo:9} {ts(a)} -> {ts(b)}  {c.get('bold') or c.get('texto') or c.get('titulo') or ''}")
    if versao == "youtube2" and os.path.exists("dinamica_youtube2.json"):
        from dinamica import sons
        T.sfx += [(t + OFF, tipo) for t, tipo in sons(json.load(open("dinamica_youtube2.json")))]
    open(f"insercoes_{versao}.ass", "w", encoding="utf-8").write(CAB + "\n".join(T.ev) + "\n")
    mixar(versao, T.sfx)


# ------------------------------------------------------------------ efeitos sonoros (mesmos do EP1)
def env(n, ataque, queda):
    t = np.arange(n) / SR
    return np.minimum(1, t / ataque) * np.exp(-t / queda)


def som(tipo, rng=np.random.default_rng(7)):
    if tipo == "whoosh":
        n = int(0.55 * SR)
        ruido = rng.standard_normal(n)
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
    if tipo in ("zoom_in", "zoom_out"):
        # whoosh curto e abafado; entrada sobe, saída desce (bem abaixo da voz)
        n = int(0.32 * SR)
        t = np.arange(n) / SR
        ruido = rng.standard_normal(n)
        sobe = tipo == "zoom_in"
        fc = (300 + 2600 * (t / t[-1]) ** 2) if sobe else (2600 - 2300 * (t / t[-1]) ** 0.5)
        y = np.zeros(n)
        lp = hp = 0.0
        for i in range(n):
            a_ = 1 - np.exp(-2 * np.pi * fc[i] / SR)
            lp += a_ * (ruido[i] - lp)
            hp += 0.03 * (lp - hp)
            y[i] = lp - hp
        y *= np.sin(np.pi * (t / t[-1]) ** (0.7 if sobe else 1.4)) ** 2
        return y / np.abs(y).max() * 10 ** ((-29 if sobe else -32) / 20)
    if tipo == "bloco":
        # "toc" grave de encaixe
        n = int(0.18 * SR)
        t = np.arange(n) / SR
        y = np.sin(2 * np.pi * 150 * t) * env(n, 0.001, 0.045) + 0.3 * rng.standard_normal(n) * env(n, 0.0005, 0.008)
        return y / np.abs(y).max() * 10 ** (-27 / 20)
    raise ValueError(tipo)


CACHE = {}


def mixar(versao, sfx):
    voz = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f"voz_{versao}.wav", "-f", "f32le", "-"],
                                       capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()
    if OFF:   # áudio da abertura da editora na frente
        ab = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", "inicio_editora.mp4", "-vn", "-f", "f32le",
                                           "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout,
                           np.float32).reshape(-1, 2)[:int(OFF * SR)]
        voz = np.concatenate([ab, voz])
    for t, tipo in sfx:
        if tipo not in CACHE:
            CACHE[tipo] = som(tipo).astype(np.float32)
        y = CACHE[tipo]
        i = int(t * SR)
        j = min(len(voz), i + len(y))
        voz[i:j] += y[: j - i, None]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_f32le", f"mix_{versao}.wav"], input=voz.tobytes(), check=True)
    print(f"{versao}: {len(sfx)} efeitos sonoros")


if __name__ == "__main__":
    for v in sys.argv[1:] or ["youtube", "instagram"]:
        gerar(v)
