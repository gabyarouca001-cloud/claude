# Referência "Conteúdo 2.0" — análise do vídeo "Claude Editando"

Vídeo analisado: Reel vertical de ~1:51 (Drive `1UTg9c_FoTXuJQYW7ra5ryHkw2s-5ljFF`), um criador explica o formato e faz
4 demonstrações ("E se eu fosse corretor / médico / nutricionista / professor?"). Análise feita por transcrição
word-level (Whisper medium), folhas de quadros a cada 1 s, detecção de cortes, loudness e espectrograma.
O arquivo em si **não** vai para o repositório (só esta análise).

## Ficha técnica
| Item | Valor |
|---|---|
| Formato | 720×1280 (9:16), 30 fps, H.264 + AAC 44,1 kHz, 17 MB, 110,99 s |
| Loudness | −14,1 LUFS integrado, LRA 4,5 LU, pico −0,2 dBFS (mais "quente" que nosso padrão de pico ≤ −1,5 dBTP) |
| Fala | 330 palavras em 110,7 s = **179 palavras/min**; 0 silêncios ≥ 0,3 s (−36 dB); só 14 pausas > 0,25 s |
| Troca de imagem | 58 mudanças detectadas; mediana 0,67 s entre elas (inclui animações internas); cena de gráfico nova a cada 3–6 s |
| Áudio | Espectrograma: voz contínua, **sem trilha sustentada visível**; há eventos de banda larga que podem ser SFX — não deu para isolar (sem separação de stems nesta máquina). Conferir de ouvido. |

## A fórmula em uma frase
**Um talking head sem pausas + um gráfico explicativo que "se monta" na tela no instante em que cada ideia é falada.**
A palavra-chave dispara a animação (número que sobe, mapa que aparece, risco que corta), então o espectador *vê* o que ouve.

## Estrutura do roteiro (esqueleto repetível)
1. **0:00–0:24 Gancho + promessa + problema + gancho aberto.**
   "Esse é o novo formato… vai aparecer cada vez mais na sua tela" → "repara, eu falo e a explicação é montada em tempo real"
   → custo antigo ("um minuto de animação custava milhares de reais e uma semana de motion designer") → "Hoje, a IA faz" → **"Quer ver?"**
2. **4 demonstrações, todas com o mesmo molde (~13–27 s cada):** título "E se eu fosse **X**?" (palavra X colorida) →
   5 a 7 batidas, uma por frase, cada uma com um visual novo → fecha com o dado forte (preço, "3–4 meses", "limite", "olhar o céu é olhar o passado").
3. **1:34–1:51 Fecho:** "4 profissões, 4 estilos" (grade 2×2 das personas) → "só gravei a fala e a IA editou" → frase de marca ("Quem explica melhor, ganha mais atenção") → **CTA por palavra-chave** ("comenta EDIÇÃO e eu te mando a aula no Direct"), com caixa de comentário animada digitando a palavra.

## Layout (dois estados que se alternam)
- **Estado "rosto":** o vídeo dele num cartão de cantos arredondados (~660 px de largura, y 320–1235), sobre fundo escuro com cenário (skyline, etc.).
  Usado em gancho, títulos de capítulo ("E se eu fosse…") e CTA.
- **Estado "dividido":** metade de cima (~y 0–560) = gráfico animado; metade de baixo = cartão do rosto (~646×675, y 570–1245), borda fina com brilho quente.
  O gráfico ocupa o espaço, **nunca cobre o rosto**.
- Cada tema tem **paleta + tipografia + fundo próprios** (corretor: azul-noite + dourado + serifa; médico: branco/azul clínico; nutricionista: creme + verde + serifa itálica; professor: preto espacial + laranja). A cor da palavra do título acompanha o tema.
- Selo/pílula no início ("Claude Editando ☠") e rótulos de legalidade no canto: "imóvel ilustrativo", "conteúdo ilustrativo".

## Legendas
- Palavra a palavra, **1–3 palavras por vez**, branco ExtraBold com contorno/sombra preta, caixa baixa (frase normal), centralizadas.
- Posição acompanha o layout: ~60% da altura no estado "rosto"; sobre a parte baixa do cartão no estado dividido (y ≈ 1000–1050). Nunca em cima do gráfico.
- Textos tipográficos grandes à parte da legenda para frases de impacto ("Quem explica melhor, / ganha mais atenção" com a última palavra colorida).

## Tipos de gráfico usados (todos disparados por palavra falada)
| Ideia falada | Visual |
|---|---|
| "você fala → a IA desenha → todos entendem" | ícones ligados por setas, 7 pessoinhas que acendem |
| custo antigo | grade de avatares, linha "Orçamento / Animação / 1 minuto / R$ •••", depois calendário "1 semana" |
| "18 andares" | contador 07→17 + prédio 3D isométrico crescendo com janelas acesas |
| "4 min a pé do metrô" | mapa com pino e trajeto desenhando, contador 4 min |
| "72 m², 2 suítes, varanda" | planta 3D com móveis, etiquetas "SUÍTE 1 12 m²" |
| preço | etiqueta de preço + "A PARTIR DE R$ 1.000.000" |
| "Botox não preenche, relaxa" | seringa riscada, anatomia do rosto com músculo destacado e rótulo (Frontal, Corrugador "o famoso 11", Orbicular), corte da pele, curva "efeito do botox" com "3 dias" e "3–4 meses" |
| "35 g de açúcar = 7 sachês" | lata → copo com sachês → linha "ideal do dia OMS < 25 g" → lata virando e passando do limite (32 g → 35 g em vermelho) |
| "luz do sol demora 8 min" | cronômetro 06:17…, sol e Terra, "sol apagado há 07:23", comparação Lua 1,3 s / Sirius 8,6 anos |

Padrões: **contador animado**, **linha que se desenha**, **etiqueta que entra**, **comparação lado a lado**, **a cor de alerta (vermelho/laranja) só no ponto de virada**.

## Troca de persona (inferência)
A roupa e o cenário mudam no meio do gesto (ex.: blazer bege → preto em 3,0 s, mesmo movimento de mãos), o que indica
**vídeo-para-vídeo com IA** (reroupar/reambientar o mesmo take), e não segunda gravação. Não confirmado — é o ponto mais incerto da análise.

## O que NÃO é segredo (e o que é trabalho)
- Corte seco + 179 palavras/min + zero silêncio → já fazemos (pipeline de cortes).
- Legenda palavra a palavra → já fazemos (Rubik).
- **O que muda de patamar:** o gráfico explicativo *sincronizado por palavra* e o **planejamento do roteiro para ser desenhável** (uma ideia visual por frase, números e contrastes).
- Ativos fotográficos/3D (lata, copo, prédio, anatomia) parecem **imagens geradas ou modelos 3D**. Sem gerador de imagem nesta sessão, usamos SVG/CSS/three.js, ícones e imagens que a editora fornecer.

## Como replicar no nosso fluxo (identidade DEEP, sem copiar o visual dele)
1. **Roteiro desenhável:** a editora manda o roteiro; eu devolvo, por frase, a ideia visual e a palavra-gatilho (planilha `storyboard`).
2. **Corte** com o pipeline atual (retakes, silêncios, `checar-falas`).
3. **Transcrição word-level** (faster-whisper `medium`, `pt`) → tempos exatos dos gatilhos. *(A skill `talking-head-recut` usa `small.en` por padrão: trocar para modelo multilíngue e idioma `pt`.)*
4. **Cartões em HyperFrames** (HTML + GSAP, `motion-graphics` / `talking-head-recut`) na paleta DEEP: amarelo `#FCEDC0`, Playfair itálico + Inter Black, sem caixas escuras, sombra leve.
5. **Layout dividido** 9:16: rosto em cartão arredondado embaixo, gráfico em cima; legendas na área segura (topo 250, base 480, direita 140).
6. **SFX discretos** na entrada de cada cartão (pop, tick, whoosh) e trilha baixa (padrão "Chillax").
7. **QA:** folha de quadros a cada 1,5 s + conferência número-na-tela × número-falado + `checar-falas`.
8. **Prévia 720p < 30 MB** → aprovação → 4K. CTA por palavra-chave no final.

## Riscos e limites
- Render 4K e vertical 1080×1920 no HyperFrames ainda **não testados** aqui (teste 1080p 16:9: 4 s em 7 s).
- Dados/legalidade: tudo que é número vem **da fala da editora**; marcar "conteúdo ilustrativo" quando for ilustração.
- O criador do vídeo afirma que "a IA editou tudo": o fluxo exato dele não é público; esta fórmula é reconstruída do resultado.
