"""Utilitários de foto para os carrosséis do Japão: download, retoque de pele e recorte 4:5."""
import os, subprocess, numpy as np, cv2
from PIL import Image, ImageOps

BASE = "/home/user/work/japao_fotos"
ORIG = "/home/user/work/carrosseis/originais"
MODELO = "/home/user/work/modelos/face_landmarker.task"

_ids = None
def foto_id(num):
    global _ids
    if _ids is None:
        _ids = {}
        for l in open(f"{BASE}/jpgs.tsv"):
            i, p, n = l.rstrip("\n").split("\t")
            _ids[int(n[3:-4])] = i
    return _ids[num]

def baixar(num):
    """Baixa a foto original (cache em ORIG) e devolve o caminho."""
    out = f"{ORIG}/DSC{num:05d}.jpg"
    if not (os.path.exists(out) and os.path.getsize(out) > 100000):
        subprocess.run(["curl", "-sSL", "-m", "180", "--retry", "3", "-o", out,
                        f"https://drive.usercontent.google.com/download?id={foto_id(num)}&export=download&confirm=t"], check=True)
    return out

def abrir(num):
    im = Image.open(baixar(num)); im = ImageOps.exif_transpose(im).convert("RGB")
    return im

# ---------------- retoque de pele ----------------
_lm = None
def _landmarker():
    global _lm
    if _lm is None:
        import mediapipe as mp
        from mediapipe.tasks.python import vision, BaseOptions
        opts = vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=MODELO),
                                            num_faces=8, min_face_detection_confidence=0.3,
                                            min_face_presence_confidence=0.3)
        _lm = vision.FaceLandmarker.create_from_options(opts)
    return _lm

def _idx(conn):
    s = set()
    for a, b in conn: s.add(a); s.add(b)
    return s

def _poly(pts, ids_order):
    return np.array([pts[i] for i in ids_order], np.int32)

def _ordered(conn):
    """ordena as arestas de um contorno fechado em sequência de pontos."""
    nxt = {a: b for a, b in conn}
    start = conn[0][0]; seq = [start]; cur = nxt[start]
    while cur != start and len(seq) < 200:
        seq.append(cur); cur = nxt.get(cur)
        if cur is None: break
    return seq

def _detectar_pass(im_pil, ox=0, oy=0, esc=1.0):
    import mediapipe as mp
    res = _landmarker().detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.array(im_pil)))
    out = []
    w, h = im_pil.size
    for lm in res.face_landmarks:
        pts = np.array([[p.x * w, p.y * h] for p in lm]) / esc + np.array([ox, oy])
        x0, y0 = pts.min(0); x1, y1 = pts.max(0)
        out.append(dict(pts=pts, bbox=(x0, y0, x1, y1), larg=x1 - x0))
    return out

def detectar(im_pil, maxlado=1600, tile=1600, passo=1000):
    """Rostos: passada na imagem inteira + varredura em recortes na resolução original (rostos pequenos)."""
    w, h = im_pil.size; s = min(1.0, maxlado / max(w, h))
    small = im_pil.resize((int(w * s), int(h * s)), Image.LANCZOS)
    faces = _detectar_pass(small, 0, 0, s)
    for oy in range(0, max(1, h - tile + passo), passo):
        for ox in range(0, max(1, w - tile + passo), passo):
            ox2 = min(ox, max(0, w - tile)); oy2 = min(oy, max(0, h - tile))
            faces += _detectar_pass(im_pil.crop((ox2, oy2, ox2 + tile, oy2 + tile)), ox2, oy2, 1.0)
    # remove duplicatas (mesmo rosto achado em passadas diferentes): fica o de maior largura
    faces.sort(key=lambda f: -f["larg"]); uniq = []
    for f in faces:
        cx = (f["bbox"][0] + f["bbox"][2]) / 2; cy = (f["bbox"][1] + f["bbox"][3]) / 2
        if all(np.hypot(cx - (u["bbox"][0] + u["bbox"][2]) / 2, cy - (u["bbox"][1] + u["bbox"][3]) / 2) > 0.5 * max(f["larg"], u["larg"]) for u in uniq):
            uniq.append(f)
    uniq.sort(key=lambda f: f["bbox"][0])
    return uniq

def _mascara_pele(shape, pts, ycc):
    from mediapipe.tasks.python.vision import FaceLandmarksConnections as C
    h, w = shape
    P = pts.astype(np.float32)
    m = np.zeros((h, w), np.uint8)
    oval = _ordered([(c.start, c.end) for c in C.FACE_LANDMARKS_FACE_OVAL])
    cv2.fillPoly(m, [P[oval].astype(np.int32)], 255)
    larg = P[:, 0].max() - P[:, 0].min()
    # tira olhos, sobrancelhas e lábios (com folga) para manter nitidez
    ex = np.zeros_like(m)
    for conj, dil in ((C.FACE_LANDMARKS_LEFT_EYE, 0.020), (C.FACE_LANDMARKS_RIGHT_EYE, 0.020),
                      (C.FACE_LANDMARKS_LEFT_EYEBROW, 0.018), (C.FACE_LANDMARKS_RIGHT_EYEBROW, 0.018),
                      (C.FACE_LANDMARKS_LIPS, 0.012)):
        seq = _ordered([(c.start, c.end) for c in conj])
        tmp = np.zeros_like(m); cv2.fillPoly(tmp, [P[seq].astype(np.int32)], 255)
        k = max(3, int(larg * dil)) | 1
        ex = cv2.bitwise_or(ex, cv2.dilate(tmp, np.ones((k, k), np.uint8)))
    m = cv2.bitwise_and(m, cv2.bitwise_not(ex))
    # só pele: porta de cor calibrada pela pele do próprio rosto (descarta cabelo, óculos, sombras)
    lab = cv2.cvtColor(cv2.cvtColor(ycc, cv2.COLOR_YCrCb2RGB), cv2.COLOR_RGB2LAB).astype(np.float32)
    core_ids = [4, 5, 195, 197, 6, 50, 280, 205, 425, 118, 347, 101, 330, 152, 200]
    core = np.zeros_like(m)
    for i in core_ids: cv2.circle(core, tuple(int(v) for v in P[i]), max(2, int(larg * 0.025)), 255, -1)
    core = cv2.bitwise_and(core, m)
    sel = core > 0
    if sel.sum() < 30: sel = m > 0
    med = np.median(lab[sel], axis=0)
    dab = np.hypot(lab[..., 1] - med[1], lab[..., 2] - med[2])
    dL = np.abs(lab[..., 0] - med[0])
    gate_cor = np.clip((24 - dab) / 10, 0, 1) * np.clip((55 - dL) / 20, 0, 1)
    # textura: cabelo tem muita borda fina, pele não
    fy = ycc[..., 0].astype(np.float32)
    fine = np.abs(fy - cv2.GaussianBlur(fy, (0, 0), max(1.0, larg / 200)))
    energia = cv2.GaussianBlur(fine, (0, 0), max(2.0, larg / 60))
    ref = np.median(energia[sel]) + 1e-3
    gate_tex = np.clip((3.2 * ref - energia) / (1.2 * ref), 0, 1)
    gate = gate_cor * gate_tex
    gate = cv2.morphologyEx(gate, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.bitwise_and(m, (gate * 255).astype(np.uint8))
    # recolhe a borda externa (cabelo/contorno) para dentro
    k = max(3, int(larg * 0.03)) | 1
    m = cv2.erode(m, np.ones((k, k), np.uint8))
    f = max(5, int(larg * 0.035)) | 1
    m = cv2.GaussianBlur(m, (f * 2 + 1, f * 2 + 1), f / 2)
    return m.astype(np.float32) / 255.0

def retocar_rosto(im_pil, face, forca=0.85, textura=0.30):
    """Suaviza linhas/marcas de expressão e uniformiza a pele (estilo photoshop) só dentro do rosto."""
    arr = np.array(im_pil)
    x0, y0, x1, y1 = face["bbox"]; larg = x1 - x0
    mg = int(larg * 0.25)
    X0, Y0 = max(0, int(x0 - mg)), max(0, int(y0 - mg)); X1, Y1 = min(arr.shape[1], int(x1 + mg)), min(arr.shape[0], int(y1 + mg))
    crop = arr[Y0:Y1, X0:X1].copy()
    pts = face["pts"] - np.array([X0, Y0])
    ycc = cv2.cvtColor(crop, cv2.COLOR_RGB2YCrCb)
    m = _mascara_pele(crop.shape[:2], pts, ycc)[..., None]
    f = crop.astype(np.float32)
    # 1) camada lisa: bilateral forte (apaga linhas finas e poros, preserva bordas reais)
    sp = max(3.0, larg / 70); sc = 38
    liso = f.copy()
    for _ in range(3):
        liso = cv2.bilateralFilter(liso, 0, sc, sp)
    # 2) tira o relevo de média escala (rugas, olheiras, sulcos) com um borrão largo
    gros = cv2.GaussianBlur(liso, (0, 0), max(2.0, larg / 45))
    liso = 0.55 * liso + 0.45 * gros
    # 3) devolve parte da textura fina para não ficar plástico
    fino = f - cv2.GaussianBlur(f, (0, 0), max(1.0, larg / 160))
    novo = liso + fino * textura
    # 4) uniformiza tom (manchas/olheiras) na crominância
    lab = cv2.cvtColor(np.clip(novo, 0, 255).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
    ab = cv2.GaussianBlur(lab[..., 1:], (0, 0), max(3.0, larg / 18))
    lab[..., 1:] = 0.6 * lab[..., 1:] + 0.4 * ab
    novo = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32)
    out = f * (1 - m * forca) + novo * (m * forca)
    arr[Y0:Y1, X0:X1] = np.clip(out, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def retocar(im_pil, quais="todos", min_larg=60, **kw):
    """quais: 'todos' | 'maior' | lista de índices (esq→dir) | callable(faces)->faces."""
    faces = detectar(im_pil)
    faces = [f for f in faces if f["larg"] >= min_larg]
    if quais == "maior": faces = sorted(faces, key=lambda f: -f["larg"])[:1]
    elif isinstance(quais, (list, tuple)): faces = [faces[i] for i in quais if i < len(faces)]
    elif callable(quais): faces = quais(faces)
    for f in faces: im_pil = retocar_rosto(im_pil, f, **kw)
    return im_pil, len(faces)
