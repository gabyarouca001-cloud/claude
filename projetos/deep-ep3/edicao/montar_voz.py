"""Monta só a voz (16 kHz) a partir do edl.json — usada para checar erros de fala antes de renderizar."""
import json, wave, numpy as np
SR = 16000
w = wave.open("/home/user/work/ep3/voz_16k.wav")
x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
edl = json.load(open("edl.json"))["edl"]
out, mapa, t = [], [], 0.0
for e in edl:
    a, b = int(round(e["ini"] * SR)), int(round(e["fim"] * SR))
    out.append(x[a:b]); mapa.append((round(t, 3), e["ini"], e["fim"])); t += (b - a) / SR
y = np.concatenate(out)
o = wave.open("/home/user/work/ep3/voz_montada.wav", "wb"); o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR); o.writeframes(y.tobytes()); o.close()
json.dump(mapa, open("/home/user/work/ep3/mapa_saida.json", "w"))
print("voz montada:", round(len(y) / SR, 1), "s")
