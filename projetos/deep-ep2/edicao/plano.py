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
    53: (138.45, None),   # tirar "uma responsabilidade também" antes de "Então, lembra do nome"
}

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
    if versao == "instagram":
        tre = [t for t in tre if not t["yt"]]
    segs, zoom, t = [], 1.0, 0.0
    for b in blocos(tre):
        fs = falas(b)
        if segs:
            zoom = 1.12 if zoom == 1.0 else 1.0      # corte de retake: alterna o enquadramento
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
    return segs, t


if __name__ == "__main__":
    for v in ("youtube", "instagram"):
        segs, total = plano(v)
        json.dump(dict(segmentos=segs, duracao=total), open(f"plano_{v}.json", "w"), indent=1)
        print(f"{v}: {len(segs)} segmentos, {total:.1f}s ({int(total // 60)}:{total % 60:04.1f})")
