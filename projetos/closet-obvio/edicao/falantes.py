import json, numpy as np, parselmouth
SR=16000
x=np.fromfile("a16.f32",np.float32).astype(np.float64)
snd=parselmouth.Sound(x,SR)
p=snd.to_pitch(time_step=0.01,pitch_floor=70,pitch_ceiling=450)
f=p.selected_array['frequency']; t=p.xs()
np.save("f0.npy",np.stack([t,f]))
W=[w for s in json.load(open("transcricao.json")) for w in s["words"]]
lin=[]
for w in W:
    m=(t>=w["s"])&(t<w["e"]); v=f[m]; v=v[v>0]
    if len(v)<3: lab="·"
    else:
        med=np.median(v)
        lab="S" if med>=168 else ("G" if med<=145 else "?")
        w["f0"]=float(med)
    w["spk"]=lab
json.dump(W,open("palavras_falante.json","w"))
# imprime em linhas por pausa >0.6s
linha=[];ini=None;prev=None
for w in W:
    if prev and w["s"]-prev["e"]>0.6:
        print(f"{ini:7.2f} "+" ".join(linha)); linha=[]; ini=None
    if ini is None: ini=w["s"]
    linha.append(f"{w['w'].strip()}/{w['spk']}")
    prev=w
print(f"{ini:7.2f} "+" ".join(linha))
