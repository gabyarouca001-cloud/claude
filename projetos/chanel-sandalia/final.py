"""Render do vídeo no formato curadoria: base (original 4K) + vídeos/fotos de tela cheia + polaroids + legendas/cartões (ASS) + áudio mixado.
Uso (em /home/user/work/cur):  S=1 python3 final.py previa      -> 720x1280, 2 passes, < 28,5 MB
                               S=2 python3 final.py 4k          -> 2160x3840, H.264 CRF 19, AAC 320k
O áudio vem de sfx.py (audio_final.wav); as mídias de assets.py (ov_<S>.json); o texto de legendas.py (legendas.ass, cartoes.ass)."""
import json
import os
import subprocess
import sys

modo = sys.argv[1] if len(sys.argv) > 1 else "previa"
S = int(os.environ.get("S", "1"))
W, H = 1080 * S, 1920 * S
ov = json.load(open(f"ov_{S}.json"))
DUR = 286.65

entradas, filtros = ["-i", "original.mp4", "-i", "audio_final.wav"], [f"[0:v]scale={W}:{H}:flags=lanczos,setsar=1,format=yuv420p[v0]"]
ult, k = "v0", 2
for f in ov["full"]:
    entradas += ["-i", f["arq"]]
    filtros.append(f"[{k}:v]setpts=PTS-STARTPTS+{f['t']}/TB[f{k}];[{ult}][f{k}]overlay=eof_action=pass[o{k}]")
    ult, k = f"o{k}", k + 1
for p in ov["pol"]:
    entradas += ["-loop", "1", "-framerate", "30", "-t", f"{p['fim'] - p['t']:.3f}", "-i", p["arq"]]
    filtros.append(f"[{k}:v]format=rgba,setpts=PTS-STARTPTS+{p['t']}/TB[p{k}];[{ult}][p{k}]overlay={p['x']}:{p['y']}:eof_action=pass[o{k}]")
    ult, k = f"o{k}", k + 1
fim = f"[{ult}]ass=legendas.ass:fontsdir=fonts,ass=cartoes.ass:fontsdir=fonts"
if modo in ("previa", "teste"):
    fim += ",scale=720:1280:flags=lanczos"
filtros.append(fim + "[v]")
base = ["ffmpeg", "-v", "error", "-stats", "-y", *entradas, "-filter_complex", ";".join(filtros), "-map", "[v]"]
cor = ["-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-r", "30"]

if modo == "previa":
    kbps = int(28.2 * 8192 / DUR - 112)
    log = "passlog_previa"
    v = ["-c:v", "libx264", "-preset", "medium", "-b:v", f"{kbps}k", "-maxrate", f"{int(kbps * 1.5)}k", "-bufsize", f"{kbps * 2}k", *cor, "-passlogfile", log]
    subprocess.run([*base, *v, "-pass", "1", "-an", "-f", "null", "/dev/null"], check=True)
    subprocess.run([*base, "-map", "1:a", *v, "-pass", "2", "-c:a", "aac", "-b:a", "112k", "-t", f"{DUR}", "-movflags", "+faststart",
                    "previa_curadoria_720p.mp4"], check=True)
    print("OK previa", os.path.getsize("previa_curadoria_720p.mp4") / 1e6, "MB")
elif modo == "teste":
    subprocess.run([*base, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30", *cor, "-an", "-t", f"{DUR}", "teste_curadoria.mp4"], check=True)
    print("OK teste")
else:
    subprocess.run([*base, "-map", "1:a", "-c:v", "libx264", "-preset", "faster", "-crf", "19", *cor, "-c:a", "aac", "-b:a", "320k",
                    "-t", f"{DUR}", "-movflags", "+faststart", "chanel_curadoria_4K_2160x3840.mp4"], check=True)
    print("OK 4k", os.path.getsize("chanel_curadoria_4K_2160x3840.mp4") / 1e6, "MB")
