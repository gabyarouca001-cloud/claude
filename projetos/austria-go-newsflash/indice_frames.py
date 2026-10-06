"""Índice de quadros (64x36 cinza) para casar planos do vídeo final com o material bruto."""
import subprocess
import numpy as np

W, H = 64, 36


def quadros(arq, fps):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", arq, "-vf",
                        f"fps={fps},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},format=gray",
                        "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(b, np.uint8).reshape(-1, H, W).astype(np.float32)
    return x


def norm(x):
    c = x[:, 6:30, 10:54].reshape(len(x), -1)       # miolo do quadro (ignora bordas / tarjas)
    c = c - c.mean(1, keepdims=True)
    return c / (np.linalg.norm(c, axis=1, keepdims=True) + 1e-6)
