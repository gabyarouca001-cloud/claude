"""Corte limpo do 'O óbvio precisa ser dito' seguindo o roteiro (takes escolhidos) + melhoria de áudio."""
import json
import os
import subprocess
import sys

import numpy as np

FPS = 30
SR = 48000
SRC = "original.mov"
# cor natural: HLG decodificado com referência de 300 nits, mobius sem saturar, balanço de branco levemente neutro
HLG = ("zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=300,format=gbrpf32le,zscale=p=bt709,"
       "tonemap=tonemap=mobius:param=0.5:desat=2,zscale=t=bt709,format=gbrp,"
       "colorchannelmixer=rr=0.95:bb=1.08,zscale=m=bt709:r=tv,format=yuv420p")

# (início da 1ª palavra, fim da última palavra, linha do roteiro, texto)
TAKES = [
    (25.40, 26.78, 1, "Posso pesar o clima?"),
    (89.68, 95.62, 2, "Você não precisa ter uma opinião sobre tudo e muito menos postar sobre todas elas."),
    (137.26, 144.06, 3, "Você já parou pra pensar ... absolutamente tudo,"),
    (147.80, 150.26, 3, "É muito bom falar: eu não sei."),
    (276.36, 279.18, 4, "Se permita ser ruim em alguma coisa nova."),
    (303.18, 313.18, 4, "Até porque é muito difícil aprender ... Aliás, esse é um peso que eu tenho tentado tirar das minhas costas."),
    (405.60, 417.32, 5, "Mudar de ideia ... Aliás, eu considero um ato de coragem."),
    (442.56, 449.62, 6, "Você sabia que pode se olhar no espelho ... se aceitar como é,"),
    (459.78, 463.68, 6, "E ainda assim, reconhecer que tem algo para mudar."),
    (469.82, 472.32, 6, "E isso vai além da aparência, tá?"),
    (521.84, 524.32, 7, "Nem toda situação ruim tem um lado bom."),
    (597.74, 607.03, 7, "Mas até ela pode te ensinar algo muito valioso ... quem você não quer mais."),
    (717.76, 720.30, 8, "O óbvio precisa ser dito, né?"),
    (721.24, 722.05, 8, "Tchau!"),
]
PAD_INI, PAD_FIM = 0.10, 0.18
SIL_DB, SIL_MIN = -36.0, 0.55          # pausas internas longas também saem
MANTER_ANTES, MANTER_DEPOIS = 0.16, 0.12


PALAVRAS = [w for seg in json.load(open("transcricao.json")) for w in seg["words"]]


def snap(t):
    return round(t * FPS) / FPS


def audio():
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32)


def rms_db(x, passo=0.01):
    n = int(SR * passo)
    q = x[: len(x) // n * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt((q ** 2).mean(1)) + 1e-9)


def vale(db, t, janela=0.06):
    a, b = int((t - janela) / 0.01), int((t + janela) / 0.01)
    return (a + int(np.argmin(db[a:b]))) * 0.01


def plano(db):
    segs = []
    for ini, fim, linha, txt in TAKES:
        a = snap(vale(db, ini - PAD_INI))
        b = snap(vale(db, fim + PAD_FIM))
        # pausas internas longas
        i0, i1 = int(a / 0.01), int(b / 0.01)
        mudo = db[i0:i1] < SIL_DB
        cortes, k = [], 0
        while k < len(mudo):
            if mudo[k]:
                j = k
                while j < len(mudo) and mudo[j]:
                    j += 1
                c0, c1 = (i0 + k) * 0.01 + MANTER_ANTES, (i0 + j) * 0.01 - MANTER_DEPOIS
                dentro = any(w["s"] < c1 and w["e"] > c0 for w in PALAVRAS)
                if (j - k) * 0.01 >= SIL_MIN and k > 0 and j < len(mudo) and not dentro:
                    cortes.append((c0, c1))
                k = j
            else:
                k += 1
        pos = a
        for c0, c1 in cortes:
            segs.append((snap(pos), snap(c0), linha))
            pos = c1
        segs.append((snap(pos), b, linha))
    return [s for s in segs if s[1] - s[0] >= 2 / FPS]


def montar_audio(x, segs):
    fade = int(SR * 0.010)
    r = np.linspace(0, 1, fade, dtype=np.float32)
    partes = []
    # iguala o nível entre takes (RMS das partes com voz), no máximo ±6 dB
    def nivel(p):
        n = int(SR * 0.05); q = p[: len(p) // n * n].reshape(-1, n)
        r = np.sqrt((q ** 2).mean(1)); return 20 * np.log10(np.percentile(r, 80) + 1e-9)
    niveis = [nivel(x[int(a * SR):int(b * SR)]) for a, b, _ in segs]
    alvo = float(np.median(niveis))
    for (a, b, _), nv in zip(segs, niveis):
        p = x[int(a * SR):int(b * SR)].copy() * 10 ** (np.clip(alvo - nv, -6, 6) / 20)
        p[:fade] *= r
        p[-fade:] *= r[::-1]
        partes.append(p)
    y = np.concatenate(partes)
    y.astype(np.float32).tofile("voz_cortada.f32")
    # limpeza: passa-alta, redução de ruído do closet, menos "caixa" (250 Hz), presença, compressão, -14 LUFS
    # limpeza suave: passa-alta, ruído do closet, menos "caixa", presença leve, compressão leve sem ganho, -16 LUFS
    af = ("highpass=f=80,afftdn=nf=-30:nr=8:tn=1,"
          "equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3000:t=q:w=1.2:g=1,"
          "deesser=i=0.2,acompressor=threshold=-24dB:ratio=2:attack=15:release=200:makeup=1,"
          "loudnorm=I=-16:TP=-2:LRA=9")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "voz_cortada.f32",
                    "-af", af, "-ar", str(SR), "-ac", "2", "voz_final.wav"], check=True)


def montar_video(segs, saida):
    """Um segmento por vez (18 decodificadores 4K HEVC juntos estouram a memória)."""
    os.makedirs("seg", exist_ok=True)
    for i, (a, b, _) in enumerate(segs):
        if os.path.exists(f"seg/{i:02d}.mp4"):
            continue
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a - 1:.3f}", "-t", f"{b - a + 1.5:.3f}", "-i", SRC,
                        "-vf", f"trim=start=1:duration={b - a:.4f},setpts=PTS-STARTPTS,fps={FPS},{HLG}", "-an",
                        "-c:v", "libx264", "-preset", "faster", "-crf", "16", "-pix_fmt", "yuv420p",
                        f"seg/{i:02d}.mp4"], check=True)
        print(f"segmento {i + 1}/{len(segs)}", flush=True)
    open("seg/lista.txt", "w").write("".join(f"file '{i:02d}.mp4'\n" for i in range(len(segs))))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "seg/lista.txt",
                    "-i", "voz_final.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", saida], check=True)


if __name__ == "__main__":
    x = audio()
    db = rms_db(x)
    segs = plano(db)
    json.dump(segs, open("plano.json", "w"))
    t = 0
    for a, b, l in segs:
        print(f"L{l}  {a:7.2f}-{b:7.2f}  ({b - a:4.2f}s)  -> {t:6.2f}")
        t += b - a
    print(f"duração final: {t:.2f}s")
    if "--render" in sys.argv:
        montar_audio(x, segs)
        montar_video(segs, "OBVIO_v2_4k.mp4")
