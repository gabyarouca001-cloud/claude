"""Etapa 2: corrige o trecho de áudio ruim, monta a trilha de voz cortada e mistura os SFX."""
import json
import subprocess
import sys

import numpy as np

SR = 48000
RUIM = (271.25, 283.15)
# volume +5.5 dB e equalização para casar com o resto (menos agudo/sibilância)
FILTRO_RUIM = ("acompressor=threshold=-24dB:ratio=3:attack=3:release=120:knee=4,"
               "firequalizer=gain_entry='entry(60,-1);entry(150,-1.5);entry(500,1.2);entry(1200,0);"
               "entry(2000,-2.5);entry(3000,-4);entry(4500,-5);entry(6000,-7);entry(10000,-10);entry(16000,-10)',"
               "volume=GANHO,alimiter=limit=0.93:attack=2:release=60:level=disabled")


def ler(args):
    bruto = subprocess.run(["ffmpeg", "-v", "error", *args, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                           capture_output=True, check=True).stdout
    return np.frombuffer(bruto, np.float32).reshape(-1, 2).copy()


def gravar(x, caminho):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_f32le", caminho], input=x.astype(np.float32).tobytes(), check=True)


def rampa(n):
    return np.linspace(0, 1, n, dtype=np.float32)[:, None]


def voz_corrigida():
    x = ler(["-i", "original.mp4", "-vn"])
    a, b = RUIM
    trecho = ler(["-ss", str(a - 0.05), "-t", str(b - a + 0.1), "-i", "original.mp4", "-vn",
                  "-af", FILTRO_RUIM.replace("GANHO", sys.argv[1] if len(sys.argv) > 1 else "9dB")])
    ia, ib = int((a - 0.05) * SR), int((b + 0.05) * SR)
    trecho = trecho[: ib - ia]
    f = int(0.03 * SR)  # crossfade de 30 ms nas bordas (caem em pausas)
    mistura = x[ia:ib].copy()
    peso = np.ones((ib - ia, 1), np.float32)
    peso[:f] = rampa(f)
    peso[-f:] = rampa(f)[::-1]
    x[ia:ib] = trecho * peso + mistura * (1 - peso)
    return x


def montar(x, segmentos):
    partes = []
    f = int(0.006 * SR)
    for s in segmentos:
        p = x[int(round(s["ini"] * SR)): int(round(s["fim"] * SR))].copy()
        if len(p) > 2 * f:
            p[:f] *= rampa(f)
            p[-f:] *= rampa(f)[::-1]
        partes.append(p)
    return np.concatenate(partes)


def main():
    plano = json.load(open("plano.json"))
    x = voz_corrigida()
    gravar(x, "voz_corrigida_completa.wav")
    voz = montar(x, plano["segmentos"])
    gravar(voz, "voz_cortada.wav")
    print(f"voz: {len(voz) / SR:.2f}s")


if __name__ == "__main__":
    main()
