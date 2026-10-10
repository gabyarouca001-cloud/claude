"""Renderiza os planos da EDL em 1920x1080 25p (filme 36 com zoom/recorte), junta e (opcional) gera a prévia/final.
Uso (em /home/user/work/gn): python3 video.py planos | previa | final"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl as E, resolver as R

W = "/home/user/work/gn"
FILM = {35: f"{W}/films/V2026NR0035.mp4", 36: f"{W}/films/V2026NR0036.mp4"}
os.makedirs(f"{W}/planos", exist_ok=True)

def vf(f):
    base = "scale=1920:1080:flags=lanczos"
    if f == 36:
        z = E.ZOOM36
        return f"crop=iw/{z}:ih/{z}:(iw-iw/{z})/2:ih*0.01,{base},setsar=1,fps=25,format=yuv420p"
    return f"{base},setsar=1,fps=25,format=yuv420p"

def planos():
    lista = []
    for e in R.resolver():
        n = round(e["dur"] * E.FPS)
        arq = f"{W}/planos/p{e['i']:02d}.mp4"
        lista.append(arq)
        if os.path.exists(arq):
            continue
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{e['ss']:.3f}", "-i", FILM[e["f"]], "-an", "-vf", vf(e["f"]), "-frames:v", str(n),
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-g", "25", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", arq], check=True)
        print(e["i"], n, flush=True)
    with open(f"{W}/planos/lista.txt", "w") as fh:
        fh.writelines(f"file '{a}'\n" for a in lista)

def juntar():
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{W}/planos/lista.txt", "-c", "copy", f"{W}/saida/video_sem_audio.mp4"], check=True)

def previa():
    """720p < 30 MB, 2 passes, com a mistura (MIX)"""
    dur = E.TOTAL
    kbps = int((28.0 * 8 * 1000 / dur) - 96)
    ent = ["-i", f"{W}/saida/video_sem_audio.mp4"]
    base = ["-vf", "scale=1280:720:flags=lanczos", "-c:v", "libx264", "-preset", "slow", "-b:v", f"{kbps}k", "-pix_fmt", "yuv420p"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ent, *base, "-pass", "1", "-passlogfile", f"{W}/saida/pl", "-an", "-f", "mp4", "/dev/null"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ent, "-i", f"{W}/saida/MIX.wav", *base, "-pass", "2", "-passlogfile", f"{W}/saida/pl",
                    "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", f"{W}/saida/previa_720p.mp4"], check=True)

def final():
    s = f"{W}/saida"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{s}/video_sem_audio.mp4", "-i", f"{s}/MIX.wav", "-c:v", "libx264", "-preset", "slow", "-crf", "14",
                    "-maxrate", "30M", "-bufsize", "60M", "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    "-c:a", "pcm_s16le", "-map", "0:v", "-map", "1:a", "-r", "25", f"{s}/GO_VW_Mission_Efficiency_HD_25p.mov"], check=True)

if __name__ == "__main__":
    modo = sys.argv[1]
    if modo in ("planos", "previa", "final"):
        planos()
        juntar()
    if modo == "previa":
        previa()
    if modo == "final":
        final()
