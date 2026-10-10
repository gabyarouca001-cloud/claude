"""Resolve a EDL: (t, dur, filme, ss) e valida contra os limites de cena. Rodar em /home/user/work/gn."""
import json
import edl as E

def resolver(dir_dados="/home/user/work/gn"):
    sh = {35: json.load(open(f"{dir_dados}/shots35.json")), 36: json.load(open(f"{dir_dados}/shots36.json"))}
    import os
    batidas = json.load(open(f"{dir_dados}/beats.json")) if os.path.exists(f"{dir_dados}/beats.json") else []

    def snap(t):
        """ajusta o corte para a batida mais próxima (até ±0,12 s); o resto fica ancorado na palavra"""
        if t <= 0 or not batidas:
            return t
        b = min(batidas, key=lambda x: abs(x - t))
        return b if abs(b - t) <= 0.12 else t
    tempos = [snap(x[0]) for x in E.EDL]
    out = []
    for i, (t, f, src, obs) in enumerate(E.EDL):
        t = round(tempos[i] * E.FPS) / E.FPS
        fim = round((tempos[i + 1] if i + 1 < len(E.EDL) else E.TOTAL) * E.FPS) / E.FPS
        dur = fim - t
        if isinstance(src, tuple):
            a, b = sh[36][src[1]]
            ss = a + src[2]
        else:
            ss = src
            a = b = None
            for x, y in sh[35]:
                if x <= ss < y:
                    a, b = x, y
        aviso = ""
        if a is None or ss < a - 1e-6 or ss + dur > b + 0.04:
            aviso = f"FORA DA CENA ({a}-{b}, precisa até {ss + dur:.2f})"
        out.append(dict(i=i, t=t, dur=dur, f=f, ss=ss, obs=obs, aviso=aviso))
    return out

if __name__ == "__main__":
    for e in resolver():
        print(f"{e['i']:2d} t={e['t']:6.2f} dur={e['dur']:.2f} f={e['f']} ss={e['ss']:.2f} {e['obs']} {e['aviso']}")
