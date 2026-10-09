"""Lista de edição do vídeo "sapato da Chanel pela metade" no formato curadoria (referência: projetos/referencias/curated-list).
Cada inserção é ancorada numa palavra da fala (transcricao.json do faster-whisper) e entra 0,15–0,35 s ANTES dela.
Rodar sempre na pasta de trabalho (/home/user/work/cur) com transcricao.json, assets/ e fonts/."""
import json
import os
import re
import unicodedata

FPS = 30
T_VINHETA = 5.6   # a vinheta DEEP da editora entra neste quadro: nada de legenda nem inserção antes dela
T_VAMOS = 4.85    # "Vamos de DEEP?" já está aplicado pela editora (animação dela): sem legenda minha de 4,85 s até a vinheta
PAL = [w for s in json.load(open("transcricao.json")) for w in s["words"]]
FIX = {"cruze": "Cruise", "2627": "26/27", "blasie": "Blazy", "mathieu": "Matthieu", "chanel": "Chanel", "deep": "DEEP",
       "jóia": "joia", "gênia": "gênia"}


def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if unicodedata.category(c) != "Mn"))


TOK = [norm(w["w"]) for w in PAL]


def achar(frase, perto=0.0):
    alvo = [norm(p) for p in frase.split()]
    occ = [i for i in range(len(PAL)) if TOK[i:i + len(alvo)] == alvo]
    if not occ:
        raise ValueError("frase não encontrada: " + frase)
    i = min(occ, key=lambda k: abs(PAL[k]["s"] - perto))
    return i, i + len(alvo) - 1


def quadro(t):
    return round(t * FPS) / FPS


def T(frase, perto, lead=0.2):
    """instante de entrada = início da frase falada menos a antecedência"""
    i, _ = achar(frase, perto)
    return quadro(PAL[i]["s"] - lead)


def FIM(frase, perto, folga=0.3):
    _, j = achar(frase, perto)
    return quadro(PAL[j]["e"] + folga)


A = "assets/"
# ----------------------------------------------------------------------------- tela cheia (foto com zoom lento ou vídeo de banco)
# (nome, tipo, arquivo, frase-âncora, perto, antecedência, duração, ponto do clipe/foco, rótulo)
FULL = [
    ("f_boutique", "foto", A + "c4.jpg", "comprar um chanel", 10.7, 0.15, 0.9, (0.80, 0.42), None),
    ("f_desfile", "foto", A + "c6.jpg", "da chanel", 32.4, 0.25, 1.7, (0.5, 0.45), "Chanel · desfile de arquivo"),
    ("f_passarela", "clip", A + "m1080_52270.mp4", "o desfile aconteceu", 45.0, 0.40, 1.4, (3.0, 0.5), None),
    ("f_biarritz", "foto", A + "c0.jpg", "biarritz que é", 47.1, 0.20, 1.5, (0.55, 0.5), None),
    ("f_ondas", "clip", A + "m1080_44482.mp4", "cidade de praia", 48.4, 0.0, 1.9, (4.0, 0.5), None),
    ("f_desk", "foto", A + "c3.jpg", "história da marca", 64.7, 0.25, 1.5, (0.30, 0.40), "Gabrielle Chanel, 1931"),
    ("f_liberdade", "clip", A + "m_1208.mp4", "liberdade da praia", 73.0, 0.25, 1.9, (2.0, 0.5), None),
    ("f_mulher_mar", "clip", A + "m_33021.mp4", "uma mulher saindo", 82.0, 0.25, 2.6, (3.0, 0.5), None),
    ("f_pe_nu", "clip", A + "m1080_2054.mp4", "o pé quase nu", 93.4, 0.25, 2.0, (2.0, 0.5), None),
    # imagens reais do desfile Cruise 26/27 (Biarritz) e da Margaret Qualley, achadas na web (WWD, Russh, Ara)
    ("f_look_cruise", "foto", A + "w_look_cruise.jpg", "chanel criada pelo", 32.4, 0.20, 1.6, (0.5, 0.5), "Chanel Cruise 26/27, Biarritz"),
    ("f_look_desfile", "foto", A + "w_look_desfile.jpg", "o desfile aconteceu", 45.0, 0.40, 1.5, (0.5, 0.5), None),
    ("f_close_pe", "foto", A + "w_close_pe.jpg", "o pé quase nu", 93.4, 0.25, 2.0, (0.55, 0.5), "Chanel Cruise 26/27"),
    ("f_close_pele", "foto", A + "w_close_pele.jpg", "a pele aparece de verdade", 167.8, 0.25, 1.8, (0.55, 0.5), "Chanel Cruise 26/27"),
    ("f_qualley", "foto", A + "w_qualley.jpg", "sapato em tapete vermelho", 213.9, 0.0, 1.4, (0.5, 0.5), "Margaret Qualley, em Londres"),
    ("f_qualley_pes", "foto", A + "w_qualley_pes.jpg", "em tapete vermelho", 214.6, -0.7, 1.1, (0.5, 0.5), None),
    ("f_lagerfeld", "foto", A + "k12.jpg", "lagerfeld e agora", 150.4, 0.25, 1.9, (0.55, 0.45), "Karl Lagerfeld"),
    ("f_tapete", "clip", A + "m_23333.mp4", "em tapete vermelho", 214.6, 0.30, 2.1, (6.0, 0.5), None),
    ("f_flashes", "clip", A + "m_50641.mp4", "parar para olhar", 265.9, 0.20, 1.6, (3.0, 0.5), None),
]
# ----------------------------------------------------------------------------- foto com moldura branca ao lado dela (polaroid)
# (nome, arquivo, frase, perto, antecedência, duração, lado, ângulo, rótulo, foco)
POLAROID = [
    ("p_gabrielle", A + "c2.jpg", "gabrielle chanel abriu", 52.9, 0.20, 2.5, "esq", -2.5, "Gabrielle Chanel", (0.5, 0.5)),
    ("p_1957", A + "c2.jpg", "gabrielle chanel lançou", 118.5, 0.20, 2.0, "esq", 2.5, "Gabrielle Chanel", (0.5, 0.5)),
]
# ----------------------------------------------------------------------------- cartões de texto (ASS): (nome, frase-início, perto, antecedência, fim, linhas)
# linha = (texto, estilo, y, tamanho, cor)  estilos: sans (Jost Light, caixa alta) | serif (Cormorant itálico) | numero
BR, AM = "&H00FFFFFF&", "&H00C1ECFB&"
CARTOES = [
    ("c_chanel", "um chanel pela metade", 11.0, -0.5, 13.55, [("CHANEL", "sans", 860, 150, BR), ("pela metade", "serif", 985, 108, AM)]),
    ("c_cruise", "coleção cruze", 29.9, 0.35, 32.15, [("CHANEL", "sans", 800, 64, BR), ("CRUISE", "sans", 905, 150, BR), ("26/27", "serif", 1025, 120, AM)]),
    ("c_blazy", "mathieu blasie", 34.5, 0.30, 37.9, [("MATTHIEU BLAZY", "sans", 860, 86, BR), ("diretor criativo da Chanel", "serif", 955, 70, AM)]),
    ("c_biarritz", "biarritz que é", 47.1, 0.13, 48.37, [("BIARRITZ", "sans", 0, 140, BR), ("França", "serif", 0, 92, AM)]),
    ("c_1915", "em 1915", 55.8, 0.25, 57.7, [("1915", "numero", 900, 300, BR), ("casa de costura", "serif", 1060, 88, AM)]),
    ("c_marca", "e segundo a explicação", 74.9, 0.15, 78.9, [("SEGUNDO A MARCA", "sans", 860, 72, BR), ("divulgado pela imprensa", "serif", 945, 74, AM)]),
    ("c_1957", "em 1957", 120.4, 0.15, 123.0, [("1957", "numero", 900, 300, BR), ("o clássico bege e preto", "serif", 1060, 82, AM)]),
    ("c_bege", "o bege ajudava", 127.0, 0.25, 131.3, [("BEGE", "sans", 840, 140, BR), ("alonga a perna", "serif", 950, 92, AM)]),
    ("c_ponta", "ponta preta", 132.2, 0.25, 139.3, [("PONTA PRETA", "sans", 840, 120, BR), ("pé menor, disfarça marcas", "serif", 945, 82, AM)]),
    ("c_antes", "assinatura da chanel", 145.9, 0.0, 150.2, [("DESDE 1957", "sans", 860, 90, BR), ("uma assinatura da Chanel", "serif", 950, 76, AM)]),
    ("c_agora", "agora com blasie", 151.7, -0.40, 155.2, [("AGORA", "sans", 840, 120, BR), ("Matthieu Blazy", "serif", 950, 92, AM)]),
    ("c_redes", "nas redes sociais", 192.2, 0.3, 194.5, [("NAS REDES", "sans", 860, 110, BR), ("a conversa pegou", "serif", 955, 84, AM)]),
    ("c_venda", "nenhuma confirmação", 225.5, 0.30, 231.7, [("SEM CONFIRMAÇÃO", "sans", 850, 88, BR), ("de venda ou lançamento", "serif", 940, 78, AM)]),
]
# balões de "o que diziam" (caixa branca, serifa itálica): (nome, frase, perto, antecedência, fim, texto, x, y)
BALOES = [
    ("b_sapato", "questionando se isso", 195.5, 0.20, 199.3, "ISSO É UM SAPATO?", 70, 790),
    ("b_chao", "no chão que é", 200.8, 0.35, 203.1, "E O CHÃO, QUE É SUJO?", 190, 880),
    ("b_joia", "olhar para o pé", 206.4, 0.35, 210.2, "O PÉ COMO JOIA", 330, 970),
]
# ----------------------------------------------------------------------------- destaques de legenda (estilos aprovados): (frase, tipo, partes, perto)
DESTAQUES = [
    ("vamos de deep", "rubik", [["VAMOS DE"], ["DEEP?"]], 5.0),
    ("tá faltando um pedaço dele", "rubik", [["TÁ FALTANDO"], ["UM PEDAÇO"]], 3.3),
    ("tão doida", "amatic", ["TÃO", "DOIDA"], 17.3),
    ("a história por trás desse sapato", "playfair", [[("a história", BR)], [("por trás desse", BR), ("sapato", "&H000BCEF1&")]], 23.4),
    ("quase parecesse uma jóia", "playfair", [[("quase parecesse", BR)], [("uma", BR), ("joia", "&H000BCEF1&")]], 87.6),
    ("uma gênia", "amatic", ["UMA GÊNIA"], 139.5),
    ("a pele aparece de verdade", "playfair", [[("a pele aparece", BR)], [("de verdade", "&H000BCEF1&")]], 167.8),
    ("onde é que a gente usa isso", "rubik", [["ONDE A GENTE"], ["USA ISSO?"]], 186.0),
    ("um dupe", "rubik", [["UM DUPE"]], 245.4),
    ("precisa ser esquisito", "amatic", ["PRECISA SER", "ESQUISITO?"], 253.1),
    ("continuar falando da chanel", "playfair", [[("continuar falando", BR)], [("da", BR), ("Chanel", "&H000BCEF1&")]], 271.5),
    ("me conta", "rubik", [["ME CONTA"]], 274.4),
    ("sairia assim na rua", "rubik", [["SAIRIA ASSIM"], ["NA RUA?"]], 284.8),
]
# ----------------------------------------------------------------------------- revisão da editora (revisao.json: {id: "apagar"})
REMOVER = set()
if os.path.exists("revisao.json"):
    REMOVER = {k for k, v in json.load(open("revisao.json")).items() if v == "apagar"}
DESTAQUES = [d for n, d in enumerate(DESTAQUES) if f"d{n}" not in REMOVER]
CHAVE = {"chanel", "deep", "sapato", "cruise", "biarritz", "gabrielle", "lagerfeld", "blazy", "dupe", "joia", "bege", "preta",
         "pele", "viralizar", "esquisito", "polêmico", "polemico", "desfile", "colecao", "coleção"}


def resolver():
    """tempos absolutos de tudo (para o relatório e para a mixagem de efeitos)"""
    ev = {"full": [], "pol": [], "cart": [], "bal": []}
    for nome, tipo, arq, fr, perto, lead, dur, par, rot in FULL:
        if nome in REMOVER:
            continue
        if not os.path.exists(arq) or os.path.getsize(arq) < 20000:
            continue
        t = T(fr, perto, lead)
        ev["full"].append(dict(nome=nome, tipo=tipo, arq=arq, t=t, dur=dur, fim=quadro(t + dur), par=par, rot=rot))
    for nome, arq, fr, perto, lead, dur, lado, ang, rot, foco in POLAROID:
        if nome in REMOVER:
            continue
        t = T(fr, perto, lead)
        ev["pol"].append(dict(nome=nome, arq=arq, t=t, dur=dur, fim=quadro(t + dur), lado=lado, ang=ang, rot=rot, foco=foco))
    for nome, fr, perto, lead, fim, linhas in CARTOES:
        if nome in REMOVER:
            continue
        t = T(fr, perto, lead)
        ev["cart"].append(dict(nome=nome, t=t, fim=min(fim, quadro(t + 3.0)), linhas=linhas))
    for nome, fr, perto, lead, fim, txt, x, y in BALOES:
        if nome in REMOVER:
            continue
        t = T(fr, perto, lead)
        ev["bal"].append(dict(nome=nome, t=t, fim=fim, txt=txt, x=x, y=y))
    return ev


if __name__ == "__main__":
    ev = resolver()
    for k, v in ev.items():
        for e in v:
            print(f"{k:5s} {e['nome']:14s} {e['t']:7.2f} -> {e.get('fim', 0):7.2f}")
    for fr, tipo, partes, perto in DESTAQUES:
        i, j = achar(fr, perto)
        print(f"dest  {tipo:9s} {PAL[i]['s']:7.2f} -> {PAL[j]['e']:7.2f}  {fr}")
    # conflitos: destaque x cartão/balão
    iv = [(e["t"], e["fim"], e["nome"]) for k in ("cart", "bal") for e in ev[k]]
    for fr, tipo, partes, perto in DESTAQUES:
        i, j = achar(fr, perto)
        a, b = PAL[i]["s"] - 0.1, PAL[j]["e"] + 0.5
        for ta, tb, n in iv:
            if ta < b and a < tb:
                print("CONFLITO destaque", fr, "x", n)
