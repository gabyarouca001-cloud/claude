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
    extra = f"_d{abs(hash(s['zexpr'] + str(s['rosto']))) % 10**8}" if s.get("zexpr") else ""
    return f"{s['fonte']}_{s['ini']:.3f}_{s['fim']:.3f}_{s['zoom']}{extra}"


def render(s):
    saida = f"{PASTA}/{chave(s)}.mp4"
    if os.path.exists(saida):
        return saida
    z = s["zoom"]
    vf = "fps=30,"
    if s.get("zexpr"):
        vf += s["zexpr"]
    elif z != 1.0:
        # punch-in levemente acima do centro (mantém o rosto no terço superior)
        vf += f"crop=trunc(iw/{z}/2)*2:trunc(ih/{z}/2)*2:(iw-ow)/2:(ih-oh)*0.35,"
    if not s.get("zexpr"):
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
    if os.path.exists(f"dinamica_{versao}.json") and os.path.exists(f"rosto_{versao}.json"):
        from dinamica import filtro
        import numpy as np
        din = json.load(open(f"dinamica_{versao}.json"))
        rost = json.load(open(f"rosto_{versao}.json"))
        fy_take = {f: float(np.median([r[1] for s, r in zip(segs, rost) if s["fonte"] == f]))
                   for f in {s["fonte"] for s in segs}}
        camb = []
        for a, b in din["camb"]:
            rs = [r for s, r in zip(segs, rost) if s["t"] < b and s["t"] + s["fim"] - s["ini"] > a]
            camb.append((a, b, float(np.mean([r[0] for r in rs])), float(np.mean([r[1] for r in rs]))))
        din["camb"] = camb
        for s in segs:
            r = (0.5, fy_take[s["fonte"]])
            s["zexpr"], s["rosto"] = filtro(s, r, din, LARG, ALT), r
    lista = []
    for i, s in enumerate(segs):
        lista.append(f"file '{os.path.basename(render(s))}'")
        if i % 20 == 0:
            print(f"{versao} {i + 1}/{len(segs)}", flush=True)
    open(f"{PASTA}/lista_{versao}.txt", "w").write("\n".join(lista) + "\n")
    print("FIM", versao, flush=True)
