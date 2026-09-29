"""Transforma uma lista de cortes (JSON) numa timeline XML que o Premiere importa.

Uso:
    python cortes_para_xml.py cortes.json
    python cortes_para_xml.py cortes.json -o minha_timeline.xml --fps 29.97

O JSON tem este formato (veja exemplos/cortes_exemplo.json):
    {
      "sequencia": "Reels 01",
      "video": "entrevista.mp4",
      "cortes": [
        {"inicio": "00:01:02,500", "fim": "00:01:10,000", "nota": "gancho"},
        {"arquivo": "take2.mp4", "inicio": "12.3", "fim": "20"}
      ]
    }

Caminhos relativos são resolvidos a partir da pasta do JSON. O formato gerado é
o Final Cut Pro 7 XML (xmeml), importado pelo Premiere em Arquivo > Importar.
Se o ffprobe (FFmpeg) estiver instalado, fps, resolução e áudio são lidos dos
próprios vídeos; caso contrário use --fps / --largura / --altura / --canais.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from fractions import Fraction
from urllib.parse import quote

FPS_NTSC = {
    23.976: Fraction(24000, 1001),
    29.97: Fraction(30000, 1001),
    47.952: Fraction(48000, 1001),
    59.94: Fraction(60000, 1001),
}


def normalizar_fps(valor):
    """Converte 29.97, "30000/1001", "25" etc. em Fraction exata."""
    if isinstance(valor, str) and "/" in valor:
        num, den = valor.split("/")
        fps = Fraction(int(num), int(den))
    else:
        fps = Fraction(str(valor))
    for aproximado, exato in FPS_NTSC.items():
        if abs(float(fps) - aproximado) < 0.01:
            return exato
    return fps


def timebase_e_ntsc(fps):
    timebase = round(float(fps))
    return timebase, fps.denominator == 1001


def tempo_para_frames(valor, fps):
    """Aceita segundos (12.5), MM:SS, HH:MM:SS,mmm (SRT) ou HH:MM:SS:FF (timecode)."""
    if isinstance(valor, (int, float)):
        return round(Fraction(str(valor)) * fps)
    texto = str(valor).strip().replace(",", ".")
    partes = texto.split(":")
    if len(partes) == 4:
        h, m, s, f = (int(p) for p in partes)
        timebase, _ = timebase_e_ntsc(fps)
        return (h * 3600 + m * 60 + s) * timebase + f
    if not 1 <= len(partes) <= 3 or not all(re.fullmatch(r"\d+(\.\d+)?", p) for p in partes):
        raise ValueError(f"Tempo inválido: {valor!r}")
    segundos = Fraction(0)
    for parte in partes:
        segundos = segundos * 60 + Fraction(parte)
    return round(segundos * fps)


def eh_caminho_windows_absoluto(caminho):
    return bool(re.match(r"^[A-Za-z]:[\\/]", caminho)) or caminho.startswith("\\\\")


def resolver_caminho(caminho, pasta_base):
    if eh_caminho_windows_absoluto(caminho) or os.path.isabs(caminho):
        return caminho
    return os.path.abspath(os.path.join(pasta_base, caminho))


def caminho_para_url(caminho):
    caminho = caminho.replace("\\", "/")
    if caminho.startswith("//"):
        return "file:" + quote(caminho, safe="/:")
    if not caminho.startswith("/"):
        caminho = "/" + caminho
    return "file://localhost" + quote(caminho, safe="/:")


def analisar_video(caminho):
    """Lê fps, resolução, duração e áudio com o ffprobe. Retorna {} se indisponível."""
    if not shutil.which("ffprobe") or not os.path.exists(caminho):
        return {}
    resultado = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", caminho],
        capture_output=True, text=True,
    )
    if resultado.returncode != 0:
        return {}
    dados = json.loads(resultado.stdout)
    info = {}
    for stream in dados.get("streams", []):
        if stream.get("codec_type") == "video" and "fps" not in info:
            info["fps"] = normalizar_fps(stream.get("avg_frame_rate") or stream["r_frame_rate"])
            info["largura"] = stream.get("width")
            info["altura"] = stream.get("height")
        elif stream.get("codec_type") == "audio" and "canais" not in info:
            info["canais"] = stream.get("channels", 2)
            info["taxa_audio"] = int(stream.get("sample_rate", 48000))
    if "duration" in dados.get("format", {}):
        info["duracao_s"] = Fraction(dados["format"]["duration"])
    return info


def sub(pai, tag, texto=None):
    elemento = ET.SubElement(pai, tag)
    if texto is not None:
        elemento.text = str(texto)
    return elemento


def adicionar_rate(pai, fps):
    timebase, ntsc = timebase_e_ntsc(fps)
    rate = sub(pai, "rate")
    sub(rate, "timebase", timebase)
    sub(rate, "ntsc", "TRUE" if ntsc else "FALSE")


class Midia:
    def __init__(self, indice, caminho, info, config):
        self.id = f"file-{indice}"
        self.caminho = caminho
        self.nome = os.path.basename(caminho.replace("\\", "/"))
        self.fps = info.get("fps") or config["fps"]
        self.largura = info.get("largura") or config["largura"]
        self.altura = info.get("altura") or config["altura"]
        self.canais = info.get("canais", config["canais"])
        self.taxa_audio = info.get("taxa_audio", 48000)
        self.duracao = round(info["duracao_s"] * self.fps) if "duracao_s" in info else None
        self.ja_escrito = False

    def escrever(self, pai):
        """A primeira referência leva a descrição completa; as demais só o id."""
        elemento = sub(pai, "file")
        elemento.set("id", self.id)
        if self.ja_escrito:
            return
        self.ja_escrito = True
        sub(elemento, "name", self.nome)
        sub(elemento, "pathurl", caminho_para_url(self.caminho))
        adicionar_rate(elemento, self.fps)
        sub(elemento, "duration", self.duracao)
        media = sub(elemento, "media")
        video = sub(media, "video")
        carac = sub(video, "samplecharacteristics")
        adicionar_rate(carac, self.fps)
        sub(carac, "width", self.largura)
        sub(carac, "height", self.altura)
        if self.canais:
            audio = sub(media, "audio")
            carac = sub(audio, "samplecharacteristics")
            sub(carac, "depth", 16)
            sub(carac, "samplerate", self.taxa_audio)
            sub(audio, "channelcount", self.canais)


def carregar_cortes(caminho_json, args):
    with open(caminho_json, encoding="utf-8") as f:
        dados = json.load(f)
    pasta_base = os.path.dirname(os.path.abspath(caminho_json))
    config = {
        "fps": normalizar_fps(args.fps or dados.get("fps", 29.97)),
        "largura": args.largura or dados.get("largura", 1920),
        "altura": args.altura or dados.get("altura", 1080),
        "canais": args.canais if args.canais is not None else dados.get("canais", 2),
    }
    midias = {}
    cortes = []
    for numero, corte in enumerate(dados.get("cortes", []), start=1):
        arquivo = corte.get("arquivo") or dados.get("video")
        if not arquivo:
            raise ValueError(f"Corte {numero}: sem 'arquivo' e sem 'video' padrão no JSON.")
        caminho = resolver_caminho(arquivo, pasta_base)
        if caminho not in midias:
            info = {} if args.sem_ffprobe else analisar_video(caminho)
            if args.fps:
                info.pop("fps", None)
            midias[caminho] = Midia(len(midias) + 1, caminho, info, config)
        midia = midias[caminho]
        entrada = tempo_para_frames(corte["inicio"], midia.fps)
        saida = tempo_para_frames(corte["fim"], midia.fps)
        if saida <= entrada:
            raise ValueError(f"Corte {numero}: 'fim' precisa ser depois de 'inicio'.")
        if midia.duracao is not None and saida > midia.duracao:
            raise ValueError(f"Corte {numero}: termina depois do fim de {midia.nome}.")
        cortes.append({"midia": midia, "entrada": entrada, "saida": saida, "nota": corte.get("nota", "")})
    if not cortes:
        raise ValueError("O JSON não tem nenhum corte.")
    for midia in midias.values():
        if midia.duracao is None:
            midia.duracao = max(c["saida"] for c in cortes if c["midia"] is midia)
    return dados.get("sequencia", "Timeline IA"), config, cortes


def montar_xml(nome_sequencia, config, cortes):
    fps = cortes[0]["midia"].fps
    raiz = ET.Element("xmeml", version="4")
    sequencia = sub(raiz, "sequence")
    sequencia.set("id", "sequence-1")
    sub(sequencia, "name", nome_sequencia)
    duracao_total = sum(c["saida"] - c["entrada"] for c in cortes)
    sub(sequencia, "duration", duracao_total)
    adicionar_rate(sequencia, fps)

    media = sub(sequencia, "media")
    video = sub(media, "video")
    formato = sub(video, "format")
    carac = sub(formato, "samplecharacteristics")
    adicionar_rate(carac, fps)
    sub(carac, "width", cortes[0]["midia"].largura)
    sub(carac, "height", cortes[0]["midia"].altura)
    sub(carac, "pixelaspectratio", "square")
    trilha_video = sub(video, "track")

    audio = sub(media, "audio")
    max_canais = max(c["midia"].canais for c in cortes)
    trilhas_audio = [sub(audio, "track") for _ in range(max_canais)]

    posicao = 0
    for indice, corte in enumerate(cortes, start=1):
        midia = corte["midia"]
        duracao = corte["saida"] - corte["entrada"]
        ids = [f"clipitem-v{indice}"] + [f"clipitem-a{indice}-{c}" for c in range(1, midia.canais + 1)]

        def clip(trilha, clip_id, tipo, indice_trilha):
            item = sub(trilha, "clipitem")
            item.set("id", clip_id)
            sub(item, "name", midia.nome)
            sub(item, "enabled", "TRUE")
            sub(item, "duration", midia.duracao)
            adicionar_rate(item, midia.fps)
            sub(item, "start", posicao)
            sub(item, "end", posicao + duracao)
            sub(item, "in", corte["entrada"])
            sub(item, "out", corte["saida"])
            midia.escrever(item)
            if tipo == "audio":
                origem = sub(item, "sourcetrack")
                sub(origem, "mediatype", "audio")
                sub(origem, "trackindex", indice_trilha)
            for n, link_id in enumerate(ids):
                link = sub(item, "link")
                sub(link, "linkclipref", link_id)
                sub(link, "mediatype", "video" if n == 0 else "audio")
                sub(link, "trackindex", 1 if n == 0 else n)
                sub(link, "clipindex", indice)
                if n > 0:
                    sub(link, "groupindex", 1)
            return item

        clip(trilha_video, ids[0], "video", 1)
        for canal in range(1, midia.canais + 1):
            clip(trilhas_audio[canal - 1], ids[canal], "audio", canal)

        if corte["nota"]:
            marcador = sub(sequencia, "marker")
            sub(marcador, "name", corte["nota"])
            sub(marcador, "comment", corte["nota"])
            sub(marcador, "in", posicao)
            sub(marcador, "out", -1)
        posicao += duracao

    ET.indent(raiz)
    return '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n' + ET.tostring(raiz, encoding="unicode") + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Gera timeline XML do Premiere a partir de uma lista de cortes.")
    parser.add_argument("cortes", help="arquivo JSON com os cortes")
    parser.add_argument("-o", "--saida", help="arquivo XML de saída (padrão: mesmo nome do JSON)")
    parser.add_argument("--fps", help="força o fps (ex.: 29.97, 25, 23.976)")
    parser.add_argument("--largura", type=int, help="largura do vídeo se não houver ffprobe")
    parser.add_argument("--altura", type=int, help="altura do vídeo se não houver ffprobe")
    parser.add_argument("--canais", type=int, help="canais de áudio se não houver ffprobe")
    parser.add_argument("--sem-ffprobe", action="store_true", help="não lê informações dos vídeos")
    args = parser.parse_args(argv)

    try:
        nome, config, cortes = carregar_cortes(args.cortes, args)
    except (ValueError, KeyError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1

    saida = args.saida or os.path.splitext(args.cortes)[0] + ".xml"
    with open(saida, "w", encoding="utf-8") as f:
        f.write(montar_xml(nome, config, cortes))

    fps = cortes[0]["midia"].fps
    total = sum(c["saida"] - c["entrada"] for c in cortes)
    print(f"{len(cortes)} cortes, {float(total / fps):.1f}s de timeline -> {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
