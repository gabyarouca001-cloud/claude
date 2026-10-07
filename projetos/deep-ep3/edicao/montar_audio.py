"""Áudio da prévia (48 kHz estéreo, sem normalizar) a partir do edl.json, com fades de 8 ms nas emendas."""
import json
import wave

import numpy as np

W, SR = "/home/user/work/ep3", 48000
edl = json.load(open("edl.json"))["edl"]
w = wave.open(f"{W}/orig_48k.wav")
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32768
partes = []
for i, e in enumerate(edl):
    p = x[int(round(e["ini"] * SR)):int(round(e["fim"] * SR))].copy()
    f = int(0.008 * SR)
    if i > 0:
        p[:f] *= np.linspace(0, 1, f)[:, None]
    if i < len(edl) - 1:
        p[-f:] *= np.linspace(1, 0, f)[:, None]
    partes.append(p)
y = np.concatenate(partes)
o = wave.open(f"{W}/audio_montado.wav", "wb"); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR)
o.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()); o.close()
print("áudio montado:", round(len(y) / SR, 3), "s")
