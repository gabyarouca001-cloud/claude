"""Trilha (Mixkit 34 "Raising Me Higher", 112 BPM) + envelope de volume: −22 dB sob a voz, até −6 dB nas pausas (subida/descida rápidas),
−6 dB nos 4 s de abertura e de encerramento. A voz não é tocada (mesmo arquivo, só deslocada em OFF s).
Gera, em /home/user/work/gn/saida: VOX.wav, MUSIK.wav, MIX.wav (48 kHz, 16 bits, estéreo) e beats.json (batidas, para ajustar os cortes)."""
import json, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl as E

W = "/home/user/work/gn"
SR = 48000
os.makedirs(f"{W}/saida", exist_ok=True)

def ler(arq, extra=()):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", arq, *extra, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32).reshape(-1, 2).copy()

def gravar(y, arq):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_s16le", arq], input=y.astype(np.float32).tobytes(), check=True)

def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)

def envelope(n, trechos, subida=0.12, descida=0.10, fade_final=2.5):
    t = np.arange(n) / SR
    voz = [(a + E.OFF, b + E.OFF) for a, b in trechos]
    gdb = np.full(n, -22.0)
    pausas = [(0.0, voz[0][0], 1.0, False, True)]
    for (a0, b0), (a1, b1) in zip(voz[:-1], voz[1:]):
        pausas.append((b0, a1, float(np.clip((a1 - b0 - 0.18) / 0.5, 0, 1)), True, True))
    pausas.append((voz[-1][1], n / SR, 1.0, True, False))
    for a, b, prof, com_subida, com_descida in pausas:
        m = (t >= a) & (t < b)
        s = smooth((t[m] - a) / subida) if com_subida else np.ones(m.sum())
        d = smooth((b - t[m]) / descida) if com_descida else np.ones(m.sum())
        gdb[m] = -22.0 + 16.0 * prof * np.minimum(s, d)
    g = 10 ** (gdb / 20)
    g *= np.clip((n / SR - t) / fade_final, 0, 1) ** 1.5      # fecha a trilha nos últimos 2,5 s
    return g.astype(np.float32), gdb

def main():
    n = int(round(E.TOTAL * SR))
    voz = ler(f"{W}/voz/VW_mixdown.mp3")
    vox = np.zeros((n, 2), np.float32)
    i0 = int(round(E.OFF * SR))
    vox[i0:i0 + len(voz)] = voz[:n - i0]
    mus = ler(f"{W}/musica/34.mp3")[:n]
    mus = mus / np.abs(mus).max() * 0.98                          # referência 0 dB = pico da música
    trechos = json.load(open(f"{W}/voz/trechos.json"))
    g, gdb = envelope(n, trechos)
    musik = mus * g[:, None]
    mix = vox + musik
    print("pico VOX %.1f dBFS | MUSIK %.1f | MIX %.1f" % tuple(20 * np.log10(np.abs(x).max()) for x in (vox, musik, mix)))
    for nome, y in (("VOX", vox), ("MUSIK", musik), ("MIX", mix)):
        gravar(y, f"{W}/saida/{nome}.wav")
    import librosa
    ym, sr = librosa.load(f"{W}/musica/34.mp3", sr=22050, mono=True)
    _, b = librosa.beat.beat_track(y=ym, sr=sr)
    json.dump([float(x) for x in librosa.frames_to_time(b, sr=sr)], open(f"{W}/beats.json", "w"))

if __name__ == "__main__":
    main()
