"""Cortes do DEEP EP2 para Reels / TikTok / Shorts — um por capítulo do YouTube (trecho mais forte de cada um).
9:16 1080x1920 a partir dos takes verticais centralizados pela editora (ig/take*.mp4), montagem = versão youtube2
(com os cortes de erro de fala), legenda no estilo aprovado do Reels DEEP (Rubik SemiBold + palavra-chave amarela,
sombra leve), gancho com título olho de peixe no topo, trilha "Chillax" baixinha e "EPISÓDIO COMPLETO NO YOUTUBE"
no fim. Cada corte < 30 MB (2 passes). Rodar em /home/user/work/ep2."""
import json
import math
import os
import re
import subprocess
import sys
import unicodedata

sys.path.insert(0, "/home/user/claude/projetos/deep-influencer/edicao")
from titulo_olho_peixe import titulo as titulo_olho_peixe  # noqa: E402

W, H, FPS = 1080, 1920, 30
SR = 48000
DESLOC = {"take1": -16.0, "take2": 0.0, "take3": 0.0}          # take vertical x horizontal
TRILHA = "/home/user/work/broll/mus_655.mp3"
BRANCO, MANTEIGA = "&H00FFFFFF&", "&H00C1ECFB&"
CX, BASE_Y = 540, 1221
FIX = {"dip": "DEEP", "deep": "DEEP", "substacks": "Substack", "substeques": "Substack"}
CHAVE = {"deep", "instagram", "substack", "substacks", "podcast", "podcasts", "newsletter", "faturamento", "fatura",
         "constroi", "construir", "construindo", "construcao", "dependencia", "feed", "atencao", "rotina", "confiar",
         "milhoes", "profundidade", "referencias", "comunidade", "campanha", "carreira", "motivo", "reputacao",
         "nome", "algoritmo", "aplicativo", "plataformas", "conversa", "concreto", "reconhecivel", "contexto",
         "compreender", "descobrir", "pesquisas", "custo", "caminhos"}

# (nome, frase de início, frase final (o corte termina no fim dela), gancho em 2 linhas, texto do post)
CORTES = [
    ("01_quem_a_gente_vai_procurar", "e foi aí que eu comecei a perceber", "estão se encontrando",
     ("Por que a gente vai", "atrás de algumas pessoas?")),
    ("02_descobrir_x_compreender", "e tem uma diferença importantíssima", "as possíveis contradições",
     ("Descobrir não é", "compreender")),
    ("03_faturar_x_construir", "qual é a diferença entre o que você fatura", "interessado no que você faz",
     ("O que você fatura", "× o que você constrói")),
    ("04_mais_caminhos_mesma_dependencia", "hoje existem mais caminhos", "também tem um custo",
     ("Mais caminhos,", "a mesma dependência")),
    ("05_o_que_merece_sua_rotina", "a pessoa precisa encontrar um motivo", "mesmo quando o formato muda",
     ("O que merece fazer parte", "da rotina de alguém?")),
]


def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if unicodedata.category(c) != "Mn"))


PAL = json.load(open("checar_youtube2.json"))          # palavras da montagem youtube2 (tempo da voz)
TOK = [norm(w["w"]) for w in PAL]
SEGS = json.load(open("plano_youtube2.json"))["segmentos"]


def achar(frase):
    alvo = [norm(p) for p in frase.split()]
    for i in range(len(PAL)):
        if TOK[i:i + len(alvo)] == alvo:
            return i, i + len(alvo) - 1
    raise ValueError(frase)


def ts(t):
    t = max(0, t)
    return f"0:{int(t // 60):02d}:{t % 60:05.2f}"


CAB = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Base,Rubik SemiBold,46,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Label,Inter Medium,30,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,6,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ev(evs, camada, a, b, estilo, texto, sombra=True):
    evs.append(f"Dialogue: {camada + 1},{ts(a)},{ts(b)},{estilo},,0,0,0,,{texto}")
    if sombra:   # sombra preta leve só para dar leitura (padrão aprovado do Reels)
        s = re.sub(r"\\1c&H[0-9A-Fa-f]+&", "", texto)
        s = "{\\1c&H000000&\\3c&H000000&\\bord3\\blur8\\alpha&H78&" + (s[1:] if s.startswith("{") else "}" + s)
        evs.append(f"Dialogue: {camada},{ts(a)},{ts(b)},{estilo},,0,0,0,,{s}")


def legendas(evs, i0, i1, v0, ini_txt):
    blocos, atual = [], []
    for i in range(i0, i1 + 1):
        w = PAL[i]["w"].strip()
        atual.append(i)
        chars = sum(len(PAL[k]["w"].strip()) + 1 for k in atual)
        prox_longe = i + 1 <= i1 and PAL[i + 1]["s"] - PAL[i]["e"] > 0.35
        if len(atual) >= 3 or chars >= 14 or w[-1:] in ".?!," or prox_longe or (norm(w) in CHAVE and len(atual) >= 2):
            blocos.append(atual)
            atual = []
    if atual:
        blocos.append(atual)
    for n, bl in enumerate(blocos):
        a = PAL[bl[0]]["s"] - v0 - 0.03
        b = PAL[bl[-1]]["e"] - v0 + 0.12
        if n + 1 < len(blocos):
            b = min(max(b, PAL[blocos[n + 1][0]]["s"] - v0 - 0.03), PAL[bl[-1]]["e"] - v0 + 0.6,
                    PAL[blocos[n + 1][0]]["s"] - v0 - 0.03)
        if b <= ini_txt:      # durante o gancho a legenda continua (fica embaixo); nada a esconder
            pass
        partes = []
        for k in bl:
            p = PAL[k]["w"].strip()
            base = re.sub(r"[^\wÀ-ú-]", "", p)
            if norm(base) in FIX:
                p = p.replace(base, FIX[norm(base)])
            p = re.sub(r"[.,!]+$", "", p) if not p.endswith("?") else p
            if norm(base) in CHAVE:
                p = r"{\fnRubik Black\1c" + MANTEIGA + r"\fs52}" + p + r"{\fnRubik SemiBold\1c&HFFFFFF&\fs46}"
            partes.append(p)
        pop = r"\fscx112\fscy112\t(0,90,\fscx100\fscy100)"
        ev(evs, 1, a, b, "Base", rf"{{\an5\pos({CX},{BASE_Y}){pop}}}" + " ".join(partes))


def cta(evs, fim):
    a, b = fim - 3.2, fim
    ev(evs, 1, a, b, "Label", rf"{{\an7\pos(70,270)\fad(300,300)\1c{MANTEIGA}\bord0\shad0\p1}}m 0 0 l 8 0 8 112 0 112{{\p0}}",
       sombra=False)
    ev(evs, 2, a, b, "Label", rf"{{\an7\move(80,272,96,272,0,350)\fad(300,300)\fs36}}EPISÓDIO COMPLETO")
    ev(evs, 2, a + 0.1, b, "Label", rf"{{\an7\move(80,318,96,318,0,350)\fad(300,300)\1c{MANTEIGA}\fs60\b1\fsp4}}NO YOUTUBE")


def pecas(v0, v1):
    """trechos da montagem youtube2 entre v0 e v1 (tempo da voz) -> (fonte, ini, fim) no take"""
    out = []
    for s in SEGS:
        a, b = s["t"], s["t"] + s["fim"] - s["ini"]
        x, y = max(a, v0), min(b, v1)
        if y - x > 0.02:
            out.append((s["fonte"], s["ini"] + x - a, s["ini"] + y - a))
    return out


def render(nome, i0, i1, gancho):
    v0 = PAL[i0]["s"] - 0.25
    v1 = PAL[i1]["e"] + 0.5
    dur = v1 - v0
    pasta = f"social/{nome}"
    os.makedirs(pasta, exist_ok=True)
    # vídeo: pedaços dos takes verticais
    lista = []
    for k, (f, a, b) in enumerate(pecas(v0, v1)):
        arq = f"{pasta}/{k:03d}.mp4"
        n = max(1, round((b - a) * FPS))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a + DESLOC[f]:.3f}", "-i", f"ig/{f}.mp4", "-t", f"{b - a:.3f}",
                        "-an", "-vf", f"fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1", "-frames:v", str(n),
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", arq], check=True)
        lista.append(f"file '{k:03d}.mp4'")
    open(f"{pasta}/lista.txt", "w").write("\n".join(lista) + "\n")
    # textos
    evs = []
    legendas(evs, i0, i1, v0, 3.5)
    cta(evs, dur)
    open(f"{pasta}/textos.ass", "w", encoding="utf-8").write(CAB + "\n".join(evs) + "\n")
    os.chdir("/home/user/work/ep2/fonts")
    titulo_olho_peixe(list(gancho), f"/home/user/work/ep2/{pasta}/gancho.png", fonte="PlayfairMedium.ttf")
    os.chdir("/home/user/work/ep2")
    # áudio: voz (mesma montagem) -14 LUFS + trilha -33 LUFS
    n_tr = max(2, math.ceil(dur / 140) + 1)
    pre = "highpass=f=70,acompressor=threshold=-22dB:ratio=2:attack=10:release=150:makeup=1"
    cadeia = (f"[0:a]atrim={v0:.3f}:{v1:.3f},asetpts=PTS-STARTPTS,{pre},loudnorm=I=-14:TP=-1.5:LRA=9,"
              f"afade=t=out:st={dur - 0.25:.3f}:d=0.25[v];"
              + ";".join(["[1:a][2:a]acrossfade=d=4[x1]"] + [f"[x{k}][{k + 2}:a]acrossfade=d=4[x{k + 1}]" for k in range(1, n_tr - 1)])
              + f";[x{n_tr - 1}]lowpass=f=9000,loudnorm=I=-20:TP=-1.5:LRA=9,volume=-13dB,atrim=0:{dur:.3f},"
              f"afade=t=in:d=1.5,afade=t=out:st={dur - 2:.3f}:d=2[m];[v][m]amix=inputs=2:normalize=0:duration=first,"
              "alimiter=limit=0.84:level=disabled[o]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "voz_youtube2.wav", *sum([["-i", TRILHA] for _ in range(n_tr)], []),
                    "-filter_complex", cadeia, "-map", "[o]", "-ar", "48000", f"{pasta}/audio.wav"], check=True)
    # render final 2 passes < 30 MB
    kbps = int((27.0 * 8 * 1024 * 1024 / dur) / 1000) - 140
    filtro = (f"[0:v]ass={pasta}/textos.ass:fontsdir=fonts[t];[1:v]format=rgba,fade=t=in:st=0:d=0.3:alpha=1,"
              f"fade=t=out:st=3.3:d=0.4:alpha=1[g];[t][g]overlay=(W-w)/2:175:enable='lte(t,3.8)'[v]")
    comum = ["-f", "concat", "-safe", "0", "-i", f"{pasta}/lista.txt", "-loop", "1", "-t", "4", "-i", f"{pasta}/gancho.png",
             "-i", f"{pasta}/audio.wav", "-filter_complex", filtro, "-map", "[v]", "-map", "2:a", "-t", f"{dur:.3f}",
             "-c:v", "libx264", "-preset", "medium", "-b:v", f"{kbps}k", "-pix_fmt", "yuv420p", "-r", str(FPS)]
    saida = f"social/DEEP_EP2_corte_{nome}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *comum, "-pass", "1", "-passlogfile", f"{pasta}/p", "-an", "-f", "mp4",
                    "/dev/null"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", *comum, "-pass", "2", "-passlogfile", f"{pasta}/p", "-c:a", "aac",
                    "-b:a", "128k", "-movflags", "+faststart", saida], check=True)
    print(f"OK {saida} {dur:.1f}s {os.path.getsize(saida) / 1e6:.1f}MB", flush=True)


if __name__ == "__main__":
    so = sys.argv[1:]
    for nome, f0, f1, gancho in CORTES:
        if so and not any(nome.startswith(p) for p in so):
            continue
        i0, _ = achar(f0)
        _, i1 = achar(f1)
        render(nome, i0, i1, gancho)
