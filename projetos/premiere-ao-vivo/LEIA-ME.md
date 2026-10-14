# Editar no Premiere ao vivo (Claude no seu PC com Windows)

Usa o **Premiere Pro MCP** (https://github.com/leancoderkavy/premiere-pro-mcp, licença MIT, versão 1.24.0 no README lido em 14/10/2026; Premiere 2020–2026).
O Claude precisa rodar **no mesmo computador do Premiere** (Claude Desktop ou Claude Code). A sessão em nuvem não alcança o Premiere.
Li o README e o SECURITY.md; **não li o código-fonte nem rodei**. Teste primeiro numa **cópia** do projeto.

## Instalar (caminho mais simples: Claude Desktop)
1. Feche o Premiere. No Premiere, abra seu projeto e faça **Arquivo > Salvar como** (ex.: `EP3_teste.prproj`). Só vamos mexer nessa cópia.
2. Baixe o pacote do Claude Desktop (`premiere-pro-mcp-1.24.0.mcpb`) na página de releases oficial do repositório acima.
   Claude Desktop > **Configurações > Extensões > Configurações avançadas > Instalar extensão** > escolha o arquivo > reinicie o Claude Desktop. (Não precisa de Node.js.)
3. Instale o **conector do Premiere** (`MCPBridgeCEP.zxp`, mesma página de releases) com um instalador de ZXP.
   Sem instalador de ZXP: instale o Node.js 20.19+ e, no PowerShell, rode `npm install -g premiere-pro-mcp` e depois `premiere-pro-mcp --install-cep`.
   (Confira que o pacote se chama exatamente `premiere-pro-mcp`, não `adobe-premiere-pro-mcp`.)
4. Abra o Premiere, abra a cópia do projeto com uma sequência ativa e vá em **Janela > Extensões > MCP for Adobe Premiere Pro**. Deve aparecer "Running".
5. No Claude Desktop, mande: `Verifique minha conexão com o Premiere usando verify_premiere_connection. Não faça nenhuma alteração.`

## Primeiros testes (um por vez, sempre na cópia)
1. Só leitura: "Liste as sequências e as trilhas da sequência ativa, sem alterar nada."
2. Marcadores: "Coloque marcadores com nome nos pontos [tempos] da sequência ativa." (reversível com Ctrl+Z)
3. Corte: "Na trilha V1, corte a sequência nos tempos [..] e apague o trecho [..]. Descreva o que vai fazer antes e espere eu confirmar."
4. Motion: "Importe `overlay.webm` (ou .mov com transparência) e coloque na trilha V2 a partir de [tempo]."

## Regras de segurança
- Sempre na cópia; peça para o Claude **descrever antes de alterar** e confirme.
- Mantenha o perfil padrão (sem "unsafe-script"): não libere execução de scripts livres.
- Feche e reabra o Premiere depois de instalar ou atualizar o conector.

## Para o Claude do PC conhecer o nosso padrão
Clone este repositório no PC (`git clone <repo>`) e abra o Claude Code na pasta: ele lê o `CLAUDE.md` (padrão visual, ordem da pós-produção, regras de corte).
Tarefas pesadas (transcrição, render de motion, verificação) funcionam melhor aqui na nuvem; no PC o Claude cuida da timeline.
