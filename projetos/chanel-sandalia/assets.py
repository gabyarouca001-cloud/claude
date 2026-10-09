"""Prepara as mídias das inserções na resolução do render: S=1 (prévia 1080x1920) ou S=2 (final 2160x3840).
Tela cheia: foto com zoom lento (Ken Burns) ou vídeo de banco recortado em 9:16, sem áudio. Polaroid: PNG com borda branca,
leve rotação e sombra. Saída em ov_<S>/ + ov_<S>.json (lista para o render)."""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

import edl

S = int(os.environ.get("S", "1"))
W, H = 1080 * S, 1920 * S
PASTA = f"ov_{S}"
os.makedirs(PASTA, exist_ok=True)


def recorte_916(img, foco, escala_zoom=1.0):
    """recorta a janela 9:16 mais larga possível, centrada no foco (fração x,y da foto)"""
    w, h = img.size
    cw = min(w, int(h * 9 / 16))
    ch = int(cw * 16 / 9)
    if ch > h:
        ch = h
        cw = int(ch * 9 / 16)
    cx, cy = foco[0] * w, foco[1] * h
    x0 = int(min(max(cx - cw / 2, 0), w - cw))
    y0 = int(min(max(cy - ch / 2, 0), h - ch))
    return img.crop((x0, y0, x0 + cw, y0 + ch))


def foto_kb(e):
    img = ImageOps.exif_transpose(Image.open(e["arq"])).convert("RGB")
    if e["par"][0] == "contain":      # foto inteira na largura, sobre ela mesma desfocada e escurecida
        fundo = recorte_916(img, (0.5, 0.5)).resize((W * 2, H * 2), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40 * S))
        fundo = Image.eval(fundo, lambda v: int(v * 0.45))
        fr = img.resize((W * 2, int(img.height * W * 2 / img.width)), Image.LANCZOS)
        fundo.paste(fr, (0, (H * 2 - fr.height) // 2))
        img = fundo
    else:
        img = recorte_916(img, e["par"])
        img = img.resize((W * 2, H * 2), Image.LANCZOS)
    tmp = f"{PASTA}/{e['nome']}_base.png"
    img.save(tmp)
    n = round(e["dur"] * 30)
    saida = f"{PASTA}/{e['nome']}.mp4"
    zp = f"zoompan=z='1+0.07*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps=30"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", tmp, "-vf", zp + ",setsar=1,format=yuv420p", "-frames:v", str(n),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", saida], check=True)
    os.remove(tmp)
    return saida


def clip_banco(e):
    ss, cx = e["par"]
    n = round(e["dur"] * 30)
    saida = f"{PASTA}/{e['nome']}.mp4"
    info = subprocess.run(["ffmpeg", "-hide_banner", "-i", e["arq"]], capture_output=True, text=True).stderr
    import re
    m = re.search(r"Video:.* (\d{3,5})x(\d{3,5})", info)
    vw, vh = int(m.group(1)), int(m.group(2))
    if vh >= vw:        # já vertical
        vf = f"scale={W}:{H}:flags=lanczos"
    else:
        vf = f"scale=-2:{H}:flags=lanczos,crop={W}:{H}:'min(max(iw*0.5-{W // 2},0),iw-{W})':0"
    vf += f",scale=w='{W}*(1+0.05*t/{e['dur']})':h=-2:eval=frame:flags=bicubic,crop={W}:{H},fps=30,setsar=1,format=yuv420p"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-i", e["arq"], "-t", str(e["dur"]), "-an", "-vf", vf,
                    "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", saida], check=True)
    return saida


def polaroid(e):
    img = ImageOps.exif_transpose(Image.open(e["arq"])).convert("RGB")
    w, h = img.size
    if h >= w:                                 # retrato 3:4
        cw, ch = w, int(w * 4 / 3)
        if ch > h:
            ch, cw = h, int(h * 3 / 4)
        larg = 360 * S
    else:                                      # paisagem 4:3
        ch, cw = h, int(h * 4 / 3)
        if cw > w:
            cw, ch = w, int(w * 3 / 4)
        larg = 420 * S
    x0 = int(min(max(e["foco"][0] * w - cw / 2, 0), w - cw))
    y0 = int(min(max(e["foco"][1] * h - ch / 2, 0), h - ch))
    img = img.crop((x0, y0, x0 + cw, y0 + ch)).resize((larg, int(larg * ch / cw)), Image.LANCZOS)
    b, bb = 14 * S, 46 * S
    card = Image.new("RGBA", (img.width + 2 * b, img.height + b + bb), (250, 248, 244, 255))
    card.paste(img, (b, b))
    pad = 60 * S
    base = Image.new("RGBA", (card.width + 2 * pad, card.height + 2 * pad), (0, 0, 0, 0))
    sombra = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rectangle((pad + 6 * S, pad + 10 * S, pad + card.width + 6 * S, pad + card.height + 10 * S), fill=(0, 0, 0, 120))
    sombra = sombra.filter(ImageFilter.GaussianBlur(14 * S))
    base.alpha_composite(sombra)
    base.alpha_composite(card, (pad, pad))
    base = base.rotate(e["ang"], resample=Image.BICUBIC, expand=True)
    x = 14 * S - pad // 2 if e["lado"] == "esq" else W - base.width + pad // 2 - 14 * S
    y = 900 * S - base.height + pad // 2   # mais alto: acima do peito, sem cobrir o rosto
    saida = f"{PASTA}/{e['nome']}.png"
    base.save(saida)
    return saida, x, y, base.width, base.height, card.width, card.height, bb


if __name__ == "__main__":
    ev = edl.resolver()
    lista = {"full": [], "pol": []}
    for e in ev["full"]:
        arq = foto_kb(e) if e["tipo"] == "foto" else clip_banco(e)
        lista["full"].append(dict(nome=e["nome"], arq=arq, t=e["t"], fim=e["fim"], rot=e["rot"], tipo=e["tipo"]))
        print("full", e["nome"], arq, flush=True)
    for e in ev["pol"]:
        arq, x, y, w, h, cw, ch, bb = polaroid(e)
        lista["pol"].append(dict(nome=e["nome"], arq=arq, t=e["t"], fim=e["fim"], x=x, y=y, w=w, h=h, cw=cw, ch=ch, bb=bb, ang=e["ang"], rot=e["rot"], lado=e["lado"]))
        print("pol", e["nome"], arq, x, y, flush=True)
    json.dump(lista, open(PASTA + ".json", "w"), indent=1)
