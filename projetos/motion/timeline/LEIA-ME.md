# Painel "Timeline DEEP" (artifact)
Página publicada em https://claude.ai/artifact/RySvWELiDZYR1bYpD9Nbbu (privada). Código em `index.html`; para atualizar, publicar este arquivo na mesma URL.
Capabilities: `db`, `assets`, `user`. Motions são desenhados ao vivo (DOM + GSAP 3.12.5), então cor/posição/tamanho mudam na hora; o render final continua sendo do pipeline (HyperFrames/FFmpeg).

## Dados (ler com ArtifactData)
- `clips/<id>`: um bloco. Campos comuns: `track` (video|motion|dest|base), `kind`, `start`, `dur` (s, linha do tempo de SAÍDA).
  - video: `asset` (id do arquivo), `in` (s na fonte), `srcDur`, `ord`. Faixa magnética: ao soltar, os cortes se encaixam sem buracos.
  - motion/dest/base: `x`,`y` (px em 1920x1080), `scale`, `cor` (hex) + textos do `kind` (lettering: l1,l2,echo · pessoas: num,rotA,rotB,capK,capT · grafico: titulo,fim,rot · dest/base: text com *chave*, estilo rubik|playfair).
- `projeto/meta.nota`: recado do Claude mostrado no topo. `projeto/log.itens`: últimas 40 alterações da editora (t, txt).
- `pedidos/<id>`: botão "Pedir render" (`status`: pedido → marcar `feito` ao terminar, `nota`, `resumo`).
- Ao alterar um bloco por aqui, a tela da editora atualiza sozinha (onSnapshot). Escrever sempre com `if_version` da última leitura.

## Limites conhecidos
Prévia 360p; teto de 20 MiB por arquivo enviado (vídeo longo entra em partes); H.264 só confirmado por leitura (o Chromium de teste não decodifica), seek depende de o servidor de `/_blob` aceitar Range (não verificado).
Teste local: stub de `window.claude.db` + Playwright em `/tmp` (não versionado).
