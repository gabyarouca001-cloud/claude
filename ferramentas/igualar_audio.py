"""Deixa um áudio gravado em duas fontes (celular + microfone em casa) com o mesmo timbre e volume."""
import subprocess
import sys

import numpy as np

SR = 44100
ENTRADA = sys.argv[1]
SAIDA = sys.argv[2]
# trechos gravados no celular (cortes em pausas); o resto é o microfone de casa
CELULAR = [(0.0, 2.24), (6.66, 8.70), (15.74, 20.86), (32.08, 35.36), (57.74, 999)]
BANDAS = [80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500,
          3150, 4000, 5000, 6300, 8000, 10000, 12500]


def ler(args, canais=2):
    bruto = subprocess.run(["ffmpeg", "-v", "error", *args, "-ac", str(canais), "-ar", str(SR), "-f", "f32le", "-"],
                           capture_output=True, check=True).stdout
    return np.frombuffer(bruto, np.float32).reshape(-1, canais).copy()


def mascara(n):
    m = np.zeros(n, np.float32)
    for a, b in CELULAR:
        m[int(a * SR):int(min(b * SR, n))] = 1
    # transição suave de 40 ms (as trocas caem em pausas)
    k = int(0.04 * SR)
    return np.convolve(m, np.ones(k) / k, mode="same").astype(np.float32)


def espectro(x, m, alvo):
    """Espectro médio (1/3 de oitava) só dos trechos com voz de uma das fontes."""
    mono = x.mean(1)
    n = 4096
    acc = np.zeros(n // 2 + 1)
    cont = 0
    for i in range(0, len(mono) - n, n // 2):
        if abs(m[i + n // 2] - alvo) > 0.01:
            continue
        s = mono[i:i + n]
        if 20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-9) < -40:
            continue
        acc += np.abs(np.fft.rfft(s * np.hanning(n))) ** 2
        cont += 1
    f = np.fft.rfftfreq(n, 1 / SR)
    return np.array([10 * np.log10(acc[(f >= c / 1.12) & (f < c * 1.12)].mean() + 1e-12) for c in BANDAS])


def eq(ganhos):
    entradas = ";".join(f"entry({c},{g:.1f})" for c, g in zip(BANDAS, ganhos))
    return f"firequalizer=gain_entry='entry(20,{ganhos[0]:.1f});{entradas};entry(20000,{ganhos[-1]:.1f})'"


def nivel_voz(x, m, alvo):
    """Nível médio de voz (quadros de 50 ms com fala) só nos trechos de uma das fontes."""
    mono = x.mean(1)
    h = int(0.05 * SR)
    k = len(mono) // h
    q = mono[:k * h].reshape(-1, h)
    dentro = np.abs(m[:k * h, 0].reshape(-1, h).mean(1) - alvo) < 0.01
    r = 20 * np.log10(np.sqrt((q ** 2).mean(1)) + 1e-9)[dentro]
    r = r[r > r.max() - 30]
    return np.mean(r[r > np.percentile(r, 50)])


def main():
    x = ler(["-i", ENTRADA])
    m = mascara(len(x))
    e_casa, e_cel = espectro(x, m, 0), espectro(x, m, 1)
    # normaliza pelo nível médio e define um alvo no meio do caminho, com graves controlados
    e_casa -= e_casa.mean()
    e_cel -= e_cel.mean()
    alvo = (e_casa + e_cel) / 2
    alvo[:5] -= 1.5  # segura 80–200 Hz (o microfone de casa embola)
    g_casa = np.clip(alvo - e_casa, -9, 9)
    g_cel = np.clip(alvo - e_cel, -9, 9)
    g_cel[-3:] = np.minimum(g_cel[-3:], 3)  # não inventa agudo que o celular não gravou (evita chiado)
    for c, a, b in zip(BANDAS, g_casa, g_cel):
        print(f"{c:6d} Hz  casa {a:+5.1f} dB   celular {b:+5.1f} dB")

    comp = "acompressor=threshold=-22dB:ratio=3:attack=5:release=120:knee=4:makeup=1"
    casa = ler(["-i", ENTRADA, "-af", f"highpass=f=70,{eq(g_casa)},{comp}"])
    cel = ler(["-i", ENTRADA, "-af", f"afftdn=nr=20:nf=-36:tn=1,agate=threshold=0.02:ratio=2:range=0.35:attack=5:release=200,highpass=f=70,{eq(g_cel)},{comp}"])
    n = min(len(x), len(casa), len(cel))
    casa, cel, m = casa[:n], cel[:n], m[:n, None]

    # mesmo volume de voz nas duas fontes
    nc = nivel_voz(casa, m, 0)
    nl = nivel_voz(cel, m, 1)
    cel *= 10 ** ((nc - nl) / 20)
    print(f"voz casa {nc:.1f} dB, celular {nl:.1f} dB -> ajuste do celular {nc - nl:+.1f} dB")
    y = casa * (1 - m) + cel * m

    tmp = SAIDA + ".tmp.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", tmp],
                   input=y.astype(np.float32).tobytes(), check=True)
    # loudness final: -14 LUFS, pico -1.5 dBTP (dois passes)
    med = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af",
                          "loudnorm=I=-14:TP=-1.5:LRA=7:print_format=summary", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    i_in = float(med.split("Input Integrated:")[1].split("LUFS")[0])
    ganho = -14 - i_in
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af",
                    f"volume={ganho:.2f}dB,alimiter=limit=0.84:attack=3:release=80:level=disabled",
                    "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "320k", SAIDA], check=True)
    print(f"loudness {i_in:.1f} -> -14 LUFS (ganho {ganho:+.1f} dB)")


if __name__ == "__main__":
    main()
