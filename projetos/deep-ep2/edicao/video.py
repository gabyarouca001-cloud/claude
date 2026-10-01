"""Renderiza os segmentos em 4K (punch-in quando zoom > 1) e junta cada versão. Segmentos iguais entre
YouTube e Instagram são reaproveitados (cache por fonte/início/fim/zoom)."""
import json
import os
import subprocess
import sys

from audio import FONTES

# PREVIA=1: segmentos 1280x720 (rápido) para a prévia de aprovação; senão 4K para o final
PREVIA = os.environ.get("PREVIA") == "1"
PASTA, LARG, ALT = ("seg720", 1280, 720) if PREVIA else ("seg", 3840, 2160)
os.makedirs(PASTA, exist_ok=True)


def chave(s):
    return f"{s['fonte']}_{s['ini']:.3f}_{s['fim']:.3f}_{s['zoom']}"


def render(s):
    saida = f"{PASTA}/{chave(s)}.mp4"
    if os.path.exists(saida):
        return saida
    z = s["zoom"]
    vf = "fps=30,"
    if z != 1.0:
        # punch-in levemente acima do centro (mantém o rosto no terço superior)
        vf += f"crop=trunc(iw/{z}/2)*2:trunc(ih/{z}/2)*2:(iw-ow)/2:(ih-oh)*0.35,"
    vf += f"scale={LARG}:{ALT}:flags=lanczos,setsar=1"
    dur = s["fim"] - s["ini"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s['ini']:.3f}", "-i", FONTES[s["fonte"]],
                    "-t", f"{dur:.3f}", "-an", "-vf", vf, "-frames:v", str(round(dur * 30)),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18" if PREVIA else "16", "-pix_fmt", "yuv420p", "-g", "60",
                    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    saida + ".tmp.mp4"], check=True)
    os.replace(saida + ".tmp.mp4", saida)
    return saida


for versao in sys.argv[1:] or ["youtube", "instagram"]:
    segs = json.load(open(f"plano_{versao}.json"))["segmentos"]
    lista = []
    for i, s in enumerate(segs):
        lista.append(f"file '{os.path.basename(render(s))}'")
        if i % 20 == 0:
            print(f"{versao} {i + 1}/{len(segs)}", flush=True)
    open(f"{PASTA}/lista_{versao}.txt", "w").write("\n".join(lista) + "\n")
    print("FIM", versao, flush=True)
