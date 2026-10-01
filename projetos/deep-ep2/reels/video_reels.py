"""Segmentos 9:16 (1080x1920) recortados do 4K, centrados nela; punch-in de 12% alternado nos retakes."""
import json
import os
import subprocess

from audio import FONTES

os.makedirs("seg_reels", exist_ok=True)
plano = json.load(open("plano_reels.json"))["segmentos"]
cx = json.load(open("centros_reels.json"))["segmentos"]


def crop(z, c):
    h = 2160 / z
    w = h * 9 / 16
    x = min(max(c * 3840 - w / 2, 0), 3840 - w)
    y = (2160 - h) * 0.35
    return f"crop={int(w) // 2 * 2}:{int(h) // 2 * 2}:{int(x)}:{int(y)},scale=1080:1920:flags=lanczos,setsar=1"


lista = []
for i, s in enumerate(plano):
    saida = f"seg_reels/{i:03d}.mp4"
    lista.append(f"file '{i:03d}.mp4'")
    if os.path.exists(saida):
        continue
    dur = s["fim"] - s["ini"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s['ini']:.3f}", "-i", FONTES[s["fonte"]], "-t", f"{dur:.3f}",
                    "-an", "-vf", "fps=30," + crop(s["zoom"], cx[str(i)]), "-frames:v", str(round(dur * 30)),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    saida + ".tmp.mp4"], check=True)
    os.replace(saida + ".tmp.mp4", saida)
    if i % 20 == 0:
        print(i, "/", len(plano), flush=True)
open("seg_reels/lista.txt", "w").write("\n".join(lista) + "\n")

# abertura da editora: recorte nela; "Vamo de Deep?" (7,00–8,03 s) com o quadro 16:9 inteiro sobre fundo desfocado
ab = json.load(open("centros_reels.json"))["abertura"]
c0 = ab["0"]
fc = (f"[0:v]split=3[a][b][c];"
      f"[a]trim=0:7.0,setpts=PTS-STARTPTS,{crop(1.0, c0)}[p1];"
      f"[b]trim=7.0:8.0333,setpts=PTS-STARTPTS,split[b1][b2];"
      f"[b1]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=40,eq=brightness=-0.06[fundo];"
      f"[b2]scale=1080:-2[frente];[fundo][frente]overlay=0:(H-h)/2,setsar=1[p2];"
      f"[c]trim=8.0333,setpts=PTS-STARTPTS,{crop(1.0, 0.5)}[p3];"
      f"[p1][p2][p3]concat=n=3:v=1:a=0,fps=30[v]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "inicio_editora.mp4", "-filter_complex", fc, "-map", "[v]",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", "abertura_reels.mp4"], check=True)
print("FIM")
