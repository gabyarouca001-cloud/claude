"""Trilha original estilo desfile (house elegante, 120 BPM) + efeitos de fotógrafo. Tudo sintetizado."""
import numpy as np

SR = 48000
BPM = 120
BEAT = 60 / BPM
DUR = 37.0
rng = np.random.default_rng(11)


def t_(d):
    return np.arange(int(d * SR)) / SR


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def hp(x, fc):
    return x - lp(x, fc)


def lp_rapido(x, fc):
    """Passa-baixa por FFT (para sinais longos)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (f / fc) ** 4)
    return np.fft.irfft(X, len(x))


def hp_rapido(x, fc):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (fc / np.maximum(f, 1)) ** 4)
    return np.fft.irfft(X, len(x))


# ---------------------------------------------------------------- instrumentos
def kick():
    t = t_(0.4)
    f = 45 + 110 * np.exp(-t * 28)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    y[:int(0.004 * SR)] += rng.standard_normal(int(0.004 * SR)) * 0.35
    return y


def clap():
    n = int(0.25 * SR)
    y = np.zeros(n)
    for k, off in enumerate((0, 0.011, 0.022)):
        i = int(off * SR)
        m = n - i
        y[i:] += rng.standard_normal(m) * env(m, 0.0005, 0.012 if k < 2 else 0.09)
    return hp_rapido(lp_rapido(y, 3500), 900) * 0.8


def hat(aberto=False):
    n = int((0.22 if aberto else 0.045) * SR)
    y = hp_rapido(rng.standard_normal(n), 7000) * env(n, 0.0005, 0.07 if aberto else 0.012)
    return y * (0.35 if aberto else 0.28)


def nota(freq, d, tipo="saw"):
    t = t_(d)
    if tipo == "sin":
        return np.sin(2 * np.pi * freq * t)
    y = np.zeros_like(t)
    for det in (-0.12, 0, 0.12):  # três serras levemente desafinadas
        ph = (freq * 2 ** (det / 12) * t) % 1
        y += 2 * ph - 1
    return y / 3


# progressão em Lá menor: Am – F – C – G (um acorde por compasso de 2 s)
ACORDES = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
RAIZ = [45, 41, 36, 43]


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def trilha():
    N = int(DUR * SR)
    mix = {k: np.zeros(N) for k in ("kick", "clap", "hat", "baixo", "pad", "fx")}

    def por(canal, som, t, g=1.0):
        i = int(t * SR)
        j = min(N, i + len(som))
        if i < N:
            mix[canal][i:j] += som[:j - i] * g

    K, C, H, HO = kick(), clap(), hat(), hat(True)
    batidas = int(DUR / BEAT)
    for b in range(batidas):
        t = b * BEAT
        compasso = int(t // 2) % 4
        # seções: 0–4 intro | 4–12 montagem | 12–26 produtos | 26–28 subida | 28–34 clímax | 34+ final
        if 4 <= t < 26 or 28 <= t < 34:
            por("kick", K, t)
        if (8 <= t < 26 or 28 <= t < 34) and b % 2 == 1:
            por("clap", C, t, 0.9 if t < 12 or t >= 28 else 0.6)
        if t < 34:
            if t >= 2:
                por("hat", H, t + BEAT / 2, 1.0)  # contratempo
            if (4 <= t < 12 or 28 <= t < 34):
                por("hat", H, t + BEAT / 4, 0.5)
                por("hat", H, t + 3 * BEAT / 4, 0.5)
            if t >= 12 and t < 26 and b % 4 == 3:
                por("hat", HO, t + BEAT / 2, 0.8)
        # baixo: colcheias no contratempo, estilo house
        if 4 <= t < 26 or 28 <= t < 34:
            f = hz(RAIZ[compasso])
            for off in (BEAT / 2,):
                s = nota(f, BEAT * 0.45, "sin") + 0.25 * nota(f * 2, BEAT * 0.45, "sin")
                por("baixo", s * env(len(s), 0.004, 0.18), t + off, 0.55)
    # pad: acordes longos, filtrados
    for c in range(int(DUR // 2) + 1):
        t = c * 2.0
        if t >= 34:
            break
        acorde = ACORDES[c % 4]
        s = sum(nota(hz(m), 2.05) for m in acorde) / 3
        s = lp_rapido(s, 1400 if t < 4 else 2200)
        e = np.minimum(1, t_(2.05) / 0.25) * np.minimum(1, (2.05 - t_(2.05)) / 0.3)
        por("pad", s * e, t, 0.32)
    # sidechain: pad e baixo "respiram" com o bumbo
    duck = np.ones(N)
    for b in range(batidas):
        t = b * BEAT
        if 4 <= t < 26 or 28 <= t < 34:
            i = int(t * SR)
            n = int(0.22 * SR)
            j = min(N, i + n)
            duck[i:j] = np.minimum(duck[i:j], 0.35 + 0.65 * (np.arange(j - i) / n) ** 0.7)
    mix["pad"] *= duck
    mix["baixo"] *= 0.5 + 0.5 * duck

    # subidas (antes do drop e do clímax) e impacto final
    for ini, d in ((2.0, 2.0), (26.0, 2.0)):
        n = int(d * SR)
        ruido = rng.standard_normal(n)
        corte = np.linspace(400, 9000, n)
        y = np.zeros(n)
        bloco = 2048
        for k in range(0, n, bloco):
            y[k:k + bloco] = hp_rapido(lp_rapido(ruido[k:k + bloco], corte[k]), corte[k] / 4)
        y *= np.linspace(0, 1, n) ** 2
        por("fx", y, ini, 0.35)
    boom = nota(hz(33), 3.0, "sin") * env(int(3 * SR), 0.002, 0.9)
    por("fx", boom + hp_rapido(rng.standard_normal(len(boom)), 3000) * env(len(boom), 0.001, 0.4) * 0.3, 34.0, 0.8)
    por("fx", boom * 0.7, 4.0, 0.7)
    por("fx", boom * 0.6, 28.0, 0.6)
    # final: pad soando e sumindo
    s = lp_rapido(sum(nota(hz(m), 3.0) for m in ACORDES[0]) / 3, 1200)
    por("pad", s * np.linspace(1, 0, len(s)) ** 2, 34.0, 0.3)

    niveis = {"kick": 0.9, "clap": 0.45, "hat": 0.5, "baixo": 0.6, "pad": 0.55, "fx": 0.6}
    y = sum(mix[k] * g for k, g in niveis.items())
    return y / np.abs(y).max() * 0.9


# ---------------------------------------------------------------- efeitos de fotógrafo
def obturador():
    """Clique de câmera: espelho + cortina (dois transientes) com corpo grave."""
    n = int(0.12 * SR)
    y = np.zeros(n)
    for off, g, d in ((0.0, 1.0, 0.006), (0.028, 0.8, 0.009)):
        i = int(off * SR)
        m = n - i
        y[i:] += hp_rapido(rng.standard_normal(m), 1800) * env(m, 0.0002, d) * g
    t = t_(0.12)
    y += np.sin(2 * np.pi * 140 * t) * env(n, 0.0005, 0.012) * 0.5
    return y / np.abs(y).max()


def flash():
    """Recarga de flash (agudo subindo) + estalo."""
    t = t_(0.35)
    f = 2500 + 6000 * (t / t[-1]) ** 1.5
    carga = np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / t[-1]) * 0.15
    pop = hp_rapido(rng.standard_normal(int(0.05 * SR)), 2500) * env(int(0.05 * SR), 0.0002, 0.01)
    y = np.concatenate([carga, pop])
    return y / np.abs(y).max()


if __name__ == "__main__":
    import subprocess
    y = trilha()
    st = np.stack([y, y], 1).astype(np.float32)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "trilha.wav"], input=st.tobytes(), check=True)
    for nome, som in (("obturador", obturador()), ("flash", flash())):
        s = np.stack([som, som], 1).astype(np.float32)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        f"{nome}.wav"], input=s.tobytes(), check=True)
    print("ok")
