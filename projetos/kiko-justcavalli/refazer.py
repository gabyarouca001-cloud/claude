"""Refaz só alguns segmentos da v2 e remonta (sem re-renderizar o resto)."""
import subprocess, sys
import montagem_v2 as m
from montagem import mixar, final

idx = [int(x) for x in sys.argv[1:]]
for i in idx:
    arq, ini, dur, vel, ef = m.EDL[i]
    vf = m.cadeia(arq, dur, vel, ef)
    entradas = ["-ss", f"{ini:.3f}", "-t", f"{dur * vel + 0.25:.3f}", "-i", f"bruto/{arq}"]
    if "logo" in ef:
        entradas += ["-loop", "1", "-t", f"{dur:.3f}", "-i", m.LOGO[ef["logo"]]]
        fc = (f"[0:v]{vf}[v];[1:v]format=rgba,fade=t=in:st=0.2:d=0.4:alpha=1,"
              f"fade=t=out:st={dur - 0.45:.2f}:d=0.4:alpha=1[l];[v][l]overlay=(W-w)/2:(H-h)/2-120:shortest=1")
        filtro = ["-filter_complex", fc]
    else:
        filtro = ["-vf", vf]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, *filtro, "-t", f"{dur:.3f}", "-an", "-c:v", "libx264",
                    "-preset", "ultrafast", "-crf", "14", "-pix_fmt", "yuv420p", "-r", str(m.FPS), f"seg2/{i:03d}.mp4"], check=True)
    print("refeito", i, arq)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "seg2/lista.txt", "-c", "copy", "montado.mp4"], check=True)
total = sum(e[2] for e in m.EDL)
final(total, "KIKO_JustCavalli_stories_v2.mp4")
