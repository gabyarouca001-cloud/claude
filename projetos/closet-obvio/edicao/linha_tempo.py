import numpy as np, torch, json, sys
from speechbrain.inference.speaker import EncoderClassifier
SR=16000
x=np.fromfile("a16.f32",np.float32)
enc=EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",savedir="/home/user/work/ecapa")
def emb(a,b):
    with torch.no_grad(): e=enc.encode_batch(torch.tensor(x[int(a*SR):int(b*SR)])[None])[0,0].numpy()
    return e/np.linalg.norm(e)
def ref(rs,L=0.6):
    out=[]
    for a,b in rs:
        for c in np.arange(a+L/2,b-L/2,0.3): out.append(emb(c-L/2,c+L/2))
    return np.array(out)
RS=ref([(89.68,96.2),(147.8,150.3),(189.3,200.0)])
RG=ref([(38.7,42.9),(170.8,182.5),(183.4,188.5),(152.64,168.0),(60.06,74.0)])
W=[w for s in json.load(open("transcricao.json")) for w in s["words"]]
def score(c,L=0.6):
    e=emb(c-L/2,c+L/2)
    s=np.sort(RS@e)[-5:].mean(); g=np.sort(RG@e)[-5:].mean()   # kNN
    return s-g
segs=json.load(open("plano.json"))
res={}
for a,b,l in segs:
    linha=""; vals=[]
    for c in np.arange(a+0.3,b-0.3+1e-6,0.1):
        q=x[int((c-0.05)*SR):int((c+0.05)*SR)]
        if 20*np.log10(np.sqrt((q**2).mean())+1e-9)<-42: linha+="."; vals.append(None); continue
        d=score(c); vals.append(float(d))
        linha+= "S" if d>0.05 else ("G" if d<-0.05 else "?")
    res[str(a)]=vals
    print(f"L{l} {a:.2f}-{b:.2f}\n{linha}")
json.dump(res,open("linha_tempo.json","w"))
