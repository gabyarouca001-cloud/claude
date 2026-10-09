# Sapato da Chanel pela metade: edição no formato curadoria

Vídeo da editora já cortado (vertical 4K, 4:46). Edição aplicada: inserções (fotos, vídeos, cartões de texto, balões), legendas
dinâmicas no padrão aprovado e efeitos sonoros no estilo da referência (`projetos/referencias/curated-list/GUIA.md`).

Pipeline (rodar em `/home/user/work/cur`, com `original.mp4`, `transcricao.json`, `assets/` e `fonts/`):
1. `transcrever.py` (faster-whisper medium, pt, word_timestamps) → `transcricao.json`
2. `edl.py`: lista de edição, cada inserção ancorada numa palavra (entra 0,15 a 0,35 s antes). `python3 edl.py` mostra tempos e conflitos.
3. `S=1 python3 assets.py`: mídias na resolução do render (S=2 para 4K).
4. `S=1 python3 legendas.py`: `legendas.ass`, `cartoes.ass`, `sfx.json`.
5. `python3 sfx.py`: voz em −14 LUFS + efeitos → `audio_final.wav`.
6. `S=1 python3 final.py previa` (720p < 30 MB) | `S=2 python3 final.py 4k` (só depois de aprovada a prévia).

Materiais livres usados (créditos obrigatórios nas licenças CC):
- Fotos (Wikimedia Commons): Grande Plage de Biarritz 2025 (Espandero, CC BY-SA 4.0); Coco Chanel in Los Angeles, 1931 (Los Angeles Times, CC BY 4.0);
  Gabrielle Chanel en marinière (domínio público); Chanel boutique, Rue Cambon, Paris 2009 (CC BY 2.0); Karl Lagerfeld 0445 (CC BY-SA 4.0).
- Vídeos de banco (Mixkit, licença livre, sem atribuição): ids 52270, 44482, 1208, 33021, 2054, 23333, 50641.
Não há imagem nem vídeo do desfile Cruise 2026/27 da Chanel: não existe material livre. Slots prontos em `edl.py` (`f_desfile`).

## Revisão dos inserts (a editora escolhe o que fica)
`python3 revisao_gerar.py previa_curadoria_720p.mp4 saida.html` gera a página (miniaturas da prévia) publicada como Artifact "Revisão dos Inserts".
Ela marca Manter / Apagar / Alterar por inserção (coleção `revisao/<id>` no db do artifact; `_geral` = efeitos sonoros, legenda de base e recado).
Aplicar: ler as escolhas com `ArtifactData`, gravar `revisao.json` ({id: "apagar"}) na pasta de trabalho e rodar de novo `assets.py`, `legendas.py`, `sfx.py`, `final.py`.
Ids: f_* (tela cheia), p_* (foto com moldura), c_* (cartões), b_* (balões), d0..d12 (destaques de legenda). "Alterar" é tratado à mão a partir da nota.
