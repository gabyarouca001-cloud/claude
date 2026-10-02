"""Seja chata: corte limpo seguindo o roteiro (takes de trechos.json) + áudio suave; cor original do iPhone
(HEVC 10 bits HLG, 60 fps, sem alteração)."""
import json
import os
import subprocess
import sys

import numpy as np

SR, SR16 = 48000, 16000
SIL_DB, SIL_MIN = -42.0, 0.55
MANTER = 0.14
X265 = "colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc:range=limited:repeat-headers=1"
COR = ["-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc", "-tag:v", "hvc1"]
A16 = {}


def a16(f):
    if f not in A16:
        A16[f] = np.fromfile(f"{f}_16k.wav", np.int16)[22:].astype(np.float32) / 32768
    return A16[f]


def snap(t, fps=60):
    return round(t * fps) / fps


def plano():
    segs = []
    for t in json.load(open("trechos.json")):
        f, a, b = t["fonte"], max(0.0, t["ini"]), t["fim"]
        x = a16(f)
        n = int((b - a) / 0.01)
        e = np.array([20 * np.log10(np.sqrt((x[int((a + k * 0.01) * SR16):int((a + (k + 1) * 0.01) * SR16)] ** 2).mean()) + 1e-9)
                      for k in range(n)])
        mudo = e < SIL_DB
        pos, k = a, 0
        while k < n:
            if mudo[k]:
                j = k
                while j < n and mudo[j]:
                    j += 1
                if (j - k) * 0.01 >= SIL_MIN and k > 0 and j < n:
                    segs.append((f, snap(pos), snap(a + k * 0.01 + MANTER), t["n"]))
                    pos = a + j * 0.01 - MANTER
                k = j
            else:
                k += 1
        segs.append((f, snap(pos), snap(b), t["n"]))
    return segs


def audio(segs):
    fade = int(SR * 0.008)
    r = np.linspace(0, 1, fade, dtype=np.float32)
    cache, partes = {}, []
    for f, a, b, _ in segs:
        if f not in cache:
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{f}.MOV", "-map", "0:a:0", "-ac", "1", "-ar", str(SR),
                                  "-f", "f32le", "-"], capture_output=True, check=True).stdout
            cache[f] = np.frombuffer(raw, np.float32)
        p = cache[f][int(a * SR):int(b * SR)].copy()
        p[:fade] *= r
        p[-fade:] *= r[::-1]
        partes.append(p)
    # iguala o nível entre takes (±6 dB)
    def nivel(p):
        n = int(SR * 0.05)
        q = p[: len(p) // n * n].reshape(-1, n)
        return 20 * np.log10(np.percentile(np.sqrt((q ** 2).mean(1)), 80) + 1e-9)
    nv = [nivel(p) for p in partes]
    alvo = float(np.median(nv))
    y = np.concatenate([p * 10 ** (np.clip(alvo - v, -6, 6) / 20) for p, v in zip(partes, nv)])
    y.astype(np.float32).tofile("voz.f32")
    af = ("highpass=f=80,afftdn=nf=-30:nr=8:tn=1,equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3000:t=q:w=1.2:g=1,"
          "deesser=i=0.2,acompressor=threshold=-24dB:ratio=2:attack=15:release=200:makeup=1,loudnorm=I=-16:TP=-2:LRA=9")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "voz.f32", "-af", af,
                    "-ar", str(SR), "-ac", "2", "voz_final.wav"], check=True)


def video(segs):
    os.makedirs("seg", exist_ok=True)
    for i, (f, a, b, _) in enumerate(segs):
        out = f"seg/{i:02d}.mp4"
        if os.path.exists(out):
            continue
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, a - 1):.3f}", "-i", f"{f}.MOV",
                        "-vf", f"trim=start={min(1, a):.4f}:duration={b - a:.4f},setpts=PTS-STARTPTS,fps=60,format=yuv420p10le",
                        "-an", "-c:v", "libx265", "-preset", "fast", "-crf", "16", "-x265-params", X265, *COR,
                        out + ".tmp.mp4"], check=True)
        os.replace(out + ".tmp.mp4", out)
        print(f"segmento {i + 1}/{len(segs)}", flush=True)
    open("seg/lista.txt", "w").write("".join(f"file '{i:02d}.mp4'\n" for i in range(len(segs))))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "seg/lista.txt", "-i", "voz_final.wav",
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-tag:v", "hvc1", "-c:a", "aac", "-b:a", "320k",
                    "-shortest", "-movflags", "+faststart", "SEJA_CHATA_4K_HDR.mp4"], check=True)


if __name__ == "__main__":
    s = plano()
    t = 0
    for f, a, b, n in s:
        print(f"{n:02d} {f} {a:7.2f}-{b:7.2f} -> {t:6.2f}")
        t += b - a
    print("duração", round(t, 2))
    if "--render" in sys.argv:
        audio(s)
        video(s)
