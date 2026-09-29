# DEEP — edição do episódio "Como ser influencer"

Pipeline que pegou o vídeo pré-editado (4K, 8:29) e entregou a versão final (7:16).

| Etapa | Script | O que faz |
|---|---|---|
| 1 | `plano.py` | Retakes e silêncios a remover a partir de 4:43 (`plano.json`) |
| 2 | `audio.py` | Corrige o áudio de 4:31–4:43 (+ganho, compressão, EQ) e monta a voz cortada |
| 3 | `video.py` | Renderiza cada segmento em 4K, com punch-in de 12% alternado nos retakes e sem a linha verde do topo |
| 4 | `insercoes.py` | Textos animados (`insercoes.ass`), gráfico de -35% e efeitos sonoros sintetizados |
| 5 | `final.py` | Junta tudo, normaliza em -14 LUFS e exporta YouTube e Instagram |

Pré-requisitos: `original.mp4` e `transcricao.json` (faster-whisper `medium`, com tempo por palavra) na mesma pasta, além das fontes Playfair Display Italic e Inter (Black, ExtraBold, Medium) em `fonts/`.

## Retakes removidos (tempo do vídeo original)
- 5:20–5:35 — "A segunda… / Desce um pouco, Gabi / Vai"
- 6:12–6:19 — "Porque essa audiência é só sua, entendeu?" (repetida)
- 6:25–6:41 — "publi não é um formato… / Desce um pouco, Gabi / Mais"
- 6:58–7:02 — "que funciona, independente de marca." (incompleta)
- 7:07–7:28 — "E esse mercado… / Vai / Volta, só mais um pouco"
- 7:56–8:00 — "a pergunta que vale você fazer hoje é…" (repetida)
