"""Valida as emendas do edl.json: acusa corte com fala passando por cima (palavra mochada) — energia alta
nos 50 ms antes do fim ou depois do início de cada pedaço.  Uso: python3 validar_cortes.py"""
import json
import wave

import numpy as np

w = wave.open("/home/user/work/ep3/voz_16k.wav")
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
db = 20 * np.log10(np.sqrt((x[:len(x) // 160 * 160].reshape(-1, 160) ** 2).mean(1)) + 1e-9)
edl = json.load(open("edl.json"))["edl"]
LIM = -38.0
n = 0
for k, e in enumerate(edl[1:], 1):
    ini, fim = e["ini"], e["fim"]
    a = db[int(ini * 100):int(ini * 100) + 2]          # primeiros 20 ms
    b = db[int(fim * 100) - 2:int(fim * 100)]          # últimos 20 ms
    if len(b) and k < len(edl) - 1 and b.max() > LIM:
        print(f"FIM em fala  orig {fim:7.2f}  (máx {b.max():.0f} dB)  trecho {ini:.2f}-{fim:.2f}"); n += 1
    if len(a) and a.max() > LIM and e["junta"] == "pausa":
        print(f"INÍCIO em fala orig {ini:7.2f}  (máx {a.max():.0f} dB)"); n += 1
print(n, "emendas suspeitas de", len(edl) - 1)
