"""Monta a voz de cada versão (48 kHz) a partir do plano, com fades curtos em cada corte."""
import json
import subprocess
import sys

import numpy as np

SR = 48000
FONTES = {"take1": "take1.mp4", "take2": "take2.mp4", "take3": "take3.mp4",
          "lado_inicio": "lado_inicio.mp4", "vinheta": "vinheta_ep1.mov"}
CACHE = {}


def ler(f):
    if f not in CACHE:
        b = subprocess.run(["ffmpeg", "-v", "error", "-i", FONTES[f], "-vn", "-ac", "2", "-ar", str(SR),
                            "-f", "f32le", "-"], capture_output=True, check=True).stdout
        CACHE[f] = np.frombuffer(b, np.float32).reshape(-1, 2)
    return CACHE[f]


def montar(versao):
    plano = json.load(open(f"plano_{versao}.json"))
    fade = int(SR * 0.006)
    r = np.linspace(0, 1, fade, dtype=np.float32)[:, None]
    partes = []
    for s in plano["segmentos"]:
        x = ler(s["fonte"])
        p = x[int(s["ini"] * SR):int(s["ini"] * SR) + int(round((s["fim"] - s["ini"]) * SR))].copy()
        n = int(round((s["fim"] - s["ini"]) * SR))
        if len(p) < n:
            p = np.vstack([p, np.zeros((n - len(p), 2), np.float32)])
        if s["fonte"] != "vinheta":
            p[:fade] *= r
            p[-fade:] *= r[::-1]
        partes.append(p)
    y = np.concatenate(partes)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_f32le", f"voz_{versao}.wav"], input=y.tobytes(), check=True)
    print(versao, len(y) / SR)


if __name__ == "__main__":
    for v in sys.argv[1:] or ["youtube", "instagram"]:
        montar(v)
