# DEEP — EP2 "O mercado mudou. O que você está construindo?"

Material bruto (sem pré-edição): take 1 (abertura → fim do 1º trecho exclusivo do YouTube), take 2
("Foi dessa vontade…" → "…abrir a mensagem"), take 3 (até o "Tchau") e a câmera do lado (abertura).
4K 30 fps. Versões: YouTube (12:03, com os 2 trechos exclusivos) e Instagram (8:19, sem eles; mesmo final).

| Etapa | Script | O que faz |
|---|---|---|
| 1 | `edl.py` | Trechos escolhidos seguindo o roteiro (fonte, tempos aproximados, primeiras/últimas palavras, exclusivo YT) |
| 2 | `refinar.py` | Retranscreve cada trecho e corta no silêncio real (energia), sem invadir palavra vizinha → `trechos.json` |
| 3 | `plano.py` | Junta trechos contíguos, tira pausas ≥ 0,30 s, punch-in de 12% alternado nos cortes de retake, vinheta; ajustes manuais conferidos (`AJUSTES`) |
| 4 | `audio.py` | Monta a voz de cada versão (fades de 6 ms) |
| 5 | `video.py` | Segmentos (PREVIA=1 → 720p; senão 4K) |
| 6 | `vamo.py` | "Vamo de DEEP?" atravessando atrás da cabeça (máscara de pessoa, LiteRT selfie_multiclass) |
| 7 | `insercoes.py` | Textos ASS no padrão do EP1 + SFX; âncoras nas palavras da montagem (`final_youtube.json`); Instagram remapeado |
| 8 | `final.py` | `previa` (720p < 30 MB, YouTube em 2 partes) ou render 4K; mix -14 LUFS / -1,5 dBTP |

Conferência: a montagem inteira é retranscrita e comparada com o roteiro (sobras encontradas e removidas:
tentativa repetida "E essa busca…", "Cacilda", "uma responsabilidade também", "O" cortado em "O que eu quero").
Vinheta: a mesma do EP1 (extraída de 8,52–10,08 s do vídeo do EP1).
