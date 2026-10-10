"""Mistura (voz tratada + efeitos das inserções + trilha) e composição do Reel. Uso (em /home/user/work/ep):
  python3 final.py audio | previa | 4k        (previa: 720p < 30 MB, 2 passes; 4k: 2160x3840 30 fps, CRF 17)"""
import json, os, subprocess, sys
import numpy as np
from scipy.signal import butter, sosfilt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfx

W = "/home/user/work/ep"
SR = 48000
DUR = 81.73
MUSICA = f"{W}/musica/6.mp3"          # Mixkit "Fun and Games"
MUS_ENTRA, MUS_FADE_IN, MUS_SAI, MUS_FADE_OUT = 7.4, 1.8, 80.0, 1.7
MUS_DB_ABAIXO_DA_VOZ = 19.0


def ler(arq):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", arq, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32).reshape(-1, 2).copy()


def gravar(y, arq, codec="pcm_s16le"):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", codec, arq], input=y.astype(np.float32).tobytes(), check=True)


def rms_fala_db(x, limiar=-34.0):
    n = 4800
    fr = x[:len(x) // n * n].mean(1).reshape(-1, n)
    r = 10 * np.log10((fr ** 2).mean(1) + 1e-12)
    return float(10 * np.log10((fr[r > limiar] ** 2).mean()))


def trilha(n, voz):
    m = ler(MUSICA)
    i0 = int(MUS_ENTRA * SR)
    seg = m[:n - i0]
    sos = butter(2, 110, "highpass", fs=SR, output="sos")                 # tira a base (disputa com a voz)
    seg = sosfilt(sos, seg, axis=0)
    # recuo de 3 dB na faixa de presença da voz (2–4 kHz)
    from scipy.signal import iirpeak
    b, a = iirpeak(3000 / (SR / 2), 1.0)
    seg = (seg - 0.30 * __import__("scipy.signal", fromlist=["lfilter"]).lfilter(b, a, seg, axis=0)).astype(np.float32)
    alvo = rms_fala_db(voz) - MUS_DB_ABAIXO_DA_VOZ
    atual = rms_fala_db(seg, -60)
    seg *= 10 ** ((alvo - atual) / 20)
    t = np.arange(len(seg)) / SR + MUS_ENTRA
    env = np.clip((t - MUS_ENTRA) / MUS_FADE_IN, 0, 1) ** 1.5 * np.clip((MUS_SAI + MUS_FADE_OUT - t) / MUS_FADE_OUT, 0, 1) ** 1.5
    out = np.zeros((n, 2), np.float32)
    out[i0:i0 + len(seg)] = seg * env[:, None]
    print(f"trilha: voz {rms_fala_db(voz):.1f} dB, trilha {alvo:.1f} dB ({MUS_DB_ABAIXO_DA_VOZ:.0f} dB abaixo)")
    return out


def sons(n):
    man = json.load(open(f"{W}/ov_1/manifesto.json"))
    banco = {"varredura": sfx.varredura, "tique": lambda: sfx.tique(1900), "tique2": lambda: sfx.tique(2400), "acorde": sfx.acorde,
             "saida": sfx.saida, "ding": sfx.ding, "nota1": lambda: sfx.nota(1046.5), "nota2": lambda: sfx.nota(1318.5),
             "nota3": lambda: sfx.nota(1568.0), "nota4": lambda: sfx.nota(2093.0)}
    out = np.zeros((n, 2), np.float32)
    for t, tipo in man["eventos"]:
        y = banco[tipo]()
        i = int(t * SR)
        j = min(n, i + len(y))
        out[i:j] += y[:j - i, None].astype(np.float32) * np.array([[1.0, 0.92]], np.float32)
    return out


def audio():
    voz = ler(f"{W}/voz_tratada.wav")
    n = len(voz)
    mix = voz + sons(n) + trilha(n, voz)
    gravar(mix, f"{W}/mix_pre.wav", "pcm_f32le")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{W}/mix_pre.wav", "-af", "alimiter=limit=0.89:attack=5:release=60:level=disabled", "-c:a", "pcm_s16le", f"{W}/mix.wav"], check=True)
    print("mix.wav pronto")


def video(modo):
    S = 1 if modo == "previa" else 2
    man = json.load(open(f"{W}/ov_{S}/manifesto.json"))
    ent = ["-i", f"{W}/original.mp4"]
    filt, ult = [], "b0"
    if modo == "previa":
        filt.append("[0:v]scale=1080:1920:flags=bicubic[b0]")
    else:
        filt.append("[0:v]null[b0]")
    for k, ins in enumerate(man["inserts"], 1):
        ent += ["-framerate", "30", "-itsoffset", f"{ins['t0']:.3f}", "-i", f"{W}/ov_{S}/{ins['nome']}/%04d.png"]
        filt.append(f"[{ult}][{k}:v]overlay=format=auto:eof_action=pass[b{k}]")
        ult = f"b{k}"
    n_in = len(man["inserts"]) + 1
    ent += ["-i", f"{W}/mix.wav"]
    if modo == "previa":
        filt.append(f"[{ult}]scale=720:1280:flags=lanczos,format=yuv420p[v]")
        kbps = int(28.0 * 8000 / DUR - 96)
        base = ["-filter_complex", ";".join(filt), "-map", "[v]", "-c:v", "libx264", "-preset", "slow", "-b:v", f"{kbps}k", "-r", "30"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", *ent, *base, "-pass", "1", "-passlogfile", f"{W}/pl", "-an", "-t", f"{DUR}", "-f", "mp4", "/dev/null"], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", *ent, *base, "-pass", "2", "-passlogfile", f"{W}/pl", "-map", f"{n_in}:a", "-c:a", "aac", "-b:a", "96k",
                        "-t", f"{DUR}", "-movflags", "+faststart", f"{W}/previa_720p.mp4"], check=True)
    else:
        filt.append(f"[{ult}]format=yuv420p[v]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", *ent, "-filter_complex", ";".join(filt), "-map", "[v]", "-map", f"{n_in}:a", "-c:v", "libx264", "-preset", "faster",
                        "-crf", "17", "-r", "30", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-c:a", "aac", "-b:a", "320k",
                        "-t", f"{DUR}", "-movflags", "+faststart", f"{W}/DEEP_DisneySprings_final_4K.mp4"], check=True)


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "audio":
        audio()
    else:
        video(modo)
