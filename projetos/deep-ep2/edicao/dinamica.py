"""Zooms dinâmicos do YouTube EP2 (pedido da editora: mais dinamismo, sempre com a Samara em foco).
- punch: zoom rápido (0,25 s) numa frase de impacto, segura e volta (0,4 s); whoosh na entrada e na saída
- escada: perguntas em sequência, cada uma sobe um degrau; volta tudo no fim
- push: aproximação lenta ao longo de uma fala reflexiva (sem som)
Gera dinamica_youtube2.json com os eventos no tempo da montagem (sem a abertura)."""
import json
import os

os.environ.setdefault("BASE", "youtube2")
from insercoes import achar, OFF  # noqa: E402  (âncoras na retranscrição da montagem)

# (tipo, frase de início, perto (tempo do vídeo final), fim (frase ou duração), amplitude)
ZOOMS = [
    ("punch", "você pensou em alguém", 9.7, "então guarda esse", 0.18),
    ("push", "e essa busca me fez", 46.3, "porque eu trabalho", 0.07),
    ("punch", "do outro lado", 57.0, "e foi aí que", 0.16),
    ("punch", "até o final", 23.0 + 60, 1.6, 0.14),
    ("push", "e tem criador buscando", 107.1, "e a minha leitura", 0.07),
    ("punch", "importantíssima", 165.0, "porque você pode passar", 0.16),
    ("escada", "o que aconteceu antes", 190.6, "e aí eu fui atrás", 0.10),
    ("escada", "quais são as dúvidas", 191.8, "e aí eu fui atrás", 0.10),
    ("escada", "onde aquela explicação", 194.8, "e aí eu fui atrás", 0.10),
    ("punch", "para quem cria também", 240.9, "como desenvolver uma", 0.15),
    ("punch", "por isso gente", 268.5, "eu entendo essa busca", 0.16),
    ("push", "qual é a diferença entre", 297.9, "lembra que no primeiro", 0.08),
    ("punch", "outra pergunta", 324.5, "como fazer esse trabalho", 0.16),
    ("punch", "acompanhar você", 345.0, "e é aí que a conversa", 0.14),
    ("push", "essa pergunta começou a", 387.7, "o que eu quero desenvolver", 0.06),
    ("escada", "o que eu quero desenvolver", 393.4, "e assim hoje existem", 0.09),
    ("escada", "que tipo de conversa", 397.5, "e assim hoje existem", 0.09),
    ("escada", "por que alguém escolheria", 400.8, "e assim hoje existem", 0.09),
    ("punch", "vamos lá", 468.5, "mudar de lugar sozinho", 0.16),
    ("push", "imagina que cada canal", 490.5, "então antes de abrir", 0.07),
    ("punch", "tem uma pergunta", 509.5, "o que a pessoa vai", 0.15),
    ("push", "você ganha uma possibilidade", 567.5, "por isso diversificar", 0.07),
    ("punch", "a pessoa precisa encontrar", 585.7, "por isso quando eu", 0.15),
    ("punch", "olha eu ainda estou", 626.5, "a newsletter é uma", 0.15),
    ("punch", "então lembra do nome", 644.0, "talvez você procure", 0.18),
    ("punch", "porque gente o faturamento", 666.8, "mas o que você constrói", 0.15),
    ("push", "e aí como nós vamos", 701.6, "e é sobre isso", 0.12),
]


GANHO = 1.4


def tempos():
    evs = []
    for tipo, frase, perto, fim, amp in ZOOMS:
        s0, _ = achar(frase, perto - OFF, novo=True)
        a = s0 - 0.08
        if isinstance(fim, str):
            b = achar(fim, s0, apos=s0 + 0.2)[0] - 0.12
        else:
            b = a + fim
        if tipo == "punch":
            b = max(b, a + 1.3)
        evs.append(dict(tipo=tipo, ini=round(a, 3), fim=round(b, 3), amp=round(amp * GANHO, 3)))
    return evs


GANHO = 1.4          # na 1ª prévia interna os zooms ficaram sutis demais
RISE = {"punch": 0.22, "escada": 0.3}
FALL = {"punch": 0.4, "escada": 0.5, "push": 0.6}


def _ss(u):
    c = f"clip({u},0,1)"
    return f"({c}*{c}*(3-2*{c}))"


def expr_zoom(t0, dur, base, evs):
    """expressão do zoompan para um segmento que começa em t0 (tempo da montagem) e dura dur"""
    T = f"(on/30+{t0:.3f})"
    termos = []
    for e in evs:
        fall = FALL[e["tipo"]]
        if e["fim"] + fall < t0 or e["ini"] > t0 + dur:
            continue
        rise = RISE.get(e["tipo"], max(e["fim"] - e["ini"], 0.5))
        a_ = _ss("(" + T + "-" + f"{e['ini']:.3f}" + ")/" + f"{rise}")
        b_ = _ss("(" + T + "-" + f"{e['fim']:.3f}" + ")/" + f"{fall}")
        termos.append(f"{e['amp']}*{a_}*(1-{b_})")
    z = "1" if not termos else "1+" + "+".join(termos)
    return f"{base}*({z})" if base != 1.0 else z


def sons(evs):
    """whoosh de zoom: entrada em cada punch/degrau, saída no fim (uma vez por escada)"""
    out, fins = [], set()
    for e in evs:
        if e["tipo"] == "push":
            continue
        out.append((e["ini"] - 0.06, "zoom_in"))
        if round(e["fim"], 1) not in fins:
            fins.add(round(e["fim"], 1))
            out.append((e["fim"] - 0.05, "zoom_out"))
    return out


if __name__ == "__main__":
    evs = tempos()
    json.dump(evs, open("dinamica_youtube2.json", "w"), indent=1)
    for e in evs:
        t = e["ini"] + OFF
        print(f"{int(t // 60)}:{t % 60:04.1f}  {e['tipo']:7s} {e['fim'] - e['ini']:5.1f}s  +{e['amp']:.2f}")
