---
name: checar-falas
description: Checagem obrigatória de erros de fala (gaguejos, repetições, falsos começos, palavras truncadas, sobras de outra frase) em qualquer vídeo editado com a voz da Samara — Reels, YouTube, cortes. Usar ANTES de entregar qualquer montagem falada e em todo corte de retake.
---

# Erros de fala — conferir SEMPRE antes de entregar (lição do Reels DEEP EP2)

O Whisper "limpa" gaguejos e repetições na transcrição, então eles passaram e a editora teve que cortar à mão.
O que ela tirou da minha v3:
"E aí, e foi aí" (falso começo) · "acompanha, pras pessoas, e o motivo" (resto de outra frase) · "e co… e fazer parte de uma carreira" · "existem mais, existem mais" · "nos, nos formatos" · "mais facil… mais facilidade" · "conseguir decidir, conseguir decidir".

## Como checar
- Rodar `projetos/deep-ep2/edicao/checar_falas.py voz_16k.wav saida.json` (pedaços curtos cortados nas pausas + confirmação em janela centrada; validado: pega os erros do Reels sem alarme falso). **Transcrever em janela longa NÃO serve.**
- (Alternativa antiga) Retranscrever a **voz final montada** com `initial_prompt` cheio de hesitações ("Hum, é, tipo, assim, né, eh. Então, eu, eu... ela, ela tá.") e `condition_on_previous_text=False`, e procurar: palavra/dupla repetida em < 3 s, palavra truncada ("…"), sílaba solta antes de palavra igual.
- Em todo corte de retake, ouvir/conferir 1 s antes e depois do ponto (sobra de outra frase).
- Ficar com a **última repetição** (a mais fluida) e cortar no vale de energia.
- Mostrar à editora a lista de achados com tempos antes de renderizar.

## Lição da versão final dela (EP2 Reels, 7:23)
Ela cortou erros de fala (0,5–1,5 s em ~7 pontos) antes de "E foi aí", "Então um pode", "e o motivo", "E assim, hoje", "e eu realmente", "mais facilidade", "E aí, como". Não era só pausa. → Pausas entre frases mais curtas e tirar apostos que repetem a ideia.

## Troca de música numa versão da editora
Alinhar o áudio dela com o meu (correlação), recortar minha voz+SFX sem música no mapa dela e trocar só o áudio (`-c:v copy`) → script `projetos/deep-ep2/reels/musica_versao_editora.py`.
