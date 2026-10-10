"""Casa o áudio gravado (locução da Samara por cima das imagens de apoio) com o áudio da câmera, sem tocar no resto.
Entrada: original.mp4 da editora (em /home/user/work/ep). Saída: voz_tratada.wav (estéreo 48 kHz, float) + relatório.
 1) EQ de correspondência: espectro médio (só quadros com fala) dos trechos da câmera − espectro dos trechos gravados,
    suavizado em 1/3 de oitava e limitado a −8/+6 dB, aplicado só nos trechos gravados (FIR de fase linear).
 2) Ambiente: o gravado é "seco" (piso de ruído ~9 dB abaixo da câmera) → soma ruído com o espectro do piso da câmera,
    só nos trechos gravados, para o corte não "afundar" o ambiente.
 3) Emendas: crossfade de 60 ms (potência constante) entre o original e o tratado, sempre dentro de pausas da fala."""
import json
import os
import subprocess
import sys

import numpy as np
from scipy.signal import firwin2, fftconvolve

W = "/home/user/work/ep"
SR = 48000
# trechos que a editora indicou como áudio gravado (limites refinados nas pausas da fala, ±0,1 s dos tempos dela)
GRAVADO = [(14.36, 19.43), (23.65, 41.80), (47.72, 51.22), (54.30, 72.84)]
# trechos de áudio da câmera, fora dos efeitos da abertura (vinheta DEEP)
CAMERA = [(0.3, 5.0), (8.0, 13.2), (19.7, 23.4), (42.0, 47.2), (51.6, 54.1), (73.0, 81.2)]
N = 4096
FQ = np.fft.rfftfreq(N, 1 / SR)


def ler():
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{W}/original.mp4", "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32).reshape(-1, 2).copy()


def gravar(y, arq):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_f32le", arq],
                   input=y.astype(np.float32).tobytes(), check=True)


def quadros(x, regioes):
    out = []
    for s, e in regioes:
        seg = x[int(s * SR):int(e * SR)]
        for i in range(0, len(seg) - N, N // 2):
            out.append(seg[i:i + N] * np.hanning(N))
    return out


def rms_db(f):
    return 10 * np.log10((f ** 2).mean() / (np.hanning(N) ** 2).mean() + 1e-12)


def espectro_fala(x, regioes, limiar=-34.0):
    """potência média dos quadros com fala, normalizada pela faixa 400–1600 Hz (tira a diferença de nível)"""
    fr = [f for f in quadros(x, regioes) if rms_db(f) > limiar]
    p = np.mean([np.abs(np.fft.rfft(f)) ** 2 for f in fr], 0)
    ref = p[(FQ >= 400) & (FQ < 1600)].sum()
    return p / ref, len(fr)


def espectro_piso(x, regioes, frac=0.06):
    fr = quadros(x, regioes)
    lv = np.array([rms_db(f) for f in fr])
    idx = np.argsort(lv)[:max(4, int(len(fr) * frac))]
    p = np.mean([np.abs(np.fft.rfft(fr[i])) ** 2 for i in idx], 0)
    return p, float(lv[idx].mean())


def suave(g_db, oit=3):
    """suavização em 1/3 de oitava sobre o eixo de frequências"""
    out = g_db.copy()
    lf = np.log2(np.maximum(FQ, 1.0))
    for i, f in enumerate(FQ):
        if f < 20:
            continue
        m = np.abs(lf - lf[i]) <= 0.5 / oit
        out[i] = g_db[m].mean()
    return out


def curva_eq(mono):
    pc, nc = espectro_fala(mono, CAMERA)
    pg, ng = espectro_fala(mono, GRAVADO)
    dif = 10 * np.log10(pc + 1e-20) - 10 * np.log10(pg + 1e-20)
    dif = suave(dif)
    dif = np.clip(dif, -8.0, 8.0)
    dif[FQ < 70] = np.minimum(dif[FQ < 70], 0) - np.clip((70 - FQ[FQ < 70]) / 70 * 12, 0, 12)       # corta a base abaixo de 70 Hz
    alto = FQ > 11000
    dif[alto] *= np.clip((16000 - FQ[alto]) / 5000, 0, 1)                                               # não mexe no ar acima de 11 kHz
    return dif, (nc, ng)


def fir(g_db, taps=4097):
    f = np.concatenate([[0], FQ[1:]]) / (SR / 2)
    return firwin2(taps, np.clip(f, 0, 1), 10 ** (g_db / 20), fs=2)


def main():
    st = ler()
    mono = st.mean(1)
    g, (nc, ng) = curva_eq(mono)
    h = fir(g)
    print(f"quadros com fala: câmera {nc}, gravado {ng}")
    for f0 in (100, 200, 400, 800, 1600, 3200, 6400, 10000):
        print(f"  EQ {f0:5d} Hz: {g[np.argmin(np.abs(FQ - f0))]:+.1f} dB")

    # piso de ruído da câmera (modelo) e do gravado (medido)
    pc_piso, lc = espectro_piso(mono, CAMERA)
    pg_piso, lg = espectro_piso(mono, GRAVADO)
    print(f"piso de ruído (quadros mais quietos): câmera {lc:.1f} dB, gravado {lg:.1f} dB")

    eq = np.stack([fftconvolve(st[:, c], h, mode="same") for c in range(2)], 1).astype(np.float32)
    # ruído com o espectro do piso da câmera, canais independentes
    rng = np.random.default_rng(7)
    nz = np.zeros_like(st)
    mag = np.sqrt(pc_piso)
    mag = suave(20 * np.log10(mag + 1e-12))
    mag = 10 ** (mag / 20)
    L = 1 << 17
    for c in range(2):
        espec = np.zeros(L // 2 + 1, complex)
        fq = np.fft.rfftfreq(L, 1 / SR)
        espec[:] = np.interp(fq, FQ, mag) * np.exp(1j * rng.uniform(0, 2 * np.pi, L // 2 + 1))
        raw = np.fft.irfft(espec, L)
        raw = np.tile(raw, int(np.ceil(len(st) / L)))[:len(st)]
        nz[:, c] = raw
    alvo = lc + 0.0
    falta = max(10 ** (alvo / 10) - 10 ** (lg / 10), 0)
    ganho = np.sqrt(falta) / (np.sqrt((nz ** 2).mean() / (np.hanning(N) ** 2).mean()) * np.sqrt(1.0))
    nz *= ganho * 1.0
    print(f"ruído somado: {20 * np.log10(np.sqrt((nz ** 2).mean()) + 1e-12):.1f} dB rms (média no vídeo todo)")

    t = np.arange(len(st)) / SR
    mascara = np.zeros(len(st))
    rampa = 0.06
    for s, e in GRAVADO:
        mascara = np.maximum(mascara, np.clip(np.minimum((t - (s - rampa / 2)) / rampa, ((e + rampa / 2) - t) / rampa), 0, 1))
    m_eq = np.sin(mascara * np.pi / 2)[:, None]            # potência constante
    m_or = np.cos(mascara * np.pi / 2)[:, None]
    saida = st * m_or + (eq + nz * mascara[:, None] ** 1) * m_eq
    gravar(saida.astype(np.float32), f"{W}/voz_tratada.wav")

    # relatório depois
    mono2 = saida.mean(1)
    pc, _ = espectro_fala(mono, CAMERA)
    pg0, _ = espectro_fala(mono, GRAVADO)
    pg1, _ = espectro_fala(mono2, GRAVADO)
    bandas = [(80, 160), (160, 320), (320, 640), (640, 1250), (1250, 2500), (2500, 5000), (5000, 10000)]
    def b(p):
        return [10 * np.log10(p[(FQ >= lo) & (FQ < hi)].sum() + 1e-20) for lo, hi in bandas]
    print("faixas Hz        ", " ".join(f"{lo:>5d}" for lo, _ in bandas))
    print("câmera (alvo)    ", " ".join(f"{v:+5.1f}" for v in b(pc)))
    print("gravado antes    ", " ".join(f"{v:+5.1f}" for v in b(pg0)))
    print("gravado depois   ", " ".join(f"{v:+5.1f}" for v in b(pg1)))
    _, l2 = espectro_piso(mono2, GRAVADO)
    print(f"piso do gravado depois: {l2:.1f} dB (câmera {lc:.1f})")
    json.dump({"gravado": GRAVADO, "camera": CAMERA}, open(f"{W}/trechos_audio.json", "w"))


if __name__ == "__main__":
    main()
