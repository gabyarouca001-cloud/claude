"""Stories v2 (revisão da editora): chegada -> fotógrafo -> produtos -> maquiagem -> final.
Sem congelados; velocidades variadas (câmera lenta com interpolação na DJI); logos reais; zoom rápido, espiral e brilho."""
import os
import subprocess

from montagem import FPS, H, HLG, W, final, mixar

LOGO = {"kiko": "logos/texto_kiko.png", "jc": "logos/texto_jc.png"}

# (arquivo, início na fonte, duração na timeline, velocidade, efeitos)
EDL = [
    # chegada (0–10.5 s)
    ("DJI_0265.MP4", 0.3, 2.0, 0.5, {"logo": "kiko"}),
    ("DJI_0266.MP4", 0.6, 2.0, 0.5, {"logo": "jc"}),
    ("IMG_1770.MOV", 1.7, 1.0, 1.2, {"zoomrapido": 1, "flash": 1}),
    ("IMG_1723.MOV", 3.0, 1.5, 0.5, {"brilho": 1, "zoom": 1}),
    ("DJI_0279.MP4", 0.8, 1.0, 1.0, {"flash": 1}),
    ("IMG_1729.MOV", 0.3, 1.0, 0.6, {"flash": 1}),
    ("IMG_1745.MOV", 0.5, 1.0, 0.8, {"espiral": 1, "flash": 1}),
    ("IMG_1744.MOV", 0.5, 1.0, 0.8, {"espiral": 1, "flash": 1}),
    # fotógrafo (10.5–16 s)
    ("DJI_0287.MP4", 0.0, 1.5, 1.0, {"flash": 1, "cliques": 3}),
    ("DJI_0289.MP4", 2.5, 1.0, 1.0, {"flash": 1, "cliques": 2}),
    ("DJI_0287.MP4", 5.8, 2.0, 0.6, {"flash": 1, "zoom": 1}),
    ("DJI_0287.MP4", 10.0, 1.0, 0.8, {"flash": 1, "cliques": 1}),
    # conhecendo os produtos (16–26 s)
    ("DJI_0273.MP4", 6.0, 2.0, 1.0, {"zoom": 1}),
    ("IMG_1722.MOV", 2.9, 2.0, 0.5, {"zoom": 1}),
    ("DJI_0296.MP4", 0.2, 1.5, 0.8, {"zoom": 1}),
    ("DJI_0295.MP4", 5.0, 1.5, 0.8, {"zoom": 1}),
    ("IMG_1721.MOV", 0.8, 1.5, 0.5, {}),
    ("IMG_1714.MOV", 3.3, 1.5, 0.7, {}),
    # bancada do maquiador, rápido (26–28 s)
    ("DJI_0278.MP4", 0.8, 0.5, 1.0, {"flash": 1}),
    ("IMG_1742.MOV", 0.4, 0.5, 1.5, {"flash": 1}),
    ("IMG_1738.MOV", 7.6, 0.5, 1.5, {"flash": 1}),
    ("IMG_1739.MOV", 10.4, 0.5, 1.5, {"flash": 1}),
    # maquiagem com o maquiador da marca (28–34 s)
    ("IMG_1734.MOV", 3.0, 1.5, 0.5, {"flash": 1}),
    ("IMG_1741.MOV", 0.2, 1.0, 0.6, {}),
    ("IMG_1733.MOV", 3.0, 1.0, 0.7, {}),
    ("IMG_1742.MOV", 3.2, 0.5, 1.0, {"flash": 1}),
    ("IMG_1740.MOV", 5.8, 1.0, 0.6, {}),
    ("IMG_1737.MOV", 1.4, 1.0, 0.8, {}),
    # final (34–37 s)
    ("DJI_0278.MP4", 10.3, 3.0, 0.6, {}),
]


def cadeia(arq, dur, vel, ef):
    iphone = arq.startswith("IMG")
    vf = (HLG if iphone else "format=yuv420p,") + f"scale={W}:{H}:flags=lanczos,setsar=1"
    if not iphone and vel < 1:
        # DJI a 30 fps: cria quadros intermediários para a câmera lenta ficar fluida
        vf += ",minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
    vf += f",setpts=(PTS-STARTPTS)/{vel},fps={FPS}"
    D = dur
    if ef.get("zoom"):
        n = int(D * FPS)
        vf += (f",scale={int(W * 1.12)}:{int(H * 1.12)},"
               f"zoompan=z='1+0.07*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}")
    if ef.get("brilho"):
        vf += ",format=gbrp,split[b1][b2];[b2]gblur=sigma=28[bg];[b1][bg]blend=all_mode=screen:all_opacity=0.30,format=yuv420p"
    if ef.get("zoomrapido"):
        vf += (f",scale=w='trunc({W}*(1+0.3*pow(t/{D},2))/2)*2':h='trunc({H}*(1+0.3*pow(t/{D},2))/2)*2':eval=frame,"
               f"crop={W}:{H},tmix=frames=6")
    if ef.get("espiral"):
        vf += (f",rotate=a='0.28*t/{D}':fillcolor=black,"
               f"scale=w='trunc({W}*(1.1+0.5*t/{D})/2)*2':h='trunc({H}*(1.1+0.5*t/{D})/2)*2':eval=frame,"
               f"crop={W}:{H},tmix=frames=2")
    if ef.get("flash"):
        vf += ",fade=t=in:st=0:d=0.13:color=white"
    return vf


def render_segmentos():
    os.makedirs("seg2", exist_ok=True)
    lista, eventos, t = [], [], 0.0
    for i, (arq, ini, dur, vel, ef) in enumerate(EDL):
        saida = f"seg2/{i:03d}.mp4"
        vf = cadeia(arq, dur, vel, ef)
        entradas = ["-ss", f"{ini:.3f}", "-t", f"{dur * vel + 0.25:.3f}", "-i", f"bruto/{arq}"]
        if "logo" in ef:
            entradas += ["-loop", "1", "-t", f"{dur:.3f}", "-i", LOGO[ef["logo"]]]
            fc = (f"[0:v]{vf}[v];[1:v]format=rgba,fade=t=in:st=0.2:d=0.4:alpha=1,"
                  f"fade=t=out:st={dur - 0.45:.2f}:d=0.4:alpha=1[l];[v][l]overlay=(W-w)/2:(H-h)/2-120:shortest=1")
            filtro = ["-filter_complex", fc]
        else:
            filtro = ["-vf", vf]
        subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, *filtro, "-t", f"{dur:.3f}", "-an",
                        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "14", "-pix_fmt", "yuv420p",
                        "-r", str(FPS), saida], check=True)
        lista.append(saida)
        if ef.get("flash"):
            eventos.append((t, "obturador"))
        for k in range(1, ef.get("cliques", 0)):
            eventos.append((t + k * dur / ef["cliques"], "obturador"))
        if ef.get("zoomrapido") or ef.get("espiral"):
            eventos.append((t, "flash_suave"))
        t += dur
        print(f"{i + 1}/{len(EDL)} {arq} -> {t:.2f}s", flush=True)
    open("seg2/lista.txt", "w").write("".join(f"file '{os.path.basename(s)}'\n" for s in lista))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "seg2/lista.txt",
                    "-c", "copy", "montado.mp4"], check=True)
    return eventos, t


if __name__ == "__main__":
    ev, total = render_segmentos()
    print(f"duração: {total:.2f}s")
    mixar(ev, total)
    final(total, "KIKO_JustCavalli_stories_v2.mp4")
