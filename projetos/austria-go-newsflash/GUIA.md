# GO! Newsflash — guia de edição (aprendido do "Bentley 01" da editora)

Cliente na Áustria (pubbles). Formato: notícia curta de carro, **locução em alemão (VOX) + música + às vezes
efeitos/atmo**, só imagens do material de imprensa da marca. Referência analisada: `GO NEWSFLASH BENTLEY 01`
(1:29, 81 planos). Tabela completa plano a plano: `analise_bentley01_planos.md`.

## O que chega
- `Films/` — vídeos de imprensa da marca (B-roll), de cores/versões e formatos diferentes (4K, 1080p, 3126×2160,
  1562×1080…), às vezes com entrevistas, cartelas de título e logos.
- `Voice & Text/` — locução de estúdio em alemão (`.aif`, 48 kHz) + o texto (`.docx`).
- `Doc/Music & Settings.docx` — especificações do cliente (abaixo). A música vem da biblioteca Universal Production
  Music (o login está no documento do cliente; **não copiar a senha para o repositório**).
- `Examples/` — outros episódios do GO! Newsflash (Audi, Hyundai, Nissan) como referência de formato.

## Especificações do cliente (Music & Settings)
- Export: **1920×1080, QuickTime MOV, Rec709, 25 fps** (o documento diz "1080i"; o Bentley 01 final foi entregue em
  3840×2160 25p — confirmar com a editora qual entregar). Áudio sem compressão, 48 kHz, estéreo, 16 bit.
- Mix: −6 dB. Stems: **VOX −6 dB**, **MUSIK −6 dB sem fala / −22 dB com fala**, ATMO −24 dB.
- Entregar também as **trilhas separadas** (no Newsflash: VOX e MUSIK, às vezes ATMO; a editora entregou
  VOICE / MUSIC / SOUND EFFECTS em MP3).

## Estrutura (Bentley 01)
| trecho | o que acontece |
|---|---|
| 0:00–3:8 | **Abertura só com música** (−16 dB RMS), 2 planos-herói do carro: frente de perto, lateral/traseira em detalhe |
| 3:8 | entra a locução; a música **abaixa ~20 dB em ~0,5 s** (fica −34 a −37 dB RMS sob a voz) |
| 3:8–88:9 | locução contínua, imagem sempre "ilustrando" a frase |
| 88:9–89:4 | termina meio segundo depois da última palavra, num plano aberto (aéreo/paisagem); música some junto |

## Regras de montagem (o "jeito dela")
1. **A locução manda.** A voz do estúdio foi **enxugada**: pausas entre frases de 0,15–1,4 s viraram **0,05–0,4 s**
   (95 s → 85 s de fala). Sem cortar dentro das palavras, sem acelerar a voz.
2. **Cada frase ganha a imagem do que está sendo dito**, e a imagem entra **0,2–0,6 s ANTES da palavra-chave**
   (grade: imagem 0,66 s antes de "Kühlergrill"; "Radstand" 0,62 s; "Leder" 0,46 s; "Reichweite" 0,40 s).
3. **Ritmo:** plano médio de **1,1 s** (mediana 0,9 s, de 0,24 a 3,9 s). ~1 corte por segundo de fala.
   Os cortes **não seguem o beat** da música (só 11% caem no tempo); seguem a fala e caem soltos, inclusive no
   meio de palavras — o que importa é a imagem chegar junto do assunto.
   - **Planos mais longos (2–4 s)** nas frases de "respiro"/números grandes: aceleração 0–100 (3,9 s, carro vindo
     na estrada), bateria, final.
   - **Rajada rápida (0,2–0,4 s)** quando o texto enumera ou fecha uma ideia: "Leder, Merinowolle, Aluminium, Holz…
     spielen die Hauptrollen" = 4 planos de 0,25 s de textura/emblema; "Diamantendesign" = 2 planos de 0,3 s.
4. **Mapa assunto → imagem** (o que ela escolheu):
   - "marca X fica elétrica / novo modelo" → planos-herói externos: frente, traseira na montanha, aéreos, carro na estrada
   - medidas/proporções ("5 m", "o mais curto") → vista **de cima** (top-down), lateral, teto
   - "grade iluminada / design de diamante" → grade acesa ao entardecer + **macro abstrato do padrão**
   - "entre-eixos longo" → **perfil lateral** completo
   - "laterais traseiras musculosas" → traseira 3/4, lanterna, carro passando
   - "aparência confiante" → **emblema/lettering** da marca
   - "interior / tela OLED / reconhecimento facial" → painel aberto, tela, mão na tela, volante
   - "artesanato clássico" → mão no comando, emblema bordado
   - lista de materiais → um plano de cada material, na ordem da fala, depois rajada de texturas
   - "botões de verdade" → console com botões + **mão apertando**
   - potência/torque → carro em movimento, aéreos de estrada
   - "0 a 100 em X s" → **plano longo** do carro vindo em direção à câmera na estrada
   - bateria/autonomia → carro rodando/indo embora pela estrada, carroceria
   - carregamento → **tampa do carregador, mão plugando** (ela usou um trecho **de trás pra frente** para o plug "entrar")
   - fechamento ("assim a marca imagina o futuro…") → roda, contraluz do sol, aéreo de curva, **mãos no volante (POV)**,
     plano-herói de frente, **aéreo de paisagem** no último plano
5. **Uma cor de carro só no exterior.** O bruto tinha o modelo em verde (Electrum Satin) e em prata (Astral):
   exterior **só o verde**; do prata ela usou **interior, macros, emblemas e planos distantes** em que a cor não aparece.
6. **O que ela NÃO usa:** entrevistas/cabeças falantes e qualquer plano com nome/cargo na tela; designer desenhando;
   cartelas de título, datas, logos em fundo preto, telas pretas; paisagem sem carro (rochas); bastidores de fábrica,
   carros antigos. Do vídeo "Torcal materials" (fábrica/tecidos) usou só 1,5 s de textura.
7. **Velocidade:** quase tudo em 1×. Acelera (2,4×–3,7×) planos lentos de detalhe para caber numa rajada;
   reverso pontual quando o movimento "ao contrário" conta melhor a frase.
8. **Sem tratamento de cor** (cor idêntica ao bruto), **só cortes secos** (sem dissolve/flash), **sem textos/letterings**
   próprios (os avisos legais que já vêm queimados no filme da marca ficaram).
9. **Áudio:** voz −18 LUFS (pico −5), música −27 LUFS no total (−16 dB RMS sem fala → −34/−37 com fala),
   mix final **−17,4 LUFS, pico −1,3 dBTP**. Efeitos sonoros raros: só ~3 momentos, em planos de carro passando
   (som de passagem/motor em 0:10, 0:24 e 0:54).

## Processo para um novo episódio (o que eu faço quando chegar o bruto)
1. Baixar tudo; ler o texto e o "Music & Settings"; conferir formatos/fps dos filmes.
2. Transcrever a locução (Whisper `medium`, `language="de"`, tempo por palavra) e **tirar as pausas** entre frases
   (deixar 0,05–0,4 s; manter respiração natural; nunca cortar palavra).
3. Catalogar o bruto: detectar planos de cada filme (mudança de cena), uma miniatura por plano, e marcar:
   cor/versão do carro, tipo (externo herói, detalhe, interior, macro, estrada, aéreo, carregamento…), movimento,
   e **descartar** entrevistas, letterings, cartelas, logos, pretos, pessoas sem relação.
4. Para cada frase da locução, escolher planos do assunto (mapa acima), entrando 0,2–0,6 s antes da palavra-chave;
   ~1 s por plano, longos nos números grandes, rajadas nas enumerações; não repetir plano; variar
   aberto/detalhe/interior; exterior numa cor só.
5. Abertura de ~3–4 s só com música e 2 planos-herói; final com aéreo/paisagem, terminando ~0,5 s após a última palavra.
6. Música: −6 dB sem fala, **−22 dB com fala** (abaixar em ~0,5 s quando a voz entra); efeitos só em carro passando.
7. Prévia leve para a editora aprovar → export no formato do cliente + stems separados (VOX / MUSIK / SFX ou ATMO).
