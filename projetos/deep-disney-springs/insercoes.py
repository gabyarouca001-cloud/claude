"""Inserções "mágicas" (texto animado com pó de fada) para o Reel do Disney Springs. Só ADICIONA: o vídeo da editora não é alterado.
Gera PNGs com transparência (30 fps) por inserção em ov_<S>/<nome>/ + ov_<S>/eventos.json (instantes dos efeitos sonoros).
S=1 → 1080x1920 (prévia) | S=2 → 2160x3840 (final).   Uso (em /home/user/work/ep): S=1 python3 insercoes.py [nome ...]"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = int(os.environ.get("S", "1"))
W, H = 1080 * S, 1920 * S
FPS = 30
FONTES = "/home/user/work/fonts"
MANTEIGA = (252, 237, 192)
OURO_TOPO = (255, 246, 212)
OURO_BASE = (240, 202, 104)
BRANCO = (255, 255, 255)
SAIDA = f"ov_{S}"


def fonte(arq, tam, wght=None):
    f = ImageFont.truetype(f"{FONTES}/{arq}", int(tam * S))
    if wght is not None:
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    return f


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ brilhos
def _sprite(n=192):
    y, x = np.mgrid[-1:1:n * 1j, -1:1:n * 1j]
    h = np.exp(-(y / 0.045) ** 2) * np.exp(-(np.abs(x) / 0.55) ** 1.3)
    v = np.exp(-(x / 0.045) ** 2) * np.exp(-(np.abs(y) / 0.55) ** 1.3)
    g = np.exp(-((x ** 2 + y ** 2) ** 0.5 / 0.16) ** 2)
    return np.clip(h + v + 0.9 * g, 0, 1).astype(np.float32)


SPR = _sprite()
SPR_IMG = Image.fromarray((SPR * 255).astype(np.uint8), "L")


def estrela(canvas, x, y, tam, alpha=1.0, giro=0.0, cor=(255, 247, 214)):
    """estrela de 4 pontas com brilho central; canvas é RGBA (mistura por alfa máxima)"""
    tam = max(int(tam), 2)
    sp = SPR_IMG.resize((tam, tam), Image.BICUBIC)
    if giro:
        sp = sp.rotate(giro, resample=Image.BICUBIC)
    a = sp.point(lambda v: int(v * alpha))
    cam = Image.new("RGBA", sp.size, cor + (0,))
    cam.putalpha(a)
    canvas.alpha_composite(cam, (int(x - tam / 2), int(y - tam / 2)))


class Poeira:
    """partículas que nascem ao longo de um caminho (cabeça de varinha) e caem"""

    def __init__(self, caminho, t0, dur, seed=1, n_por_s=90, vida=(0.5, 1.0), tam=(14, 40), cor=(255, 247, 214)):
        self.caminho, self.t0, self.dur, self.cor = caminho, t0, dur, cor
        rng = np.random.default_rng(seed)
        self.p = []
        n = int(n_por_s * dur)
        for _ in range(n):
            u = rng.uniform(0, 1)
            nasc = t0 + u * dur
            x, y = caminho(u)
            self.p.append(dict(nasc=nasc, x=x + rng.normal(0, 14), y=y + rng.normal(0, 14), vx=rng.normal(0, 22), vy=rng.uniform(10, 70),
                               vida=rng.uniform(*vida), tam=rng.uniform(*tam), fase=rng.uniform(0, 6.28), giro=rng.uniform(0, 90)))

    def desenhar(self, canvas, t):
        for q in self.p:
            a = t - q["nasc"]
            if a < 0 or a > q["vida"]:
                continue
            k = a / q["vida"]
            pisca = 0.55 + 0.45 * math.sin(a * 24 + q["fase"])
            alpha = (1 - k) ** 1.2 * min(a / 0.05, 1.0) * pisca
            x = q["x"] + q["vx"] * a * S
            y = q["y"] + q["vy"] * a * S + 90 * a * a * S
            estrela(canvas, x, y, q["tam"] * S * (1 - 0.45 * k), alpha, q["giro"] + 60 * a, self.cor)
        # cabeça brilhante
        u = (t - self.t0) / self.dur
        if 0 <= u <= 1:
            x, y = self.caminho(u)
            estrela(canvas, x, y, 120 * S, 1.0, 0, self.cor)


def explosao(canvas, cx, cy, t, t0, seed=5, n=26, raio=380, cor=(255, 247, 214)):
    a = t - t0
    if a < 0 or a > 1.0:
        return
    rng = np.random.default_rng(seed)
    for i in range(n):
        ang = rng.uniform(0, 6.28)
        v = rng.uniform(0.35, 1.0)
        vida = rng.uniform(0.5, 1.0)
        if a > vida:
            continue
        k = a / vida
        d = raio * S * v * ease_out(k)
        estrela(canvas, cx + math.cos(ang) * d, cy + math.sin(ang) * d + 40 * S * k * k, rng.uniform(16, 44) * S * (1 - 0.5 * k),
                (1 - k) * (0.6 + 0.4 * math.sin(a * 30 + i)), rng.uniform(0, 90), cor)


# ------------------------------------------------------------------ texto
def gradiente(w, h, topo=OURO_TOPO, base=OURO_BASE):
    g = np.linspace(0, 1, h)[:, None, None]
    arr = np.array(topo)[None, None, :] * (1 - g) + np.array(base)[None, None, :] * g
    return Image.fromarray(np.repeat(arr, w, 1).astype(np.uint8), "RGB")


def camada_texto(txt, f, cor="gradiente", espaco=0, largura=None):
    """máscara do texto (L) + caixa. espaco = tracking em px (já em escala S)"""
    if espaco:
        larg = sum(f.getlength(c) for c in txt) + espaco * (len(txt) - 1)
    else:
        larg = f.getlength(txt)
    asc, desc = f.getmetrics()
    m = Image.new("L", (int(larg) + 8 * S, asc + desc + 8 * S), 0)
    d = ImageDraw.Draw(m)
    if espaco:
        x = 4 * S
        for c in txt:
            d.text((x, 4 * S), c, font=f, fill=255)
            x += f.getlength(c) + espaco
    else:
        d.text((4 * S, 4 * S), txt, font=f, fill=255)
    return m


def colar_texto(canvas, mascara, cx, cy, cor="gradiente", alpha=1.0, escala=1.0, dy=0.0, brilho=True, sombra=True):
    if escala != 1.0:
        mascara = mascara.resize((max(int(mascara.width * escala), 2), max(int(mascara.height * escala), 2)), Image.LANCZOS)
    x = int(cx - mascara.width / 2)
    y = int(cy - mascara.height / 2 + dy)
    pad = 60 * S
    layer = Image.new("RGBA", (mascara.width + 2 * pad, mascara.height + 2 * pad), (0, 0, 0, 0))
    mp = Image.new("L", layer.size, 0)
    mp.paste(mascara, (pad, pad))
    mp = mp.point(lambda v: int(v * alpha))
    if sombra:
        for raio, forca, desl in ((10, 0.75, 5), (3, 0.5, 2)):
            sh = mp.filter(ImageFilter.GaussianBlur(raio * S)).point(lambda v, f=forca: min(int(v * f * 1.6), 255))
            sh_l2 = Image.new("RGBA", layer.size, (0, 0, 0, 0))
            sh_l2.paste(Image.new("RGBA", layer.size, (0, 0, 0, 255)), (0, desl * S), sh)
            layer.alpha_composite(sh_l2)
    if cor == "gradiente":
        borda = mp.filter(ImageFilter.MaxFilter(2 * int(2.2 * S) + 1)).point(lambda v: int(v * 0.85))
        b_l = Image.new("RGBA", layer.size, (104, 72, 20, 0))
        b_l.putalpha(borda)
        layer.alpha_composite(b_l)
    if brilho:
        gl = mp.filter(ImageFilter.GaussianBlur(14 * S)).point(lambda v: int(v * 0.42))
        gl_l = Image.new("RGBA", layer.size, MANTEIGA + (0,))
        gl_l.putalpha(gl)
        layer.alpha_composite(gl_l)
    if cor == "gradiente":
        fill = gradiente(layer.width, layer.height).convert("RGBA")
    else:
        fill = Image.new("RGBA", layer.size, tuple(cor) + (255,))
    fill.putalpha(mp)
    layer.alpha_composite(fill)
    canvas.alpha_composite(layer, (x - pad, y - pad))


def veu(canvas, cx, cy, w, h, alpha):
    """escurecimento esfumado e quase invisível atrás do texto, para ler sobre céu/parede clara (não é um bloco)"""
    if alpha <= 0.01:
        return
    pad = 160 * S
    m = Image.new("L", (int(w * S) + 2 * pad, int(h * S) + 2 * pad), 0)
    ImageDraw.Draw(m).ellipse((pad, pad, pad + int(w * S), pad + int(h * S)), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(70 * S)).point(lambda v: int(v * 0.26 * alpha))
    l = Image.new("RGBA", m.size, (0, 0, 0, 0))
    l.putalpha(m)
    canvas.alpha_composite(l, (int(cx - m.width / 2), int(cy - m.height / 2)))


PEDIDOS = set()


def salvar(nome, k, img):
    """grava o quadro já no disco (em 4K a lista inteira não cabe na memória) e devolve só o índice"""
    if not PEDIDOS or nome in PEDIDOS:
        pasta = f"{SAIDA}/{nome}"
        os.makedirs(pasta, exist_ok=True)
        img.save(f"{pasta}/{k:04d}.png", compress_level=1)
    return k


def novo():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


# ------------------------------------------------------------------ inserções
def arco(x0, y0, x1, y1, curva):
    def f(u):
        x = x0 + (x1 - x0) * ease_io(u)
        y = y0 + (y1 - y0) * u + curva * math.sin(math.pi * u)
        return x * S, y * S
    return f


def odometro(canvas, valores_pos, digitos, f, cx, cy, largura_dig, alpha=1.0, escala=1.0):
    """colunas de dígitos que rolam. valores_pos[i]: posição contínua (em dígitos) da coluna i; digitos[i]: lista cíclica de caracteres"""
    LH = int(f.getmetrics()[0] + f.getmetrics()[1])
    n = len(digitos)
    tot = largura_dig * n
    for i in range(n):
        pos = valores_pos[i]
        janela = Image.new("L", (int(largura_dig) + 12 * S, int(LH * 0.98)), 0)
        d = ImageDraw.Draw(janela)
        base = math.floor(pos)
        for k in (base - 1, base, base + 1, base + 2):
            ch = digitos[i][k % len(digitos[i])]
            yk = (k - pos) * LH * 0.98
            d.text((int((largura_dig + 12 * S - f.getlength(ch)) / 2), int(yk - LH * 0.06)), ch, font=f, fill=255)
        # esmaece topo/base da janela (efeito de rolo)
        fade = np.ones(janela.height, np.float32)
        m = int(janela.height * 0.2)
        fade[:m] = np.linspace(0.0, 1, m)
        fade[-m:] = np.linspace(1, 0.0, m)
        janela = Image.fromarray((np.asarray(janela, np.float32) * fade[:, None]).astype(np.uint8), "L")
        x = cx - tot / 2 + largura_dig * (i + 0.5)
        colar_texto(canvas, janela, x, cy, "gradiente", alpha, escala)


def insercao_ano(ev, ano="1975", t0=14.45, t1=16.55):
    """1975: pó de fada varre a tela, o número rola feito um contador e pousa (acorde) junto com a fala"""
    nome = "ano_1975"
    f = fonte("PlayfairBlackItalic.ttf", 270)
    cx, cy = W / 2, 700 * S
    larg = max(f.getlength(c) for c in "0123456789")
    dur = t1 - t0
    R = 0.12                              # início das colunas (s após t0)
    DUR_ROLO = 0.55
    alvos = [(1, 0.0, 0), (9, 0.0, 0), (7, 0.0, 0), (5, 0.20, 1)]     # (dígito, atraso, ciclos extras)
    digs = [list("0123456789")] * 4
    pouso = t0 + R + 0.20 + DUR_ROLO + 0.04
    ev.append((t0, "varredura"))
    for k in range(7):
        ev.append((t0 + R + 0.04 + k * 0.06, "tique"))
    for k in range(14):
        ev.append((t0 + R + 0.20 + 0.03 + k * 0.032, "tique2"))
    ev.append((pouso, "acorde"))
    ev.append((t1 - 0.30, "saida"))
    poeira = Poeira(arco(60, 900, 1020, 560, -140), t0, 0.5, seed=11)
    quadros = []
    for i in range(int(dur * FPS)):
        t = t0 + i / FPS
        c = novo()
        a = t - t0
        al = min(ease_out(a / 0.30), 1 - ease_io((a - (dur - 0.35)) / 0.35))
        pos = []
        for j, (alvo, atraso, ciclos) in enumerate(alvos):
            if j < 2:
                pos.append(float(alvo))
            else:
                u = (a - R - atraso) / DUR_ROLO
                total = alvo + ciclos * 10
                pos.append(alvo + (ease_out(u) - 1) * total)
        esc = 0.92 + 0.08 * ease_out(a / 0.35) + 0.05 * math.exp(-((t - pouso) / 0.12) ** 2) * (1 if t >= pouso - 0.05 else 0)
        veu(c, cx, cy, 980, 520, al * 0.3)
        odometro(c, pos, digs, f, cx, cy, larg * 1.02, al, esc)
        poeira.desenhar(c, t)
        explosao(c, cx, cy, t, pouso, seed=9)
        quadros.append(salvar(nome, len(quadros), c))
    return nome, quadros, t0


def contador_texto(v, casas_milhar=False):
    s = f"{int(round(v)):d}"
    if casas_milhar and len(s) > 3:
        s = s[:-3] + "." + s[-3:]
    return s


def insercao_contador(ev, nome, t0, t1, topo, grande, base, final, prefixo="", casas_milhar=False, t_pouso=None, y=700, cor_base="gradiente", tam_num=290, tam_base=96, trac=14):
    f_top = fonte("PlayfairBoldItalic.ttf", 80)
    f_big = fonte("PlayfairBlackItalic.ttf", tam_num)
    f_base = fonte("InterBlack.ttf", tam_base, 900)
    f_big_largura = f_big.getlength(prefixo + contador_texto(final, casas_milhar))
    cx, cy = W / 2, y * S
    dur = t1 - t0
    ev.append((t0, "varredura"))
    t_cont = 0.62
    for k in range(10):
        ev.append((t0 + 0.12 + k * 0.06, "tique"))
    pouso = t0 + 0.12 + t_cont
    ev.append((pouso, "acorde"))
    ev.append((t1 - 0.30, "saida"))
    poeira = Poeira(arco(1020, 520, 60, 860, 130), t0, 0.5, seed=21)
    quadros = []
    for i in range(int(dur * FPS)):
        t = t0 + i / FPS
        a = t - t0
        c = novo()
        al = min(ease_out(a / 0.28), 1 - ease_io((a - (dur - 0.35)) / 0.35))
        u = (a - 0.12) / t_cont
        v = final * ease_out(u)
        txt = prefixo + contador_texto(v, casas_milhar)
        # largura fixa: ancora pela largura final, alinhando à esquerda do número
        veu(c, cx, cy, 980, 640, al)
        m = camada_texto(txt, f_big)
        mf = camada_texto(prefixo + contador_texto(final, casas_milhar), f_big)
        esc = 0.94 + 0.06 * ease_out(a / 0.35) + 0.045 * math.exp(-((a - (pouso - t0)) / 0.12) ** 2)
        colar_texto(c, m, cx - mf.width / 2 + m.width / 2, cy, "gradiente", al, esc)
        if topo:
            colar_texto(c, camada_texto(topo, f_top), cx, cy - 215 * S, BRANCO, al * ease_out((a - 0.1) / 0.3), brilho=False)
        if base:
            colar_texto(c, camada_texto(base, f_base, espaco=trac * S), cx, cy + 215 * S, MANTEIGA if cor_base != "gradiente" else "gradiente",
                        al * ease_out((a - 0.45) / 0.3))
        poeira.desenhar(c, t)
        explosao(c, cx, cy, t, pouso, seed=3 + int(final) % 7)
        quadros.append(salvar(nome, len(quadros), c))
    return nome, quadros, t0


def insercao_lista(ev, t0, t1, itens):
    """lista à esquerda (padrão DEEP): estrela-brilho + texto Inter Black; item a item, na hora da fala. itens=[(t_entrada, linha_topo, linha_forte)]"""
    nome = "lista_gratis"
    f_t = fonte("PlayfairBoldItalic.ttf", 62)
    f_g = fonte("InterBlack.ttf", 86, 900)
    x0 = 96 * S
    y0 = 330 * S
    passo = 142 * S
    ev.append((t1 - 0.30, "saida"))
    quadros = []
    pos = [(ti, ln1, ln2) for ti, ln1, ln2 in itens]
    for ti, _, _ in pos:
        ev.append((ti, "ding"))
    poeiras = [Poeira(arco(60, y0 / S + passo / S * k + 30, 420, y0 / S + passo / S * k + 30, -30), ti - 0.05, 0.3, seed=40 + k, n_por_s=70, tam=(12, 30))
               for k, (ti, _, _) in enumerate(pos)]
    for i in range(int((t1 - t0) * FPS)):
        t = t0 + i / FPS
        c = novo()
        saida = 1 - ease_io((t - (t1 - 0.35)) / 0.35)
        veu(c, 420 * S, y0 + passo * 1.0, 900, 640, saida * min(1, max(0, (t - pos[0][0]) / 0.3)))
        for k, (ti, ln1, ln2) in enumerate(pos):
            a = t - ti
            if a < 0:
                continue
            al = ease_out(a / 0.25) * saida
            y = y0 + passo * k
            desl = (1 - ease_out(a / 0.3)) * -60 * S
            estrela(c, x0 - 36 * S + desl, y + 8 * S, 70 * S, al, 0.0)
            mt = camada_texto(ln1, f_t)
            mg = camada_texto(ln2, f_g, espaco=4 * S)
            colar_texto(c, mt, x0 + 22 * S + mt.width / 2 + desl, y - 46 * S, BRANCO, al, brilho=False)
            colar_texto(c, mg, x0 + 22 * S + mg.width / 2 + desl, y + 22 * S, MANTEIGA, al)
            poeiras[k].desenhar(c, t)
        quadros.append(salvar(nome, len(quadros), c))
    return nome, quadros, t0


def insercao_areas(ev, t0, t1, tempos_pontos):
    """4 ÁREAS: número grande + quatro estrelas que acendem uma a uma a cada 'época' (cada uma tem cara de uma época)"""
    nome = "quatro_areas"
    f_big = fonte("PlayfairBlackItalic.ttf", 300)
    f_base = fonte("InterBlack.ttf", 96, 900)
    f_top = fonte("PlayfairBoldItalic.ttf", 78)
    cx, cy = W / 2, 700 * S
    ev.append((t0, "varredura"))
    notas = ["nota1", "nota2", "nota3", "nota4"]
    for tp, nt in zip(tempos_pontos, notas):
        ev.append((tp, nt))
    ev.append((t1 - 0.30, "saida"))
    poeira = Poeira(arco(60, 560, 1020, 840, 120), t0, 0.5, seed=31)
    quadros = []
    dur = t1 - t0
    for i in range(int(dur * FPS)):
        t = t0 + i / FPS
        a = t - t0
        c = novo()
        al = min(ease_out(a / 0.28), 1 - ease_io((a - (dur - 0.35)) / 0.35))
        esc = 0.92 + 0.08 * ease_out(a / 0.35)
        veu(c, cx, cy + 40 * S, 980, 760, al)
        colar_texto(c, camada_texto("são", f_top), cx, cy - 215 * S, BRANCO, al * ease_out((a - 0.05) / 0.3), brilho=False)
        colar_texto(c, camada_texto("4", f_big), cx, cy, "gradiente", al, esc)
        colar_texto(c, camada_texto("ÁREAS", f_base, espaco=14 * S), cx, cy + 215 * S, "gradiente", al * ease_out((a - 0.3) / 0.3))
        for k, tp in enumerate(tempos_pontos):
            x = cx + (k - 1.5) * 150 * S
            y = cy + 330 * S
            ba = t - tp
            fraco = 0.28
            if ba < 0:
                estrela(c, x, y, 70 * S, fraco * al)
            else:
                pulso = 1 + 0.55 * math.exp(-ba / 0.18)
                estrela(c, x, y, 130 * S * pulso, al, ba * 40)
        poeira.desenhar(c, t)
        quadros.append(salvar(nome, len(quadros), c))
    return nome, quadros, t0


def insercao_anos60(ev, t0, t1):
    nome = "anos_60"
    f_big = fonte("PlayfairBlackItalic.ttf", 300)
    f_top = fonte("PlayfairBoldItalic.ttf", 84)
    cx, cy = W / 2, 700 * S
    ev.append((t0, "varredura"))
    ev.append((t0 + 0.30, "acorde"))
    ev.append((t1 - 0.30, "saida"))
    poeira = Poeira(arco(1020, 900, 60, 560, -120), t0, 0.5, seed=51)
    quadros = []
    dur = t1 - t0
    for i in range(int(dur * FPS)):
        t = t0 + i / FPS
        a = t - t0
        c = novo()
        al = min(ease_out(a / 0.28), 1 - ease_io((a - (dur - 0.35)) / 0.35))
        pop = 0.55 + 0.45 * ease_out((a - 0.2) / 0.35) + 0.07 * math.exp(-((a - 0.45) / 0.12) ** 2)
        veu(c, cx, cy, 980, 560, al * 0.6)
        colar_texto(c, camada_texto("anos", f_top), cx, cy - 215 * S, BRANCO, al * ease_out((a - 0.05) / 0.3), brilho=False)
        colar_texto(c, camada_texto("60", f_big), cx, cy, "gradiente", al * ease_out((a - 0.15) / 0.25), pop)
        poeira.desenhar(c, t)
        explosao(c, cx, cy, t, t0 + 0.30, seed=61, n=18, raio=300)
        quadros.append(salvar(nome, len(quadros), c))
    return nome, quadros, t0


def construir():
    """lista de funções (uma por inserção) + eventos de som; cada função gera os quadros só quando chamada (poupa memória em 4K)"""
    ev = []
    obras = [
        lambda: insercao_ano(ev),
        lambda: insercao_contador(ev, "mais_150", 29.50, 32.35, "mais de", None, "LOJAS", 150, tam_num=300),
        lambda: insercao_lista(ev, 36.90, 41.85, [(37.35, "sem", "INGRESSO"), (38.45, "sem", "PORTÃO"), (39.70, "estacionamento", "GRÁTIS")]),
        lambda: insercao_areas(ev, 47.85, 51.15, [48.75, 49.25, 49.75, 50.25]),
        lambda: insercao_contador(ev, "m2_4700", 57.90, 61.00, "são", None, "M² DE PRODUTOS", 4700, casas_milhar=True, y=700, tam_num=250, tam_base=64, trac=6),
        lambda: insercao_anos60(ev, 64.95, 67.15),
    ]
    return obras, ev


if __name__ == "__main__":
    PEDIDOS.update(sys.argv[1:])
    os.makedirs(SAIDA, exist_ok=True)
    obras, ev = construir()
    manifesto = []
    for fn in obras:
        nome, quadros, t0 = fn()
        if PEDIDOS and nome not in PEDIDOS:
            continue
        manifesto.append(dict(nome=nome, t0=t0, n=len(quadros)))
        print(nome, len(quadros), "quadros", flush=True)
    json.dump(dict(inserts=manifesto, eventos=sorted(ev)), open(f"{SAIDA}/manifesto.json", "w"), indent=1)
