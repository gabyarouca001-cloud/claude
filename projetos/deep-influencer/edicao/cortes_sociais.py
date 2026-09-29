"""Cortes verticais (9:16) por capítulo para Reels / TikTok / Shorts, com inserções na área segura."""
import contextlib
import io
import json
import os
import re
import subprocess
import sys

with contextlib.redirect_stdout(io.StringIO()):
    import insercoes as I  # reaproveita INS, achar(), mapa(), palavras

W, H = 1080, 1920
# área segura (Reels/TikTok/Shorts): topo 250, base 480, direita 140, esquerda 60
CX = 510                     # centro levemente à esquerda (ícones ficam à direita)
LARG = 820                   # largura útil do texto
AMARELO, BRANCO = "&H00C0EDFC&", "&H00FFFFFF&"
FIX = {"nixo": "nicho", "gane": "ganha", "criators": "creators"}

CORTES = [
    ("01_sonho_vs_realidade", ("primeiro quando as pessoas", 30), ("mas por que tanta", 132), None,
     ("como ser influencer:", "O SONHO VS. A REALIDADE")),
    ("02_por_que_todo_mundo_quer_entrar", ("mas por que tanta", 132), ("e as marcas", 201), None,
     ("por que todo mundo", "QUER SER INFLUENCER?")),
    ("03_o_que_o_mercado_compra_hoje", ("e as marcas", 201), ("então qual é a diferença", 284), None,
     ("o que as marcas", "COMPRAM HOJE")),
    ("04_quem_sobrevive_x_quem_constroi", ("então qual é a diferença", 284), ("e eu diria mais", 448), None,
     ("quem sobrevive x quem constrói:", "3 COISAS")),
    ("05_o_que_voce_esta_construindo", ("e eu diria mais", 448), None, ("você quer ser mais um", 500),
     ("a pergunta que", "VALE FAZER HOJE")),
]
TEXTO_ORIGINAL = (65.8, 67.8)  # texto da editora gravado na imagem: mostrar o quadro 16:9 inteiro

CAB = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Serif,Playfair Display,62,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,0,-1,0,0,100,100,0,0,1,0,1.5,5,0,0,0,1
Style: Bold,Inter Black,120,&H00C0EDFC,&H00FFFFFF,&H00000000,&HB4000000,0,0,0,0,100,100,-2,0,1,0,2,5,0,0,0,1
Style: Eco,Inter Black,380,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,-6,0,1,0,0,5,0,0,0,1
Style: Label,Inter Medium,30,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,0,0,0,0,100,100,6,0,1,0,2,7,0,0,0,1
Style: Lista,Inter ExtraBold,48,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,0,0,0,0,100,100,0,0,1,0,1.5,4,0,0,0,1
Style: Legenda,Inter ExtraBold,70,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,0,3.5,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def quebra(texto, max_chars=12):
    """Quebra em duas linhas equilibradas quando a frase é longa."""
    if len(texto) <= max_chars or " " not in texto:
        return texto, len(texto)
    palavras = texto.split()
    melhor = min(range(1, len(palavras)),
                 key=lambda i: abs(len(" ".join(palavras[:i])) - len(" ".join(palavras[i:]))))
    l1, l2 = " ".join(palavras[:melhor]), " ".join(palavras[melhor:])
    return f"{l1}\\N{l2}", max(len(l1), len(l2))


def fs_bold(n, base=120):
    return min(base, int(LARG / (0.68 * max(n, 1))))


class Clip:
    def __init__(self, ini, fim):
        self.ini, self.fim, self.ev, self.ocupado = ini, fim, [], []

    def add(self, camada, a, b, estilo, texto):
        a, b = max(a, self.ini), min(b, self.fim)
        if b > a:
            self.ev.append(f"Dialogue: {camada},{I.ts(a - self.ini)},{I.ts(b - self.ini)},{estilo},,0,0,0,,{texto}")

    def titulo(self, a, b, serif, bold, eco=None, extra=None, y_serif=1085):
        d = int((b - a) * 1000)
        txt, n = quebra(bold)
        fs = fs_bold(n)
        duas = "\\N" in txt
        y_bold = y_serif + 60 + (fs if duas else fs // 2)
        if eco:
            self.add(0, a, b, "Eco", rf"{{\an5\pos({CX},{y_serif + 70})\fs{min(380, int(1000 / (0.62 * len(eco))))}"
                                     rf"\alpha&HC4&\fad(250,300)\fscx96\fscy96\t(0,{d},\fscx106\fscy106)}}{eco}")
        self.add(2, a, b, "Serif", rf"{{\an5\move({CX},{y_serif + 18},{CX},{y_serif},0,300)\fad(220,200)}}{serif}")
        self.add(2, a + 0.08, b, "Bold", rf"{{\an5\pos({CX},{y_bold})\fs{fs}\fscx115\fscy115\blur8\alpha&HFF&"
                                         r"\t(0,240,\fscx100\fscy100\blur0\alpha&H00&)\fad(0,200)}" + txt)
        if extra:
            self.add(2, a + 0.3, b, "Serif", rf"{{\an5\pos({CX},{y_bold + (fs if duas else fs // 2) + 45})\fs44\fad(250,200)}}{extra}")
        self.ocupado.append((a, b))

    def lista(self, a, b, titulo, itens):
        self.add(2, a, b, "Serif", rf"{{\an4\move(70,990,90,990,0,300)\fad(250,250)\fs52}}{titulo}")
        for n, (t, texto) in enumerate(itens):
            y = 1070 + n * 74
            self.add(2, t, b, "Lista", rf"{{\an4\move(70,{y},90,{y},0,250)\fad(200,250)}}{{\1c{AMARELO}}}— {{\1c{BRANCO}}}{texto}")
        self.ocupado.append((a, b))

    def versus(self, a, b):
        d = int((b - a) * 1000)
        self.add(2, a + 0.1, b, "Bold", rf"{{\an5\pos({CX},1030)\fs120\fad(200,200)}}RELAÇÃO")
        self.add(2, a, b, "Serif", rf"{{\an5\move({CX},1135,{CX},1120,0,300)\fad(220,200)}}vale mais do que")
        self.add(2, a + 0.5, b, "Bold", rf"{{\an5\pos({CX},1215)\fs120\fad(250,200)\alpha&H60&\t(0,{d},\alpha&H90&)}}VITRINE")
        self.ocupado.append((a, b))

    def citacao(self, a, b, serif, bold):
        s, _ = quebra(serif, 26)
        t, n = quebra(bold, 14)
        self.add(2, a, b, "Serif", rf"{{\an5\move({CX},1070,{CX},1050,0,400)\fs56\fad(350,300)}}{s}")
        self.add(2, a + 0.6, b, "Bold", rf"{{\an5\pos({CX},1215)\fs{fs_bold(n, 78)}\fad(300,300)}}{t}")
        self.ocupado.append((a, b))

    def grafico(self, a, b, serif, bold):
        self.add(2, a + 0.3, b, "Bold", rf"{{\an5\pos({CX},1290)\fs150\fscx115\fscy115\blur8\alpha&HFF&"
                                        r"\t(0,260,\fscx100\fscy100\blur0\alpha&H00&)\fad(0,200)}" + bold)
        self.add(2, a + 0.4, b, "Serif", rf"{{\an5\move({CX},1400,{CX},1385,0,300)\fs46\fad(250,200)}}{serif}")
        self.ocupado.append((a, b))

    def gancho(self, serif, bold):
        a, b = self.ini, self.ini + 3.2
        txt, n = quebra(bold, 14)
        fs = fs_bold(n, 104)
        self.add(2, a, b, "Serif", rf"{{\an5\move({CX},290,{CX},275,0,300)\fs54\fad(200,250)}}{serif}")
        self.add(2, a + 0.1, b, "Bold", rf"{{\an8\pos({CX},318)\fs{fs}\fscx112\fscy112\alpha&HFF&"
                                        r"\t(0,240,\fscx100\fscy100\alpha&H00&)\fad(0,250)}" + txt)

    def cta(self):
        a, b = self.fim - 3.2, self.fim
        self.add(1, a, b, "Label", rf"{{\an7\pos(70,270)\fad(300,300)\1c{AMARELO}\bord0\shad0\p1}}m 0 0 l 8 0 8 112 0 112{{\p0}}")
        self.add(2, a, b, "Label", rf"{{\an7\move(80,272,96,272,0,350)\fad(300,300)\fs36}}EPISÓDIO COMPLETO")
        self.add(2, a + 0.1, b, "Label", rf"{{\an7\move(80,318,96,318,0,350)\fad(300,300)\1c{AMARELO}\fs60\b1\fsp4}}NO YOUTUBE")

    def legendas(self):
        grupos, atual = [], []
        for w in I.palavras:
            if not any(s["ini"] <= w["s"] < s["fim"] for s in I.plano["segmentos"]):
                continue  # palavra de trecho cortado
            t = I.mapa(w["s"])
            if not (self.ini <= t < self.fim):
                continue
            txt = w["w"].strip()
            if I.norm(txt) in FIX:
                txt = re.sub(r"\w+", FIX[I.norm(txt)], txt, count=1)
            atual.append((t, I.mapa(w["e"]), txt))
            fim_frase = re.search(r"[.?!,]$", txt)
            if len(atual) >= 3 or len(" ".join(x[2] for x in atual)) >= 16 or fim_frase:
                grupos.append(atual)
                atual = []
        if atual:
            grupos.append(atual)
        for i, g in enumerate(grupos):
            a = g[0][0]
            b = min(grupos[i + 1][0][0] if i + 1 < len(grupos) else g[-1][1] + 0.4, g[-1][1] + 0.5)
            if any(x < b and a < y for x, y in self.ocupado):
                continue  # não sobrepor as inserções
            texto = re.sub(r"[.,!]", "", " ".join(x[2] for x in g)).replace("...", "")
            self.add(1, a, b, "Legenda", rf"{{\an5\pos({CX},1330)}}{texto}")


def tempo(ancora, delta=0.0):
    return I.mapa(I.achar(*ancora)[0]) + delta


def main():
    os.makedirs("social", exist_ok=True)
    g = json.load(open("insercoes.json"))["grafico"]
    so = sys.argv[1:]  # opcional: prefixos de cortes a renderizar
    for nome, ini_anc, fim_anc, fim_depois, (h1, h2) in CORTES:
        if so and not any(nome.startswith(p) for p in so):
            continue
        ini = tempo(ini_anc, -0.12)
        if fim_anc:
            fim = tempo(fim_anc, -0.10)
        else:
            _, e = I.achar(*fim_depois)
            fim = I.mapa(e) + 0.45
        c = Clip(ini, fim)
        for tipo, frase, depois, dur, d in I.INS:
            s0, _ = I.achar(frase, depois)
            a = I.mapa(s0) - 0.05
            if isinstance(dur, str):
                b = I.mapa(I.achar(dur, s0 + 0.1)[0]) - 0.08
            else:
                b = a + dur
            if b <= ini or a >= fim:
                continue  # fora do corte
            if tipo == "titulo":
                c.titulo(a, b, d["serif"], d["bold"], d.get("eco"), d.get("extra"))
            elif tipo == "lista":
                itens = [(I.mapa(I.achar(f, dd)[0]) - 0.05, txt) for f, dd, txt in d["itens"]]
                c.lista(a, b, d["titulo"], itens)
            elif tipo == "versus":
                c.versus(a, b)
            elif tipo == "citacao":
                c.citacao(a, b, d["serif"], d["bold"])
            elif tipo == "grafico":
                c.grafico(a, b, d["serif"], d["bold"])
        c.gancho(h1, h2)
        c.cta()
        c.legendas()
        ass = f"social/{nome}.ass"
        open(ass, "w", encoding="utf-8").write(CAB + "\n".join(c.ev) + "\n")

        dur = fim - ini
        entradas = ["-ss", f"{ini:.3f}", "-t", f"{dur:.3f}", "-i", "video_cortado.mp4",
                    "-ss", f"{ini:.3f}", "-t", f"{dur:.3f}", "-i", "mix.wav"]
        # recorte vertical; no trecho com o texto original, quadro inteiro sobre fundo desfocado
        ta, tb = TEXTO_ORIGINAL
        vf = ("[0:v]split[v1][v2];"
              "[v1]crop=1215:2160:(iw-1215)/2:0,scale=1080:1920:flags=lanczos[vert];"
              "[v2]scale=1080:-2,split[f1][f2];"
              "[f1]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=40,eq=brightness=-0.12[fundo];"
              "[fundo][f2]overlay=0:(H-h)/2[fit];"
              f"[vert][fit]overlay=0:0:enable='between(t,{ta - ini:.3f},{tb - ini:.3f})'[base]")
        if g and ini <= g["ini"] < fim:
            entradas += ["-itsoffset", f"{g['ini'] - ini:.3f}", "-framerate", "25", "-i", "grafico/%04d.png"]
            vf += ";[2:v]scale=780:-1,format=rgba[gr];[base][gr]overlay=90:840:eof_action=pass[base2]"
        else:
            vf += ";[base]null[base2]"
        vf += (f";[base2]ass={ass}:fontsdir=fonts,fade=t=in:st=0:d=0.25,fade=t=out:st={dur - 0.5:.2f}:d=0.5[v];"
               f"[1:a]volume=-2.1dB,alimiter=limit=0.84:attack=3:release=80:level=disabled,"
               f"afade=t=in:st=0:d=0.15,afade=t=out:st={dur - 0.5:.2f}:d=0.5[a]")
        # cabe no limite de 30 MB do chat
        kbps = int((28.5 * 8 * 1024 * 1024 / dur) / 1000) - 130
        comum = ["-filter_complex", vf, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow",
                 "-b:v", f"{kbps}k", "-pix_fmt", "yuv420p", "-r", "25", "-g", "50",
                 "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, *comum, "-pass", "1", "-passlogfile",
                        f"social/{nome}", "-an", "-f", "mp4", "/dev/null"], check=True)
        saida = f"social/DEEP_{nome}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, *comum, "-pass", "2", "-passlogfile",
                        f"social/{nome}", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", saida], check=True)
        print(f"OK {saida} {dur:.1f}s {kbps}k {os.path.getsize(saida) / 1e6:.1f}MB", flush=True)


if __name__ == "__main__":
    main()
