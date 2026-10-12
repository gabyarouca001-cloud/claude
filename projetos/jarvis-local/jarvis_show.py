"""Modo show do Jarvis: duas palmas seguidas -> jingle + interface web + conversa por voz.

Variaveis de ambiente (Windows: set VAR=valor):
  JARVIS_CLAP_THRESH  sensibilidade da palma, pico 0-1 (padrao 0.25). Subir = menos sensivel.
  JARVIS_MIC          indice ou parte do nome do microfone (veja "jarvis-show --mics").
"""
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import numpy as np

RATE = 16000
BLOCK = int(RATE * 0.02)  # blocos de 20 ms
MIN_GAP, MAX_GAP = 0.12, 1.0  # intervalo aceito entre as duas palmas (s)
URL = "http://127.0.0.1:8000"


class ClapDetector:
    """Detecta duas palmas: pico alto e curto, depois silencio, depois outro pico."""

    def __init__(self, thresh):
        self.thresh = thresh
        self.first = None
        self.last_hit = -9.0

    def feed(self, block, now):
        peak = float(np.max(np.abs(block))) if len(block) else 0.0
        if peak < self.thresh or now - self.last_hit < MIN_GAP:
            return False
        self.last_hit = now
        if self.first is not None and now - self.first <= MAX_GAP:
            self.first = None
            return True
        self.first = now
        return False


def pick_mic(sd):
    want = os.environ.get("JARVIS_MIC")
    if not want:
        return None
    return int(want) if want.isdigit() else want


def listen_for_claps():
    import sounddevice as sd

    thresh = float(os.environ.get("JARVIS_CLAP_THRESH", "0.25"))
    det = ClapDetector(thresh)
    print(f"Escutando... bata palma 2x (sensibilidade {thresh}). Ctrl+C para sair.")
    with sd.InputStream(samplerate=RATE, channels=1, blocksize=BLOCK,
                        dtype="float32", device=pick_mic(sd)) as stream:
        while True:
            block, _ = stream.read(BLOCK)
            if det.feed(block[:, 0], time.monotonic()):
                return


def main():
    here = Path(__file__).resolve().parent
    if "--mics" in sys.argv:
        import sounddevice as sd
        print(sd.query_devices())
        return
    listen_for_claps()
    jingle = here / "voz" / "assets" / "jingle.mp3"
    if jingle.exists():
        os.startfile(str(jingle))  # abre no player padrao do Windows
    subprocess.run(["uv", "run", "jarvis", "start"], cwd=here)
    time.sleep(2)
    webbrowser.open(URL)
    subprocess.run(["uv", "run", "jarvis", "chat", "--voice"], cwd=here)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
