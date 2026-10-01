"""Render final: segmentos 4K (concat) + 'Vamo de DEEP?' + textos ASS + mix normalizado em -14 LUFS."""
import json
import re
import subprocess
import sys

X264 = ["-c:v", "libx264", "-preset", "faster", "-crf", "19", "-pix_fmt", "yuv420p", "-g", "60",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000"]


def audio_final(versao, dur, fade=0.6):
    """voz + SFX -> passa-alta, compressão leve, loudnorm em 2 passes (-14 LUFS, -1,5 dBTP), fade out"""
    pre = "highpass=f=70,acompressor=threshold=-22dB:ratio=2:attack=10:release=150:makeup=1"
    med = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"mix_{versao}.wav", "-af",
                          pre + ",loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    j = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", med, re.S).group(0))
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"mix_{versao}.wav", "-af",
                    f"{pre},{ln},alimiter=limit=0.84:level=disabled,afade=t=out:st={dur - fade:.2f}:d={fade}",
                    "-ar", "48000", "-c:a", "pcm_s16le", f"final_{versao}.wav"], check=True)


def render(versao, saida, fade=0.6, extra=()):
    dur = json.load(open(f"plano_{versao}.json"))["duracao"]
    v = json.load(open(f"vamo_{versao}.json"))
    audio_final(versao, dur, fade)
    filtro = (f"[1:v]format=rgba,setpts=PTS+{v['ini']:.4f}/TB[vamo];"
              f"[0:v][vamo]overlay=0:0:eof_action=pass,"
              f"ass=insercoes_{versao}.ass:fontsdir=fonts,"
              f"fade=t=out:st={dur - fade:.2f}:d={fade}{''.join(extra)}[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-stats", "-y",
                    "-f", "concat", "-safe", "0", "-i", f"seg/lista_{versao}.txt",
                    "-framerate", "30", "-i", "vamo/%04d.png",
                    "-i", f"final_{versao}.wav",
                    "-filter_complex", filtro, "-map", "[v]", "-map", "2:a", "-t", f"{dur:.3f}",
                    *X264, saida], check=True)
    print("OK", saida, flush=True)


def previa(versao, partes=1, mb=28.5):
    """prévia 720p < 30 MB por arquivo (2 passes), em uma ou mais partes"""
    dur = json.load(open(f"plano_{versao}.json"))["duracao"]
    v = json.load(open(f"vamo720_{versao}.json"))
    audio_final(versao, dur)
    filtro = (f"[1:v]format=rgba,setpts=PTS+{v['ini']:.4f}/TB[vamo];"
              f"[0:v][vamo]overlay=0:0:eof_action=pass,scale=1280:720:flags=bicubic,"
              f"ass=insercoes_{versao}.ass:fontsdir=fonts,fade=t=out:st={dur - 0.6:.2f}:d=0.6[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-stats", "-y", "-f", "concat", "-safe", "0", "-i", f"seg720/lista_{versao}.txt",
                    "-framerate", "30", "-i", "vamo720/%04d.png", "-filter_complex", filtro, "-map", "[v]",
                    "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p",
                    f"previa_{versao}_tmp.mp4"], check=True)
    corte = [dur * k / partes for k in range(partes + 1)]
    for k in range(partes):
        a, b = corte[k], corte[k + 1]
        kbps = int(mb * 8 * 1024 / (b - a)) - 96
        nome = f"DEEP_EP2_{versao}_previa" + (f"_parte{k + 1}" if partes > 1 else "") + ".mp4"
        comum = ["-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", f"previa_{versao}_tmp.mp4", "-ss", f"{a:.3f}",
                 "-t", f"{b - a:.3f}", "-i", f"final_{versao}.wav", "-map", "0:v", "-map", "1:a",
                 "-c:v", "libx264", "-preset", "medium", "-b:v", f"{kbps}k"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", *comum, "-pass", "1", "-passlogfile", f"p_{versao}", "-an",
                        "-f", "mp4", "/dev/null"], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", *comum, "-pass", "2", "-passlogfile", f"p_{versao}",
                        "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", nome], check=True)
        print("OK", nome, flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "previa":
        previa("youtube", 2)
        previa("instagram", 1)
    else:
        for v in sys.argv[1:]:
            render(v, f"DEEP_EP2_{v}_4K.mp4")
