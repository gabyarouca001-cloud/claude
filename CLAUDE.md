# Editor IA — padrão de trabalho (DEEP, por Samara Checon)

Repositório de apoio à edição de vídeo da editora (usa CapCut e Premiere, Windows). Falar sempre em **português do Brasil**.
Referência completa do episódio 1 em `projetos/deep-influencer/` (roteiro, scripts de edição, textos e thumb).

## Fluxo de um episódio
1. A editora manda o **roteiro** → salvar em `projetos/<episodio>/roteiro.md` e devolver a estrutura (blocos, tempo estimado, ponto de corte do IG se houver).
2. A editora manda o **link do Drive** do vídeo pré-editado (4K). Baixar com
   `curl -L -o original.mp4 "https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t"` em `/home/user/work/` (fora do repo).
   Se der 403, a rede do ambiente precisa liberar `drive.google.com` e `drive.usercontent.google.com`.
3. **Transcrever** com faster-whisper `medium`, `language="pt"`, `word_timestamps=True` (precisa de huggingface.co liberado). Leva ~6 min para 8 min de áudio.
4. Perguntar/confirmar **até onde ela já editou**: só cortar a parte bruta e só inserir elementos a partir do ponto que ela indicar. Nunca mexer no que ela já editou (inclusive cortes).
5. Mostrar a **lista de retakes/cortes** com tempos antes de renderizar.
6. Gerar **prévia em 720p < 30 MB** (2 passes, ~430 kbps) para aprovação. **Só renderizar o 4K depois da aprovação.**
7. Entregar o 4K (ver "Entrega").
8. Fazer **título, descrição com capítulos, tags, comentário fixado e thumb** (`projetos/<episodio>/publicacao/`).

Pipeline (scripts em `projetos/deep-influencer/edicao/`, adaptar os dados do episódio):
`plano.py` (retakes + silêncios) → `audio.py` (correções de áudio e voz cortada) → `video.py` (segmentos 4K) → `insercoes.py` (textos ASS, gráfico, SFX) → `final.py` (render) → `thumb.py`.
Ferramentas: FFmpeg via `pip install imageio-ffmpeg` (link para `/usr/local/bin/ffmpeg`; não tem ffprobe nem drawtext → textos via ASS/libass), Pillow, numpy.

## Edição
- **Cortes:** retakes ("desce um pouco, Gabi", "vai", "volta"), frases repetidas/incompletas e silêncios ≥ 0,30 s (limiar −36 dBFS, mantém 0,10 s antes e 0,08 s depois). Cortes sempre no grid de frames (25 fps) e em vales de energia, sem cortar palavra.
- **Punch-in de 12%** alternado a cada corte de retake (esconde o pulo); plano normal no fim.
- Remover a **linha verde** no topo do export do CapCut (crop de 8 px nas bordas).
- **Áudio:** trechos com volume/timbre diferente → igualar (compressão + EQ + ganho, crossfade de 30 ms em pausas). Mix final em **−14 LUFS**, pico ≤ −1,5 dBTP.
- **Efeitos sonoros:** limpos e discretos (whoosh nas entradas de texto, tick em itens de lista, chime suave em capítulos), bem abaixo da voz.
- Fade out de 0,6 s no final.

## Padrão visual das inserções (aprovado pela editora)
- **Cor de destaque única: amarelo manteiga `#FCEDC0`** (ASS `&H00C0EDFC&`). Nada de azul/ciano. Qualquer destaque (palavra, traço, barra, gráfico, número) usa esse amarelo.
- **Texto principal (2 linhas, centralizado):**
  - Linha de cima: *Playfair Display Italic*, branca, 92 px (base 1080p), y = 636.
  - Linha de baixo (ênfase): *Inter Black*, CAIXA ALTA, **amarelo**, até 190 px (reduz para caber em 1700 px), y = 750.
  - **Espaçamento curto** entre as duas linhas. A ênfase fica na ideia principal (ex.: "30% dos criadores" / **NÃO MONETIZAM**, não o número).
  - Eco opcional: palavra gigante branca translúcida (~25%) atrás, só nos momentos fortes.
  - Sombra suave e discreta; **sem blocos/caixas escuras** atrás do texto.
- **Capítulo:** canto inferior esquerdo, barra vertical amarela + "CAPÍTULO" pequeno em amarelo + título em Inter Medium branco.
- **Próximo episódio:** só "PRÓXIMO EPISÓDIO" no **canto superior esquerdo**, em amarelo, com a barra. Sem texto extra.
- **Lista:** à esquerda, traço amarelo + texto branco Inter ExtraBold, itens entrando conforme a fala.
- **Gráfico:** linha amarela desenhando, número grande amarelo ao lado, sem cobrir o rosto.
- Nunca colocar texto sobre o rosto.
- Fontes: baixar pela API CSS do Google Fonts (`https://fonts.googleapis.com/css2?family=...` → URL `.ttf` do fonts.gstatic.com), porque o GitHub raw fica bloqueado.

## Thumb (1280×720, JPG < 2 MB)
- **A editora escolhe o quadro** da Samara. Se ela não mandar, sugerir alguns quadros e deixar ela decidir.
- Ela à direita, com o rosto livre; gradiente escuro à esquerda para o texto.
- Texto à esquerda, no mesmo estilo do vídeo: linha em Playfair itálico branco + linha Inter Black branca + palavra-chave grande em amarelo `#FCEDC0`.
- Assinatura discreta no topo: barra amarela + "D E E P · S A M A R A   C H E C O N".
- Thumb e título se completam (a thumb provoca, o título promete a resposta).

## Textos do YouTube
Título com a palavra-chave no começo e um motivo para clicar (+ 2 alternativas para teste A/B); descrição com gancho nas 2 primeiras linhas, resumo, **capítulos com os tempos reais do vídeo final**, CTA, chamada do próximo episódio, 3 hashtags; tags; comentário fixado com pergunta. Usar só números que ela fala no vídeo e sugerir colocar a fonte.

## Cortes para redes (Reels / TikTok / Shorts)
Script base: `projetos/deep-influencer/edicao/cortes_sociais.py` (um corte por capítulo do YouTube).
- 9:16, 1080×1920, recorte central do 4K (sem as inserções do 16:9, refeitas para o vertical).
- **Área segura:** topo 250 px, base 480 px, direita 140 px livres; texto centrado em x ≈ 510, largura útil 820 px.
- **Gancho** no topo nos primeiros ~3,5 s: título em Playfair Display (caixa normal), **todo amarelo #FCEDC0, com efeito olho de peixe** (`titulo_olho_peixe.py`), na faixa acima da cabeça (y ≈ 175–515); **legendas** palavra a palavra (Inter ExtraBold 70, branco, y = 1330), escondidas enquanto há inserção; inserções entre y ≈ 1000 e 1420.
- Fim: "EPISÓDIO COMPLETO / NO YOUTUBE" no canto superior esquerdo, com barra amarela.
- Trechos com texto da editora gravado na imagem: mostrar o quadro 16:9 inteiro sobre fundo desfocado.
- Cada corte fica com menos de 30 MB (2 passes, bitrate calculado pela duração) e vai com sugestão de texto de post e hashtags.

## Entrega
- Limite de envio no chat: **30 MB por arquivo**. A conexão com o Drive não sobe vídeo grande, e o envio para sites de transferência é bloqueado pelas permissões.
- **4K:** dividir em partes de 29 MB (`split -b 29000000 -d -a 2 --numeric-suffixes=1 arquivo.mp4 NOME.mp4.part`) + `juntar.bat` (copy /b + checagem SHA256 com certutil). Enviar em lotes de 8 pelo chat. Ela junta no PC e sobe no Drive (pasta `claude`).
- Vídeos, partes e prévias ficam no `.gitignore` (nunca commitar arquivos grandes).
- Render final: H.264 4K 25 fps, CRF 19, preset faster, AAC 320k, `+faststart`.

## Preferências da editora
- Formato principal: **YouTube 16:9 em 4K**. A versão Instagram (termina no ponto de corte do roteiro) só quando ela pedir.
- Ela aprova por prévia leve antes do render final.
- Episódios novos às quintas-feiras (aprox.).

## Stories de evento / marca (referência: KIKO × Just Cavalli, versão final da editora)
Só takes + trilha, 9:16 4K 30 fps, ~37 s. O que ela manteve e o que mudou na minha v2:
- **Mantém:** abertura com os nomes em texto (KIKO / JUST CAVALLI, Jost branco, espaçado, sombra suave), cortes no ritmo da música, flashes brancos curtos, zoom rápido/espiral pontual, final dela sorrindo/acenando.
- **Prefere momentos humanos e reais:** ela cumprimentando gente, passando batom, sendo maquiada, olhando pro espelho. Trocou 3 planos repetidos dela posando no painel por: fotógrafo → foto desfocada/flash → ela abraçando amiga.
- **Produtos limpos e reconhecíveis** (totem da collab com batons, pó compacto aberto, batons em fila, base com o logo) em vez de detalhes confusos (estojos de oncinha, banner amarelo cortado). Um plano por produto, sem repetir.
- **Não repetir o mesmo enquadramento** em sequência; variar plano aberto / close / produto.
- Lavados (fade branco) só como transição curta, não abrindo seções.
- Áudio: **nunca deixar vazar voz/ambiente** por baixo da trilha (só música + SFX). Mandar a trilha separada na minutagem exata quando pedir.
