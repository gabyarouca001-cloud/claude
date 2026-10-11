"""Separa voz x música com Demucs (htdemucs_ft — modelo especialista em voz).
Pesos carregados com torch.load(weights_only=True), liberando só as classes do Demucs/numpy necessárias
(o arquivo baixado não executa código). Áudio lido/gravado pelo ffmpeg (sem torchaudio/torchcodec).
Uso: python3 separar_voz.py entrada(audio/video) voz.wav [musica.wav]   (pesos em /home/user/work/modelos/demucs)"""
import fractions
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch
import demucs.demucs
import demucs.hdemucs
import demucs.htdemucs
from demucs.apply import apply_model
from demucs.pretrained import get_model

torch.serialization.add_safe_globals([
    demucs.htdemucs.HTDemucs, demucs.hdemucs.HDemucs, demucs.demucs.Demucs, fractions.Fraction,
    (np._core.multiarray.scalar, "numpy.core.multiarray.scalar"), np.dtype,
    *[getattr(np.dtypes, n) for n in dir(np.dtypes) if n.endswith("DType")]])

SR = 44100
entrada, saida_voz = sys.argv[1], sys.argv[2]
saida_mus = sys.argv[3] if len(sys.argv) > 3 else None
b = subprocess.run(["ffmpeg", "-v", "error", "-i", entrada, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                   capture_output=True, check=True).stdout
wav = torch.from_numpy(np.frombuffer(b, np.float32).reshape(-1, 2).T.copy())
modelo = get_model("vocals_ft", repo=Path("/home/user/work/modelos/demucs"))
modelo.eval()
torch.set_num_threads(4)
ref = wav.mean(0)
m, s = ref.mean(), ref.std()
with torch.no_grad():
    fontes = apply_model(modelo, ((wav - m) / s)[None], device="cpu", shifts=1, split=True, overlap=0.25,
                         progress=True, num_workers=0)[0] * s + m
voz = fontes[modelo.sources.index("vocals")]
for arq, x in [(saida_voz, voz), (saida_mus, wav - voz)]:
    if arq:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_s16le",
                        arq], input=x.T.contiguous().numpy().astype(np.float32).tobytes(), check=True)
print("OK", saida_voz, saida_mus)
