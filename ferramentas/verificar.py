"""Verificação do vídeo renderizado antes de mostrar a prévia ou entregar o 4K.

Mede o ARQUIVO FINAL (não o que o script planejou) e gera um relatório honesto, item a item, com um destes status:
  ✔ verificado   ✘ falhou   ⚠ revisar (candidato: precisa de olho humano)   – não verificado

O que faz:
  - arquivo: decodifica inteiro, streams, resolução, fps e duração (se esperados forem informados)
  - áudio: loudness integrado (LUFS) e true peak medidos com ebur128; buracos de silêncio
  - vídeo: quadros pretos e imagem congelada
  - cortes (--plano ou --pontos): estalo de áudio em cada corte + folha com quadros antes/depois e a onda
  - folha de quadros do vídeo inteiro (um quadro a cada --passo segundos), com tonemap se o bruto for HDR
  - falas (--falas voz_16k.wav): roda checar_falas.py (gagueira/repetição que o Whisper em janela longa 'limpa')
Nunca diz que ouviu ou assistiu: escuta e conferência visual da folha ficam como 'não verificado' para o humano.

Uso: python3 ferramentas/verificar.py video.mp4 [--plano plano.json | --pontos 12.4,30.1] [--falas voz_16k.wav]
Saída: pasta verificacao_<nome>/ com relatorio.md, relatorio.json, folha_XX.jpg e cortes_XX.jpg. Código de saída 1 se algo falhou.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SR = 48000
OK, FALHOU, REVISAR, NAO = "verificado", "falhou", "revisar", "não verificado"
SIMBOLO = {OK: "✔", FALHOU: "✘", REVISAR: "⚠", NAO: "–"}
CHECAR_FALAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "projetos", "deep-ep2", "edicao",
                            "checar_falas.py")
# HDR (iPhone HLG/PQ) -> SDR só para as miniaturas; a cor do arquivo nunca é alterada
TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
           "zscale=t=bt709:m=bt709:r=tv,format=yuv420p,")


def mmss(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def rodar(cmd, binario=False):
    return subprocess.run(cmd, capture_output=True, text=not binario)


# ---------------------------------------------------------------- sondagem
def fracao(txt):
    a, _, b = (txt or "0/1").partition("/")
    return float(a) / float(b or 1) if float(b or 1) else 0.0


def sondar(arq):
    """Metadados do arquivo. Usa ffprobe; se não existir (ambiente antigo), lê a saída de `ffmpeg -i`."""
    if shutil.which("ffprobe"):
        r = rodar(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", arq])
        if r.returncode:
            raise SystemExit(f"ffprobe não conseguiu abrir o arquivo: {r.stderr.strip()[-300:]}")
        d = json.loads(r.stdout)
        v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
        a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
        return dict(duracao=float(d["format"].get("duration") or 0), tem_audio=a is not None, tem_video=v is not None,
                    largura=int(v["width"]) if v else 0, altura=int(v["height"]) if v else 0,
                    fps=fracao(v.get("avg_frame_rate")) if v else 0.0, codec=v["codec_name"] if v else "",
                    codec_audio=a["codec_name"] if a else "", transfer=(v or {}).get("color_transfer", ""),
                    pix_fmt=(v or {}).get("pix_fmt", ""))
    txt = rodar(["ffmpeg", "-hide_banner", "-i", arq]).stderr
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", txt)
    vid = re.search(r"Video: (\w+).*?, (\d{2,5})x(\d{2,5})[^,]*,.*?([\d.]+) fps", txt)
    return dict(duracao=int(dur[1]) * 3600 + int(dur[2]) * 60 + float(dur[3]) if dur else 0.0,
                tem_audio="Audio:" in txt, tem_video=vid is not None,
                largura=int(vid[2]) if vid else 0, altura=int(vid[3]) if vid else 0,
                fps=float(vid[4]) if vid else 0.0, codec=vid[1] if vid else "",
                codec_audio=(re.search(r"Audio: (\w+)", txt) or [0, ""])[1],
                transfer="arib-std-b67" if "arib-std-b67" in txt else "", pix_fmt="")


def filtro_cor(info):
    """Tonemap só se o arquivo for HDR e o ffmpeg tiver zscale; senão devolve vazio."""
    if info["transfer"] in ("arib-std-b67", "smpte2084") and "zscale" in rodar(["ffmpeg", "-filters"]).stdout:
        return TONEMAP
    return ""


# ---------------------------------------------------------------- medições
def decodifica(arq):
    """Decodifica o arquivo inteiro (vídeo + áudio); devolve as mensagens de erro do ffmpeg."""
    r = rodar(["ffmpeg", "-v", "error", "-i", arq, "-f", "null", "-"])
    return [l for l in r.stderr.splitlines() if l.strip()]


def medir_loudness(arq):
    r = rodar(["ffmpeg", "-hide_banner", "-nostats", "-i", arq, "-vn", "-af", "ebur128=peak=true:framelog=quiet",
               "-f", "null", "-"])
    resumo = r.stderr.split("Summary:")[-1]

    def pega(padrao):
        m = re.search(padrao, resumo)
        return float(m[1]) if m else None            # 'inf'/'-inf' também viram float
    return dict(lufs=pega(r"I:\s+(-?[\d.]+|-?inf)\s+LUFS"), lra=pega(r"LRA:\s+([\d.]+)\s+LU"),
                pico=pega(r"Peak:\s+(-?[\d.]+|-?inf)\s+dBFS"))


def detectar_video(arq):
    """Quadros pretos e imagem congelada, em miniatura (rápido mesmo no 4K)."""
    r = rodar(["ffmpeg", "-hide_banner", "-nostats", "-i", arq, "-an", "-vf",
               "scale=-2:360,blackdetect=d=0.2:pix_th=0.10,freezedetect=n=-60dB:d=2", "-f", "null", "-"])
    pretos = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)]
    ini = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", r.stderr)]
    dur = [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", r.stderr)]
    return pretos, list(zip(ini, dur))


def detectar_silencios(arq, duracao):
    r = rodar(["ffmpeg", "-hide_banner", "-nostats", "-i", arq, "-vn", "-af", "silencedetect=n=-50dB:d=1.5",
               "-f", "null", "-"])
    ini = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    dur = [float(x) for x in re.findall(r"silence_duration: ([\d.]+)", r.stderr)]
    return [(max(a, 0.0), dur[i] if i < len(dur) else duracao - a) for i, a in enumerate(ini)]


def ler_audio(arq):
    b = rodar(["ffmpeg", "-v", "error", "-i", arq, "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
              binario=True).stdout
    return np.frombuffer(b, np.int16)


def detectar_estalo(x, t, sr=SR, janela=0.003, fator=3.0, minimo=0.03):
    """Descontinuidade brusca de amostra a amostra no corte `t` (estalo/pop). None se limpo.
    Compara o maior salto em ±3 ms com o salto típico (percentil 99,5) do áudio em volta, sem o miolo."""
    c = int(t * sr)
    a, b = max(1, c - int(janela * sr)), min(len(x), c + int(janela * sr))
    if b - a < 4:
        return None
    d = np.abs(np.diff(x.astype(np.float32) / 32768))
    centro = float(d[a - 1:b - 1].max())
    ra, rb = max(0, c - sr), min(len(d), c + sr)
    ref = d[ra:rb].copy()
    ref[max(0, c - int(0.012 * sr) - ra):c + int(0.012 * sr) - ra] = 0
    tipico = float(np.percentile(ref, 99.5)) if ref.size else 0.0
    return dict(salto=round(centro, 4), tipico=round(tipico, 4)) if centro > minimo and centro > fator * tipico else None


# ---------------------------------------------------------------- imagens
def fonte(tam):
    try:
        return ImageFont.load_default(size=tam)
    except TypeError:                                   # Pillow antigo
        return ImageFont.load_default()


def etiqueta(d, xy, texto, f):
    x, y = xy
    box = d.textbbox((x, y), texto, font=f)
    d.rectangle((box[0] - 3, box[1] - 2, box[2] + 3, box[3] + 2), fill=(0, 0, 0))
    d.text(xy, texto, font=f, fill=(255, 235, 150))


def tamanho_miniatura(info, largura):
    return largura, max(2, round(largura * info["altura"] / info["largura"] / 2) * 2)


def folha_quadros(arq, info, passo, pasta, cor):
    retrato = info["altura"] > info["largura"]
    w, h = tamanho_miniatura(info, 108 if retrato else 192)
    r = rodar(["ffmpeg", "-v", "error", "-i", arq, "-an", "-vf", f"{cor}fps=1/{passo},scale={w}:{h}", "-f", "rawvideo",
               "-pix_fmt", "rgb24", "-"], binario=True)
    n = len(r.stdout) // (w * h * 3)
    if n == 0:
        return []
    q = np.frombuffer(r.stdout[:n * w * h * 3], np.uint8).reshape(n, h, w, 3)
    cols, linhas = (12, 6) if retrato else (8, 10)
    f, arquivos = fonte(13), []
    for p in range(0, n, cols * linhas):
        lote = q[p:p + cols * linhas]
        folha = Image.new("RGB", (cols * w, -(-len(lote) // cols) * h), "black")
        d = ImageDraw.Draw(folha)
        for i, quadro in enumerate(lote):
            xy = ((i % cols) * w, (i // cols) * h)
            folha.paste(Image.fromarray(quadro), xy)
            etiqueta(d, (xy[0] + 3, xy[1] + 3), mmss((p + i) * passo), f)
        arquivos.append(os.path.join(pasta, f"folha_{p // (cols * linhas) + 1:02d}.jpg"))
        folha.save(arquivos[-1], quality=82)
    return arquivos


def quadro_em(arq, t, w, h, cor):
    r = rodar(["ffmpeg", "-v", "error", "-ss", f"{max(t, 0):.3f}", "-i", arq, "-an", "-frames:v", "1", "-vf",
               f"{cor}scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], binario=True)
    if len(r.stdout) < w * h * 3:
        return Image.new("RGB", (w, h), (60, 0, 0))
    return Image.fromarray(np.frombuffer(r.stdout[:w * h * 3], np.uint8).reshape(h, w, 3))


def onda(x, t, largura, altura=56, meia=1.5):
    """Onda de ±meia segundos em volta do corte; linha vermelha no ponto do corte."""
    im = Image.new("RGB", (largura, altura), (20, 20, 20))
    a, b = int((t - meia) * SR), int((t + meia) * SR)
    d = ImageDraw.Draw(im)
    if len(x) and b > 0 and a < len(x):
        pad = np.zeros(b - a, np.float32)
        lo, hi = max(a, 0), min(b, len(x))
        pad[lo - a:hi - a] = x[lo:hi] / 32768
        bordas = np.linspace(0, len(pad), largura + 1).astype(int)
        mn, mx = np.minimum.reduceat(pad, bordas[:-1]), np.maximum.reduceat(pad, bordas[:-1])
        meio = altura / 2
        for i in range(largura):
            d.line((i, meio - mx[i] * meio, i, meio - mn[i] * meio), fill=(120, 200, 255))
    d.line((largura // 2, 0, largura // 2, altura), fill=(255, 60, 60))
    return im


def folha_cortes(arq, info, pontos, x, pasta, cor):
    """Uma linha por corte: quadro 0,5 s antes | último quadro antes | primeiro depois | 0,5 s depois + a onda."""
    retrato = info["altura"] > info["largura"]
    w, h = tamanho_miniatura(info, 144 if retrato else 256)
    um_quadro = 1 / (info["fps"] or 25)
    fim = max(info["duracao"] - um_quadro, 0)
    offs = [-0.5, -um_quadro, 0.0, 0.5]
    tarefas = [(i, k, min(max(t + o, 0), fim)) for i, (t, _) in enumerate(pontos) for k, o in enumerate(offs)]
    with ThreadPoolExecutor(4) as ex:
        imgs = list(ex.map(lambda a: quadro_em(arq, a[2], w, h, cor), tarefas))
    f, linhas, arquivos = fonte(14), 8 if not retrato else 4, []
    for p in range(0, len(pontos), linhas):
        lote = pontos[p:p + linhas]
        folha = Image.new("RGB", (4 * w, len(lote) * (h + 56)), "black")
        d = ImageDraw.Draw(folha)
        for j, (t, rotulo) in enumerate(lote):
            y = j * (h + 56)
            for k in range(4):
                folha.paste(imgs[(p + j) * 4 + k], (k * w, y))
            folha.paste(onda(x, t, 4 * w), (0, y + h))
            etiqueta(d, (4, y + 4), f"corte {p + j + 1} · {mmss(t)} · {rotulo}", f)
        arquivos.append(os.path.join(pasta, f"cortes_{p // linhas + 1:02d}.jpg"))
        folha.save(arquivos[-1], quality=85)
    return arquivos


# ---------------------------------------------------------------- pontos de corte
def pontos_do_plano(arq_plano, deslocamento):
    """Cortes na linha do tempo da SAÍDA: soma cumulativa das durações dos segmentos do plano.json."""
    segs = json.load(open(arq_plano, encoding="utf-8"))["segmentos"]
    t, pontos = deslocamento, []
    for s in segs[:-1]:
        t += s["fim"] - s["ini"]
        pontos.append((round(t, 3), s.get("corte_depois", "corte")))
    return pontos


def amostrar(pontos, maximo):
    if len(pontos) <= maximo:
        return pontos
    return [pontos[int(i)] for i in np.linspace(0, len(pontos) - 1, maximo)]


# ---------------------------------------------------------------- falas
def checar_falas(wav, pasta):
    saida = os.path.join(pasta, "falas.json")
    r = subprocess.run([sys.executable, CHECAR_FALAS, wav, saida], capture_output=True, text=True)
    if r.returncode:
        motivo = "faster-whisper não instalado" if "faster_whisper" in r.stderr else r.stderr.strip()[-200:]
        return NAO, f"checar_falas.py não rodou ({motivo})", []
    erros = json.load(open(saida.replace(".json", "_erros.json"), encoding="utf-8"))
    if erros:
        return FALHOU, f"{len(erros)} erro(s) de fala confirmado(s) — cortar antes de entregar", erros
    return OK, "nenhuma repetição, falso começo ou palavra truncada", []


# ---------------------------------------------------------------- relatório
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--saida", help="pasta do relatório (padrão: verificacao_<nome>)")
    ap.add_argument("--plano", help="plano.json do pipeline (cortes = soma dos segmentos)")
    ap.add_argument("--pontos", help="cortes na saída, em segundos, separados por vírgula")
    ap.add_argument("--deslocamento", type=float, default=0.0, help="segundos antes do 1º segmento (ex.: vinheta)")
    ap.add_argument("--falas", help="voz_16k.wav da voz montada, para rodar o checar_falas.py")
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--tol-lufs", type=float, default=1.0)
    ap.add_argument("--pico", type=float, default=-1.5, help="true peak máximo em dBTP")
    ap.add_argument("--resolucao", help="esperada, ex.: 3840x2160")
    ap.add_argument("--fps", type=float, help="esperado")
    ap.add_argument("--duracao", type=float, help="esperada, em segundos")
    ap.add_argument("--tol-duracao", type=float, default=0.3)
    ap.add_argument("--passo", type=float, default=1.5, help="segundos entre quadros da folha")
    ap.add_argument("--max-cortes", type=int, default=60)
    ap.add_argument("--sem-imagens", action="store_true", help="pula as folhas de quadros (só medições)")
    a = ap.parse_args(argv)

    if not os.path.isfile(a.video):
        raise SystemExit(f"arquivo não encontrado: {a.video}")
    nome = os.path.splitext(os.path.basename(a.video))[0]
    pasta = a.saida or f"verificacao_{nome}"
    os.makedirs(pasta, exist_ok=True)
    info = sondar(a.video)
    itens, arquivos = [], []

    def item(nome_, status, detalhe):
        itens.append(dict(item=nome_, status=status, detalhe=detalhe))

    # arquivo
    erros = decodifica(a.video)
    item("Decodifica inteiro", FALHOU if erros else OK, f"{len(erros)} erro(s): {erros[0][:120]}" if erros else "sem erros do ffmpeg")
    item("Streams", OK if info["tem_video"] and info["tem_audio"] else FALHOU,
         f"vídeo {info['codec']} {info['largura']}x{info['altura']} {info['fps']:.3f} fps · áudio {info['codec_audio'] or 'AUSENTE'}"
         f" · {mmss(info['duracao'])}")
    if a.resolucao:
        ok = f"{info['largura']}x{info['altura']}" == a.resolucao
        item("Resolução", OK if ok else FALHOU, f"{info['largura']}x{info['altura']} (esperado {a.resolucao})")
    if a.fps:
        item("FPS", OK if abs(info["fps"] - a.fps) < 0.01 else FALHOU, f"{info['fps']:.3f} (esperado {a.fps})")
    if a.duracao:
        ok = abs(info["duracao"] - a.duracao) <= a.tol_duracao
        item("Duração", OK if ok else FALHOU, f"{info['duracao']:.2f} s (esperado {a.duracao} ± {a.tol_duracao})")

    # áudio
    x = np.zeros(0, np.int16)
    if info["tem_audio"]:
        m = medir_loudness(a.video)
        if m["lufs"] is None or m["lufs"] == float("-inf"):
            item("Loudness integrado", FALHOU, "áudio mudo ou não medido")
        else:
            ok = abs(m["lufs"] - a.lufs) <= a.tol_lufs
            item("Loudness integrado", OK if ok else FALHOU,
                 f"{m['lufs']:.1f} LUFS (alvo {a.lufs} ± {a.tol_lufs}) · LRA {m['lra']} LU")
        if m["pico"] is not None:
            item("True peak", OK if m["pico"] <= a.pico else FALHOU, f"{m['pico']:.1f} dBTP (máximo {a.pico})")
        sil = detectar_silencios(a.video, info["duracao"])
        item("Buracos de áudio (≥1,5 s)", REVISAR if sil else OK,
             "; ".join(f"{mmss(s)} ({d:.1f} s)" for s, d in sil[:8]) if sil else "nenhum")
        x = ler_audio(a.video)

    # vídeo
    if info["tem_video"]:
        pretos, congelados = detectar_video(a.video)
        item("Quadros pretos", REVISAR if pretos else OK,
             "; ".join(f"{mmss(s)}–{mmss(e)}" for s, e in pretos[:8]) if pretos else "nenhum")
        item("Imagem congelada (≥2 s)", REVISAR if congelados else OK,
             "; ".join(f"{mmss(s)} ({d:.1f} s)" for s, d in congelados[:8]) if congelados else "nenhuma")

    # cortes
    pontos = []
    if a.plano:
        pontos = pontos_do_plano(a.plano, a.deslocamento)
    elif a.pontos:
        pontos = [(float(t) + a.deslocamento, "corte") for t in a.pontos.split(",") if t.strip()]
    if pontos and len(x):
        ruins = [(t, r, e) for t, r in pontos if (e := detectar_estalo(x, t))]
        item(f"Estalo de áudio nos cortes ({len(pontos)})", REVISAR if ruins else OK,
             "; ".join(f"{mmss(t)} {r} (salto {e['salto']} vs típico {e['tipico']})" for t, r, e in ruins[:8])
             if ruins else "nenhum")
    elif pontos:
        item("Estalo de áudio nos cortes", NAO, "vídeo sem áudio")

    # falas
    if a.falas:
        status, detalhe, erros_fala = checar_falas(a.falas, pasta)
        item("Erros de fala", status, detalhe + ("; " + "; ".join(f"{mmss(e['t'])} {e['tipo']}" for e in erros_fala[:8])
                                                 if erros_fala else ""))
    else:
        item("Erros de fala", NAO, "rode com --falas voz_16k.wav (checar_falas.py, ~6 min por 8 min de áudio)")

    # imagens
    if not a.sem_imagens and info["tem_video"]:
        cor = filtro_cor(info)
        arquivos += folha_quadros(a.video, info, a.passo, pasta, cor)
        if pontos:
            arquivos += folha_cortes(a.video, info, amostrar(pontos, a.max_cortes), x, pasta, cor)
        item("Folhas de quadros geradas", OK if arquivos else FALHOU, f"{len(arquivos)} imagem(ns) em {pasta}/")
    # o que só um humano confere
    item("Conferir folhas: texto cortado, rosto coberto, resto de texto original, sincronia", NAO, "olhar as folhas")
    item("Escuta completa (voz, SFX, trilha, finais truncados)", NAO, "não foi ouvido por mim — só medido")

    falhou = [i for i in itens if i["status"] == FALHOU]
    revisar = [i for i in itens if i["status"] == REVISAR]
    veredito = "REPROVADO" if falhou else ("APROVADO COM PONTOS A REVISAR" if revisar else "APROVADO NAS MEDIÇÕES")
    linhas = [f"# Verificação: {os.path.basename(a.video)}", "", f"**{veredito}** — {len(falhou)} falhou · "
              f"{len(revisar)} para revisar · {sum(i['status'] == NAO for i in itens)} não verificado(s)", "",
              "| Item | Status | Detalhe |", "|---|---|---|"]
    linhas += [f"| {i['item']} | {SIMBOLO[i['status']]} {i['status']} | {i['detalhe']} |" for i in itens]
    linhas += ["", "Arquivos: " + ", ".join(os.path.basename(f) for f in arquivos) if arquivos else ""]
    texto = "\n".join(linhas) + "\n"
    open(os.path.join(pasta, "relatorio.md"), "w", encoding="utf-8").write(texto)
    json.dump(dict(video=a.video, veredito=veredito, info=info, itens=itens, arquivos=arquivos),
              open(os.path.join(pasta, "relatorio.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(texto)
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
