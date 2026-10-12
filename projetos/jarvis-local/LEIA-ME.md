# Jarvis local no Windows (guia @marcondes.ai)

Roda 100% no seu PC: Ollama (gemma4:e4b) pensa, faster-whisper ouve, Kokoro (voz `pf_dora`) fala em português.
Precisa de ~15 GB livres. Use o **Prompt de Comando (cmd)**, não o PowerShell.

## Jeito mais fácil
1. Baixe esta pasta no seu PC.
2. Abra o cmd na pasta e rode `instalar_jarvis.bat` (se pedir, feche e abra um cmd novo e rode de novo).
3. Copie `jarvis_show.py` e `jarvis-show.cmd` para dentro da pasta `jarvis` que o instalador criou.
4. (Opcional) coloque um áudio de abertura em `jarvis\voz\assets\jingle.mp3`.

## Uso diário (dentro da pasta jarvis)
- `uv run jarvis chat --voice` — conversa por voz
- `uv run jarvis start` — interface web em http://127.0.0.1:8000 (parar: `uv run jarvis stop`)
- `jarvis-show` — bata palma 2x: toca o jingle, abre a web e inicia a conversa por voz

## Ajustes do jarvis-show
- `set JARVIS_CLAP_THRESH=0.35` — mais alto = menos sensível (padrão 0.25). Abre sozinho → suba; não pega → desça.
- `set JARVIS_MIC=1` — escolhe o microfone (índice ou parte do nome). Liste com `jarvis-show --mics`.

## Se travar
Rode `uv run jarvis doctor`. Ollama mudo: abra o app na bandeja ou `ollama serve`. Sem som no microfone: Configurações > Privacidade > Microfone.
Máquina fraca: troque o modelo por `gemma4:e2b` (7,2 GB).
Nunca digite chaves de API no navegador: elas vão no arquivo `.env`.
