"""Reels final: abertura da editora + segmentos 9:16 + legendas/inserções + mix (-14 LUFS)."""
import json
import re
import subprocess

import numpy as np

import insercoes as Y

SR = 48000
OFF = 9.8
voz = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", "voz_reels.wav", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                                   capture_output=True, check=True).stdout, np.float32).reshape(-1, 2)
ab = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", "inicio_v2.mp4", "-vn", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                                  capture_output=True, check=True).stdout, np.float32).reshape(-1, 2)[:int(OFF * SR)]
mix = np.concatenate([ab, voz]).copy()
cache = {}
for t, tipo in json.load(open("sfx_reels.json")):
    y = cache.setdefault(tipo, Y.som(tipo).astype(np.float32))
    i = int(t * SR)
    j = min(len(mix), i + len(y))
    mix[i:j] += y[:j - i, None]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_f32le",
                "mix_reels.wav"], input=mix.tobytes(), check=True)
dur = len(mix) / SR
pre = "highpass=f=70,acompressor=threshold=-22dB:ratio=2:attack=10:release=150:makeup=1"
med = subprocess.run(["ffmpeg", "-hide_banner", "-i", "mix_reels.wav", "-af", pre + ",loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json",
                      "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", med, re.S).group(0))
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
      f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "mix_reels.wav", "-af",
                f"{pre},{ln},alimiter=limit=0.84:level=disabled,afade=t=out:st={dur - 0.6:.2f}:d=0.6",
                "-ar", "48000", "-c:a", "pcm_s16le", "final_reels.wav"], check=True)

open("lista_reels_total.txt", "w").write("file 'abertura_reels.mp4'\n" + "".join(
    f"file 'seg_reels/{l.split(chr(39))[1]}'\n" for l in open("seg_reels/lista.txt") if l.strip()))
subprocess.run(["ffmpeg", "-v", "error", "-stats", "-y", "-f", "concat", "-safe", "0", "-i", "lista_reels_total.txt",
                "-i", "final_reels.wav", "-filter_complex",
                f"[0:v]ass=insercoes_reels.ass:fontsdir=fonts,fade=t=out:st={dur - 0.6:.2f}:d=0.6[v]",
                "-map", "[v]", "-map", "1:a", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "DEEP_EP2_Reels_1080x1920.mp4"], check=True)
print("OK", dur)
