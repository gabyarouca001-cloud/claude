import json, numpy as np, torch
from speechbrain.inference.speaker import EncoderClassifier
SR=16000
x=np.fromfile("a16.f32",np.float32)
enc=EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",savedir="/home/user/work/ecapa")
def emb(a,b):
    with torch.no_grad(): e=enc.encode_batch(torch.tensor(x[int(a*SR):int(b*SR)])[None])[0,0].numpy()
    return e/np.linalg.norm(e)
def lv(a,b): q=x[int(a*SR):int(b*SR)]; return 20*np.log10(np.sqrt((q**2).mean()))
S=np.mean([emb(*r) for r in [(89.68,97.0),(147.8,150.3),(189.3,200.0)]],0); S/=np.linalg.norm(S)
G=np.mean([emb(*r) for r in [(170.8,182.5),(183.4,188.5),(486.5,494.5),(501.0,509.5),(650.2,656.0)]],0); G/=np.linalg.norm(G)
C={"L1":[(3.5,5.14),(16.84,18.6),(25.40,27.02)],"L2":[(38.70,42.90),(89.68,97.0)],
"L3a":[(105.9,110),(137.26,144.06)],"L3b":[(147.80,150.26)],
"L4a":[(263.72,268.5),(269.82,274),(276.36,279.18)],
"L4b":[(289.94,295),(303.18,309.5),(336.16,341.82),(364.14,369.5)],
"L4c":[(309.5,316),(345.28,349.36),(369.5,373.5),(373.62,378)],
"L5":[(387.06,393),(405.60,412.14),(412.36,417.32)],
"L6a":[(425.06,432),(442.56,449.62)],"L6b":[(452.78,458.9),(458.9,465),(459.78,463.68)],
"L6c":[(465.12,469),(469.82,472.32)],"L7a":[(486.5,494),(511.96,515),(521.84,524.32)],
"L7b":[(534.38,540),(597.74,607.03)],
"L8":[(660.12,663.5),(668.28,672),(685.46,689),(710.30,713.5),(717.76,720.14)],"Tchau":[(690.36,691),(721.28,721.72)],
"ref_G?":[(60.06,74)],"ref_lido":[(152.64,168)]}
for k,v in C.items():
    for a,b in v:
        e=emb(a,b); print(f"{k:6s} {a:7.2f}-{b:7.2f}  S={e@S:.2f} G={e@G:.2f}  nível={lv(a,b):.1f}")
