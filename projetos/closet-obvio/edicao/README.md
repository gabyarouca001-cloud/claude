# O óbvio precisa ser dito — corte limpo

Bruto: IMG_1712.MOV (Drive `1X6WKGgfkC8S47bbkYZSlbAsyis4354IL`), 12:07, 2160×3840, 60 fps, HEVC HLG (iPhone).
Pedido: edição simples, só cortes limpos seguindo o roteiro + melhoria no áudio ("o resto eu faço").

`corte.py`: takes escolhidos por linha do roteiro → bordas em vales de energia no grid de 30 fps →
remove pausas internas ≥ 0,40 s (sem cortar palavra) → HLG→SDR (hable) → 4K vertical 30 fps.
Áudio: passa-alta 80 Hz, afftdn, −2,5 dB em 250 Hz, +2 dB em 3,2 kHz, de-esser, compressor 3:1, −14 LUFS / −1,5 dBTP.

Observações:
- Linha 1: "Então vamos lá" não foi gravado; entra "Posso pesar o clima? Posso, né?".
- Linha 4: usados os takes centralizados (os primeiros ela estava na borda do quadro).
- Linha 4 e 7 ficaram com as palavras gravadas ("Esse é um peso que eu tenho tentado tirar das minhas costas",
  "…sobre aquilo que você não quer ou sobre quem você não quer mais").
