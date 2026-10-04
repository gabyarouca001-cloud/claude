"""Efeitos sonoros dos destaques (sintetizados, discretos): pop nas palavras do Rubik Black, brilho nas do
Playfair, cliques de digitação nas letras do Amatic e um som de saída diferente para cada estilo."""
import json
import subprocess

import numpy as np

SR = 48000
rng = np.random.default_rng(3)


def env(n, ataque, queda):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(ataque, 1e-4)) * np.exp(-t / queda)


def norm(y, db):
    return y / (np.abs(y).max() + 1e-9) * 10 ** (db / 20)


def passa_banda(x, f0, f1):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < f0) | (f > f1)] = 0
    return np.fft.irfft(X, len(x))


def pop(v):
    """bolha suave: varredura descendente curta + clique, tom sobe a cada palavra"""
    n = int(0.11 * SR)
    t = np.arange(n) / SR
    f0 = 520 * 2 ** (min(v, 5) * 2 / 12)
    f = f0 * np.exp(-t * 18) + 140
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.035)
    return norm(y, -27)


def brilho(v):
    """sininho delicado: parciais agudas com brilho (shimmer)"""
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    base = [1318.5, 1568.0, 1760.0, 2093.0][v % 4]
    y = sum(a * np.sin(2 * np.pi * base * m * t) * env(n, 0.003, 0.28 / m) for m, a in ((1, 1), (2.01, .35), (3.02, .15)))
    y *= 1 + 0.15 * np.sin(2 * np.pi * 9 * t)
    return norm(y, -31)


def tecla(v):
    """clique de digitação/caneta: ruído curto filtrado, timbre varia por letra"""
    n = int(0.035 * SR)
    x = rng.standard_normal(n) * env(n, 0.0005, 0.006)
    y = passa_banda(x, 1800 + 300 * (v % 5), 6500)
    return norm(y, -33 - (v % 3))


def whoosh_reverso():
    """saída do Rubik: ar crescendo e cortando (whoosh ao contrário)"""
    n = int(0.32 * SR)
    t = np.arange(n) / SR
    x = passa_banda(rng.standard_normal(n), 500, 5000)
    y = x * (t / t[-1]) ** 2.2 * np.minimum(1, (t[-1] - t) / 0.02)
    return norm(y, -30)


def brilho_descendo():
    """saída do Playfair: arpejo agudo descendo, bem suave"""
    partes = []
    for k, f in enumerate((2093.0, 1760.0, 1318.5)):
        n = int(0.22 * SR)
        t = np.arange(n) / SR
        partes.append((k * 0.07, np.sin(2 * np.pi * f * t) * env(n, 0.002, 0.08)))
    y = np.zeros(int(0.5 * SR))
    for t0, p in partes:
        i = int(t0 * SR)
        y[i:i + len(p)] += p
    return norm(y, -32)


def papel():
    """saída do Amatic: 'swipe' curto de papel"""
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    x = passa_banda(rng.standard_normal(n), 2500, 9000)
    y = x * np.sin(np.pi * t / t[-1]) ** 1.5
    return norm(y, -32)


SONS = {"pop": pop, "brilho": brilho, "tecla": tecla}
SAIDA = {"saida_rubik": whoosh_reverso, "saida_playfair": brilho_descendo, "saida_amatic": papel}

if __name__ == "__main__":
    eventos = json.load(open("sfx.json"))
    audio = subprocess.run(["ffmpeg", "-v", "error", "-i", "editado.mp4", "-vn", "-ac", "2", "-ar", str(SR),
                            "-f", "f32le", "-"], capture_output=True, check=True).stdout
    mix = np.frombuffer(audio, np.float32).reshape(-1, 2).copy()
    for t, tipo, v in eventos:
        y = SONS[tipo](v) if tipo in SONS else SAIDA[tipo]()
        i = int(t * SR)
        j = min(len(mix), i + len(y))
        mix[i:j] += y[: j - i, None].astype(np.float32)
    pico = np.abs(mix).max()
    print(len(eventos), "efeitos; pico", round(20 * np.log10(pico), 2), "dBFS")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", "alimiter=limit=0.89:level=disabled", "-c:a", "pcm_s16le", "audio_com_sfx.wav"],
                   input=mix.tobytes(), check=True)
