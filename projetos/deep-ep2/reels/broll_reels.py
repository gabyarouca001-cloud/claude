"""Reels v3: inserções de banco de imagem (Mixkit, licença livre), sem áudio, em tela cheia 9:16,
com zoom lento. Cada entrada leva um clique de câmera (no final_reels_v3.py)."""
import json
import os
import re
import subprocess
import unicodedata

OFF = 9.8
K4 = os.environ.get("K4") == "1"
LW, LH = (2160, 3840) if K4 else (1080, 1920)
PASTA = "broll_v3_4k" if K4 else "broll_v3"
BROLL = "/home/user/work/broll"
# (frase falada, vídeo, duração, centro horizontal do recorte 0-1, início no clipe)
INSERCOES = [
    ("substacks", "4950", 1.2, 0.5, 2.0),
    ("podcasts", "2951", 1.3, 0.72, 3.0),
    ("acompanhar uma ideia", "42741", 2.2, 0.47, 2.0),
    ("consumindo um pouco", "4919", 2.2, 0.42, 1.0),
    ("encontrar referências", "42655", 2.2, 0.55, 1.5),
    ("num podcast num texto", "44049", 1.1, 0.5, 2.0),
    ("num texto", "50731", 0.7, 0.6, 3.0),
    ("numa comunidade", "41813", 1.4, 0.45, 1.0),
    ("4 milhões", "50406", 2.4, 0.27, 1.0),
    ("programas produtos", "28723", 2.4, 0.45, 1.0),
    ("newsletter", "206", 2.2, 0.62, 0.5),
    ("num e mail", "1787", 2.0, 0.38, 2.0),
    ("pelo conhecimento", "43266", 2.4, 0.38, 2.0),
    ("disputando a nossa", "39780", 2.2, 0.38, 3.0),
]


def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if unicodedata.category(c) != "Mn"))


W = [w for s in json.load(open("final_reels.json")) for w in s["words"]]
T = [norm(w["w"]) for w in W]


def achar(frase):
    a = [norm(p) for p in frase.split()]
    return [W[i]["s"] for i in range(len(W)) if T[i:i + len(a)] == a][0]


os.makedirs(PASTA, exist_ok=True)
lista = []
for n, (frase, vid, dur, cx, ss) in enumerate(INSERCOES):
    t = round((OFF + achar(frase) - 0.08) * 30) / 30
    if lista and t < lista[-1]["fim"]:            # sequência rápida: emenda no anterior
        t = lista[-1]["fim"]
    lista.append(dict(t=t, fim=round(t + dur, 3), vid=vid, arq=f"{PASTA}/{n:02d}.mp4"))
    vf = (f"scale=-2:{LH}:flags=lanczos,crop={LW}:{LH}:'min(max(iw*{cx}-{LW // 2},0),iw-{LW})':0,"
          f"scale=w='{LW}*(1+0.05*t/{dur})':h=-2:eval=frame:flags=bicubic,crop={LW}:{LH},fps=30,setsar=1")
    if vid == "4950":                               # já é vertical
        vf = (f"scale={LW}:{LH}:flags=lanczos,scale=w='{LW}*(1+0.05*t/{dur})':h=-2:eval=frame:flags=bicubic,"
              f"crop={LW}:{LH},fps=30,setsar=1")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-i", f"{BROLL}/v_{vid}.mp4", "-t", str(dur), "-an",
                    "-vf", vf, "-frames:v", str(round(dur * 30)), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                    "-pix_fmt", "yuv420p", lista[-1]["arq"]], check=True)
    print(f"{t:7.2f}  {frase:24s} {vid}")
json.dump(lista, open(PASTA + ".json", "w"), indent=1)
