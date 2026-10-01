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

## v2 (revisão da editora)
Pedidos: tirar a voz da editora (ela lê o roteiro durante a gravação), cortes mais limpos, áudio sem estourar,
cor real (a v1 estava laranja), início só com "Posso pesar o clima?".
- **Voz da editora:** identificada por pitch (voz masculina ~105–135 Hz × Samara ~160–240 Hz, `falantes.py`) +
  embeddings ECAPA (speechbrain, `takes_spk.py`/`linha_tempo.py`) + nível (ela está longe do celular: −30 a −45 dB).
  A linha 2 da v1 (38,7 s) era a editora lendo; trocada pelo take dela em 89,7 s. "Posso, né?" também era a editora.
- **Linha 4:** take contínuo 303,2–313,2 s ("Até porque… Aliás, esse é um peso…").
- **Bordas** checadas por envelope de energia (sem respiro/fala antes ou depois); pausas internas só ≥ 0,55 s.
- **Cor:** HLG decodificado com npl=300, tonemap mobius sem saturar, balanço de branco R×0,95 / B×1,08.
- **Áudio:** nível igualado entre takes (±6 dB), passa-alta, afftdn leve, −2 dB em 250 Hz, +1 dB em 3 kHz,
  compressão 2:1 sem ganho extra, −16 LUFS / −2 dBTP.

## v3
- A editora reprovou a correção de cor da v2. **Padrão: não mexer na cor do bruto do iPhone.** Exportar HEVC 10 bits
  HLG (BT.2020), 60 fps, como o original, e ela trata no CapCut.
- Final "O óbvio precisa ser dito, né? … Tchau!" num trecho contínuo (respiro natural antes do tchau).
