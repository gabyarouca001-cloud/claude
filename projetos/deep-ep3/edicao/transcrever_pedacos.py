"""Transcreve o bruto em PEDAÇOS curtos cortados nas pausas (o Whisper em janela longa 'limpa' gaguejos e funde takes:
no EP3 escondeu 'Ah, minha voz falhou').  Uso: python3 transcrever_pedacos.py ini fim saida.json"""
import json
import os
import sys
import wave

import numpy as np
from faster_whisper import WhisperModel

SR = 16000
P = os.environ.get("PROMPT", "Hum, é, tipo, assim, né, eh, ah. Ah, minha voz falhou. Peraí, de novo. Errei. Desce um pouco, Gabi. Vai. Volta.")
w = wave.open(os.environ.get("WAV", "/home/user/work/ep3/voz_16k.wav"))
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
ini, fim = float(sys.argv[1]), float(sys.argv[2])
e = 20 * np.log10(np.sqrt((x[:len(x) // 160 * 160].reshape(-1, 160) ** 2).mean(1)) + 1e-9)
sil = e < -43
a0, a1 = int(ini * 100), min(int(fim * 100), len(e) - 1)
cortes, k = [a0], a0
while k < a1:
    if sil[k]:
        j = k
        while j < a1 and sil[j]:
            j += 1
        if j - k >= 15 and k - cortes[-1] >= 60:       # pausa >= 0,15 s e pedaço >= 0,6 s
            cortes.append((k + j) // 2)
        k = j
    else:
        k += 1
cortes.append(a1)
# pedaços longos (> 6 s) são divididos no ponto de menor energia
final = []
for a, b in zip(cortes[:-1], cortes[1:]):
    if b - a > 600:
        m = a + 200 + int(np.argmin(e[a + 200:b - 200]))
        final += [(a, m), (m, b)]
    else:
        final.append((a, b))
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
saida = []
for a, b in final:
    segs, _ = m.transcribe(x[a * 160:b * 160], language="pt", word_timestamps=True, beam_size=5,
                           condition_on_previous_text=False, initial_prompt=P)
    txt = " ".join(s.text.strip() for s in segs).strip()
    saida.append(dict(ini=a / 100, fim=b / 100, texto=txt))
    print(f"{a / 100:7.2f}-{b / 100:7.2f} {txt}", flush=True)
json.dump(saida, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
