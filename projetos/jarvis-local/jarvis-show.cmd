@echo off
rem Roda o modo show de dentro da pasta jarvis (palma 2x -> jingle + web + voz).
rem Ajustes:  set JARVIS_CLAP_THRESH=0.35   e   set JARVIS_MIC=1
cd /d "%~dp0"
uv run --with sounddevice --with numpy python jarvis_show.py %*
