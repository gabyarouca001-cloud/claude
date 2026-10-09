"""Gera a página de revisão dos inserts (HTML para publicar como Artifact): cada inserção com miniatura, tempo, fala e a escolha
Manter / Apagar / Alterar. As miniaturas saem da prévia já renderizada. Rodar em /home/user/work/cur:
  python3 revisao_gerar.py previa_curadoria_720p.mp4 /caminho/saida.html"""
import base64
import json
import os
import subprocess
import sys
import tempfile

import edl
from edl import PAL, achar

VIDEO, SAIDA = sys.argv[1], sys.argv[2]
AQUI = os.path.dirname(os.path.abspath(__file__))

NOME_FULL = {
    "f_boutique": "Foto do letreiro da boutique Chanel", "f_passarela": "Vídeo de passarela (banco de imagens)",
    "f_biarritz": "Foto da praia de Biarritz", "f_ondas": "Vídeo de ondas na praia (banco)", "f_desk": "Foto de Gabrielle Chanel, 1931",
    "f_liberdade": "Vídeo de mulher na praia (banco)", "f_mulher_mar": "Vídeo de mulher de branco olhando o mar (banco)",
    "f_pe_nu": "Vídeo de mulher andando descalça na praia (banco)", "f_lagerfeld": "Foto do letreiro Karl Lagerfeld",
    "f_tapete": "Vídeo de tapete vermelho (banco)", "f_flashes": "Vídeo de estúdio com fotógrafo (banco)",
}


def fala(t, n=3.2):
    pal = []
    for w in PAL:
        if t - 0.25 <= w["s"] <= t + n:
            x = w["w"].strip()
            base = "".join(c for c in x if c.isalnum() or c == "ó")
            pal.append(x.replace(base, edl.FIX[edl.norm(base)]) if edl.norm(base) in edl.FIX else x)
    return " ".join(pal)


def mmss(t):
    return f"{int(t // 60)}:{t % 60:04.1f}".replace(".", ",")


itens = []
ev = edl.resolver()
for e in ev["full"]:
    itens.append(dict(id=e["nome"], tipo="Cena em tela cheia", t=e["t"], dur=round(e["fim"] - e["t"], 1),
                      titulo=NOME_FULL.get(e["nome"], e["nome"]), rotulo=e["rot"] or "", ft=e["t"] + min(0.7, (e["fim"] - e["t"]) / 2)))
for e in ev["pol"]:
    itens.append(dict(id=e["nome"], tipo="Foto com moldura", t=e["t"], dur=round(e["fim"] - e["t"], 1),
                      titulo="Foto antiga ao lado dela: " + e["rot"], rotulo=e["rot"], ft=e["t"] + 0.8))
for e in ev["cart"]:
    linhas = " · ".join(l[0] for l in e["linhas"])
    itens.append(dict(id=e["nome"], tipo="Cartão de texto", t=e["t"], dur=round(e["fim"] - e["t"], 1), titulo=linhas, rotulo="", ft=e["t"] + 0.9))
for e in ev["bal"]:
    itens.append(dict(id=e["nome"], tipo="Balão", t=e["t"], dur=round(e["fim"] - e["t"], 1), titulo=e["txt"], rotulo="", ft=e["t"] + 0.6))
# destaques (ids d0..d12 na ordem do edl original, antes de qualquer remoção)
orig = [d for d in __import__("importlib").import_module("edl").DESTAQUES]
for n, (fr, tipo, partes, perto) in enumerate(orig):
    i, j = achar(fr, perto)
    ini, fim = PAL[i]["s"], PAL[j]["e"]
    if tipo == "rubik":
        txt = " ".join(" ".join(l) for l in partes)
    elif tipo == "amatic":
        txt = " ".join(partes)
    else:
        txt = " ".join(" ".join(p for p, _ in l) for l in partes)
    estilo = {"rubik": "amarelo grande", "playfair": "itálico branco e dourado", "amatic": "letra a letra"}[tipo]
    itens.append(dict(id=f"d{n}", tipo="Legenda em destaque", t=round(ini, 2), dur=round(fim - ini, 1), titulo=txt.upper() if tipo != "playfair" else txt,
                      rotulo=estilo, ft=max(ini + 0.2, fim - 0.15)))
itens.sort(key=lambda x: x["t"])

with tempfile.TemporaryDirectory() as tmp:
    for it in itens:
        arq = f"{tmp}/{it['id']}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{it['ft']:.2f}", "-i", VIDEO, "-frames:v", "1", "-vf", "scale=216:384",
                        "-q:v", "6", arq], check=True)
        it["img"] = "data:image/jpeg;base64," + base64.b64encode(open(arq, "rb").read()).decode()
        it["fala"] = fala(it["t"])
        it["tempo"] = mmss(it["t"])
        del it["ft"]
dados = json.dumps(itens, ensure_ascii=False)
html = open(f"{AQUI}/revisao_template.html", encoding="utf-8").read().replace("/*DADOS*/[]", dados)
open(SAIDA, "w", encoding="utf-8").write(html)
print(len(itens), "itens;", round(os.path.getsize(SAIDA) / 1e6, 2), "MB")
