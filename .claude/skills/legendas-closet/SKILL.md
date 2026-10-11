---
name: legendas-closet
description: Reels do closet da editora ("Posso pesar o clima", "Seja chata") — legendas animadas (Rubik, Playfair, Amatic) com SFX por estilo e regras de corte (um take contínuo por fala, entrada/saída, final com ela saindo do quadro, nunca deixar a voz da Gabi). Usar quando a editora mandar takes do closet para cortar ou pedir legendas desses Reels.
---

# Reels do closet

## Legendas "Posso pesar o clima" (padrão aprovado)
Script: `projetos/closet-obvio/legendas/legendas.py` + `sfx.py`. Não legendar o "Posso pesar o clima?" do início (ela já faz).
- **Base:** Rubik SemiBold branca, 2–3 palavras, ~64% da altura (CapCut: tamanho 8, Y −493), sombra preta esfumada. Todas as palavras faladas que não estão num destaque.
- **Destaques** (variar a fonte): Rubik Black amarelo manteiga palavra a palavra; Playfair Display itálico branco + ouro `#F1CE0B` palavra a palavra; Amatic SC branca letra a letra. **Linhas quase encostando**, sem invadir. Nunca sobre o rosto.
- **SFX discretos por estilo:** pop por palavra (Rubik), sininho por palavra (Playfair), cliques de digitação por letra (Amatic) + som de saída (whoosh reverso / brilho descendo / swipe de papel) com fade curto.

## Cortes de Reels no closet ("Posso pesar o clima", "Seja chata") — referência: versão da editora do Seja chata
Material: iPhone vertical HDR, ela se trocando enquanto fala, a editora (Gabi) lê o roteiro em voz alta → **nunca deixar a voz dela**.
- **Uma fala = um take contínuo** sempre que existir (ex.: "urgente… afinal, nem tudo é" do mesmo take), em vez de emendar frases de takes diferentes.
- Escolher o take com melhor entrega e com ela **dentro do quadro e de frente**; descartar takes em que ela sai do quadro.
- **Entrada:** começar ~0,3–0,4 s antes da primeira sílaba (sem longos silêncios antes); **saída:** ~0,15–0,2 s depois da última. Pode cortar a pausa entre o título ("Seja chata.") e a frase seguinte.
- Tirar muletas no começo de frase quando não fazem falta (ex.: "Bom," antes de "se isso é ser chata").
- **Final:** depois do "Tchau", manter o take correndo até ela **sair do quadro** (aceno + saída), sem cortar.
- Cor original (HLG 10 bits, 60 fps); prévia para o chat sempre em H.264 (HEVC/HDR não abre no chat).
- Rodar `checar-falas` antes de entregar.
