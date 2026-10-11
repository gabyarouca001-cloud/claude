---
name: deep-reels-cortes
description: Cortes verticais 9:16 (Reels/TikTok/Shorts) dos episódios DEEP — área segura, gancho com título olho de peixe, legendas palavra a palavra, ajustes aprovados no EP2 (sombra, brilho amarelo, B-roll Mixkit, trilha "Chillax") e o fluxo "versão da editora → legendar e tirar a música" do EP3. Usar quando a editora pedir Reels, cortes para redes, legendas de uma versão dela ou troca de trilha.
---

# Reels / cortes verticais DEEP

Sempre rodar a skill `checar-falas` antes de entregar. Prévia para o chat sempre em H.264 (HEVC/HDR não abre no chat).

## Cortes para redes (um corte por capítulo do YouTube)
Script base: `projetos/deep-influencer/edicao/cortes_sociais.py`.
- 9:16, 1080×1920, recorte central do 4K (sem as inserções do 16:9, refeitas para o vertical).
- **Área segura:** topo 250 px, base 480 px, direita 140 px livres; texto centrado em x ≈ 510, largura útil 820 px.
- **Gancho** no topo nos primeiros ~3,5 s: título em Playfair Display (caixa normal), **todo amarelo #FCEDC0, com efeito olho de peixe** (`titulo_olho_peixe.py`), na faixa acima da cabeça (y ≈ 175–515); **legendas** palavra a palavra (Inter ExtraBold 70, branco, y = 1330), escondidas enquanto há inserção; inserções entre y ≈ 1000 e 1420.
- Fim: "EPISÓDIO COMPLETO / NO YOUTUBE" no canto superior esquerdo, com barra amarela.
- Trechos com texto da editora gravado na imagem: mostrar o quadro 16:9 inteiro sobre fundo desfocado.
- Cada corte fica com menos de 30 MB (2 passes, bitrate calculado pela duração) e vai com sugestão de texto de post e hashtags.

## Ajustes da editora no Reels DEEP EP2 (v3)
- **Textos sobrepostos/destaques:** sombra preta leve (`\bord3\blur8`, ~50% de opacidade). **Brilho só nas palavras amarelas**; branco sem brilho.
- Destaques menores e dentro da **área segura do Instagram**: centro x = 540 (ela achou 510 torto), largura útil ≤ 800 px (reduz a escala se passar).
- Legenda base: Rubik SemiBold **46** (palavra-chave 52).
- **B-roll de banco (Mixkit):** tela cheia 9:16, ~1–2,4 s, **sem áudio**, zoom lento, com **clique de câmera** leve na entrada; sequência rápida quando ela enumera.
- **Trilha** por todo o vídeo, bem baixa (~−33 LUFS sob a voz em −14), entra depois da abertura. **Tranquila: nem triste nem alegre** (aprovada: Mixkit 655 "Chillax", tom maior, lenta). Piano melancólico (714, 593) ela achou triste demais. Conferir o nome da faixa pelo card do site (ids e títulos se desencontram na listagem).
- **Sem fade out no final:** deixar o "Tchau" completo (+~1 s de take).
- Pode encurtar tirando frases que não mudam o sentido (8 min ficou longo; v3 ficou com ~7:34; a final dela ficou 7:23).

## Versão da editora → legendar e tirar a música (DEEP EP3, 9:16 4K)
Scripts em `projetos/deep-ep3/` (rodar em `/home/user/work/deep3`):
- `mapear_insercoes.py` (OCR RapidOCR a 5 fps → intervalos + caixa de cada texto dela) e `mapear_video_inserts.py` (B-roll = trechos sem o rosto dela, modelo selfie_multiclass). Blips de OCR < 0,5 s são falso positivo.
- `projetos/ferramentas/separar_voz.py` (Demucs htdemucs_ft) → voz + "música". O stem "música" leva junto os **efeitos sonoros** dela: `audio_sem_musica.py` devolve só os efeitos (transientes fortes ou na entrada das inserções/itens de lista) e mantém o som original da vinheta DEEP. Mix −14 LUFS.
- `legendas_ep3.py`: legenda tudo depois da vinheta (Rubik SemiBold 46 + chave Rubik Black 52 amarela, sombra leve). Durante uma inserção a legenda **muda de altura** (abaixo ou acima do texto, folga de 50 px, 1 s antes do OCR por causa do fade de entrada), entre o queixo (y ≥ 860) e a área segura (y ≤ 1440). Ecos translúcidos o OCR não vê → lista `ECOS` manual. Conferir com folha de quadros a cada 1,5 s.
- Texto da legenda: transcrição em janela longa (fiel) + "pra"/"tá" da transcrição em pedaços; conferir palavras que a janela longa engole (ex.: "recebendo").
