"""Efeitos sonoros sintetizados no estilo da referência Curated List (medido): golpe grave + whoosh curto no quadro em que a imagem
entra, clique de obturador nas rajadas, estalo de foto/papel nas polaroids, tick suave nos cartões. Níveis em dBFS no áudio já
normalizado (voz em −14 LUFS). Mais os sons dos destaques (pop / sininho / tecla) já aprovados (sfx_deep.py)."""
import json
import subprocess
import sys

import numpy as np

sys.path.insert(0, "/home/user/claude/projetos/deep-ep2/reels")
import sfx_deep as D  # noqa: E402

SR = 48000
rng = np.random.default_rng(11)
NIVEL = {"impacto": -13.0, "cartao": -21.0, "balao": -19.0, "foto": -16.0, "clique": -17.0}   # pico de cada efeito


def banda(x, f0, f1):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < f0) | (f > f1)] = 0
    return np.fft.irfft(X, len(x))


def pico(y, db):
    return y / (np.abs(y).max() + 1e-9) * 10 ** (db / 20)


def impacto(v=None):
    """whoosh que sobe (0,28 s) + golpe grave exatamente no instante da entrada + ar que escapa (0,4 s). Retorna (som, offset do golpe)."""
    pre, pos = 0.28, 0.55
    n = int((pre + pos) * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    # whoosh de entrada: ruído com banda subindo
    m = int(pre * SR)
    ruido = rng.standard_normal(m)
    sw = np.zeros(m)
    for k, (f0, f1) in enumerate(((300, 1500), (800, 4000), (1800, 8000))):
        sw += banda(ruido, f0, f1) * np.clip((np.arange(m) / m - k * 0.25) * 2, 0, 1)
    y[:m] += sw / (np.abs(sw).max() + 1e-9) * (np.arange(m) / m) ** 1.6 * 0.55
    # golpe grave + corpo + clique
    i0 = m
    tt = np.arange(n - i0) / SR
    f = 52 + 38 * np.exp(-tt * 28)
    thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.11)
    corpo = np.sin(2 * np.pi * 118 * tt) * np.exp(-tt / 0.05) * 0.5
    clique = banda(rng.standard_normal(n - i0), 1500, 7000) * np.exp(-tt / 0.006) * 0.8
    y[i0:] += thump + corpo + clique
    # ar: brilho que cai (2–14 kHz)
    ar = banda(rng.standard_normal(n - i0), 2500, 14000) * np.exp(-tt / 0.16) * 0.38
    y[i0:] += ar
    return pico(y, NIVEL["impacto"]), pre


def cartao(v=None):
    n = int(0.32 * SR)
    t = np.arange(n) / SR
    ar = banda(rng.standard_normal(n), 1800, 9000) * np.sin(np.pi * np.minimum(t / 0.3, 1)) ** 1.5
    tick = np.sin(2 * np.pi * 1700 * t) * np.exp(-t / 0.012)
    return pico(ar * 0.6 + tick * 0.5, NIVEL["cartao"]), 0.0


def balao(v=None):
    return pico(D.pop(2), NIVEL["balao"]), 0.0


def foto(v=None):
    """estalo de foto/papel batendo: golpe seco curto + ruído médio-agudo"""
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    papel = banda(rng.standard_normal(n), 900, 6500) * np.exp(-t / 0.035)
    baque = np.sin(2 * np.pi * 135 * t) * np.exp(-t / 0.05)
    click = banda(rng.standard_normal(n), 2500, 9000) * np.exp(-t / 0.004)
    return pico(papel * 0.8 + baque * 0.9 + click * 0.6, NIVEL["foto"]), 0.0


def clique(v=None):
    """obturador de câmera: dois estalos mecânicos próximos"""
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    y = banda(rng.standard_normal(n), 1800, 8000) * np.exp(-t / 0.006)
    t2 = np.clip(t - 0.055, 0, None)
    y += 0.7 * banda(rng.standard_normal(n), 900, 5000) * np.exp(-t2 / 0.009) * (t >= 0.055)
    y += 0.5 * np.sin(2 * np.pi * 220 * t) * np.exp(-t / 0.02)
    return pico(y, NIVEL["clique"]), 0.0


SONS = {"impacto": impacto, "cartao": cartao, "balao": balao, "foto": foto, "clique": clique}


def ler(arq, *extra):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", arq, *extra, "-vn", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32).reshape(-1, 2).copy()


def loudnorm(entrada, saida, filtro, alvo):
    import re
    med = subprocess.run(["ffmpeg", "-hide_banner", "-i", entrada, "-af", filtro + f"loudnorm=I={alvo}:TP=-1.5:LRA=9:print_format=json",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", med, re.S).group(0))
    ln = (f"loudnorm=I={alvo}:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
          f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", entrada, "-af", filtro + ln, "-ar", str(SR), "-c:a", "pcm_f32le", saida], check=True)


def montar(video="original.mp4", saida="audio_final.wav"):
    voz = ler(video)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_f32le", "voz_bruta.wav"],
                   input=voz.tobytes(), check=True)
    loudnorm("voz_bruta.wav", "voz_norm.wav", "highpass=f=70,acompressor=threshold=-22dB:ratio=2:attack=10:release=150:makeup=1,", -14)
    mix = ler("voz_norm.wav")[:len(voz)]
    eventos = []
    for t, tipo, v in json.load(open("sfx.json")):
        if tipo == "clique" and isinstance(v, str):             # f_flashes: rajada de obturadores durante o clipe (a cada ~0,33 s)
            eventos += [(t + 0.33 * k, "clique", k) for k in range(5)]
        else:
            eventos.append((t, tipo, v))
    n = 0
    for t, tipo, v in eventos:
        if tipo in SONS:
            y, off = SONS[tipo](v)
        else:                                                   # pop / brilho / tecla dos destaques
            y, off = D.SONS[tipo](v if isinstance(v, int) else 0), 0.0
        i = int((t - off) * SR)
        if i < 0:
            y = y[-i:]
            i = 0
        j = min(len(mix), i + len(y))
        mix[i:j] += y[:j - i, None].astype(np.float32)
        n += 1
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", "alimiter=limit=0.84:level=disabled",
                    "-c:a", "pcm_s16le", saida], input=mix.astype(np.float32).tobytes(), check=True)
    print(n, "efeitos mixados ->", saida)


if __name__ == "__main__":
    montar()
