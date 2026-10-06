"""Reels "Garrafa inteligente" (Samara): a editora montou até 1:42; daqui pra frente cortes nos melhores takes.
Uso: python3 montar.py previa | 4k   (rodar em /home/user/work/novo2)"""
import subprocess
import sys

import numpy as np

SR = 16000
x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", "video.mp4", "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                 capture_output=True, check=True).stdout, np.float32)


def vale(t, janela=0.12):
    """ponto de menor energia perto de t (corte sem picotar palavra)"""
    passo = int(0.01 * SR)
    ts = np.arange(t - janela, t + janela, 0.01)
    e = [np.sqrt((x[int(u * SR):int(u * SR) + passo] ** 2).mean()) for u in ts]
    return round(float(ts[int(np.argmin(e))]), 3)


# (início, fim) no vídeo original
PECAS = [
    (0.0, vale(102.72, 0.07)),            # trecho da editora, intocado ("...viralizada lá fora.")
    (vale(111.85), vale(123.42)),         # "Dito tudo isso... tecnologia toda," (2º take)
    (vale(126.22), vale(132.35)),         # "você precisa carregar a bateria, trocar o filtro nos modelos que têm"
    (vale(149.50), vale(155.45)),         # "E autolimpeza não significa nunca mais lavar, tá?"
    (vale(163.40), 165.63),               # "Gente, ela tá purificando a minha água!"
    (vale(168.82), vale(170.72)),         # "Não faz nenhum barulho."
    (176.30, 178.95),                     # bebendo
    (181.30, vale(183.98)),               # "Nossa, a água tá uma delícia! Mentira!"
    (vale(231.78), 243.55),               # "Agora me conta... comprar? Tchau!" + aceno
]
# imagem por cima (sem o som dela): puxando o filtro, durante "trocar o filtro nos modelos que têm"
INSERT = (257.0, 259.85, 129.10)          # (início no original, fim, momento no original da peça de áudio)

def main(modo):
    larg, alt = (720, 1280) if modo == "previa" else (2160, 3840)
    f, v_in, a_in, t = [], [], [], 0.0
    ins_t = None
    for k, (a, b) in enumerate(PECAS):
        f.append(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS,scale={larg}:{alt}:flags=lanczos,setsar=1[v{k}]")
        f.append(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b - a - 0.012:.3f}:d=0.012[a{k}]")
        if a <= INSERT[2] <= b:
            ins_t = t + INSERT[2] - a
        t += b - a
        v_in.append(f"[v{k}]")
        a_in.append(f"[a{k}]")
    f.append("".join(f"{v}{a}" for v, a in zip(v_in, a_in)) + f"concat=n={len(PECAS)}:v=1:a=1[base][aud]")
    d = INSERT[1] - INSERT[0]
    f.append(f"[0:v]trim={INSERT[0]}:{INSERT[1]},setpts=PTS-STARTPTS+{ins_t:.3f}/TB,scale={larg}:{alt}:flags=lanczos,setsar=1[ins]")
    f.append("[base][ins]overlay=eof_action=pass[v]")
    saida = "Garrafa_inteligente_previa.mp4" if modo == "previa" else "Garrafa_inteligente_4K.mp4"
    enc = (["-c:v", "libx264", "-preset", "medium", "-b:v", "1300k", "-maxrate", "1800k", "-bufsize", "3600k"]
           if modo == "previa" else ["-c:v", "libx264", "-preset", "faster", "-crf", "17"])
    subprocess.run(["ffmpeg", "-v", "error", "-stats", "-y", "-i", "video.mp4", "-filter_complex", ";".join(f),
                    "-map", "[v]", "-map", "[aud]", *enc, "-pix_fmt", "yuv420p", "-r", "30",
                    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    "-c:a", "aac", "-b:a", "128k" if modo == "previa" else "320k", "-movflags", "+faststart", saida], check=True)
    print("OK", saida, round(t, 2), "s; filtro por cima em", round(ins_t, 2), "s por", round(d, 2), "s")
    for a, b in PECAS:
        print(f"  {a:7.2f} -> {b:7.2f}")


main(sys.argv[1] if len(sys.argv) > 1 else "previa")
