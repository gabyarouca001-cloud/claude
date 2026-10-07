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

linhas, v, a = [], [], []
zoom = False
for i, e in enumerate(edl):
    if i > 0 and e["junta"] == "retake":
        zoom = not zoom
    ini, fim = e["ini"], e["fim"]
    d = fim - ini
    z = ""
    if zoom:
        cw, ch = 720 / ZOOM, 1280 / ZOOM
        z = f",crop={cw:.2f}:{ch:.2f}:{(720 - cw) / 2:.2f}:{(1280 - ch) * 0.30:.2f},scale=720:1280:flags=lanczos"
    linhas.append(f"[0:v]trim=start={ini:.4f}:end={fim:.4f},setpts=PTS-STARTPTS{z},setsar=1[v{i}]")
    fi = 0.0 if i == 0 else 0.008
    fo = 0.0 if i == len(edl) - 1 else 0.008
    af = f"atrim=start={ini:.4f}:end={fim:.4f},asetpts=PTS-STARTPTS"
    if fi:
        af += f",afade=t=in:d={fi}"
    if fo:
        af += f",afade=t=out:st={d - fo:.4f}:d={fo}"
    linhas.append(f"[1:a]{af}[a{i}]")
    v.append(f"[v{i}]")
    a.append(f"[a{i}]")
n = len(edl)
linhas.append("".join(x + y for x, y in zip(v, a)) + f"concat=n={n}:v=1:a=1[vc][ac]")
linhas.append("[ac]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
open(f"{W}/filtro.txt", "w").write(";\n".join(linhas))

sh(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{W}/proxy_720.mp4", "-i", ORIG,
    "-filter_complex_script", f"{W}/filtro.txt", "-map", "[vc]", "-map", "[aout]", "-r", str(FPS),
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", f"{W}/montado_720.mp4"])

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
