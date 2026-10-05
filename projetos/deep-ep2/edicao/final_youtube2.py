"""YouTube EP2 final: abertura da editora (inicio_editora.mp4, já com a vinheta) + montagem youtube2
(cortes de erro de fala aplicados) + inserções no padrão do EP1 + mix -14 LUFS. Sem fade no fim: o "Tchau" termina inteiro.
Uso: python3 final_youtube2.py previa | 4k"""
import json
import math
import os
import re
import subprocess
import sys

V = "youtube2"
TRILHA = "/home/user/work/broll/mus_655.mp3"     # Mixkit "Chillax" — a mesma trilha aprovada no Reels
TRILHA_LUFS = -33                                # bem baixa, debaixo da voz em -14
OFF = 9.68
DUR = json.load(open(f"plano_{V}.json"))["duracao"] + OFF


def audio_final():
    pre = "highpass=f=70,acompressor=threshold=-22dB:ratio=2:attack=10:release=150:makeup=1"
    med = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"mix_{V}.wav", "-af",
                          pre + ",loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    j = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", med, re.S).group(0))
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"mix_{V}.wav", "-af", f"{pre},{ln}",
                    "-ar", "48000", "-c:a", "pcm_f32le", f"voz_norm_{V}.wav"], check=True)
    # trilha: loop com crossfade, -33 LUFS, entra depois da abertura (fade 2,5 s) e some nos últimos 3 s
    dt = float(re.search(r"Duration: (\d+):(\d+):([\d.]+)", subprocess.run(["ffmpeg", "-i", TRILHA], capture_output=True,
                         text=True).stderr).group(3)) + 60 * int(re.search(r"Duration: \d+:(\d+)", subprocess.run(
                             ["ffmpeg", "-i", TRILHA], capture_output=True, text=True).stderr).group(1))
    n = max(2, math.ceil((DUR - OFF) / (dt - 4)) + 1)
    cadeia = ";".join(["[0:a][1:a]acrossfade=d=4[x1]"] + [f"[x{k}][{k + 1}:a]acrossfade=d=4[x{k + 1}]" for k in range(1, n - 1)]
                      + [f"[x{n - 1}]lowpass=f=9000,loudnorm=I=-20:TP=-1.5:LRA=9,volume={TRILHA_LUFS + 20}dB,"
                         f"atrim=0:{DUR - OFF:.3f},afade=t=in:d=2.5,afade=t=out:st={DUR - OFF - 3:.3f}:d=3,"
                         f"adelay={int(OFF * 1000)}|{int(OFF * 1000)}[m]"])
    subprocess.run(["ffmpeg", "-v", "error", "-y", *sum([["-i", TRILHA] for _ in range(n)], []), "-i", f"voz_norm_{V}.wav",
                    "-filter_complex", cadeia + f";[{n}:a][m]amix=inputs=2:normalize=0:duration=first,"
                    "alimiter=limit=0.84:level=disabled[o]", "-map", "[o]", "-ar", "48000", "-c:a", "pcm_s16le",
                    f"final_{V}.wav"], check=True)


def abertura(pasta, w, h):
    saida = f"{pasta}/abertura_editora.mp4"
    if not os.path.exists(saida):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "inicio_editora.mp4", "-an", "-t", str(OFF), "-vf",
                        f"fps=30,scale={w}:{h}:flags=lanczos,setsar=1", "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "16", "-pix_fmt", "yuv420p", "-g", "60", saida], check=True)
    lista = f"{pasta}/lista_{V}_total.txt"
    open(lista, "w").write("file 'abertura_editora.mp4'\n" + open(f"{pasta}/lista_{V}.txt").read())
    return lista


def previa(partes=2, mb=28.5):
    audio_final()
    lista = abertura("seg720", 1280, 720)
    subprocess.run(["ffmpeg", "-v", "error", "-stats", "-y", "-f", "concat", "-safe", "0", "-i", lista,
                    "-vf", f"ass=insercoes_{V}.ass:fontsdir=fonts", "-t", f"{DUR:.3f}", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", f"previa_{V}_tmp.mp4"], check=True)
    corte = [DUR * k / partes for k in range(partes + 1)]
    for k in range(partes):
        a, b = corte[k], corte[k + 1]
        kbps = int(mb * 8 * 1024 / (b - a)) - 96
        nome = f"DEEP_EP2_YouTube_previa_parte{k + 1}.mp4"
        comum = ["-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", f"previa_{V}_tmp.mp4", "-ss", f"{a:.3f}",
                 "-t", f"{b - a:.3f}", "-i", f"final_{V}.wav", "-map", "0:v", "-map", "1:a",
                 "-c:v", "libx264", "-preset", "medium", "-b:v", f"{kbps}k"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", *comum, "-pass", "1", "-passlogfile", f"p_{V}", "-an",
                        "-f", "mp4", "/dev/null"], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", *comum, "-pass", "2", "-passlogfile", f"p_{V}",
                        "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", nome], check=True)
        print("OK", nome, flush=True)


def render_4k():
    audio_final()
    lista = abertura("seg", 3840, 2160)
    subprocess.run(["ffmpeg", "-v", "error", "-stats", "-y", "-f", "concat", "-safe", "0", "-i", lista,
                    "-i", f"final_{V}.wav", "-vf", f"ass=insercoes_{V}.ass:fontsdir=fonts", "-map", "0:v", "-map", "1:a",
                    "-t", f"{DUR:.3f}", "-c:v", "libx264", "-preset", "faster", "-crf", "19", "-pix_fmt", "yuv420p",
                    "-g", "60", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", "DEEP_EP2_YouTube_4K.mp4"], check=True)
    print("OK 4K", flush=True)


if __name__ == "__main__":
    previa() if sys.argv[1] == "previa" else render_4k()
