"""Mapa das inserções propostas (texto / motion / SFX) na linha do tempo da prévia (tempo de SAÍDA).
Cada entrada usa o tempo da palavra no bruto (transcricao_palavras.json) e converte pelo edl.json."""
import json

edl = json.load(open("edl.json"))["edl"]
pos, t = [], 0.0
for e in edl:
    pos.append((e["ini"], e["fim"], t)); t += e["fim"] - e["ini"]
TOTAL = t


def saida(o):
    for ini, fim, s in pos:
        if ini - 1e-6 <= o <= fim + 1e-6:
            return s + (o - ini)
    for ini, fim, s in pos:          # caiu numa pausa cortada: usa o início do próximo trecho
        if ini > o:
            return s
    return TOTAL


def mmss(x):
    return f"{int(x // 60)}:{x % 60:04.1f}"


# (tipo, descrição, entrada(s) no bruto, saída no bruto)
INS = [
    ("TEXTO", "'a história participa / DA SUA ESCOLHA'", [28.28], 29.9),
    ("MOTION", "cadeia ASSISTIR → ACREDITAR → COMPRAR (cada palavra entra na fala)", [100.28, 101.86, 102.94], 104.0),
    ("CAPÍTULO", "CAPÍTULO 1 · Produção", [106.14], 111.5),
    ("LISTA", "ESCREVER · EDITAR · CRIAR IMAGENS E VÍDEOS", [117.88, 126.10, 127.00], 129.8),
    ("TEXTO", "'a qualidade da apresentação / NÃO COMPROVA A INFORMAÇÃO'", [226.48, 229.50], 233.4),
    ("MOTION", "TESTOU ou REPETIU? (dois blocos; o 2º vira amarelo)", [239.64, 245.10], 248.3),
    ("TEXTO", "'conseguir / DEMONSTRAR O QUE SUSTENTA'", [285.00], 290.6),
    ("CAPÍTULO", "CAPÍTULO 2 · Compra", [291.72], 295.3),
    ("MOTION", "caixa 'DENTRO DO APLICATIVO': contorno, vira amarela em 'comprar na mesma hora'", [296.54, 305.00], 308.4),
    ("LISTA", "DIVERTIR · ENSINAR · GERAR COMISSÃO (comissão em amarelo)", [367.48, 369.84, 372.06], 376.0),
    ("TEXTO", "'saber que existe / INTERESSE COMERCIAL'", [379.22], 383.0),
    ("CAPÍTULO", "CAPÍTULO 3 · O tamanho do negócio", [391.66], 397.0),
    ("LISTA", "EQUIPES · PROGRAMAS · PRODUTOS · ASSINATURAS", [399.66, 400.96, 402.56, 404.24], 405.6),
    ("TEXTO", "'construindo / EMPRESAS'  (eco 'EMPRESAS' translúcido)", [420.74], 427.0),
    ("B-ROLL", "FEED → PODCAST → LOJA (3 clipes rápidos de banco de imagem)", [435.34, 436.42, 438.32], 439.6),
    ("LISTA", "RECEBER · ACOMPANHAR · PAGAR", [448.92, 452.04, 462.10], 464.4),
    ("TEXTO", "'uma questão central / CONFIANÇA'", [472.84, 473.58], 477.0),
    ("LISTA", "SE SUSTENTA? · É CUMPRIDA? · É ASSUMIDO?", [499.84, 502.20, 506.16], 509.0),
    ("TEXTO", "'perguntar, discordar e / MUDAR DE OPINIÃO'", [541.86], 543.0),
    ("TEXTO", "'todos nós' (eco gigante translúcido)", [749.07], 750.4),
    ("TEXTO", "'O QUE FAZ ALGUÉM MERECER / A SUA CONFIANÇA?'", [777.39], 781.6),
    ("TEXTO", "'E o que faria você / MUDAR DE IDEIA?'", [782.47], 785.0),
]
if __name__ == "__main__":
    print(f"{'#':>2}  {'tipo':8} {'entra (prévia)':>14}  {'sai':>6}  descrição / momentos de entrada")
    for n, (tp, d, ent, sai_) in enumerate(INS, 1):
        a = [saida(x) for x in ent]
        print(f"{n:>2}  {tp:8} {mmss(a[0] - 0.15):>14}  {mmss(saida(sai_)):>6}  {d}" + (f"  [itens em {', '.join(mmss(x) for x in a)}]" if len(a) > 1 else ""))
    print(f"\nduração da prévia: {mmss(TOTAL)}")
