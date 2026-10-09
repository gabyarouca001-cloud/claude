import sys, json
from faster_whisper import WhisperModel
d = sys.argv[1]
m = WhisperModel("medium", device="cpu", compute_type="int8")
import wave, numpy as np
w = wave.open(f"{d}/voz_16k.wav"); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
segs, _ = m.transcribe(a, language="pt", word_timestamps=True, vad_filter=False)
out = [{"start": s.start, "end": s.end, "text": s.text, "words": [{"w": w.word, "s": w.start, "e": w.end} for w in s.words]} for s in segs]
json.dump(out, open(f"{d}/transcricao.json", "w"), ensure_ascii=False)
print("ok", d, len(out))
