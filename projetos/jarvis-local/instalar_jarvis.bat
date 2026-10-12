@echo off
rem ============================================================
rem  Instalador do Jarvis local (OpenJarvis) - Windows 10/11
rem  Rode no PROMPT DE COMANDO (cmd), nao no PowerShell.
rem  Baseado no guia @marcondes.ai. Precisa de ~15 GB livres.
rem  Pode rodar de novo: pula o que ja estiver instalado.
rem ============================================================
setlocal
chcp 65001 >nul

echo.
echo [1/8] Conferindo o winget...
where winget >nul 2>nul || (
  echo O winget nao foi encontrado. Instale o "App Installer" pela Microsoft Store e rode de novo.
  exit /b 1
)

echo.
echo [2/8] Instalando uv, Git, Node LTS e Ollama (se faltarem)...
where uv   >nul 2>nul || winget install -e --id astral-sh.uv --accept-source-agreements --accept-package-agreements
where git  >nul 2>nul || winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements
where node >nul 2>nul || winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
where ollama >nul 2>nul || winget install -e --id Ollama.Ollama --accept-source-agreements --accept-package-agreements

rem Depois de instalar, o PATH so atualiza em um terminal novo.
where uv >nul 2>nul && where git >nul 2>nul && where node >nul 2>nul || (
  echo.
  echo Ferramentas recem-instaladas. FECHE esta janela, abra um Prompt de Comando NOVO
  echo e rode este arquivo outra vez para continuar.
  exit /b 0
)

echo.
echo [3/8] Clonando o OpenJarvis na pasta "jarvis"...
if not exist jarvis git clone https://github.com/open-jarvis/OpenJarvis jarvis || exit /b 1
cd jarvis

echo.
echo [4/8] Instalando pacote, ouvidos (faster-whisper) e voz (Kokoro)...
uv sync --extra desktop --extra voice || exit /b 1

echo.
echo [5/8] Baixando o modelo gemma4:e4b (9,6 GB). Se a maquina for fraca, troque por gemma4:e2b.
ollama pull gemma4:e4b || (
  echo Ollama nao respondeu. Abra o app Ollama (bandeja, ao lado do relogio) ou rode "ollama serve" e tente de novo.
  exit /b 1
)

echo.
echo [6/8] Configurando o Jarvis (Ollama, perfil pessoal, voz pf_dora em portugues)...
uv run jarvis _bootstrap --write-config --engine ollama --model gemma4:e4b || exit /b 1
uv run jarvis config set security.profile personal
uv run jarvis config set speech.voice_id pf_dora
uv run jarvis config set speech.language pt

echo.
echo [7/8] Interface web (opcional)...
pushd frontend
call npm install && call npm run build
popd

echo.
echo [8/8] Validando...
uv run jarvis doctor
uv run jarvis ask "Em uma frase, quem e voce?"

echo.
echo Pronto. Copie jarvis_show.py e jarvis-show.cmd para a pasta jarvis para ter a ativacao por palma.
echo Uso diario:  uv run jarvis chat --voice   ^|   uv run jarvis start   ^|   jarvis-show
endlocal
