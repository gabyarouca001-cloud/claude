"""Etapa 2: prévia 720p (< 30 MB) a partir do edl.json.
 - crop de 8 px nas bordas (linha preta do export) e escala para 720x1280
 - punch-in de 12% alternado a cada corte de retake (plano normal no início e no fim)
 - áudio com fades curtos nas emendas e mix em -14 LUFS / pico <= -1,5 dBTP
Uso: python3 previa.py"""
import json
import os
import subprocess

W = "/home/user/work/ep3"
ORIG = f"{W}/original.mp4"
FPS = 30
ZOOM = 1.12
edl = json.load(open("edl.json"))["edl"]


def sh(cmd):
    print(" ".join(cmd[:6]), "...")
    subprocess.run(cmd, check=True)


if not os.path.exists(f"{W}/proxy_720.mp4"):
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", ORIG, "-an",
        "-vf", "crop=2144:3824:8:8,scale=720:1280:flags=lanczos", "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-g", "30", f"{W}/proxy_720.mp4"])

import numpy as np
import wave

# --- vídeo: um arquivo por corte (não estoura a memória), depois concatena sem reencodar
os.makedirs(f"{W}/seg", exist_ok=True)
zoom = False
lista = []
for i, e in enumerate(edl):
    if i > 0 and e["junta"] == "retake":
        zoom = not zoom
    arq = f"{W}/seg/s{i:03d}.mp4"
    lista.append(f"file '{arq}'")
    if os.path.exists(arq):
        continue
    z = []
    if zoom:
        cw, ch = 720 / ZOOM, 1280 / ZOOM
        z = ["-vf", f"crop={cw:.2f}:{ch:.2f}:{(720 - cw) / 2:.2f}:{(1280 - ch) * 0.30:.2f},scale=720:1280:flags=lanczos"]
    sh(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{e['ini']:.4f}", "-t", f"{e['fim'] - e['ini']:.4f}", "-i", f"{W}/proxy_720.mp4",
        *z, "-r", str(FPS), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", arq])
open(f"{W}/seg/lista.txt", "w").write("\n".join(lista))
sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{W}/seg/lista.txt", "-c", "copy", f"{W}/video_720.mp4"])

# --- áudio: monta do original com fades curtos, depois normaliza (-14 LUFS, pico <= -1,5 dBTP)
SR = 48000
sh(["ffmpeg", "-y", "-loglevel", "error", "-i", ORIG, "-vn", "-ac", "2", "-ar", str(SR), f"{W}/orig_48k.wav"])
w = wave.open(f"{W}/orig_48k.wav")
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32768
partes = []
for i, e in enumerate(edl):
    a, b = int(round(e["ini"] * SR)), int(round(e["fim"] * SR))
    p = x[a:b].copy()
    f = int(0.008 * SR)
    if i > 0:
        p[:f] *= np.linspace(0, 1, f)[:, None]
    if i < len(edl) - 1:
        p[-f:] *= np.linspace(1, 0, f)[:, None]
    partes.append(p)
y = np.concatenate(partes)
o = wave.open(f"{W}/audio_montado.wav", "wb"); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR)
o.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()); o.close()
m = subprocess.run(["ffmpeg", "-i", f"{W}/audio_montado.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
m = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
      f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
sh(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{W}/audio_montado.wav", "-af", ln, "-ar", "48000", f"{W}/audio_final.wav"])
sh(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{W}/video_720.mp4", "-i", f"{W}/audio_final.wav", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
    "-shortest", f"{W}/montado_720.mp4"])

dur = float(subprocess.run(["ffmpeg", "-i", f"{W}/montado_720.mp4"], capture_output=True, text=True).stderr.split("Duration: ")[1].split(",")[0].split(":")[2]) \
    + 60 * int(subprocess.run(["ffmpeg", "-i", f"{W}/montado_720.mp4"], capture_output=True, text=True).stderr.split("Duration: ")[1].split(":")[1])
alvo_mb = 27.0
kbps_audio = 96
kbps_video = int((alvo_mb * 8000) / dur - kbps_audio - 8)
print(f"duração {dur:.1f}s -> vídeo {kbps_video} kbps + áudio {kbps_audio} kbps")
common = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{kbps_video}k", "-pix_fmt", "yuv420p", "-passlogfile", f"{W}/p2"]
sh(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{W}/montado_720.mp4", *common, "-pass", "1", "-an", "-f", "mp4", "/dev/null"])
sh(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{W}/montado_720.mp4", *common, "-pass", "2",
    "-c:a", "aac", "-b:a", f"{kbps_audio}k", "-movflags", "+faststart", f"{W}/DEEP_EP3_previa_720p.mp4"])
print(os.path.getsize(f"{W}/DEEP_EP3_previa_720p.mp4") / 1e6, "MB")
