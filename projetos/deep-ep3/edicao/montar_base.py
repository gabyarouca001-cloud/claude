"""Base de vídeo 720x1280 com contagem EXATA de quadros por corte (a 1ª versão ganhava 1 quadro em vários cortes
e o vídeo foi se adiantando em relação ao áudio: 1,5 s no fim).  Gera /home/user/work/ep3/video_720.mp4."""
import json
import os
import shutil
import subprocess

W = "/home/user/work/ep3"
FPS, ZOOM = 30, 1.12
edl = json.load(open("edl.json"))["edl"]
shutil.rmtree(f"{W}/seg", ignore_errors=True)
os.makedirs(f"{W}/seg")
zoom, lista, total = False, [], 0
for i, e in enumerate(edl):
    if i > 0 and e["junta"] == "retake":
        zoom = not zoom
    n = round((e["fim"] - e["ini"]) * FPS)
    total += n
    arq = f"{W}/seg/s{i:03d}.mp4"
    lista.append(f"file '{arq}'")
    z = []
    if zoom:
        cw, ch = 720 / ZOOM, 1280 / ZOOM
        z = ["-vf", f"crop={cw:.2f}:{ch:.2f}:{(720 - cw) / 2:.2f}:{(1280 - ch) * 0.30:.2f},scale=720:1280:flags=lanczos,setsar=1"]
    else:
        z = ["-vf", "setsar=1"]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{e['ini']:.4f}", "-i", f"{W}/proxy_720.mp4", *z, "-r", str(FPS),
                    "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", arq], check=True)
open(f"{W}/seg/lista.txt", "w").write("\n".join(lista))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{W}/seg/lista.txt", "-c", "copy",
                f"{W}/video_720.mp4"], check=True)
print("quadros esperados:", total, f"= {total / FPS:.3f}s")
