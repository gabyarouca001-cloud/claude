"""Plano de montagem do EP2 (YouTube e Instagram): junta trechos contíguos, tira pausas >= 0,30 s,
alterna punch-in de 12% a cada corte de retake e marca onde entra a vinheta."""
import json

import numpy as np

SR = 16000
FPS = 30
SIL_DB, SIL_MIN = -42.0, 0.30
MANTER_ANTES, MANTER_DEPOIS = 0.10, 0.08   # mantém após a palavra anterior / antes da próxima
BORDA_INI, BORDA_FIM = 0.08, 0.14          # respiro nas bordas de cada trecho
VINHETA_APOS = 2                            # índice do trecho "Vamos, DEEP?"
VINHETA_DUR = 1.56

# ajustes manuais conferidos pela energia/retranscrição (n do trecho: início, fim)
AJUSTES = {
    28: (208.45, None),   # não cortar o "O" de "O que eu quero desenvolver"
    48: (81.00, None),    # tirar o "Cacilda" antes de "Para mim, é aí que construir"
    53: (138.15, None),   # (antes cortava o começo do "Então")
    58: (None, 227.93),   # termina em "mais complexa", sem o "tá"   # tirar "uma responsabilidade também" antes de "Então, lembra do nome"
}

# Reels v3: trechos tirados para encurtar (fonte, início, fim no tempo do take), em vales de energia
EXCLUIR_REELS = [
    ("take1", 101.13, 106.98),   # "até por conta do que eu consumo, do tipo de conteúdo que eu consumo"
    ("take1", 226.80, 265.92),   # "e isso ajuda a explicar essa busca por outros lugares"
    ("take2", 175.38, 230.66),   # "Essa pergunta começou a ganhar... procurar o meu conteúdo?"
    ("take3", 108.05, 138.48),   # "Olha, eu ainda tô construindo isso... compromisso com a próxima edição"
]
# erros de fala que a editora cortou na versão final do Reels (falsos começos, repetições, sobras),
# mapeados para o tempo dos takes; valem para todas as versões
EXCLUIR_ERROS = [
    ("take1", 93.166, 93.267), ("take1", 93.6, 94.467),        # "E aí, e foi aí"
    ("take2", 119.035, 119.167), ("take2", 124.6, 125.703),    # "acompanha, pras pessoas, e o motivo"
    ("take2", 159.8, 160.267), ("take2", 163.333, 166.033),    # "e co… e fazer parte de uma carreira"
    ("take2", 166.4, 166.5),
    ("take2", 231.969, 233.467), ("take2", 238.6, 238.636),    # "existem mais, existem mais"
    ("take2", 284.869, 285.167), ("take2", 293.367, 293.403),  # "nos, nos formatos"
    ("take3", 237.236, 238.403),                               # "mais facil… mais facilidade"
    ("take3", 254.066, 254.133), ("take3", 261.933, 263.333),  # "conseguir decidir, conseguir decidir"
]
TCHAU_EXTRA = 1.1                # deixa o "Tchau!" terminar (sem fade no fim)

AUD = {}


def audio(f):
    if f not in AUD:
        AUD[f] = np.fromfile(f"{f}_16k.wav", np.int16)[22:].astype(np.float32) / 32768
    return AUD[f]


def env(x, a, b, passo=0.01):
    n = int(SR * passo)
    q = x[int(a * SR):int(a * SR) + int((b - a) / passo) * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt((q ** 2).mean(1)) + 1e-9)


def snap(t):
    return round(t * FPS) / FPS


def blocos(trechos):
    """junta trechos vizinhos da mesma fonte que se sobrepõem/encostam"""
    out = []
    for t in trechos:
        if out and out[-1]["fonte"] == t["fonte"] and t["ini"] <= out[-1]["fim"] + 0.25 \
                and out[-1]["yt"] == t["yt"] and out[-1]["n"] != VINHETA_APOS:
            out[-1]["fim"] = max(out[-1]["fim"], t["fim"])
            out[-1]["texto"] += " " + t["texto"]
            out[-1]["ns"].append(t["n"])
        else:
            out.append(dict(t, ns=[t["n"]]))
    return out


def falas(b):
    """divide o bloco em falas, tirando silêncio no começo, no fim e pausas internas longas"""
    x = audio(b["fonte"])
    e = env(x, b["ini"], b["fim"])
    voz = e > SIL_DB
    idx = np.flatnonzero(voz)
    if not len(idx):
        return []
    on, off = idx[0], idx[-1] + 1
    partes, k, ini = [], on, on
    while k < off:
        if not voz[k]:
            j = k
            while j < off and not voz[j]:
                j += 1
            if (j - k) * 0.01 >= SIL_MIN:
                partes.append((ini, k))
                ini = j
            k = j
        else:
            k += 1
    partes.append((ini, off))
    res = []
    for n, (p0, p1) in enumerate(partes):
        a = b["ini"] + p0 * 0.01 - (BORDA_INI if n == 0 else MANTER_DEPOIS)
        z = b["ini"] + p1 * 0.01 + (BORDA_FIM if n == len(partes) - 1 else MANTER_ANTES)
        res.append((snap(max(b["ini"], a)), snap(min(b["fim"] + 0.1, z))))
    return res


def plano(versao):
    tre = json.load(open("trechos.json"))
    for t in tre:
        a, b = AJUSTES.get(t["n"], (None, None))
        t["ini"] = a if a is not None else t["ini"]
        t["fim"] = b if b is not None else t["fim"]
    if versao in ("instagram", "reels"):
        tre = [t for t in tre if not t["yt"]]
    if versao in ("reels", "youtube2"):         # abertura + vinheta montadas pela editora
        tre = [t for t in tre if t["n"] > VINHETA_APOS]
    segs, zoom, t = [], 1.0, 0.0
    for b in blocos(tre):
        fs = falas(b)
        if segs:
            zoom = 1.12 if zoom == 1.0 else 1.0      # corte de retake: alterna o enquadramento
        fs = [(a, z) for a, z in fs if z - a >= 0.2]   # descarta fragmentos (cliques/respiros soltos)
        for i, (a, z) in enumerate(fs):
            segs.append(dict(fonte=b["fonte"], ini=a, fim=z, zoom=zoom, t=round(t, 3), ns=b["ns"], yt=b["yt"]))
            t += z - a
        if VINHETA_APOS in b["ns"]:
            segs.append(dict(fonte="vinheta", ini=0, fim=VINHETA_DUR, zoom=1.0, t=round(t, 3), ns=[], yt=False))
            t += VINHETA_DUR
            zoom = 1.12                                # depois da vinheta volta no plano normal
    # último trecho sempre no plano normal
    for s in segs[::-1]:
        if s["fonte"] == "vinheta":
            break
        if s["ns"] != segs[-1]["ns"]:
            break
        s["zoom"] = 1.0
    if versao == "reels":
        segs, t = encurtar(segs, EXCLUIR_REELS)
    if versao == "youtube2":                    # YouTube completo (sem os encurtamentos do Reels)
        segs, t = encurtar(segs, EXCLUIR_ERROS)
    return segs, t


def encurtar(segs, excluir):
    """tira os trechos excluídos, alterna o punch-in a cada corte e alonga o tchau"""
    out = []
    for s in segs:
        pedacos = [(s["ini"], s["fim"])]
        cortou = False
        for f, a, b in excluir:
            if f != s["fonte"]:
                continue
            novos = []
            for x, y in pedacos:
                if b <= x or a >= y:
                    novos.append((x, y))
                    continue
                cortou = True
                if a - x >= 0.2:
                    novos.append((x, snap(a)))
                if y - b >= 0.2:
                    novos.append((snap(b), y))
            pedacos = novos
        for k, (x, y) in enumerate(pedacos):
            out.append(dict(s, ini=x, fim=y, corte=cortou and (k > 0 or x != s["ini"])))
        if cortou and out and (not pedacos or pedacos[-1][1] != s["fim"]):
            out[-1]["corte_depois"] = True
    # grupos: novo grupo a cada troca de trecho (retake) ou corte de encurtamento
    g, prev = 0, None
    for s in out:
        if prev is not None and (s["ns"] != prev["ns"] or s.get("corte") or prev.get("corte_depois")):
            g += 1
        s["g"] = g
        prev = s
    out[-1]["fim"] += TCHAU_EXTRA
    t = 0.0
    for s in out:
        s["zoom"] = 1.0 if (g - s["g"]) % 2 == 0 else 1.12
        s["t"] = round(t, 3)
        t += s["fim"] - s["ini"]
        for k in ("corte", "corte_depois", "g"):
            s.pop(k, None)
    return out, t


if __name__ == "__main__":
    for v in ("youtube", "instagram", "reels", "youtube2"):
        segs, total = plano(v)
        json.dump(dict(segmentos=segs, duracao=total), open(f"plano_{v}.json", "w"), indent=1)
        print(f"{v}: {len(segs)} segmentos, {total:.1f}s ({int(total // 60)}:{total % 60:04.1f})")
