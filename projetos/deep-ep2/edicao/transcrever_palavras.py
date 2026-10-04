import json, sys
from faster_whisper import WhisperModel
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
segs, _ = m.transcribe(sys.argv[1], language="pt", word_timestamps=True, vad_filter=False, beam_size=5,
                       initial_prompt="DEEP, Samara Checon, Substack, podcasts, newsletter, Instagram, criadores, faturamento.")
json.dump([dict(w=w.word.strip(), s=w.start, e=w.end) for s in segs for w in s.words], open(sys.argv[2], "w"), ensure_ascii=False)
print("FIM")
