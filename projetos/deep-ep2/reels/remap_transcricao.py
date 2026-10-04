"""Leva as palavras da transcrição do Reels v2 para a linha do tempo nova (v3, com os trechos tirados)."""
import json
V2 = json.load(open('plano_reels_v2.json'))['segmentos']
V3 = json.load(open('plano_reels.json'))['segmentos']


def src(v):
    for s in V2:
        if s['t'] - 1e-6 <= v <= s['t'] + s['fim'] - s['ini'] + 1e-6:
            return s['fonte'], s['ini'] + v - s['t']


def novo(f, x):
    for s in V3:
        if s['fonte'] == f and s['ini'] - 0.03 <= x <= s['fim'] + 0.03:
            return s['t'] + min(max(x, s['ini']), s['fim']) - s['ini']


out = []
for seg in json.load(open('final_reels_v2.json')):
    ws = []
    for w in seg['words']:
        a, b = src(w['s']), src(w['e'])
        if not a or not b:
            continue
        ns, ne = novo(*a), novo(*b)
        if ns is None and ne is None:     # palavra dentro de trecho tirado
            continue
        if ne is None:                    # o fim da palavra caiu num corte: fecha no fim do segmento
            ne = ns + 0.25
        if ns is None:
            ns = ne - 0.25
        ws.append(dict(w, s=round(ns, 3), e=round(max(ne, ns + 0.05), 3)))
    if ws:
        if ws[0]['w'].strip() == 'hoje':
            ws[0]['w'] = ' Hoje'
        out.append(dict(start=ws[0]['s'], end=ws[-1]['e'], text=''.join(w['w'] for w in ws).strip(), words=ws))
json.dump(out, open('final_reels.json', 'w'), ensure_ascii=False)
for s in out:
    print(f"{s['start']:7.2f} {s['text']}")
