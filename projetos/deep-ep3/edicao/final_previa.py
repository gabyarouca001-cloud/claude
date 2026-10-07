"""Etapa 3: prévia 720p com TUDO — inserções ASS, B-roll de banco (Mixkit), SFX, trilha 'Chillax' (-33 LUFS) e voz em -14 LUFS.
Pré-requisitos: montar_base.py (video_720.mp4), previa.py (audio_montado.wav), insercoes_ep3.py (ASS + sfx)."""
import json
import os
import re
import subprocess
import wave

import numpy as np

import mapa_insercoes as M
import sfx_ep3 as D

W = "/home/user/work/ep3"
BR = "/home/user/work/broll3"
SR, FPS = 48000, 30
LW, LH = 720, 1280
OFF = 346 / FPS                      # a edição dela termina aqui; trilha entra depois
TRILHA_LUFS = -33
sh = lambda c: subprocess.run(c, check=True)

# (arquivo, início no clipe, duração, centro horizontal 0-1, âncora no bruto, adianta, rótulo)
BROLL = [
    ("46635", 1.0, 1.9, 0.5, 114.20, 0.10, "IA / tecnologia"),
    ("50610", 1.0, 2.0, 0.5, 234.55, 0.00, "edição de vídeo"),
    ("42136", 1.5, 2.3, 0.5, 324.70, 0.00, "compra pelo celular (vertical)"),
    ("21364", 0.5, 1.1, 0.80, 435.34, 0.08, "feed"),
    ("2948", 2.0, 1.4, 0.5, None, 0.0, "podcast"),
    ("49381", 2.0, 1.7, 0.4, None, 0.0, "loja"),
    ("13231", 3.0, 1.5, 0.5, 397.30, 0.00, "equipe"),
]


def ler(arq):
    w = wave.open(arq)
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, w.getnchannels()).astype(np.float32) / 32768
    return x if x.shape[1] == 2 else np.repeat(x, 2, 1)


def loudnorm(entrada, saida, alvo, filtro=""):
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", entrada, "-af", filtro + f"loudnorm=I={alvo}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    j = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    ln = (f"loudnorm=I={alvo}:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
          f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", entrada, "-af", filtro + ln, "-ar", str(SR), "-c:a", "pcm_s16le", saida])


# ------------------------------------------------------------ B-roll: tempos na prévia + clipes prontos (sem áudio, zoom lento)
tempos, ant = [], None
for arq, ss, dur, cx, ancora, lead, rot in BROLL:
    t = M.saida(ancora) - lead if ancora else ant["fim"]
    t = round(t * FPS) / FPS
    ant = dict(arq=arq, t=t, dur=dur, fim=round(t + dur, 3), rot=rot)
    tempos.append(ant)
os.makedirs(f"{W}/broll", exist_ok=True)
for k, (b, (arq, ss, dur, cx, *_)) in enumerate(zip(tempos, BROLL)):
    src = f"{BR}/v_{arq}.mp4"
    if arq == "42136":      # já é vertical
        vf = (f"scale={LW}:{LH}:flags=lanczos,scale=w='{LW}*(1+0.05*t/{dur})':h=-2:eval=frame:flags=bicubic,crop={LW}:{LH},fps={FPS},setsar=1")
    else:
        vf = (f"scale=-2:{LH}:flags=lanczos,crop={LW}:{LH}:'min(max(iw*{cx}-{LW // 2},0),iw-{LW})':0,"
              f"scale=w='{LW}*(1+0.05*t/{dur})':h=-2:eval=frame:flags=bicubic,crop={LW}:{LH},fps={FPS},setsar=1")
    b["arq_saida"] = f"{W}/broll/b{k}.mp4"
    sh(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(ss), "-i", src, "-t", str(dur), "-an", "-vf", vf,
        "-frames:v", str(round(dur * FPS)), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", b["arq_saida"]])
    print(f"B-roll {b['t']:7.2f}s  {b['dur']:.1f}s  {b['rot']}")
json.dump(tempos, open(f"{W}/broll_tempos.json", "w"), indent=1)

# ------------------------------------------------------------ áudio: voz + SFX -> -14 LUFS, depois a trilha por baixo
voz = ler(f"{W}/audio_montado.wav")
dur_total = len(voz) / SR
eventos = [(t, tipo) for t, tipo in json.load(open(f"{W}/sfx_insercoes.json"))]
clique = ler(f"{BR}/shutter.bin")[:, 0]
clique = clique / np.abs(clique).max()
cache = {}
for t, tipo in eventos:
    y = cache.setdefault(tipo, D.som(tipo).astype(np.float32))
    i = int(t * SR)
    j = min(len(voz), i + len(y))
    voz[i:j] += y[:j - i, None]
for k, b in enumerate(tempos):
    emendado = k and abs(b["t"] - tempos[k - 1]["fim"]) < 0.05
    y = clique * (0.10 if emendado else 0.14)
    i = int((b["t"] - 0.03) * SR)
    voz[i:i + len(y)] += y[:len(voz) - i, None][:len(y)]
o = wave.open(f"{W}/voz_sfx.wav", "wb"); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR)
o.writeframes((np.clip(voz, -1, 1) * 32767).astype(np.int16).tobytes()); o.close()
loudnorm(f"{W}/voz_sfx.wav", f"{W}/voz_norm.wav", -14, "highpass=f=70,")

n = int(np.ceil((dur_total - OFF) / 140)) + 1
sh(["ffmpeg", "-y", "-loglevel", "error", *sum([["-i", f"{BR}/mus_655.mp3"] for _ in range(n)], []), "-filter_complex",
    ";".join(["[0:a][1:a]acrossfade=d=4[x1]"] + [f"[x{k}][{k + 1}:a]acrossfade=d=4[x{k + 1}]" for k in range(1, n - 1)]),
    "-map", f"[x{n - 1}]", "-ac", "2", "-ar", str(SR), "-c:a", "pcm_s16le", f"{W}/trilha_loop.wav"])
loudnorm(f"{W}/trilha_loop.wav", f"{W}/trilha_norm.wav", -20, "lowpass=f=9000,")
tri = ler(f"{W}/trilha_norm.wav")[:int((dur_total - OFF) * SR)] * 10 ** ((TRILHA_LUFS + 20) / 20)
env = np.ones(len(tri), np.float32)
fi, fo = int(2.5 * SR), int(3.0 * SR)
env[:fi] = np.linspace(0, 1, fi); env[-fo:] = np.linspace(1, 0, fo)
final = ler(f"{W}/voz_norm.wav")[:len(voz)].copy()
final[int(OFF * SR):int(OFF * SR) + len(tri)] += tri * env[:, None]
sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", "alimiter=limit=0.76:level=disabled",
    "-c:a", "pcm_s16le", f"{W}/audio_pronto.wav"]) if False else None
p = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", "alimiter=limit=0.76:level=disabled",
                    "-c:a", "pcm_s16le", f"{W}/audio_pronto.wav"], input=final.astype(np.float32).tobytes())
assert p.returncode == 0

# ------------------------------------------------------------ vídeo: base + B-roll + inserções ASS
entradas, filtros, ult = [], [], "0:v"
for k, b in enumerate(tempos):
    entradas += ["-i", b["arq_saida"]]
    filtros.append(f"[{k + 2}:v]setpts=PTS-STARTPTS+{b['t']}/TB[b{k}];[{ult}][b{k}]overlay=eof_action=pass[o{k}]")
    ult = f"o{k}"
filtros.append(f"[{ult}]ass={W}/insercoes_ep3.ass:fontsdir={W}/fonts[v]")
sh(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{W}/video_720.mp4", "-i", f"{W}/audio_pronto.wav", *entradas, "-filter_complex", ";".join(filtros),
    "-map", "[v]", "-map", "1:a", "-t", f"{dur_total:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", f"{W}/montado_pronto_720.mp4"])

# ------------------------------------------------------------ compressão em 2 passes (< 30 MB)
alvo_mb, kbps_audio = 27.0, 96
kbps_video = int(alvo_mb * 8000 / dur_total - kbps_audio - 8)
print(f"duração {dur_total:.1f}s -> vídeo {kbps_video} kbps + áudio {kbps_audio} kbps")
com = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{kbps_video}k", "-pix_fmt", "yuv420p", "-passlogfile", f"{W}/p3"]
sh(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{W}/montado_pronto_720.mp4", *com, "-pass", "1", "-an", "-f", "mp4", "/dev/null"])
sh(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{W}/montado_pronto_720.mp4", *com, "-pass", "2", "-c:a", "aac", "-b:a", f"{kbps_audio}k",
    "-movflags", "+faststart", f"{W}/DEEP_EP3_previa_v2_720p.mp4"])
print(os.path.getsize(f"{W}/DEEP_EP3_previa_v2_720p.mp4") / 1e6, "MB")
