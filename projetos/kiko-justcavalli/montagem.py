"""Stories editorial Just Cavalli x KIKO MILANO: cortes no tempo da trilha (120 BPM), flashes e congelados."""
import os
import subprocess
import sys

import numpy as np

W, H, FPS = 1080, 1920, 30
HLG = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
       "zscale=t=bt709:m=bt709:r=tv,format=yuv420p,")

# (arquivo, início na fonte, duração na timeline, velocidade, efeito)
# efeitos: flash = entra com flash branco | zoom = aproximação lenta | congela = foto congelada em seguida
EDL = [
    # 0–4 s: chegada (intro)
    ("DJI_0265.MP4", 0.3, 1.0, 1.0, "zoom"),
    ("DJI_0266.MP4", 0.6, 1.5, 1.0, "flash"),
    ("IMG_1743.MOV", 1.6, 0.75, 1.0, "flash"),
    ("IMG_1723.MOV", 3.2, 0.75, 1.0, "flash"),
    # 4–12 s: montagem rápida (drop)
    ("DJI_0279.MP4", 0.8, 1.0, 1.0, "flash"),
    ("IMG_1729.MOV", 0.3, 0.5, 1.0, "flash"),
    ("IMG_1727.MOV", 2.0, 0.5, 1.0, "flash"),
    ("DJI_0287.MP4", 5.6, 1.0, 1.0, "flash"),
    ("DJI_0289.MP4", 2.0, 0.5, 1.0, "flash"),
    ("DJI_0278.MP4", 0.8, 0.5, 1.0, "flash"),
    ("DJI_0268.MP4", 5.6, 0.5, 1.0, "flash"),
    ("IMG_1745.MOV", 0.8, 0.5, 1.0, "flash"),
    ("DJI_0282.MP4", 0.2, 0.5, 1.0, "flash"),
    ("IMG_1725.MOV", 1.4, 0.5, 1.0, "flash"),
    ("DJI_0304.MP4", 3.4, 0.5, 1.0, "flash"),
    ("DJI_0278.MP4", 10.9, 1.0, 1.0, "flash"),
    ("IMG_1744.MOV", 0.8, 0.5, 1.0, "flash"),
    # 12–26 s: a coleção (takes longos, câmera lenta)
    ("IMG_1742.MOV", 0.4, 2.0, 0.5, "zoom"),
    ("DJI_0273.MP4", 6.0, 2.0, 1.0, "zoom"),
    ("IMG_1722.MOV", 2.9, 2.0, 0.5, "zoom"),
    ("DJI_0296.MP4", 0.2, 2.0, 1.0, "zoom"),
    ("DJI_0302.MP4", 0.2, 2.0, 1.0, "zoom"),
    ("DJI_0295.MP4", 5.0, 2.0, 1.0, "zoom"),
    ("IMG_1741.MOV", 0.2, 2.0, 0.5, "zoom"),
    # 26–28 s: subida
    ("IMG_1739.MOV", 10.4, 1.0, 0.5, "flash"),
    ("IMG_1738.MOV", 7.6, 0.5, 1.0, "flash"),
    ("IMG_1742.MOV", 3.2, 0.5, 1.0, "flash"),
    # 28–34 s: clímax com fotos congeladas
    ("IMG_1721.MOV", 1.0, 0.5, 1.0, "congela"),
    ("IMG_1740.MOV", 5.8, 0.5, 1.0, "congela"),
    ("DJI_0287.MP4", 9.8, 0.5, 1.0, "congela"),
    ("IMG_1733.MOV", 3.0, 0.5, 1.0, "flash"),
    ("IMG_1767.MOV", 7.4, 0.5, 1.0, "flash"),
    ("DJI_0291.MP4", 3.8, 0.5, 1.0, "flash"),
    ("IMG_1726.MOV", 0.5, 0.5, 1.0, "flash"),
    ("IMG_1714.MOV", 3.3, 1.0, 1.0, "flash"),
    # 34–37 s: logo da colab
    ("IMG_1770.MOV", 4.6, 3.0, 1.0, "zoom"),
]
CONGELA = 0.5

GRADE = ("eq=contrast=1.07:saturation=1.12:gamma=0.98,"
         "colorbalance=rs=0.03:gs=0.0:bs=-0.03:rh=0.02:bh=-0.02,vignette=PI/5")


def base(arq):
    return (HLG if arq.startswith("IMG") else "format=yuv420p,") + f"scale={W}:{H}:flags=lanczos,setsar=1"


def render_segmentos():
    os.makedirs("seg", exist_ok=True)
    lista, eventos, t = [], [], 0.0
    for i, (arq, ini, dur, vel, efeito) in enumerate(EDL):
        saida = f"seg/{i:03d}.mp4"
        dur_fonte = dur * vel
        vf = base(arq) + f",setpts=(PTS-STARTPTS)/{vel},fps={FPS}"
        if efeito == "zoom":
            n = int(dur * FPS)
            vf += (f",scale={int(W * 1.12)}:{int(H * 1.12)},"
                   f"zoompan=z='1+0.07*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}")
        if efeito in ("flash", "congela"):
            vf += ",fade=t=in:st=0:d=0.13:color=white"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ini:.3f}", "-t", f"{dur_fonte + 0.2:.3f}",
                        "-i", f"bruto/{arq}", "-vf", vf, "-t", f"{dur:.3f}", "-an", "-c:v", "libx264",
                        "-preset", "ultrafast", "-crf", "14", "-pix_fmt", "yuv420p", "-r", str(FPS), saida],
                       check=True)
        lista.append(saida)
        eventos.append((t, "obturador" if efeito != "zoom" else "flash_suave"))
        t += dur
        if efeito == "congela":
            # último quadro vira "foto": moldura branca sobre o fundo desfocado e escurecido
            foto = f"seg/{i:03d}_foto.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{dur - 0.07:.3f}", "-i", saida, "-frames:v", "1",
                            f"seg/{i:03d}.png"], check=True)
            fc = (f"[0:v]split[a][b];[a]gblur=sigma=30,eq=brightness=-0.25[fundo];"
                  f"[b]scale={int(W * 0.8)}:-2,pad=iw+36:ih+36:18:18:white,"
                  f"rotate=-2*PI/180:c=none:ow=rotw(-2*PI/180):oh=roth(-2*PI/180)[q];"
                  f"[fundo][q]overlay=(W-w)/2:(H-h)/2,fade=t=in:st=0:d=0.1:color=white,format=yuv420p")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", f"{CONGELA}", "-framerate", str(FPS),
                            "-i", f"seg/{i:03d}.png", "-filter_complex", fc, "-c:v", "libx264", "-preset",
                            "ultrafast", "-crf", "14", "-r", str(FPS), foto], check=True)
            lista.append(foto)
            eventos.append((t, "foto"))
            t += CONGELA
        print(f"{i + 1}/{len(EDL)} {arq} -> {t:.2f}s", flush=True)
    open("seg/lista.txt", "w").write("".join(f"file '{os.path.basename(s)}'\n" for s in lista))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "seg/lista.txt",
                    "-c", "copy", "montado.mp4"], check=True)
    return eventos, t


def ler_wav(nome, sr=48000):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", nome, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32).reshape(-1, 2).copy()


def mixar(eventos, total, sr=48000):
    y = ler_wav("trilha.wav")[:int(total * sr)]
    ob, fl = ler_wav("obturador.wav"), ler_wav("flash.wav")
    # burburinho do evento bem baixo por baixo
    amb = subprocess.run(["ffmpeg", "-v", "error", "-ss", "6", "-t", f"{total}", "-i", "bruto/DJI_0271.MP4",
                          "-af", "lowpass=f=3500,highpass=f=150", "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    amb = np.frombuffer(amb, np.float32).reshape(-1, 2)[:len(y)]
    amb = amb / (np.abs(amb).max() + 1e-9) * 10 ** (-27 / 20)
    y[:len(amb)] += amb
    for t, tipo in eventos:
        i = int(t * sr)
        for som, g in ((ob, 0.35),) if tipo == "obturador" else ((fl, 0.12), (ob, 0.45)) if tipo == "foto" \
                else ((fl, 0.06),):
            if tipo == "foto":
                j = max(0, i - len(fl) + int(0.05 * sr)) if som is fl else i
            else:
                j = i
            k = min(len(y), j + len(som))
            y[j:k] += som[:k - j] * g
    n = int(0.8 * sr)
    y[-n:] *= np.linspace(1, 0, n)[:, None]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "2", "-i", "-",
                    "mix.wav"], input=y.astype(np.float32).tobytes(), check=True)


def final(total, saida="KIKO_JustCavalli_stories.mp4"):
    vf = (f"[0:v]{GRADE},noise=alls=7:allf=t,ass=textos.ass:fontsdir=fontes,"
          f"fade=t=in:st=0:d=0.3,fade=t=out:st={total - 0.8:.2f}:d=0.8,format=yuv420p[v];"
          f"[1:a]loudnorm=I=-14:TP=-1.5:LRA=9[a]")
    kbps = int(28.5 * 8 * 1024 * 1024 / total / 1000) - 200
    comum = ["-i", "montado.mp4", "-i", "mix.wav", "-filter_complex", vf, "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-preset", "slow", "-b:v", f"{kbps}k", "-pix_fmt", "yuv420p", "-r", str(FPS),
             "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *comum, "-pass", "1", "-passlogfile", "p", "-an", "-f", "mp4",
                    "/dev/null"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", *comum, "-pass", "2", "-passlogfile", "p", "-c:a", "aac",
                    "-b:a", "192k", "-movflags", "+faststart", saida], check=True)
    print("OK", saida, f"{os.path.getsize(saida) / 1e6:.1f} MB")


if __name__ == "__main__":
    ev, total = render_segmentos()
    print(f"duração: {total:.2f}s")
    mixar(ev, total)
    if "--sem-final" not in sys.argv:
        final(total)
