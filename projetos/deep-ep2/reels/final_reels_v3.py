"""Reels v3: abertura da editora + segmentos 9:16 + B-roll mudo (clique de câmera na entrada)
+ legendas/inserções + trilha sentimental bem baixa. Sem fade no final (o "Tchau" termina inteiro)."""
import json
import os
import re
import subprocess

import numpy as np

import insercoes as Y
import sfx_deep as D

SR = 48000
OFF = 9.8
TRILHA = "/home/user/work/broll/mus_714.mp3"      # Mixkit "Piano Reflections" (licença livre)
CLIQUE = "/home/user/work/broll/shutter.mp3"      # Mixkit "Camera shutter click"
TRILHA_LUFS = -33                                 # quase imperceptível debaixo da voz (-14)


def ler(arq, *extra):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", arq, *extra, "-vn", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32).reshape(-1, 2).copy()


def loudnorm(entrada, saida, filtro, alvo):
    med = subprocess.run(["ffmpeg", "-hide_banner", "-i", entrada, "-af", filtro + f"loudnorm=I={alvo}:TP=-1.5:LRA=9:print_format=json",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", med, re.S).group(0))
    ln = (f"loudnorm=I={alvo}:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
          f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", entrada, "-af", filtro + ln, "-ar", str(SR), "-c:a", "pcm_f32le", saida],
                   check=True)


voz = ler("voz_reels.wav")
ab = ler("inicio_v2.mp4")[:int(OFF * SR)]
mix = np.concatenate([ab, voz])
dur = len(mix) / SR

# efeitos: chimes dos capítulos, sons dos destaques e clique de câmera nas inserções
cache = {}
eventos = [(t, tipo, None) for t, tipo in json.load(open("sfx_reels.json"))] + [tuple(e) for e in json.load(open("sfx_deep.json"))]
clique = ler(CLIQUE)[:, 0]
clique = clique / np.abs(clique).max()
broll = json.load(open("broll_v3.json"))
for k, b in enumerate(broll):
    emendado = k and abs(b["t"] - broll[k - 1]["fim"]) < 0.05
    eventos.append((b["t"] - 0.03, "clique", 0.10 if emendado else 0.14))
for t, tipo, v in eventos:
    if tipo == "clique":
        y = clique * v
    elif v is None:
        y = cache.setdefault(tipo, Y.som(tipo).astype(np.float32))
    else:
        y = (D.SONS[tipo](v) if tipo in D.SONS else D.SAIDA[tipo]()).astype(np.float32)
    i = int(t * SR)
    j = min(len(mix), i + len(y))
    mix[i:j] += y[:j - i, None]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_f32le",
                "mix_reels_v3.wav"], input=mix.tobytes(), check=True)
loudnorm("mix_reels_v3.wav", "voz_norm_v3.wav", "highpass=f=70,acompressor=threshold=-22dB:ratio=2:attack=10:release=150:makeup=1,", -14)

# trilha: em loop com crossfade, entra depois da abertura e some suave só nos últimos 3 s
n = int(np.ceil((dur - OFF) / 140)) + 1
subprocess.run(["ffmpeg", "-v", "error", "-y", *sum([["-i", TRILHA] for _ in range(n)], []), "-filter_complex",
                ";".join([f"[0:a][1:a]acrossfade=d=4[x1]"] + [f"[x{k}][{k + 1}:a]acrossfade=d=4[x{k + 1}]" for k in range(1, n - 1)]),
                "-map", f"[x{n - 1}]", "-ac", "2", "-ar", str(SR), "-c:a", "pcm_f32le", "trilha_loop.wav"], check=True)
loudnorm("trilha_loop.wav", "trilha_norm.wav", "lowpass=f=9000,", -20)
tri = ler("trilha_norm.wav")[:int((dur - OFF) * SR)] * 10 ** ((TRILHA_LUFS + 20) / 20)
env = np.ones(len(tri), np.float32)
fi, fo = int(2.5 * SR), int(3.0 * SR)
env[:fi] = np.linspace(0, 1, fi)
env[-fo:] = np.linspace(1, 0, fo)
final = ler("voz_norm_v3.wav")[:len(mix)]
final[int(OFF * SR):int(OFF * SR) + len(tri)] += tri * env[:, None]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                "alimiter=limit=0.84:level=disabled", "-c:a", "pcm_s16le", "final_reels_v3.wav"],
               input=final.astype(np.float32).tobytes(), check=True)

if os.environ.get("SO_AUDIO"):
    raise SystemExit(f"áudio pronto ({dur:.1f}s)")
open("lista_reels_total.txt", "w").write("file 'abertura_reels.mp4'\n" + "".join(
    f"file 'seg_reels/{l.split(chr(39))[1]}'\n" for l in open("seg_reels/lista.txt") if l.strip()))

# vídeo: base + B-roll por cima (some no fim de cada clipe) + inserções/legendas por cima de tudo
entradas, filtros, ult = [], [], "0:v"
for k, b in enumerate(broll):
    entradas += ["-i", b["arq"]]
    filtros.append(f"[{k + 2}:v]setpts=PTS-STARTPTS+{b['t']}/TB[b{k}];[{ult}][b{k}]overlay=eof_action=pass[o{k}]")
    ult = f"o{k}"
filtros.append(f"[{ult}]ass=insercoes_reels.ass:fontsdir=fonts,ass=legendas_deep.ass:fontsdir=fonts[v]")
subprocess.run(["ffmpeg", "-v", "error", "-stats", "-y", "-f", "concat", "-safe", "0", "-i", "lista_reels_total.txt",
                "-i", "final_reels_v3.wav", *entradas, "-filter_complex", ";".join(filtros),
                "-map", "[v]", "-map", "1:a", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "DEEP_EP2_Reels_v3_1080x1920.mp4"], check=True)
print("OK", dur)
