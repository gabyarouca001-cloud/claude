"""Gera a composição HyperFrames (index.html, 1080x1920, 30 fps, fundo transparente) com as inserções animadas
do vídeo "sapato pela metade da Chanel" (DEEP). Cada cartão = (tipo, ini, fim, parâmetros). Padrão visual DEEP:
amarelo manteiga #FCEDC0, Playfair Display itálico + Inter Black, sombra leve, SEM caixas escuras, nada sobre o rosto.
Zonas livres (1080x1920): faixa de cima y 260–450 e coluna esquerda x 56–470, y 520–1100. Legenda dela fica em y ≈ 1210.
Uso: python3 gerar.py cartoes.json saida_dir   (cartoes.json = lista de cartões)"""
import json
import math
import sys
from pathlib import Path

AMARELO = "#FCEDC0"
W, H, DUR_PAD = 1080, 1920, 0.4


def fit(txt, size, largura, k=0.62):
    """reduz o tamanho para o texto caber na largura (estimativa por caractere)."""
    return min(size, int(largura / max(1, len(txt) * k)))


class Cartao:
    def __init__(self, cid, ini, fim, trilha):
        self.id, self.ini, self.fim, self.trilha = cid, ini, fim, trilha
        self.html, self.js = [], []

    def el(self, html):
        self.html.append(html)

    def tw(self, linha):
        self.js.append(linha)

    # tempos locais -> absolutos
    def a(self, t):
        return round(self.ini + t, 3)

    def saida(self, ids, dur=0.35):
        for i in ids:
            self.tw(f'tl.to("#{i}", {{ opacity: 0, duration: {dur}, ease: "power2.in" }}, {self.fim - dur:.3f});')


def titulo2(c, p):
    """Duas linhas centradas na faixa de cima: cima = Playfair itálico branco, baixo = Inter Black amarelo caixa alta."""
    y = p.get("y", 262)
    cima, baixo = p["cima"], p["baixo"].upper()
    sc, sb = p.get("sc", 54), fit(p["baixo"], p.get("sb", 96), 940)
    tb = p.get("t_b", 0.22)
    c.el(f'<div id="{c.id}_c" class="t-cima" style="top:{y}px;font-size:{sc}px">{cima}</div>')
    c.el(f'<div id="{c.id}_b" class="t-baixo" style="top:{y + sc + 14}px;font-size:{sb}px">{baixo}</div>')
    c.el(f'<div id="{c.id}_l" class="traco" style="top:{y + sc + 14 + sb + 20}px;left:{(W - 220) // 2}px;width:220px"></div>')
    c.tw(f'tl.fromTo("#{c.id}_c", {{ opacity: 0, y: 26 }}, {{ opacity: 1, y: 0, duration: 0.55, ease: "power3.out" }}, {c.a(0.0)});')
    c.tw(f'tl.fromTo("#{c.id}_b", {{ opacity: 0, y: 40, scale: 1.12 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.8, ease: "expo.out" }}, {c.a(tb)});')
    c.tw(f'tl.fromTo("#{c.id}_l", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.6, ease: "power2.out" }}, {c.a(tb + 0.3)});')
    c.saida([f"{c.id}_c", f"{c.id}_b", f"{c.id}_l"])


def setas(c, p):
    """A -> B na faixa de cima: A branco itálico, seta amarela que se desenha, B amarelo Inter Black."""
    y = p.get("y", 320)
    a, b = p["a"], p["b"].upper()
    sa, sb = fit(p["a"], 72, 330, 0.5), fit(p["b"], 92, 360)
    c.el(f'<div id="{c.id}_a" class="t-cima" style="top:{y}px;left:60px;width:360px;text-align:right;font-size:{sa}px;line-height:{sb}px">{a}</div>')
    c.el(f'<svg id="{c.id}_s" style="position:absolute;left:430px;top:{y + 8}px" width="200" height="{sb}" viewBox="0 0 200 {sb}">'
         f'<path id="{c.id}_p" d="M10 {sb / 2} L170 {sb / 2} M140 {sb / 2 - 24} L172 {sb / 2} L140 {sb / 2 + 24}" fill="none" stroke="{AMARELO}" '
         f'stroke-width="7" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/></svg>')
    c.el(f'<div id="{c.id}_b" class="t-baixo" style="top:{y}px;left:640px;width:400px;text-align:left;font-size:{sb}px;line-height:{sb}px">{b}</div>')
    c.tw(f'tl.fromTo("#{c.id}_a", {{ opacity: 0, x: -30 }}, {{ opacity: 1, x: 0, duration: 0.6, ease: "power3.out" }}, {c.a(0.0)});')
    c.tw(f'tl.to("#{c.id}_p", {{ strokeDashoffset: 0, duration: 0.7, ease: "power2.inOut" }}, {c.a(0.45)});')
    c.tw(f'tl.fromTo("#{c.id}_b", {{ opacity: 0, x: 30, scale: 1.1 }}, {{ opacity: 1, x: 0, scale: 1, duration: 0.7, ease: "expo.out" }}, {c.a(p.get("t_b", 0.9))});')
    c.saida([f"{c.id}_a", f"{c.id}_s", f"{c.id}_b"])


def lista(c, p):
    """Coluna esquerda: itens [(t, texto)] com traço amarelo + número; entram conforme a fala."""
    y0, passo = p.get("y", 560), p.get("passo", 118)
    if p.get("titulo"):
        c.el(f'<div id="{c.id}_h" class="mini" style="left:56px;top:{y0 - 70}px">{p["titulo"].upper()}</div>')
        c.tw(f'tl.fromTo("#{c.id}_h", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, {c.a(0)});')
    ids = [f"{c.id}_h"] if p.get("titulo") else []
    for i, (t, txt) in enumerate(p["itens"]):
        y = y0 + i * passo
        c.el(f'<div id="{c.id}_i{i}" class="item" style="left:56px;top:{y}px"><span class="barra"></span>'
             f'<span class="n">{p.get("marca", i + 1)}</span><span class="tx">{txt}</span></div>')
        c.tw(f'tl.fromTo("#{c.id}_i{i}", {{ opacity: 0, x: -50 }}, {{ opacity: 1, x: 0, duration: 0.6, ease: "power3.out" }}, {c.a(t)});')
        ids.append(f"{c.id}_i{i}")
    c.saida(ids)


def mapa(c, p):
    """Silhueta estilizada da França com pino pulsando no sudoeste (Biarritz). Coluna esquerda."""
    x0, y0, s = 70, p.get("y", 540), 380
    pts = [(.55, .02), (.74, .10), (.80, .19), (.90, .27), (.88, .40), (.93, .55), (.97, .68), (.84, .76), (.74, .84),
           (.58, .93), (.50, .98), (.30, .93), (.16, .90), (.10, .80), (.13, .66), (.15, .50), (.07, .42), (.00, .33),
           (.10, .29), (.22, .24), (.30, .15), (.42, .12)]
    d = "M" + " L".join(f"{x * s:.1f} {y * s:.1f}" for x, y in pts) + " Z"
    px, py = .13 * s, .88 * s
    c.el(f'<svg id="{c.id}_m" style="position:absolute;left:{x0}px;top:{y0}px;overflow:visible" width="{s}" height="{s}" viewBox="0 0 {s} {s}">'
         f'<path id="{c.id}_mp" d="{d}" fill="rgba(252,237,192,.10)" stroke="{AMARELO}" stroke-width="4" stroke-linejoin="round" '
         f'pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" style="filter:drop-shadow(0 3px 10px rgba(0,0,0,.45))"/>'
         f'<circle id="{c.id}_r" cx="{px}" cy="{py}" r="22" fill="none" stroke="{AMARELO}" stroke-width="4"/>'
         f'<circle id="{c.id}_d" cx="{px}" cy="{py}" r="11" fill="{AMARELO}"/></svg>')
    c.el(f'<div id="{c.id}_t" class="t-baixo" style="left:{x0 + 20}px;top:{y0 + s + 18}px;font-size:46px;text-align:left">{p["rotulo"].upper()}</div>')
    c.el(f'<div id="{c.id}_u" class="mini" style="left:{x0 + 20}px;top:{y0 + s + 74}px">{p.get("sub", "").upper()}</div>')
    c.tw(f'tl.to("#{c.id}_mp", {{ strokeDashoffset: 0, duration: 1.1, ease: "power2.inOut" }}, {c.a(0.0)});')
    c.tw(f'tl.fromTo("#{c.id}_d", {{ scale: 0, transformOrigin: "50% 50%" }}, {{ scale: 1, duration: 0.4, ease: "back.out(2)", transformOrigin: "50% 50%" }}, {c.a(p.get("t_pino", 0.9))});')
    c.tw(f'tl.fromTo("#{c.id}_r", {{ scale: 0.4, opacity: 0.9, transformOrigin: "50% 50%" }}, {{ scale: 2.6, opacity: 0, duration: 1.1, repeat: 3, ease: "power1.out", transformOrigin: "50% 50%" }}, {c.a(p.get("t_pino", 0.9) + 0.2)});')
    c.tw(f'tl.fromTo("#{c.id}_t", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }}, {c.a(p.get("t_pino", 0.9) + 0.1)});')
    c.tw(f'tl.fromTo("#{c.id}_u", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, {c.a(p.get("t_sub", 1.4))});')
    c.saida([f"{c.id}_m", f"{c.id}_t", f"{c.id}_u"])


def linha_tempo(c, p):
    """Linha do tempo horizontal na faixa de cima: nós [(t, ano, rótulo)] que acendem conforme a fala."""
    y = p.get("y", 330)
    n = p["nos"]
    x_ini, x_fim = 120, 960
    c.el(f'<div id="{c.id}_L" class="traco" style="top:{y + 62}px;left:{x_ini}px;width:{x_fim - x_ini}px;height:5px"></div>')
    c.tw(f'tl.fromTo("#{c.id}_L", {{ scaleX: 0, transformOrigin: "0% 50%" }}, {{ scaleX: 1, duration: 1.0, ease: "power2.inOut", transformOrigin: "0% 50%" }}, {c.a(0)});')
    ids = [f"{c.id}_L"]
    for i, (t, ano, rot) in enumerate(n):
        x = x_ini + (x_fim - x_ini) * i / max(1, len(n) - 1)
        c.el(f'<div id="{c.id}_n{i}" style="position:absolute;left:{x - 110:.0f}px;top:{y}px;width:220px;text-align:center">'
             f'<div class="ano">{ano}</div><div class="ponto"></div><div class="mini" style="margin-top:14px">{rot.upper()}</div></div>')
        c.tw(f'tl.fromTo("#{c.id}_n{i}", {{ opacity: 0, y: 24, scale: 0.9 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.6, ease: "back.out(1.6)" }}, {c.a(t)});')
        ids.append(f"{c.id}_n{i}")
    c.saida(ids)


def enquete(c, p):
    """Enquete estilo story, só contorno: pergunta em Playfair itálico + opções SIM/NÃO (coluna esquerda)."""
    y = p.get("y", 600)
    c.el(f'<div id="{c.id}_q" class="t-cima" style="left:56px;top:{y}px;width:460px;text-align:left;font-size:54px;line-height:64px">{p["pergunta"]}</div>')
    for i, op in enumerate(p["opcoes"]):
        c.el(f'<div id="{c.id}_o{i}" class="pill" style="left:{56 + i * 220}px;top:{y + 150}px">{op.upper()}</div>')
        c.tw(f'tl.fromTo("#{c.id}_o{i}", {{ opacity: 0, scale: 0.7 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "back.out(2)", transformOrigin: "50% 50%" }}, {c.a(0.6 + i * 0.18)});')
    c.tw(f'tl.fromTo("#{c.id}_q", {{ opacity: 0, x: -40 }}, {{ opacity: 1, x: 0, duration: 0.6, ease: "power3.out" }}, {c.a(0)});')
    c.saida([f"{c.id}_q"] + [f"{c.id}_o{i}" for i in range(len(p["opcoes"]))])


TIPOS = dict(titulo2=titulo2, setas=setas, lista=lista, mapa=mapa, linha_tempo=linha_tempo, enquete=enquete)

CSS = f"""
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: transparent; }}
#root {{ position: relative; width: {W}px; height: {H}px; }}
.card {{ position: absolute; left: 0; top: 0; width: {W}px; height: {H}px; }}
.card > * {{ position: absolute; }}
.t-cima {{ left: 0; width: {W}px; text-align: center; white-space: nowrap; color: #fff; font: italic 500 58px/1.1 "Playfair Display", serif;
  text-shadow: 0 3px 20px rgba(0,0,0,.55); }}
.t-baixo {{ left: 0; width: {W}px; text-align: center; white-space: nowrap; color: {AMARELO}; font-family: Inter, sans-serif; font-weight: 900;
  letter-spacing: -1px; line-height: 1.05; text-shadow: 0 4px 22px rgba(0,0,0,.5); }}
.traco {{ height: 6px; background: {AMARELO}; border-radius: 3px; box-shadow: 0 2px 10px rgba(0,0,0,.35); transform-origin: 50% 50%; }}
.mini {{ color: {AMARELO}; font: 700 24px Inter, sans-serif; letter-spacing: 5px; text-shadow: 0 2px 12px rgba(0,0,0,.6); white-space: nowrap; }}
.item {{ display: flex; align-items: center; gap: 18px; white-space: nowrap; }}
.item .barra {{ width: 6px; height: 64px; background: {AMARELO}; border-radius: 3px; box-shadow: 0 2px 10px rgba(0,0,0,.35); }}
.item .n {{ color: {AMARELO}; font: 900 54px Inter, sans-serif; text-shadow: 0 3px 16px rgba(0,0,0,.55); }}
.item .tx {{ color: #fff; font: 800 44px/1.1 Inter, sans-serif; text-shadow: 0 3px 18px rgba(0,0,0,.6); }}
.ano {{ color: {AMARELO}; font: 900 58px Inter, sans-serif; text-shadow: 0 3px 16px rgba(0,0,0,.55); }}
.ponto {{ width: 22px; height: 22px; border-radius: 50%; background: {AMARELO}; margin: 6px auto 0; box-shadow: 0 2px 10px rgba(0,0,0,.4); }}
.pill {{ width: 190px; height: 76px; border: 4px solid {AMARELO}; border-radius: 38px; color: {AMARELO}; font: 900 34px/68px Inter, sans-serif;
  text-align: center; letter-spacing: 3px; text-shadow: 0 2px 12px rgba(0,0,0,.55); box-shadow: 0 3px 14px rgba(0,0,0,.3); }}
"""


def gerar(cartoes, saida, duracao, fps=30):
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    blocos, js = [], []
    for i, (tipo, ini, fim, p) in enumerate(cartoes):
        c = Cartao(f"k{i:02d}", ini, fim, i)
        TIPOS[tipo](c, p)
        blocos.append(f'<div id="{c.id}" class="card clip" data-start="{ini}" data-duration="{round(fim - ini, 3)}" data-track-index="{i}">\n  '
                      + "\n  ".join(c.html) + "\n</div>")
        js += c.js
    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,500;1,700&family=Inter:wght@700;800;900&display=swap" />
<style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{duracao}" data-width="{W}" data-height="{H}">
{chr(10).join(blocos)}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body>
</html>
"""
    (saida / "index.html").write_text(html, encoding="utf-8")
    base = Path(__file__).parent
    for nome in ("hyperframes.json", "meta.json", "package.json"):
        f = base / "projeto_base" / nome
        if f.exists():
            (saida / nome).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")


if __name__ == "__main__":
    cartoes = json.load(open(sys.argv[1]))
    dur = max(c[2] for c in cartoes) + DUR_PAD
    gerar(cartoes, sys.argv[2], round(dur, 3))
    print(f"{len(cartoes)} cartões, duração {dur:.1f}s -> {sys.argv[2]}/index.html")
