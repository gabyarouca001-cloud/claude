# Editor IA

Ferramentas para acelerar a edição de vídeo com a ajuda do Claude.

**Fluxo:** transcrição (`.srt` do Premiere/CapCut) → Claude escolhe os cortes e gera um `cortes.json` → `cortes_para_xml.py` monta a timeline → você importa no Premiere e finaliza.

## Instalação no Windows (uma vez só)

Abra o **PowerShell** e rode:

```powershell
winget install Python.Python.3.12
winget install Gyan.FFmpeg
```

Feche e abra o PowerShell de novo. O FFmpeg é opcional, mas com ele o script lê sozinho o fps, a resolução e o áudio dos seus vídeos.

## Uso

1. **Transcreva** no Premiere (*Texto → Transcrição → Transcrever*, depois *Exportar → .srt*) ou no CapCut (*Legendas automáticas → exportar .srt*).
2. **Mande o `.srt` para o Claude** com o objetivo (ex.: "3 cortes de 40s para Reels"). Ele devolve um `cortes.json`.
3. **Salve o `cortes.json`** na pasta dos vídeos e rode:

   ```powershell
   python ferramentas\cortes_para_xml.py C:\Videos\Projeto\cortes.json
   ```

4. **No Premiere:** *Arquivo → Importar* e escolha o `.xml` gerado. A sequência chega montada, com marcadores nas notas de cada corte (gancho, contexto, CTA…).

## Formato do `cortes.json`

```json
{
  "sequencia": "Reels 01",
  "video": "entrevista.mp4",
  "cortes": [
    {"inicio": "00:03:12,400", "fim": "00:03:18,900", "nota": "GANCHO"},
    {"arquivo": "take2.mp4", "inicio": "12.5", "fim": "19", "nota": "CTA"}
  ]
}
```

- `video` é o arquivo padrão. Cada corte pode apontar para outro arquivo com `arquivo`.
- Caminhos relativos são lidos a partir da pasta do JSON. Em caminhos completos, use `/` (ex.: `C:/Videos/a.mp4`).
- Os tempos aceitam o formato do SRT (`00:01:02,500`), segundos (`62.5`), `MM:SS` ou timecode `HH:MM:SS:FF`.
- Sem FFmpeg, informe o formato: `--fps 29.97 --largura 1080 --altura 1920 --canais 2`.

## Testes

```powershell
python -m unittest discover -s tests
```
