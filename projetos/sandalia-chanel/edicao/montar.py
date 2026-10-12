"""Sobrepõe os cartões animados (WebM com alpha, um por cartão) ao vídeo da editora.
Uso: python3 montar.py original.mp4 hf_cards/ saida.mp4 previa|4k
  previa: 720x1280, H.264 2 passes (< 28 MB), áudio AAC 96k  (aprovação no chat, limite 30 MB)
  4k:     2160x3840 (cartões renderizados com --escala 2), CRF 19 preset faster, áudio original copiado, +faststart
O vídeo base NÃO é alterado (cortes, cor, legendas e inserções dela ficam como estão); só entram os cartões por cima."""
import json
import subprocess
import sys
from pathlib import Path

base, pasta, saida, modo = sys.argv[1:5]
pasta = Path(pasta)
man = json.load(open(pasta / "manifesto.json"))
W, H = (720, 1280) if modo == "previa" else (2160, 3840)

dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", base],
                           capture_output=True, text=True).stdout)
entradas, filtros = ["-i", base], [f"[0:v]scale={W}:{H}:flags=lanczos,format=yuv420p[b0]"]
for i, m in enumerate(man, 1):
    arq = pasta / m["dir"] / "cartao.webm"
    entradas += ["-c:v", "libvpx-vp9", "-i", str(arq)]
    filtros.append(f"[{i}:v]scale={W}:{H}:flags=lanczos,format=yuva420p,setpts=PTS-STARTPTS+{m['ini']}/TB[o{i}]")
    filtros.append(f"[b{i - 1}][o{i}]overlay=0:0:eof_action=pass:format=auto[b{i}]")
fc = ";".join(filtros)
ult = f"[b{len(man)}]"

if modo == "previa":
    kbps = int((27.5e6 * 8 - 96e3 * dur) / dur / 1000) - 20
    comum = ["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", fc, "-map", ult, "-an", "-c:v", "libx264", "-preset", "medium",
             "-b:v", f"{kbps}k", "-pix_fmt", "yuv420p", "-r", "30"]
    subprocess.run([*comum, "-pass", "1", "-passlogfile", str(pasta / "x264"), "-f", "null", "/dev/null"], check=True)
    subprocess.run([*comum, "-pass", "2", "-passlogfile", str(pasta / "x264"), str(pasta / "_video.mp4")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pasta / "_video.mp4"), "-i", base, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", saida], check=True)
else:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, "-i", base, "-filter_complex", fc, "-map", ult, "-map", f"{len(man) + 1}:a",
                    "-c:v", "libx264", "-preset", "faster", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "copy",
                    "-movflags", "+faststart", saida], check=True)
print(saida, round(Path(saida).stat().st_size / 1e6, 1), "MB")
