"""Troca a trilha da versão final da editora (editora_reels.mp4) sem reencodar o vídeo.
Usa o mapa de cortes dela (alinhamento por áudio com a minha v3) para recortar a minha voz+SFX
sem música (voz_norm_v3.wav) e soma a trilha nova, bem baixa."""
import json
import subprocess
import sys

import numpy as np

SR = 48000
EP2 = "/home/user/work/ep2"
TRILHA = sys.argv[1] if len(sys.argv) > 1 else "/home/user/work/broll/mus_593.mp3"   # Mixkit "Finding Myself"
SAIDA = sys.argv[2] if len(sys.argv) > 2 else "DEEP_EP2_Reels_editora_musica_nova.mp4"
TRILHA_LUFS = -33
INICIO = 9.7          # fim da abertura na versão dela


def ler(arq):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", arq, "-vn", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32).reshape(-1, 2).copy()


mapa = json.load(open("mapa_dela.json"))
voz = ler(f"{EP2}/voz_norm_v3.wav")
dur = float(subprocess.run(["ffmpeg", "-i", "editora_reels.mp4"], capture_output=True, text=True).stderr
            .split("Duration: ")[1].split(",")[0].split(":")[-1]) + 7 * 60
n = int(dur * SR)
out = np.zeros((n, 2), np.float32)
fronteiras = [0.0] + [c["dela"] for c in mapa["cortes"]] + [dur]
offs = [mapa["off_inicial"]] + [c["off_depois"] for c in mapa["cortes"]]
fade = int(0.008 * SR)
for a, b, o in zip(fronteiras, fronteiras[1:], offs):
    i, j = int(a * SR), int(b * SR)
    k = i + int(round(o * SR))
    p = voz[max(k, 0):k + (j - i)].copy()
    if len(p) < j - i:
        p = np.vstack([p, np.zeros((j - i - len(p), 2), np.float32)])
    if a > 0:
        p[:fade] *= np.linspace(0, 1, fade)[:, None]
    p[-fade:] *= np.linspace(1, 0, fade)[:, None]
    out[i:j] = p

# trilha nova: loudnorm em -20 e desce para -33 LUFS; entra depois da abertura, some nos últimos 3 s
copias = 3
subprocess.run(["ffmpeg", "-v", "error", "-y", *sum([["-i", TRILHA] for _ in range(copias)], []), "-filter_complex",
                ";".join(["[0:a][1:a]acrossfade=d=4[x1]"] + [f"[x{k}][{k + 1}:a]acrossfade=d=4[x{k + 1}]"
                                                             for k in range(1, copias - 1)]
                         + [f"[x{copias - 1}]lowpass=f=9000,loudnorm=I=-20:TP=-1.5:LRA=9[y]"]),
                "-map", "[y]", "-t", str(dur), "-ar", str(SR), "-ac", "2", "-c:a", "pcm_f32le", "trilha_nova.wav"],
               check=True)
tri = ler("trilha_nova.wav")[:n - int(INICIO * SR)] * 10 ** ((TRILHA_LUFS + 20) / 20)
env = np.ones(len(tri), np.float32)
fi, fo = int(2.5 * SR), int(3.0 * SR)
env[:fi] = np.linspace(0, 1, fi)
env[-fo:] = np.linspace(1, 0, fo)
out[int(INICIO * SR):int(INICIO * SR) + len(tri)] += tri * env[:, None]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                "alimiter=limit=0.84:level=disabled", "-c:a", "pcm_s16le", "audio_musica_nova.wav"],
               input=out.tobytes(), check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "editora_reels.mp4", "-i", "audio_musica_nova.wav",
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-shortest",
                "-movflags", "+faststart", SAIDA], check=True)
print("OK", SAIDA, round(dur, 2))
