"""Sons dos destaques (sintetizados, discretos) — os mesmos do EP1/EP2."""
import numpy as np

SR = 48000


def env(n, ataque, queda):
    t = np.arange(n) / SR
    return np.minimum(1, t / ataque) * np.exp(-t / queda)


def som(tipo, rng=np.random.default_rng(7)):
    if tipo == "whoosh":
        n = int(0.55 * SR)
        ruido = rng.standard_normal(n)
        t = np.arange(n) / SR
        fc = 400 + 3200 * np.sin(np.pi * t / t[-1]) ** 2
        y = np.zeros(n)
        lp = hp = 0.0
        for i in range(n):
            a = 1 - np.exp(-2 * np.pi * fc[i] / SR)
            lp += a * (ruido[i] - lp)
            hp += 0.02 * (lp - hp)
            y[i] = lp - hp
        y *= np.sin(np.pi * t / t[-1]) ** 2
        return y / np.abs(y).max() * 10 ** (-27 / 20)
    if tipo == "tick":
        n = int(0.12 * SR)
        t = np.arange(n) / SR
        y = np.sin(2 * np.pi * 1850 * t) * env(n, 0.001, 0.018) + 0.4 * np.sin(2 * np.pi * 3700 * t) * env(n, 0.001, 0.008)
        return y / np.abs(y).max() * 10 ** (-30 / 20)
    if tipo == "chime":
        n = int(1.2 * SR)
        t = np.arange(n) / SR
        y = (np.sin(2 * np.pi * 880 * t) + 0.5 * np.sin(2 * np.pi * 1320 * t) + 0.25 * np.sin(2 * np.pi * 1760 * t)) * env(n, 0.004, 0.35)
        return y / np.abs(y).max() * 10 ** (-31 / 20)
    if tipo in ("zoom_in", "zoom_out"):
        # whoosh curto e abafado; entrada sobe, saída desce (bem abaixo da voz)
        n = int(0.32 * SR)
        t = np.arange(n) / SR
        ruido = rng.standard_normal(n)
        sobe = tipo == "zoom_in"
        fc = (300 + 2600 * (t / t[-1]) ** 2) if sobe else (2600 - 2300 * (t / t[-1]) ** 0.5)
        y = np.zeros(n)
        lp = hp = 0.0
        for i in range(n):
            a_ = 1 - np.exp(-2 * np.pi * fc[i] / SR)
            lp += a_ * (ruido[i] - lp)
            hp += 0.03 * (lp - hp)
            y[i] = lp - hp
        y *= np.sin(np.pi * (t / t[-1]) ** (0.7 if sobe else 1.4)) ** 2
        return y / np.abs(y).max() * 10 ** ((-29 if sobe else -32) / 20)
    if tipo == "bloco":
        # "toc" grave de encaixe
        n = int(0.18 * SR)
        t = np.arange(n) / SR
        y = np.sin(2 * np.pi * 150 * t) * env(n, 0.001, 0.045) + 0.3 * rng.standard_normal(n) * env(n, 0.0005, 0.008)
        return y / np.abs(y).max() * 10 ** (-27 / 20)
    raise ValueError(tipo)


