"""Etapa 1: decide os segmentos mantidos (cortes de retakes + silêncios) a partir de 4:43."""
import json
import subprocess

import numpy as np

FPS = 25
SR = 48000
INICIO_BRUTO = 283.92      # fim de "…e para tentar entender." — antes disso já está editado
FIM = 509.56
AUDIO_RUIM = (271.25, 283.15)

# Retakes: (fim da última palavra boa, início da próxima palavra boa)
RETAKES = [
    (320.58, 335.78, "A segunda... / Desce um pouco, Gabi / Vai"),
    (372.22, 379.74, "Porque essa audiência é só sua, entendeu? (repetida)"),
    (384.96, 401.94, "E a terceira... publi não é um formato / Desce um pouco, Gabi / Mais"),
    (418.00, 422.22, "que funciona, independente de marca. (incompleta)"),
    (427.46, 448.86, "E esse mercado... / Vai / Volta, só mais um pouco"),
    (476.58, 480.46, "a pergunta que vale você fazer hoje é... (repetida)"),
]

SIL_DB = -36.0
SIL_MIN = 0.30
PAD_ANTES = 0.10   # mantém depois da palavra anterior
PAD_DEPOIS = 0.08  # mantém antes da próxima palavra

def snap(t):
    return round(t * FPS) / FPS

def carregar_audio():
    bruto = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", "original.mp4", "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(bruto, np.float32)

def rms_db(x, passo=0.01):
    n = int(SR * passo)
    q = x[: len(x) // n * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt((q ** 2).mean(1)) + 1e-9)

def vale(db, t, janela=0.12, passo=0.01):
    """Ponto de menor energia perto de t (para cortar entre palavras coladas)."""
    a, b = int((t - janela) / passo), int((t + janela) / passo)
    return (a + int(np.argmin(db[a:b]))) * passo

def main():
    x = carregar_audio()
    db = rms_db(x)

    remover = []
    for fim_bom, ini_bom, _ in RETAKES:
        a = vale(db, fim_bom) + 0.10 if fim_bom != 418.00 else vale(db, fim_bom, 0.10)
        b = ini_bom - 0.06
        remover.append((a, b, "retake"))

    # silêncios no trecho bruto
    silencioso = db < SIL_DB
    i0 = int(INICIO_BRUTO / 0.01)
    i1 = int(FIM / 0.01)
    i = i0
    while i < i1:
        if silencioso[i]:
            j = i
            while j < i1 and silencioso[j]:
                j += 1
            ini, fim = i * 0.01, j * 0.01
            if fim - ini >= SIL_MIN and fim < FIM - 0.3:
                remover.append((ini + PAD_ANTES, fim - PAD_DEPOIS, "silencio"))
            i = j
        else:
            i += 1

    # funde remoções sobrepostas
    remover.sort()
    fundidos = []
    for a, b, tipo in remover:
        a, b = snap(a), snap(b)
        if b - a < 0.08:
            continue
        if fundidos and a <= fundidos[-1][1]:
            ult = fundidos[-1]
            fundidos[-1] = (ult[0], max(ult[1], b), "retake" if "retake" in (ult[2], tipo) else tipo)
        else:
            fundidos.append((a, b, tipo))

    # segmentos mantidos
    segmentos = []
    pos = 0.0
    for a, b, tipo in fundidos:
        if a > pos:
            segmentos.append({"ini": pos, "fim": a, "corte_depois": tipo})
        pos = b
    segmentos.append({"ini": pos, "fim": FIM, "corte_depois": None})

    # zoom alterna a cada retake (esconde o pulo); troca natural de plano em 501.5
    zoom = 1.0
    for s in segmentos:
        s["zoom"] = zoom if s["ini"] >= INICIO_BRUTO - 0.01 else 1.0
        if s["corte_depois"] == "retake":
            zoom = 1.12 if zoom == 1.0 else 1.0
    for s in segmentos:
        if s["ini"] >= 501.4:
            s["zoom"] = 1.0

    removido = sum(b - a for a, b, _ in fundidos)
    print(f"{len(segmentos)} segmentos | removido {removido:.1f}s "
          f"(retakes {sum(b-a for a,b,t in fundidos if t=='retake'):.1f}s, "
          f"silêncios {sum(b-a for a,b,t in fundidos if t=='silencio'):.1f}s) | "
          f"duração final {FIM - removido:.1f}s")
    json.dump({"segmentos": segmentos, "removidos": fundidos}, open("plano.json", "w"), indent=1)

if __name__ == "__main__":
    main()
