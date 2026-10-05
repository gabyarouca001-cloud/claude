"""Câmera do YouTube EP2 (2ª rodada, feedback da editora):
- ENQUADRAMENTO PADRÃO fixo por take: corta a margem de parede da direita usando a cabeceira da cama como
  referência (janela com a largura da cabeceira, centrada nela). Nada de reposicionar a cada corte.
- ZOOMS só os estratégicos (punch), sempre com whoosh na entrada e na saída.
- "CÂMERA B" enquanto há gráfico/lista à esquerda: corte seco para um plano mais fechado com a Samara do lado
  direito, deixando o lado esquerdo livre para as informações; volta no fim do gráfico.
Gera dinamica_youtube2.json (tempos da montagem, sem a abertura)."""
import json
import os

os.environ.setdefault("BASE", "youtube2")
from insercoes import achar, OFF  # noqa: E402

# bordas da cabeceira medidas em cada take (px no 4K)
CABECEIRA = {"take1": (20, 3695), "take2": (40, 3720), "take3": (5, 3685)}
ZOOM_B = 1.38          # câmera B (relativo ao quadro inteiro)
ROSTO_B = 0.64         # posição horizontal do rosto na câmera B (lado direito)
AMP = 0.20             # punch estratégico
HOLD_MAX = 3.0

# (frase de início, perto (tempo do vídeo final), fim (frase ou duração))
ZOOMS = [
    ("você pensou em alguém", 9.7, "então guarda esse"),
    ("do outro lado", 57.0, "e foi aí que"),
    ("importantíssima", 165.0, 2.4),
    ("outra pergunta", 324.5, "como fazer esse trabalho"),
    ("vamos lá", 468.5, "mudar de lugar sozinho"),
    ("tem uma pergunta", 509.5, "o que a pessoa vai"),
    ("a pessoa precisa encontrar", 585.7, "por isso quando eu"),
    ("olha eu ainda estou", 626.5, "a newsletter é uma"),
    ("então lembra do nome", 644.0, "talvez você procure"),
    ("em quem confiar", 704.0, "e é sobre isso"),
]
RISE, FALL = 0.22, 0.4


def tempos():
    esq = []
    for a, b in sorted(json.load(open("esquerda_youtube2.json"))):
        a, b = a - OFF, b - OFF
        if esq and a - esq[-1][1] < 2.5:          # gráficos colados: fica na câmera B direto
            esq[-1] = (esq[-1][0], max(b, esq[-1][1]))
        else:
            esq.append((a, b))
    evs = []
    for frase, perto, fim in ZOOMS:
        s0, _ = achar(frase, perto - OFF, novo=True)
        a = s0 - 0.08
        b = achar(fim, s0, apos=s0 + 0.2)[0] - 0.12 if isinstance(fim, str) else a + fim
        b = min(max(b, a + 1.3), a + HOLD_MAX)
        if any(x - 0.5 < b + FALL and a < y + 0.5 for x, y in esq):
            continue                  # não brigar com a câmera B
        evs.append(dict(ini=round(a, 3), fim=round(b, 3), amp=AMP))
    return dict(punch=evs, camb=[(round(a, 3), round(b, 3)) for a, b in esq])


def _ss(u):
    c = f"clip({u},0,1)"
    return f"({c}*{c}*(3-2*{c}))"


def filtro(s, rosto, din, larg, alt):
    """zoompan do segmento: enquadramento padrão (cabeceira) + punches + câmera B (corte seco)"""
    t0, dur = s["t"], s["fim"] - s["ini"]
    T = f"(on/30+{t0:.3f})"
    e, d = CABECEIRA[s["fonte"]]
    z0 = 3840 / (d - e)                       # zoom do enquadramento padrão
    cx0 = (e + d) / 2 / 3840                  # centro da cabeceira
    termos = []
    for ev in din["punch"]:
        if ev["fim"] + FALL < t0 or ev["ini"] > t0 + dur:
            continue
        a_ = _ss(f"({T}-{ev['ini']:.3f})/{RISE}")
        b_ = _ss(f"({T}-{ev['fim']:.3f})/{FALL}")
        termos.append(f"{ev['amp']}*{a_}*(1-{b_})")
    zp = f"{z0:.4f}*(1+{'+'.join(termos)})" if termos else f"{z0:.4f}"
    fx, fy = rosto            # altura do rosto fixa por take (mediana) -> sem reposicionar a cada corte
    # padrão/punch: centro da cabeceira na horizontal; topo ancorado no rosto (sem cortar a cabeça)
    xp = f"{cx0:.4f}*iw-iw/zoom/2"
    yp = f"{fy:.4f}*ih-0.45*ih/zoom"
    camb = [c for c in din["camb"] if c[1] > t0 and c[0] < t0 + dur]
    if camb:
        # rosto médio do trecho inteiro do gráfico (posição única durante a câmera B)
        a, b, bx, by = camb[0][0], camb[0][1], camb[0][2], camb[0][3]
        cond = f"between({T},{a:.3f},{b:.3f})"
        z = f"if({cond},{ZOOM_B},{zp})"
        x = f"if({cond},{bx:.4f}*iw-{ROSTO_B}*iw/zoom,{xp})"
        y = f"if({cond},{by:.4f}*ih-0.42*ih/zoom,{yp})"
    else:
        z, x, y = zp, xp, yp
    return (f"zoompan=z='{z}':x='max(0,min(iw-iw/zoom,{x}))':y='max(0,min(ih-ih/zoom,{y}))':"
            f"d=1:s={larg}x{alt}:fps=30,setsar=1")


def sons(din):
    out = []
    for e in din["punch"]:
        out += [(e["ini"] - 0.06, "zoom_in"), (e["fim"] - 0.05, "zoom_out")]
    return out


if __name__ == "__main__":
    din = tempos()
    json.dump(din, open("dinamica_youtube2.json", "w"), indent=1)
    for e in din["punch"]:
        t = e["ini"] + OFF
        print(f"punch  {int(t // 60)}:{t % 60:04.1f}  {e['fim'] - e['ini']:.1f}s")
    for a, b in din["camb"]:
        print(f"câm. B {int((a + OFF) // 60)}:{(a + OFF) % 60:04.1f} -> {int((b + OFF) // 60)}:{(b + OFF) % 60:04.1f}")
