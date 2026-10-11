"""DEEP EP3 (versão da editora): tira a trilha e mantém a voz + os efeitos sonoros das inserções.
A separação (Demucs, ferramentas/separar_voz.py) põe música E efeitos no mesmo stem; aqui o stem "música" só
passa em janelas curtas nos efeitos (transientes fortes, ou transientes perto da entrada de uma inserção).
A vinheta DEEP (10,0–11,5 s) fica com o som original.
Uso (em /home/user/work/deep3): python3 audio_sem_musica.py  -> audio_sem_musica.wav (−14 LUFS)"""
import json
import subprocess

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

SR = 44100
VINHETA = (10.0, 11.5)
# listas (itens entram um a um com "tick"): dentro delas vale qualquer transiente forte
LISTAS = [(56.6, 59.8), (71.8, 75.6), (157.8, 165.6), (186.2, 191.8), (219.0, 225.8), (256.4, 264.0)]
VIDEO_INSERTS = [(68.13, 70.03), (107.17, 109.17), (183.90, 185.40), (206.27, 207.37), (207.37, 208.77), (208.77, 210.47)]


def ler(arq):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", arq, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32).reshape(-1, 2).copy()


def eventos(mus):
    """transientes do stem de música: (início, fim, excesso sobre a mediana de 3 s)"""
    n = SR // 100
    m = mus.mean(1)
    x = m[:len(m) // n * n].reshape(-1, n)
    f = 20 * np.log10(np.sqrt((x ** 2).mean(1)) + 1e-9)
    base = np.median(sliding_window_view(np.pad(f, 150, mode="edge"), 301), axis=1)[:len(f)]
    ex = f - base
    out, i = [], 0
    while i < len(ex):
        if ex[i] > 7:
            j = i
            while j < len(ex) and ex[j] > 3:
                j += 1
            out.append((i / 100, j / 100, float(ex[i:j].max())))
            i = j
        else:
            i += 1
    return out


def main():
    mix, voz, mus = ler("mix44k.wav"), ler("voz_sem_musica.wav"), ler("musica_extraida.wav")
    ins = [d for d in json.load(open("insercoes_editora.json")) if d["fim"] - d["ini"] >= 0.6]
    ancoras = [d["ini"] for d in ins] + [d["fim"] for d in ins] + [a for a, _ in VIDEO_INSERTS]
    ganho = np.zeros(len(mus), np.float32)
    mantidos = []
    for a, b, ex in eventos(mus):
        perto = any(-0.6 <= a - t <= 0.5 for t in ancoras) or any(x - 0.6 <= a <= y for x, y in LISTAS)
        if ex >= 20 or (ex >= 9 and perto):
            mantidos.append((a, b, ex))
            i0, i1 = int((a - 0.12) * SR), int((b + 0.35) * SR)
            env = np.ones(i1 - i0, np.float32)
            fi, fo = int(0.04 * SR), int(0.15 * SR)
            env[:fi] = np.linspace(0, 1, fi)
            env[-fo:] = np.linspace(1, 0, fo)
            i0c = max(i0, 0)
            ganho[i0c:i1] = np.maximum(ganho[i0c:i1], env[i0c - i0:])
    out = voz + mus * ganho[:, None]
    # vinheta com o som original (crossfade de 50 ms)
    a, b = int(VINHETA[0] * SR), int(VINHETA[1] * SR)
    w = np.zeros(len(out), np.float32)
    w[a:b] = 1
    xf = int(0.05 * SR)
    w[a - xf:a] = np.linspace(0, 1, xf)
    w[b:b + xf] = np.linspace(1, 0, xf)
    out = out * (1 - w[:, None]) + mix * w[:, None]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_s16le", "audio_bruto_sem_musica.wav"], input=out.astype(np.float32).tobytes(), check=True)
    # −14 LUFS, pico ≤ −1,5 dBTP (loudnorm em 2 passes, linear)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", "audio_bruto_sem_musica.wav", "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    med = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "audio_bruto_sem_musica.wav", "-af",
                    f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={med['input_i']}:measured_TP={med['input_tp']}:"
                    f"measured_LRA={med['input_lra']}:measured_thresh={med['input_thresh']}:"
                    f"offset={med['target_offset']}:linear=true", "-ar", str(SR), "-c:a", "pcm_s16le",
                    "audio_sem_musica.wav"], check=True)
    print(f"{len(mantidos)} efeitos mantidos; entrada {med['input_i']} LUFS -> −14")
    for a, b, ex in mantidos:
        print(f"  efeito {a:7.2f}-{b:6.2f}  +{ex:.0f} dB")


if __name__ == "__main__":
    main()
