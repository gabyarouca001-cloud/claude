"""Sequência do DEEP EP2 (YouTube) para importar no Premiere: abertura da editora + os trechos escolhidos (trechos.json,
com os AJUSTES do plano.py e sem os erros de fala de EXCLUIR_ERROS), em 4K 30 fps, com um marcador em cada corte
dizendo a fala e, quando for o caso, o capítulo e a inserção (motion) que entram ali.

Os tempos de fonte são os reais dos takes. As pausas internas NÃO foram tiradas (isso precisa do áudio dos takes):
a sequência fica mais longa que os 12:03 do final; dá para enxugar no Premiere.
Uso (em projetos/deep-ep2/edicao): python3 xml_premiere_ep2.py  ->  DEEP_EP2_youtube_cortes.json + .xml"""
import json
import subprocess
import sys

import plano as P
from timeline_ep2 import carregar, estimar

PASTA = "D:/Videos/Samara/DEEP 2"            # palpite; o Premiere pede para localizar se estiver em outro lugar
ARQ = {"take1": "take1.mp4", "take2": "take2.mp4", "take3": "take3.mp4", "lado_inicio": "lado_inicio.mp4"}
ABERTURA = ("inicio_editora.mp4", 9.68)
CAP = {"comecei a pensar", "e tem uma diferença", "e foi dessa vontade", "hoje existem mais caminhos",
       "a pessoa precisa encontrar"}


def rotulo(ins):
    tipo, d = ins[0], ins[4]
    if tipo == "capitulo":
        return "CAPÍTULO: " + d["texto"]
    if tipo == "titulo":
        return f"TÍTULO: {d['serif']} / {d['bold']}"
    if tipo in ("lista", "tijolos", "pesquisa"):
        return f"{tipo.upper()}: {d.get('titulo', '')} ({', '.join(str(i[2]) for i in d['itens'])})"
    if tipo == "citacao":
        return f"CITAÇÃO: {d['serif']} / {d['bold']}"
    if tipo == "versus":
        return f"VERSUS: {d['esq']} × {d['dir']}"
    if tipo == "formatos":
        return "FORMATOS: " + ", ".join(i[3] for i in d["itens"])
    if tipo == "app":
        return "APP: " + ", ".join(i[2] for i in d["itens"])
    return "PRÓXIMO EPISÓDIO"


def main():
    M, INS = carregar()
    # inserção -> trecho onde a frase-âncora aparece (mesmo cálculo da timeline: capítulos exatos)
    _, idx, _ = estimar(M, INS)
    alvo = {}
    for ins, i in zip(INS, idx):
        alvo.setdefault(M[i]["n"], []).append(rotulo(ins))
    cortes = [dict(arquivo=f"{PASTA}/{ABERTURA[0]}", inicio=0, fim=ABERTURA[1], nota="ABERTURA DA EDITORA + VINHETA")]
    for b in M:                                    # um corte por trecho: cada marcador cai na fala certa
        partes = [(b["ini"], b["fim"])]
        for fonte, a, z in P.EXCLUIR_ERROS:          # tira os erros de fala que caem dentro do bloco
            if fonte != b["fonte"]:
                continue
            novas = []
            for x, y in partes:
                if z <= x or a >= y:
                    novas.append((x, y))
                else:
                    if a - x > 0.2:
                        novas.append((x, a))
                    if y - z > 0.2:
                        novas.append((z, y))
            partes = novas
        notas = alvo.get(b["n"], [])
        for k, (x, y) in enumerate(partes):
            fala = b["texto"].strip()
            nota = (" | ".join(notas) + " | " if notas and k == 0 else "") + "FALA: " + fala[:160]
            cortes.append(dict(arquivo=f"{PASTA}/{ARQ[b['fonte']]}", inicio=round(x, 3), fim=round(y, 3), nota=nota))
    dados = dict(sequencia="DEEP EP2 YouTube - cortes do Claude", fps=30, largura=3840, altura=2160, cortes=cortes)
    json.dump(dados, open("DEEP_EP2_youtube_cortes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    dur = sum(c["fim"] - c["inicio"] for c in cortes)
    print(f"{len(cortes)} cortes, {dur / 60:.1f} min, {sum(len(v) for v in alvo.values())} marcações de inserção")
    subprocess.run([sys.executable, "../../../ferramentas/cortes_para_xml.py", "DEEP_EP2_youtube_cortes.json",
                    "-o", "DEEP_EP2_youtube_cortes.xml", "--fps", "30", "--largura", "3840", "--altura", "2160"], check=True)


if __name__ == "__main__":
    main()
