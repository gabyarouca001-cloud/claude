"""EP3 (vertical 4K, 30 fps) — etapa 1: escolhe os takes mantidos, tira silêncios e gera a lista de cortes.

Tudo até T_VINHETA já está editado pela editora e não é tocado.
Cada trecho: (rótulo, início da 1ª palavra, início da última palavra) tirados de transcricao_palavras.json.
O fim de cada trecho é achado pela energia (último instante falado antes da próxima pausa/palavra).
"""
import json
import sys
import wave

import numpy as np

FPS = 30
T_VINHETA = 346 / FPS          # primeiro frame do bruto (a vinheta acaba no frame 345)
DUR_TOTAL = 790.57
WAV = "/home/user/work/ep3/voz_16k.wav"
SR = 16000
SIL_DB = -36.0
SIL_MIN = 0.30
PAD_ANTES = 0.10   # fica depois da palavra anterior
PAD_DEPOIS = 0.08  # fica antes da próxima palavra
PAD_FIM = 0.12     # respiro depois da última palavra de cada trecho

# (rótulo, 1ª palavra, última palavra, junção)  junção = "retake" (punch-in alterna) ou "corrido"
TRECHOS = [
    ("Abertura: 'Talvez você tenha pensado…' (1º take, completo)", 11.74, 29.20),
    ("Ligação com o episódio anterior + 'caminho entre assistir, acreditar e comprar'", 68.54, 102.94),
    ("Produção: 'primeira mudança… ajudam a escrever,'", 104.62, 117.88),
    ("Produção: 'editar, criar imagens e vídeos' (take 2)", 126.10, 128.44),
    ("Produção: 'E uma pessoa pode produzir'", 141.62, 143.92),
    ("Produção: 'com recursos que antes exigiam uma estrutura muito maior.'", 154.18, 160.40),
    ("Produção: 'Isso abre espaço… sem ter conhecimento suficiente' (último take, corrido)", 197.70, 215.38),
    ("Produção: 'a qualidade da apresentação… descrição comercial' (sem 'Vale dizer que')", 226.22, 247.36),
    ("Produção: 'Para mim, isso significa… uma recomendação.' (último take)", 269.36, 289.40),
    ("Compra: 'A segunda mudança está na compra.'", 291.24, 294.70),
    ("Compra: 'Porque você entra para se distrair… na mesma hora.'", 296.54, 307.52),
    ("Compra: 'E também explica o sucesso de ferramentas como o TikTok Shop.'", 322.60, 327.26),
    ("Compra: 'E transforma o conteúdo num verdadeiro ponto de venda, né?'", 343.00, 348.78),
    ("Compra: 'um vídeo… pode divertir, ensinar… comissão… interesse comercial… do outro lado.'", 365.80, 389.16),
    ("Negócio: 'terceira mudança… produzir programas, lançar produtos, oferecer assinaturas.'", 389.98, 404.24),
    ("Negócio: 'E parte deles está construindo empresas enormes… O que você faz questão de acompanhar?'", 419.24, 452.04),
    ("Negócio: 'E o que vale a pena pagar? … expectativa de entrega.'", 460.74, 469.94),
    ("Confiança: 'E é por isso que eu vejo a confiança… mudar de opinião.' (take corrido)", 470.98, 542.46),
    ("Fechamento: 'Eu comecei essa série…'", 713.61, 720.67),
    ("Fechamento: 'E eu termino falando… duas perguntas… Me conta! Tchau!' (último take, até o fim)", 743.59, None),
]


def carregar():
    w = wave.open(WAV)
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    n = int(SR * 0.01)
    q = x[: len(x) // n * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt((q ** 2).mean(1)) + 1e-9)


def snap(t):
    return round(t * FPS) / FPS


def inicio_fala(db, t, atras=0.30):
    """Primeiro instante falado a partir de t-atras; devolve o ponto de entrada (com PAD_DEPOIS antes)."""
    i = int(max(0, t - atras) / 0.01)
    j = int((t + 0.15) / 0.01)
    while i < j and db[i] < SIL_DB:
        i += 1
    return max(0.0, i * 0.01 - PAD_DEPOIS)


def fim_fala(db, t, a_frente=0.80):
    """Último instante falado até t+a_frente (parando na primeira pausa longa depois de t)."""
    i = int(t / 0.01)
    lim = int((t + a_frente) / 0.01)
    ultimo = i
    sil = 0
    while i < min(lim, len(db) - 1):
        if db[i] >= SIL_DB:
            ultimo, sil = i, 0
        else:
            sil += 1
            if sil >= 30:   # 0,30 s de silêncio: a frase acabou
                break
        i += 1
    return ultimo * 0.01 + PAD_FIM


def main():
    db = carregar()
    trechos = []
    for k, (rot, p0, p1) in enumerate(TRECHOS):
        ini = snap(inicio_fala(db, p0))
        if k == 0:
            ini = T_VINHETA   # começa exatamente onde a edição dela termina
        fim = DUR_TOTAL if p1 is None else snap(fim_fala(db, p1))
        trechos.append([ini, fim, rot])

    # silêncios dentro de cada trecho (>= 0,30 s no limiar) -> remove, mantendo os respiros
    segs, pausas = [], []
    for ini, fim, rot in trechos:
        i, f = int(ini / 0.01), min(int(fim / 0.01), len(db) - 1)
        cur = ini
        k = i
        while k < f:
            if db[k] < SIL_DB:
                j = k
                while j < f and db[j] < SIL_DB:
                    j += 1
                s0, s1 = k * 0.01, j * 0.01
                if s1 - s0 >= SIL_MIN and s1 < fim - 0.2:
                    a, b = snap(s0 + PAD_ANTES), snap(s1 - PAD_DEPOIS)
                    if b - a >= 1 / FPS:
                        segs.append([cur, a, rot])
                        pausas.append((a, b))
                        cur = b
                k = j
            else:
                k += 1
        segs.append([cur, fim, rot])

    # sai o trecho ja' editado pela editora: 0 .. T_VINHETA fica inteiro
    edl = [{"ini": 0.0, "fim": T_VINHETA, "rot": "JÁ EDITADO PELA EDITORA (até o fim da vinheta)", "junta": "original"}]
    for n, (a, b, rot) in enumerate(segs):
        edl.append({"ini": round(a, 4), "fim": round(b, 4), "rot": rot, "junta": "retake" if n == 0 or segs[n - 1][2] != rot else "pausa"})
    json.dump({"fps": FPS, "edl": edl, "pausas": pausas}, open("/home/user/claude/projetos/deep-ep3/edicao/edl.json", "w"), ensure_ascii=False, indent=1)

    # relatório agrupado por trecho
    print(f"{'#':>2} {'original':>15} {'saída':>11}  {'cortes':>6}  trecho")
    saida = 0.0
    grupos = []
    for e in edl:
        d = e["fim"] - e["ini"]
        if grupos and grupos[-1]["rot"] == e["rot"]:
            g = grupos[-1]; g["fim"] = e["fim"]; g["dur"] += d; g["n"] += 1
        else:
            grupos.append({"rot": e["rot"], "ini": e["ini"], "fim": e["fim"], "dur": d, "n": 1, "saida": saida})
        saida += d
    for n, g in enumerate(grupos):
        print(f"{n:>2} {g['ini']:7.2f}-{g['fim']:7.2f} {int(g['saida']//60)}:{g['saida']%60:04.1f}-{int((g['saida']+g['dur'])//60)}:{(g['saida']+g['dur'])%60:04.1f}  {g['n']-1:>6}  {g['rot']}")
    print(f"\nduração final ≈ {saida:.1f}s ({int(saida//60)}:{int(saida%60):02d}); pausas removidas: {len(pausas)} ({sum(b-a for a,b in pausas):.1f}s)")


if __name__ == "__main__":
    main()
