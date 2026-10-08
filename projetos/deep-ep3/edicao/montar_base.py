"""Base de vídeo 720x1280 com contagem EXATA de quadros por corte (a 1ª versão ganhava 1 quadro em vários cortes
e o vídeo foi se adiantando em relação ao áudio: 1,5 s no fim).  Gera /home/user/work/ep3/video_720.mp4."""
import json
import os
import shutil
import subprocess

W = "/home/user/work/ep3"
K4 = os.environ.get("K4") == "1"
FPS, ZOOM = 30, 1.12
SEG = f"{W}/seg4k" if K4 else f"{W}/seg"
SAIDA = f"{W}/video_4k.mp4" if K4 else f"{W}/video_720.mp4"
edl = json.load(open("edl.json"))["edl"]
import hashlib
h = hashlib.md5(open("edl.json", "rb").read()).hexdigest()
if not K4 or not os.path.exists(f"{SEG}/edl.md5") or open(f"{SEG}/edl.md5").read() != h:   # plano mudou: não reaproveita cortes velhos
    shutil.rmtree(SEG, ignore_errors=True)
os.makedirs(SEG, exist_ok=True)
open(f"{SEG}/edl.md5", "w").write(h)
zoom, lista, total = False, [], 0
for i, e in enumerate(edl):
    if i > 0 and e["junta"] == "retake":
        zoom = not zoom
    n = round((e["fim"] - e["ini"]) * FPS)
    total += n
    arq = f"{SEG}/s{i:03d}.mp4"
    if os.path.exists(arq) and os.path.getsize(arq) > 1000:      # retoma de onde parou
        lista.append(f"file '{arq}'"); continue
    lista.append(f"file '{arq}'")
    if K4:       # original 2160x3840: tira 8 px das bordas (linha preta do export) e volta a 2160x3840
        if zoom:
            cw, ch = 2144 / ZOOM, 3824 / ZOOM
            z = ["-vf", f"crop={cw:.2f}:{ch:.2f}:{8 + (2144 - cw) / 2:.2f}:{8 + (3824 - ch) * 0.30:.2f},scale=2160:3840:flags=lanczos,setsar=1"]
        else:
            z = ["-vf", "crop=2144:3824:8:8,scale=2160:3840:flags=lanczos,setsar=1"]
        fonte, crf = f"{W}/original.mp4", "14"
    else:
        if zoom:
            cw, ch = 720 / ZOOM, 1280 / ZOOM
            z = ["-vf", f"crop={cw:.2f}:{ch:.2f}:{(720 - cw) / 2:.2f}:{(1280 - ch) * 0.30:.2f},scale=720:1280:flags=lanczos,setsar=1"]
        else:
            z = ["-vf", "setsar=1"]
        fonte, crf = f"{W}/proxy_720.mp4", "14"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{e['ini']:.4f}", "-i", fonte, *z, "-r", str(FPS),
                    "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", crf, "-pix_fmt", "yuv420p", arq], check=True)
open(f"{SEG}/lista.txt", "w").write("\n".join(lista))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{SEG}/lista.txt", "-c", "copy",
                SAIDA], check=True)
print("quadros esperados:", total, f"= {total / FPS:.3f}s")
