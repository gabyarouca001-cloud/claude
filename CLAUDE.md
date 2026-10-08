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
- **Cor:** não alterar a cor do bruto (iPhone HDR → manter HLG 10 bits/60 fps no arquivo para ela editar). Só mexer em cor se ela pedir.
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

## Legendas de Reels "Posso pesar o clima" (padrão da editora, aprovado)
Script: `projetos/closet-obvio/legendas/legendas.py` + `sfx.py`. Não legendar o "Posso pesar o clima?" do início (ela já faz).
- **Base:** Rubik SemiBold branca, 2–3 palavras, ~64% da altura (CapCut: tamanho 8, Y −493), sombra preta esfumada. Todas as palavras faladas que não estão num destaque.
- **Destaques** (variar a fonte): Rubik Black amarelo manteiga palavra a palavra; Playfair Display itálico branco + ouro `#F1CE0B` palavra a palavra; Amatic SC branca letra a letra. **Linhas quase encostando**, sem invadir. Nunca sobre o rosto.
- **SFX discretos por estilo:** pop por palavra (Rubik), sininho por palavra (Playfair), cliques de digitação por letra (Amatic) + som de saída (whoosh reverso / brilho descendo / swipe de papel) com fade curto.

## Cortes de Reels no closet ("Posso pesar o clima", "Seja chata") — referência: versão da editora do Seja chata
Material: iPhone vertical HDR, ela se trocando enquanto fala, a editora (Gabi) lê o roteiro em voz alta → nunca deixar a voz dela.
- **Uma fala = um take contínuo** sempre que existir (ex.: "urgente… afinal, nem tudo é" do mesmo take), em vez de emendar frases de takes diferentes.
- Escolher o take com melhor entrega e com ela **dentro do quadro e de frente**; descartar takes em que ela sai do quadro.
- **Entrada:** começar ~0,3–0,4 s antes da primeira sílaba (sem longos silêncios antes); **saída:** ~0,15–0,2 s depois da última. Pode cortar a pausa entre o título ("Seja chata.") e a frase seguinte.
- Tirar muletas no começo de frase quando não fazem falta (ex.: "Bom," antes de "se isso é ser chata").
- **Final:** depois do "Tchau", manter o take correndo até ela **sair do quadro** (aceno + saída), sem cortar.
- Cor original (HLG 10 bits, 60 fps); prévia para o chat sempre em H.264 (HEVC/HDR não abre no chat).

## Reels DEEP (ajustes da editora no EP2 v3)
- **Textos sobrepostos/destaques:** sombra preta leve atrás das letras (só o suficiente para dar leitura: `\bord3\blur8`, ~50% de opacidade). **Brilho só nas palavras amarelas**; branco sem brilho.
- Destaques menores e dentro da **área segura do Instagram**: centro x = 540 (centralizado; ela achou 510 torto), largura útil ≤ 800 px (reduz a escala se passar).
- Legenda base: Rubik SemiBold **46** (palavra-chave 52).
- **B-roll de banco (Mixkit):** tela cheia 9:16, ~1–2,4 s, **sem áudio**, zoom lento, com **clique de câmera** leve na entrada; sequência rápida quando ela enumera ("num podcast, num texto, numa comunidade").
- **Trilha** por todo o vídeo, bem baixa (~−33 LUFS sob a voz em −14), entra depois da abertura. **Tranquila: nem triste nem alegre** (aprovada: Mixkit 655 "Chillax", tom maior, lenta). Piano melancólico (714, 593) ela achou triste demais. Conferir o nome da faixa pelo card do site (ids e títulos se desencontram na listagem).
- **Sem fade out no final:** deixar o "Tchau" completo (+~1 s de take).
- Pode encurtar tirando frases que não mudam o sentido (8 min ficou longo; v3 ficou com ~7:34).
- **Versão final da editora (7:23, sobre a minha v3 4K):** tirou "e fazer parte de uma carreira" (redundante) e cortou **erros de fala** que passaram (0,5–1,5 s em ~7 pontos — ver seção abaixo; não era só pausa: antes de "E foi aí", "Então um pode", "e o motivo", "E assim, hoje", "e eu realmente", "mais facilidade", "E aí, como"). → Nas próximas, pausas entre frases mais curtas e tirar apostos que repetem a ideia.

## Erros de fala — conferir SEMPRE antes de entregar (lição do Reels DEEP EP2)
O Whisper "limpa" gaguejos e repetições na transcrição, então eles passaram e a editora teve que cortar à mão. O que ela tirou da minha v3:
"E aí, e foi aí" (falso começo) · "acompanha, pras pessoas, e o motivo" (resto de outra frase) · "e co… e fazer parte de uma carreira" · "existem mais, existem mais" · "nos, nos formatos" · "mais facil… mais facilidade" · "conseguir decidir, conseguir decidir".
- Checagem: `projetos/deep-ep2/edicao/checar_falas.py voz_16k.wav saida.json` (pedaços curtos cortados nas pausas + confirmação em janela centrada; validado: pega os erros do Reels sem alarme falso). Transcrever em janela longa NÃO serve.
- (antigo) Retranscrever a **voz final montada** com `initial_prompt` cheio de hesitações ("Hum, é, tipo, assim, né, eh. Então, eu, eu... ela, ela tá.") e `condition_on_previous_text=False`, e procurar: palavra/dupla repetida em < 3 s, palavra truncada ("…"), sílaba solta antes de palavra igual.
- Em todo corte de retake, ouvir/conferir 1 s antes e depois do ponto (sobra de outra frase).
- Ficar com a **última repetição** (a mais fluida) e cortar no vale de energia.
- Troca de música numa versão da editora: alinhar o áudio dela com o meu (correlação), recortar minha voz+SFX sem música no mapa dela e trocar só o áudio (`-c:v copy`) → script `projetos/deep-ep2/reels/musica_versao_editora.py`.

## YouTube DEEP EP2 (versão youtube2)
- Abertura 16:9 da editora (`inicio_editora.mp4`, 9,68 s, já com a vinheta) + montagem completa (com os trechos exclusivos do YouTube), sem os encurtamentos do Reels, com os cortes de erro de fala dela + os achados pela checagem.
- Inserções no padrão do EP1 **com sombra preta leve atrás das letras** (`\bord3\blur8`, ~50%) — sem ela o texto branco some na parede clara.
- Sem fade no final ("Tchau" completo). Script: `final_youtube2.py previa | 4k`.
- **Câmera (2ª rodada, feedback da editora — a 1ª com 27 zooms "incomodou", reposicionava várias vezes na mesma frase):**
  - **Enquadramento padrão fixo por take:** cortar a margem de parede da direita usando a **cabeceira da cama** como referência (janela com a largura da cabeceira, centrada nela; bordas medidas em `dinamica.py` CABECEIRA). Sem trocar enquadramento a cada corte (nem o punch-in alternado de retake).
  - **Só zooms estratégicos** (~10, frases de impacto), +0,20, com whoosh na entrada e na saída. Nada de push lento nem escada.
  - **"Câmera B" nos gráficos/listas à esquerda:** corte seco para plano mais fechado (1,38×) com a Samara do **lado direito** (rosto a 64% da largura), lado esquerdo livre para as informações; volta no fim. Gráficos colados viram um trecho só.
  - Trilha igual ao Reels ("Chillax", −33 LUFS) também no YouTube.
- **Motion graphics explicativos** (ASS vetorial, à esquerda, sem cobrir o rosto): cadeia de formatos com ícones, contador animado de números, caixa "dentro do aplicativo" só com contorno (vira amarela na virada), tijolos amarelos empilhando (texto escuro, sem sombra) com som de encaixe.

## GO! Newsflash (cliente na Áustria — propagandas/notícias de carros em alemão)
Guia completo em `projetos/austria-go-newsflash/GUIA.md` (aprendido do "Bentley 01" da editora; tabela plano a plano em
`analise_bentley01_planos.md`). Resumo: locução alemã manda, pausas enxugadas para 0,05–0,4 s; imagem do assunto entra
0,2–0,6 s antes da palavra-chave; planos de ~1 s (longos nos números, rajadas de 0,25 s nas enumerações); cortes secos,
sem cor/textos; exterior numa cor só; nada de entrevistas/cartelas/logos/pretos; abertura ~3,8 s só música, música
−22 dB sob a voz (−6 sem voz); mix ~−17 LUFS; entregar stems separados. Senha da biblioteca de música fica só no
documento do cliente — nunca no repositório.

## Painel de Demandas (registro automático do que fizemos juntos)
Painel da editora (artifact, o chefe acompanha): https://claude.ai/artifact/KJZQZ6azAkaisSrtWfyT3Y
**Sempre que concluir uma entrega com ela** (corte, prévia, 4K, thumb, textos do YouTube, legendas, agenda de posts etc.), registrar no painel com a ferramenta `ArtifactData` (`url` acima), sem precisar ela pedir. Só registrar o que foi de fato concluído; nunca inventar.
- Demanda concluída: `set` em `tasks/<id>` com `{title, scope:"dia", period:"AAAA-MM-DD", cat:"Edição|Postagem|Roteiro|Reunião|Outro", done:true, doneAt:<ISO UTC>, createdAt:<ms>}`. Título curto, em português, dizendo o que foi entregue (ex.: "Prévia 720p do EP3 aprovada").
- Demanda da semana: `scope:"semana"`, `period` = segunda-feira (AAAA-MM-DD). Meta do mês: `scope:"mes"`, `period` = "AAAA-MM".
- Anotação do dia: `set` em `notes/AAAA-MM-DD` com `{text}` (se já existir, ler antes e juntar com o texto dela).
- Post na agenda: `set` em `posts/<id>` com `{title, date, time:"HH:MM", net:"Instagram|TikTok|YouTube|Outra", fmt:"Reels|Carrossel|Story|Foto|Vídeo longo|Shorts", status:"ideia|pronto|postado", caption, createdAt}`. Textos e legendas que eu gerar para o post entram em `caption` com status "pronto".
- Se a demanda já existir no painel (ela criou), usar `update` com `done:true` e `doneAt` em vez de criar outra.
