# Painel "Timeline DEEP" (artifact)
Dois artifacts usam este código (o EP2 é a versão atual, com mais tipos de motion):
- teste de motion: https://claude.ai/artifact/RySvWELiDZYR1bYpD9Nbbu (versão anterior do código)
- **DEEP EP2 (YouTube, 12:03)**: https://claude.ai/artifact/8FiqnoacAEApbXc2MzWmRY — dados gerados por `projetos/deep-ep2/edicao/timeline_ep2.py` (estimados: capítulos exatos, resto com margem de alguns segundos; sem vídeo anexado, cada corte mostra a fala).
Páginas privadas. Código em `index.html`; para atualizar, publicar este arquivo na mesma URL.
Capabilities: `db`, `assets`, `user`. Motions são desenhados ao vivo (DOM + GSAP 3.12.5), então cor/posição/tamanho mudam na hora; o render final continua sendo do pipeline (HyperFrames/FFmpeg).

## Dados (ler com ArtifactData)
- `clips/<id>`: um bloco. Campos comuns: `track` (video|motion|dest|base), `kind`, `start`, `dur` (s, linha do tempo de SAÍDA).
  - video: `asset` (id do arquivo), `in` (s na fonte), `srcDur`, `ord`. Faixa magnética: ao soltar, os cortes se encaixam sem buracos.
  - tipos de motion (`kind`): lettering, pessoas, grafico, capitulo (capK,capT), lista e tijolos (titulo, itens[], rotulo), citacao (l1,l2), versus (l1,esq,dir), proximo; dest/base. `nota` = aviso que aparece no inspetor.
  A animação toca em velocidade natural; se o bloco for mais longo, segura o último quadro antes da saída.
- motion/dest/base: `x`,`y` (px em 1920x1080), `scale`, `cor` (hex) + textos do `kind` (lettering: l1,l2,echo · pessoas: num,rotA,rotB,capK,capT · grafico: titulo,fim,rot · dest/base: text com *chave*, estilo rubik|playfair).
- `projeto/meta.nota`: recado do Claude mostrado no topo. `projeto/log.itens`: últimas 40 alterações da editora (t, txt).
- `pedidos/<id>`: botão "Pedir render" (`status`: pedido → marcar `feito` ao terminar, `nota`, `resumo`).
- Ao alterar um bloco por aqui, a tela da editora atualiza sozinha (onSnapshot). Escrever sempre com `if_version` da última leitura.

## Limites conhecidos
Prévia 360p; teto de 20 MiB por arquivo enviado (vídeo longo entra em partes); H.264 só confirmado por leitura (o Chromium de teste não decodifica), seek depende de o servidor de `/_blob` aceitar Range (não verificado).
Teste local: stub de `window.claude.db` + Playwright em `/tmp` (não versionado).
