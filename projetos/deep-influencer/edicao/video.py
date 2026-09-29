"""Etapa 3: renderiza cada segmento mantido em 4K (com punch-in e correção da linha verde)."""
import json
import os
import subprocess

plano = json.load(open("plano.json"))
os.makedirs("seg", exist_ok=True)
lista = []
for i, s in enumerate(plano["segmentos"]):
    z = s["zoom"]
    # corta 8 px das bordas (remove a linha verde do topo) e aplica o zoom
    filtro = (f"crop=3824:2152:8:8,"
              f"crop=trunc(iw/{z}/2)*2:trunc(ih/{z}/2)*2:(iw-ow)/2:(ih-oh)*0.3,"
              f"scale=3840:2160:flags=lanczos,setsar=1,fps=25")
    saida = f"seg/{i:03d}.mp4"
    dur = s["fim"] - s["ini"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s['ini']:.3f}", "-i", "original.mp4",
                    "-t", f"{dur:.3f}", "-an", "-vf", filtro, "-c:v", "libx264", "-preset", "ultrafast",
                    "-crf", "13", "-pix_fmt", "yuv420p", "-g", "50", "-color_primaries", "bt709",
                    "-color_trc", "bt709", "-colorspace", "bt709", saida], check=True)
    lista.append(f"file '{saida}'")
    print(f"{i + 1}/{len(plano['segmentos'])} {s['ini']:.2f}-{s['fim']:.2f} zoom {z}", flush=True)
open("seg/lista.txt", "w").write("\n".join(lista) + "\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "seg/lista.txt",
                "-c", "copy", "video_cortado.mp4"], check=True)
print("FIM video")
