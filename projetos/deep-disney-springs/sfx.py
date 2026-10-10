"""Efeitos sonoros sintetizados para as inserções "mágicas" (sino/celesta, brilho, tique do contador). Discretos: pico ~ −21 dBFS."""
import numpy as np

SR = 48000
NIVEL = {"varredura": -22.0, "tique": -27.0, "acorde": -20.0, "sino": -21.0, "saida": -24.0, "nota": -22.0}


def _t(d):
    return np.arange(int(d * SR)) / SR


def _pico(y, db):
    return y / (np.abs(y).max() + 1e-9) * 10 ** (db / 20)


def sino(f, d=1.0, decay=0.28, brilho=1.0):
    """timbre de celesta/sino: fundamental + parciais inarmônicos curtos"""
    t = _t(d)
    y = np.zeros_like(t)
    for k, (m, a, dec) in enumerate(((1.0, 1.0, 1.0), (2.76, 0.35 * brilho, 0.45), (5.4, 0.16 * brilho, 0.25), (8.9, 0.06 * brilho, 0.15))):
        y += a * np.sin(2 * np.pi * f * m * t) * np.exp(-t / (decay * dec))
    y *= np.minimum(t / 0.002, 1.0)
    return y


def _mix(partes, d):
    out = np.zeros(int(d * SR) + 1)
    for t0, y in partes:
        i = int(t0 * SR)
        out[i:i + len(y)] += y[:len(out) - i]
    return out


def acorde(d=1.3):
    """arpejo maior ascendente (Dó–Mi–Sol–Dó) com eco leve: o "pouso" do número"""
    notas = [1046.5, 1318.5, 1568.0, 2093.0]
    y = _mix([(0.075 * k, sino(f, 1.1, 0.34) * (0.8 + 0.12 * k)) for k, f in enumerate(notas)], d)
    eco = np.roll(y, int(0.19 * SR)) * 0.30
    eco[:int(0.19 * SR)] = 0
    return _pico(y + eco, NIVEL["acorde"])


def varredura(d=0.5, seed=3):
    """pó de fada: grãos de sino agudos em escala pentatônica, cada vez mais densos, sobre um sopro de ar agudo"""
    rng = np.random.default_rng(seed)
    penta = np.array([2093.0, 2349.0, 2637.0, 3136.0, 3520.0, 4186.0])
    n = 18
    grãos = []
    for k in range(n):
        t0 = d * (k / n) ** 0.8 * 0.9
        f = penta[min(int(k / n * len(penta) + rng.uniform(-0.8, 0.8)), len(penta) - 1)]
        grãos.append((t0, sino(f, 0.35, 0.09, 0.6) * rng.uniform(0.35, 1.0)))
    t = _t(d + 0.3)
    y = _mix(grãos, d + 0.3)[:len(t)]
    ar = rng.standard_normal(len(t))
    X = np.fft.rfft(ar)
    f = np.fft.rfftfreq(len(ar), 1 / SR)
    X[(f < 3500) | (f > 11000)] = 0
    ar = np.fft.irfft(X, len(ar)) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2 * (t < d)
    ar = ar / (np.abs(ar).max() + 1e-9) * 0.35 * np.abs(y).max()
    return _pico(y + ar, NIVEL["varredura"])


def tique(f=1900.0):
    t = _t(0.05)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.006) + 0.5 * np.random.default_rng(int(f)).standard_normal(len(t)) * np.exp(-t / 0.002)
    return _pico(y, NIVEL["tique"])


def nota(f, d=0.8):
    return _pico(sino(f, d, 0.26), NIVEL["nota"])


def ding(f=1568.0):
    return _pico(sino(f, 0.9, 0.3) + 0.35 * sino(f * 1.5, 0.9, 0.18), NIVEL["sino"])


def saida(d=0.45):
    """brilho descendente curto: o texto se desfaz em poeira"""
    notas = [3136.0, 2637.0, 2093.0, 1568.0]
    y = _mix([(0.06 * k, sino(f, 0.4, 0.1, 0.6) * (1 - 0.18 * k)) for k, f in enumerate(notas)], d)
    return _pico(y, NIVEL["saida"])
