"""Etapa 5: junta vídeo cortado + gráfico + textos + áudio final e exporta YouTube (4K) e Instagram."""
import json
import subprocess
import sys

info = json.load(open("insercoes.json"))
g = info["grafico"]
dur = sum(s["fim"] - s["ini"] for s in json.load(open("plano.json"))["segmentos"])

AUDIO = "volume=-2.1dB,alimiter=limit=0.84:attack=3:release=80:level=disabled"
X264 = ["-c:v", "libx264", "-preset", "faster", "-crf", "19", "-pix_fmt", "yuv420p", "-g", "50",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000"]


def render(saida, fim, fade=0.6):
    filtro = (f"[1:v]scale=1290:-1,format=rgba[gr];"
              f"[0:v][gr]overlay=160:520:eof_action=pass,"
              f"ass=insercoes.ass:fontsdir=fonts,"
              f"fade=t=out:st={fim - fade:.2f}:d={fade}[v];"
              f"[2:a]{AUDIO},afade=t=out:st={fim - fade:.2f}:d={fade}[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-stats", "-y",
                    "-i", "video_cortado.mp4",
                    "-itsoffset", f"{g['ini']:.2f}", "-framerate", "25", "-i", "grafico/%04d.png",
                    "-i", "mix.wav",
                    "-filter_complex", filtro, "-map", "[v]", "-map", "[a]", "-t", f"{fim:.2f}",
                    *X264, saida], check=True)
    print("OK", saida, flush=True)


if "youtube" in sys.argv:
    render("DEEP_youtube_4K.mp4", dur)
if "instagram" in sys.argv:
    render("DEEP_instagram_4K.mp4", 284.04, fade=0.5)
