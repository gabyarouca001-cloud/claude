"""Acha o ponto exato de cada trecho da EDL: retranscreve a janela do trecho, localiza as primeiras/últimas
palavras esperadas e corta em vale de energia sem invadir a palavra vizinha. Saída: trechos.json"""
import difflib
import json
import re
import unicodedata

import numpy as np
from faster_whisper import WhisperModel

from edl import EDL

SR = 16000
FPS = 30
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
AUDIO = {}


def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if unicodedata.category(c) != "Mn"))


def audio(fonte):
    if fonte not in AUDIO:
        AUDIO[fonte] = np.fromfile(f"{fonte}_16k.wav", np.int16)[22:].astype(np.float32) / 32768
    return AUDIO[fonte]


def db(x, a, b):
    q = x[int(a * SR):int(b * SR)]
    return 20 * np.log10(np.sqrt((q ** 2).mean()) + 1e-9) if len(q) else -120


def vale(x, a, b, passo=0.01):
    """instante de menor energia entre a e b"""
    ts = np.arange(a, max(a + passo, b), passo)
    return float(min(ts, key=lambda t: db(x, t - 0.015, t + 0.015)))


SIL = -42.0


def silencio(x, t, run=0.15):
    """True se há >= run s de silêncio começando em t"""
    return db(x, t, t + run) < SIL and max(db(x, t + k * 0.03, t + k * 0.03 + 0.03) for k in range(int(run / 0.03))) < SIL + 4


def ataque(x, t):
    """início real da fala perto de t (pela energia): volta até achar silêncio, ou avança até achar voz"""
    if db(x, t - 0.015, t + 0.015) > SIL:
        for k in range(130):
            u = t - k * 0.01
            if silencio(x, u - 0.15):
                return u
        return t - 1.3
    for k in range(50):
        u = t + k * 0.01
        if db(x, u - 0.015, u + 0.015) > SIL:
            return u
    return t


def soltura(x, t):
    """fim real da fala perto de t: avança até achar silêncio, ou volta até achar voz"""
    if db(x, t - 0.015, t + 0.015) > SIL:
        for k in range(130):
            u = t + k * 0.01
            if silencio(x, u):
                return u
        return t + 1.3
    for k in range(50):
        u = t - k * 0.01
        if db(x, u - 0.015, u + 0.015) > SIL:
            return u
    return t


def melhor(tokens, alvo, dica, tempos, de_tras=False):
    k = len(alvo)
    cands = []
    for i in range(0, max(1, len(tokens) - k + 1)):
        s = difflib.SequenceMatcher(None, tokens[i:i + k], alvo).ratio()
        t = tempos[i + k - 1][1] if de_tras else tempos[i][0]
        cands.append((round(s, 2), -abs(t - dica), i))
    s, _, i = max(cands)
    return i, s


def snap(t):
    return round(t * FPS) / FPS


import os, sys
SO = [int(v) for v in sys.argv[1:]]
saida = json.load(open("trechos.json")) if SO and os.path.exists("trechos.json") else []
for n, (fonte, a, b, prim, ult, yt) in enumerate(EDL):
    if SO and n not in SO:
        continue
    x = audio(fonte)
    j0, j1 = max(0, a - 1.2), b + 1.2
    segs, _ = m.transcribe(x[int(j0 * SR):int(j1 * SR)], language="pt", word_timestamps=True,
                           vad_filter=False, beam_size=5, condition_on_previous_text=False)
    ws = [(j0 + w.start, j0 + w.end, w.word.strip()) for s in segs for w in s.words]
    toks = [norm(w[2]) for w in ws]
    tempos = [(w[0], w[1]) for w in ws]
    i0, s0 = melhor(toks, [norm(p) for p in prim.split()], a, tempos)
    alvo_u = [norm(p) for p in ult.split()]
    i1, s1 = melhor(toks[i0:], alvo_u, b, tempos[i0:], de_tras=True)
    i1 = i0 + i1 + len(alvo_u) - 1
    w_ini, w_fim = ws[i0][0], ws[i1][1]
    ant = ws[i0 - 1][1] if i0 > 0 else j0
    prox = ws[i1 + 1][0] if i1 + 1 < len(ws) else j1
    # corte pela energia (os tempos de palavra do whisper às vezes atrasam/adiantam o começo)
    ini = ataque(x, w_ini + 0.03) - 0.04
    fim = soltura(x, w_fim - 0.03) + 0.04
    texto = " ".join(w[2] for w in ws[i0:i1 + 1])
    aviso = "  <<< CONFERIR" if min(s0, s1) < 0.75 else ""
    print(f"{n:02d} {fonte:11s} {ini:7.2f}-{fim:7.2f} [{s0:.2f}/{s1:.2f}] {'YT ' if yt else ''}{texto}{aviso}", flush=True)
    item = dict(n=n, fonte=fonte, ini=snap(ini), fim=snap(fim), yt=yt, texto=texto, conf=min(s0, s1))
    if SO:
        saida[n] = item
    else:
        saida.append(item)
json.dump(saida, open("trechos.json", "w"), ensure_ascii=False, indent=1)
