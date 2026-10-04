"""Checagem de erros de fala na voz montada (lição do Reels EP2: o Whisper em janela longa 'limpa' gaguejos).
Divide a voz nas pausas em pedaços curtos (1,5–5 s), transcreve cada um isolado (sem contexto anterior) e aponta:
palavras/duplas repetidas em sequência, palavras truncadas e palavras de baixa confiança.
Uso: python3 checar_falas.py voz_16k.wav saida.json [ini fim]"""
import json
import re
import sys
import unicodedata

import numpy as np
from faster_whisper import WhisperModel

SR = 16000
P = "Hum, é, tipo, assim, né, eh, ah. Então, eu, eu... ela, ela tá. Nos, nos formatos. Mais facil... mais facilidade."
x = np.frombuffer(open(sys.argv[1], "rb").read()[44:], np.int16).astype(np.float32) / 32768
ini, fim = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0, len(x) / SR)
x = x[int(ini * SR):int(fim * SR)]
e = 20 * np.log10(np.sqrt((x[:len(x) // 160 * 160].reshape(-1, 160) ** 2).mean(1)) + 1e-9)   # 10 ms
limiar = np.percentile(e, 10) + 10          # adaptativo (voz normalizada / ruído de sala)
silencio = e < limiar
# pontos de corte: meio de pausas >= 0,12 s
pausas, k = [], 0
while k < len(e):
    if silencio[k]:
        j = k
        while j < len(e) and silencio[j]:
            j += 1
        if j - k >= 12:
            pausas.append((k + j) // 2)
        k = j
    else:
        k += 1
def dividir(a, b):
    """pedaços de no máximo 5 s, cortando no vale de energia"""
    if b - a <= 500:
        return [(a, b)]
    meio = a + 150 + int(np.argmin(e[a + 150:b - 150]))
    return dividir(a, meio) + dividir(meio, b)


pedacos, a = [], 0
for p in pausas + [len(e)]:
    if (p - a) >= 150 or p == len(e):
        pedacos += dividir(a, p)
        a = p
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
W = []
for a, b in pedacos:
    segs, _ = m.transcribe(x[a * 160:b * 160], language="pt", word_timestamps=True, vad_filter=False, beam_size=5,
                           condition_on_previous_text=False, initial_prompt=P)
    for s in segs:
        for w in s.words:
            W.append(dict(w=w.word.strip(), s=round(ini + a / 100 + w.start, 2), e=round(ini + a / 100 + w.end, 2),
                          p=round(w.probability, 2)))
json.dump(W, open(sys.argv[2], "w"), ensure_ascii=False)


def n(t):
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if unicodedata.category(c) != "Mn"))


def detectar(W):
    T = [n(w["w"]) for w in W]
    achados = []
    for i in range(len(W)):
        for k in (1, 2, 3):
            if i + 2 * k <= len(W) and T[i:i + k] == T[i + k:i + 2 * k] and all(T[i:i + k]) \
                    and W[i + k]["s"] - W[i]["s"] < 3 and not (k == 1 and T[i] in {"e", "que", "muito"}):
                achados.append((W[i]["s"], "REPETIÇÃO", i, 2 * k))
        if re.search(r"(\.\.\.|…)$", W[i]["w"]) and i + 1 < len(W) and T[i + 1][:2] == T[i][:2]:
            achados.append((W[i]["s"], "FALSO COMEÇO", i, 2))
        elif re.search(r"(\.\.\.|…|-)$", W[i]["w"]):
            achados.append((W[i]["s"], "TRUNCADA", i, 1))
    return achados


achados = detectar(W)
# 2ª etapa: confirma cada suspeita retranscrevendo uma janela centrada nela (as bordas dos pedaços geram falsos "...")
confirmados = []
for t, tipo, i, k in sorted(achados):
    if confirmados and t - confirmados[-1][0] < 1.0:
        continue
    a = max(0, t - ini - 1.5)
    segs, _ = m.transcribe(x[int(a * SR):int((t - ini + 2.5) * SR)], language="pt", word_timestamps=True,
                           vad_filter=False, beam_size=5, condition_on_previous_text=False, initial_prompt=P)
    J = [dict(w=w.word.strip(), s=round(ini + a + w.start, 2), e=round(ini + a + w.end, 2), p=w.probability)
         for s_ in segs for w in s_.words]
    J = J[:-1] if J and re.search(r"(\.\.\.|…)$", J[-1]["w"]) else J     # última palavra da janela pode estar cortada
    for t2, tipo2, i2, k2 in detectar(J):
        if abs(t2 - t) < 2.0 and i2 > 0:
            confirmados.append((t2, tipo2, " ".join(w["w"] for w in J)))
            break
for t, tipo, txt in confirmados:
    print(f"{int(t // 60)}:{t % 60:05.2f}  {tipo:12s} {txt}")
print(len(pedacos), "pedaços,", len(achados), "suspeitas,", len(confirmados), "confirmados")
json.dump([dict(t=t, tipo=tipo, texto=txt) for t, tipo, txt in confirmados], open(sys.argv[2].replace(".json", "_erros.json"), "w"),
          ensure_ascii=False, indent=1)
