"""Segmentos 9:16 (1080x1920) recortados do 4K, centrados nela; punch-in de 12% alternado nos retakes."""
import json
import os
import subprocess

# material vertical centralizado pela editora (9:16, 2160x3840); take 1 começa 16,0 s depois do original
FONTES = {"take1": "ig/take1.mp4", "take2": "ig/take2.mp4", "take3": "ig/take3.mp4"}
DESLOC = {"take1": -16.0, "take2": 0.0, "take3": 0.0}

os.makedirs("seg_reels", exist_ok=True)
for f in os.listdir("seg_reels"):
    if f.endswith(".mp4"):
        os.remove(os.path.join("seg_reels", f))
plano = json.load(open("plano_reels.json"))["segmentos"]
cx = json.load(open("centros_reels.json"))["segmentos"]


def crop_vertical(z):
    if z == 1.0:
        return "scale=1080:1920:flags=lanczos,setsar=1"
    return (f"crop=trunc(iw/{z}/2)*2:trunc(ih/{z}/2)*2:(iw-ow)/2:(ih-oh)*0.35,"
            "scale=1080:1920:flags=lanczos,setsar=1")


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
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s['ini'] + DESLOC[s['fonte']]:.3f}", "-i", FONTES[s["fonte"]],
                    "-t", f"{dur:.3f}", "-an", "-vf", "fps=30," + crop_vertical(s["zoom"]), "-frames:v", str(round(dur * 30)),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    saida + ".tmp.mp4"], check=True)
    os.replace(saida + ".tmp.mp4", saida)
    if i % 20 == 0:
        print(i, "/", len(plano), flush=True)
open("seg_reels/lista.txt", "w").write("\n".join(lista) + "\n")

print("FIM")
