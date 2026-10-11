---
name: deep-hyperframes
description: Como usar o HyperFrames (HTML + GSAP → MP4) para criar inserções animadas no padrão visual DEEP — textos de 2 linhas, capítulos, listas, contadores e gráficos mais ricos que o ASS. Usar quando a editora pedir uma animação/motion graphic/inserção "mais cinematográfica", ou quando um texto/gráfico precisar de movimento além do que o libass faz.
---

# HyperFrames no padrão DEEP

Complementa `deep-episodio` (padrão visual) e as skills `hyperframes*`, `motion-graphics` e `talking-head-recut`
(instaladas em `.claude/skills/`). **Ler `hyperframes` primeiro** (roteador); depois `hyperframes-core` antes de escrever HTML.
O padrão visual da editora (amarelo manteiga `#FCEDC0`, Playfair itálico + Inter Black, sem caixas, sombra leve, nada sobre o rosto) **prevalece**.

## Preparar o ambiente (sessão nova)
O container é descartável. Verificado em 2026-10: Node 22, FFmpeg/FFprobe do sistema e npx funcionam.
```bash
cd /home/user/work/hf                      # fora do repositório
npx --yes hyperframes browser ensure       # baixa o Chrome Headless Shell (~114 MB), 1x por sessão
npx --yes hyperframes doctor               # Whisper/TTS/MusicGen/Docker ausentes são opcionais
```

## Fluxo
1. Copiar o modelo: `cp -r projetos/ferramentas/hyperframes/modelo_texto_deep /home/user/work/hf/<nome>` (1920×1080, 4 s: eco "30%" + linha Playfair + ênfase Inter Black amarela).
2. Editar `index.html` (textos, tempos, `data-duration`; **uma timeline GSAP pausada** em `window.__timelines["main"]`).
3. `npx hyperframes check` — corrige os erros antes de renderizar. O aviso de contraste no eco translúcido é esperado.
4. `npx hyperframes render --quality draft --output draft.mp4` para iterar (4 s renderizaram em ~7 s a 1080p), depois `--quality looks`/`delivery`.
5. Conferir um quadro (`ffmpeg -ss 2 -i draft.mp4 -frames:v 1 q.png`) e mostrar à editora **prévia leve (< 30 MB)** antes do 4K.
6. Para entrar no vídeo: sobrepor o resultado com FFmpeg no `final.py` (o render 4K do episódio continua pelo pipeline normal).

## Armadilhas já encontradas
- **Não animar `letterSpacing`** (nem width/height/margin): treme no render quadro a quadro. Animar só `x/y/scale/opacity`.
- Fontes: link do Google Fonts no `<head>` funciona (Playfair Display itálico + Inter 900 carregaram).
- Texto nunca sobre o rosto: usar o lado esquerdo (informações) como nas inserções do EP2.
- Nunca renderizar o final só porque o `check` passou — esperar a aprovação da editora.
- Se o shell matar processos ao fim do comando, usar `HYPERFRAMES_RENDER_DETACHED=1` (ver `hyperframes-cli`).
- Não testado ainda: render 4K (3840×2160) e fundo transparente para overlay; testar antes de prometer prazo.

## Quando usar qual
- Inserção simples de texto → o ASS atual basta.
- Texto cinético, contador, gráfico animado, mapa, lower-third elaborado → HyperFrames (`motion-graphics`).
- Pacote de overlays sincronizado com a transcrição sobre o vídeo dela → `talking-head-recut`.
