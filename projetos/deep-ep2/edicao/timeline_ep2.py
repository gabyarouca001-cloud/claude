"""Monta os blocos da timeline do EP2 (YouTube, 12:03) para o painel "Timeline DEEP" a partir do que o repositório tem:
trechos.json (cortes escolhidos, com fonte, tempos e fala), INS de insercoes.py (inserções com frase-âncora e tempo-guia)
e os capítulos reais de publicacao/youtube.md.

ATENÇÃO: sem o áudio dos takes não dá para repetir a remoção de pausas do plano.py. Por isso:
  - a duração de cada corte é a do trecho escalada para a montagem somar 12:03 (aproximada);
  - o início de cada inserção vem do texto do trecho onde a frase-âncora aparece (ou do tempo-guia quando o texto não casa)
    e é calibrado nos 5 capítulos reais (esses ficam exatos; o resto tem margem de alguns segundos).
Os tempos exatos saem do render (final_youtube2.py).
Uso (em projetos/deep-ep2/edicao): python3 timeline_ep2.py  ->  timeline_ep2.json (documentos do painel)"""
import difflib
import json
import re
import unicodedata

import numpy as np

import plano as P

OFF = 9.68                    # abertura da editora (inicio_editora.mp4, já com a vinheta)
TOTAL = 723.0                 # 12:03
CAPITULOS = {"comecei a pensar": 13.0, "e tem uma diferença": 163.0, "e foi dessa vontade": 286.0,
             "hoje existem mais caminhos": 406.0, "a pessoa precisa encontrar": 585.0}   # publicacao/youtube.md
COR = "#FCEDC0"


def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", t).split())


def carregar():
    T = json.load(open("trechos.json"))
    for t in T:
        a, b = P.AJUSTES.get(t["n"], (None, None))
        t["ini"] = a if a is not None else t["ini"]
        t["fim"] = b if b is not None else t["fim"]
    M = [t for t in T if t["n"] > P.VINHETA_APOS]
    src = open("insercoes.py", encoding="utf-8").read()
    a = src.index("INS = [")
    b = src.index("\n]\n", a) + 3
    ns = {}
    exec(src[a:b], ns)
    return M, ns["INS"]


def main():
    M, INS = carregar()
    tot = sum(t["fim"] - t["ini"] for t in M)
    k = (TOTAL - OFF) / tot
    cum, x = [], 0.0
    for t in M:
        cum.append(x)
        x += (t["fim"] - t["ini"]) * k

    def casa(frase, lo, hi):
        f = norm(frase)
        melhor = (0.0, None, 0.0)
        for i, t in enumerate(M):
            if not lo <= OFF + cum[i] <= hi:
                continue
            tx = norm(t["texto"])
            tx2 = tx + (" " + norm(M[i + 1]["texto"]) if i + 1 < len(M) else "")
            if f in tx:
                return i, tx.index(f) / max(1, len(tx)), 1.0
            for s in range(0, max(1, len(tx2) - len(f) + 1)):
                r = difflib.SequenceMatcher(None, f, tx2[s:s + len(f)]).ratio()
                if r > melhor[0] + 1e-9:
                    melhor = (r, i, s / max(1, len(tx)))
        return melhor[1], melhor[2], melhor[0]

    est = []
    for ins in INS:
        hint = ins[2]
        i, fp, sc = casa(ins[1], hint - 20, hint + 45)
        t0 = None if i is None else OFF + cum[i] + min(fp, 1) * (M[i]["fim"] - M[i]["ini"]) * k
        est.append([hint, t0, sc])
    # frases que não casaram bem: tempo-guia + desvio típico dos vizinhos que casaram
    bons = sorted((h, t0 - h) for h, t0, sc in est if sc >= 0.8 and t0 is not None)
    hs, ds = [b[0] for b in bons], [b[1] for b in bons]
    for e in est:
        if e[2] < 0.8 or e[1] is None:
            e[1] = e[0] + float(np.interp(e[0], hs, ds))
    # calibra nos capítulos reais
    ancoras = sorted((e[1], CAPITULOS[ins[1]]) for ins, e in zip(INS, est) if ins[1] in CAPITULOS)
    xs = [a for a, _ in ancoras]
    dif = [r - a for a, r in ancoras]
    inicio = [float(e[1] + np.interp(e[1], xs, dif)) for e in est]
    for i in range(1, len(inicio)):      # mantém a distância que o tempo-guia dá entre inserções vizinhas
        folga = 0.8 * min(INS[i][2] - INS[i - 1][2], 8.0)
        inicio[i] = max(inicio[i], inicio[i - 1] + max(0.4, folga))

    docs = {}
    # ---- vídeo: abertura + cortes (blocos contíguos da mesma fonte)
    docs["v000"] = dict(track="video", kind="video", start=0.0, dur=OFF, **{"in": 0.0}, fonte="inicio_editora",
                        texto="Abertura da editora + vinheta DEEP", ord=0)
    blocos = P.blocos([dict(t) for t in M])
    k2 = (TOTAL - OFF) / sum(b["fim"] - b["ini"] for b in blocos)      # fecha em 12:03 depois de juntar os trechos contíguos
    x = OFF
    for n, b in enumerate(blocos, 1):
        d = (b["fim"] - b["ini"]) * k2
        docs[f"v{n:03d}"] = dict(track="video", kind="video", start=round(x, 2), dur=round(d, 2), **{"in": round(b["ini"], 2)},
                                 fonte=b["fonte"], texto=b["texto"].strip(), ord=n)
        x += d

    # ---- inserções
    def duracao(ins, t0, prox):
        tipo, extra = ins[0], ins[3]
        if isinstance(extra, (int, float)):
            return float(extra)
        if tipo == "proximo":
            return TOTAL - t0
        its = ins[4].get("itens") or []
        if its:
            tt = [it[1] for it in its] + ([ins[4]["virada"][1]] if tipo == "app" and ins[4].get("virada") else [])
            return float(min(12, max(4.5, tt[-1] - tt[0] + 3.2)))
        return 3.6 if tipo != "citacao" else 5.0

    for n, (ins, t0) in enumerate(zip(INS, inicio), 1):
        tipo, dados = ins[0], ins[4]
        base = dict(track="motion", start=round(t0, 2), x=0, y=0, scale=1, cor=COR)
        prox = inicio[n] if n < len(inicio) else TOTAL
        dur = round(min(duracao(ins, t0, prox), TOTAL - t0), 2)
        if tipo == "titulo":
            d = dict(kind="lettering", l1=dados["serif"], l2=dados["bold"], echo=dados.get("eco", ""))
            if dados.get("extra"):
                d["nota"] = "No render entra também a linha: " + dados["extra"] + " (contador animado)."
        elif tipo == "capitulo":
            d = dict(kind="capitulo", capK="CAPÍTULO", capT=dados["texto"])
        elif tipo in ("lista", "tijolos"):
            d = dict(kind=tipo, titulo=dados["titulo"], itens=[it[2] for it in dados["itens"]])
        elif tipo == "pesquisa":
            d = dict(kind="lista", rotulo="pesquisa", titulo=dados["titulo"], itens=[it[2] for it in dados["itens"]],
                     nota=dados.get("fonte", ""))
        elif tipo == "formatos":
            d = dict(kind="lista", rotulo="formatos", titulo="o mesmo assunto, em…", itens=[it[3] for it in dados["itens"]],
                     nota="No render: cadeia de formatos com ícones e os papéis (" +
                          ", ".join(p[3] for p in dados.get("papeis", [])) + "). Aqui aparece simplificado.")
        elif tipo == "app":
            d = dict(kind="lista", rotulo="app", titulo="dentro do aplicativo", itens=[it[2] for it in dados["itens"]],
                     nota="No render: caixa 'dentro do aplicativo' que vira amarela na virada. Aqui aparece simplificado.")
        elif tipo == "citacao":
            d = dict(kind="citacao", l1=dados["serif"], l2=dados["bold"])
        elif tipo == "versus":
            d = dict(kind="versus", l1=dados["serif"], esq=dados["esq"], dir=dados["dir"])
        else:
            d = dict(kind="proximo")
        docs[f"m{n:03d}"] = {**base, "dur": dur, **d}

    json.dump(docs, open("timeline_ep2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    v = [d for d in docs.values() if d["track"] == "video"]
    m = [d for d in docs.values() if d["track"] == "motion"]
    print(f"{len(v)} blocos de vídeo (fim {max(d['start'] + d['dur'] for d in v):.1f} s), {len(m)} inserções")
    for ins, d in zip(INS, [docs[f"m{n:03d}"] for n in range(1, len(INS) + 1)]):
        print(f"{int(d['start'] // 60)}:{d['start'] % 60:04.1f}  {d['dur']:4.1f}s  {ins[0]:9s} {ins[1]}")


if __name__ == "__main__":
    main()
