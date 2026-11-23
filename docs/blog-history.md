# Importação opcional de arquivos locais

Este caminho é independente da publicação automática dos agendamentos.

## Fluxo local com histórico

`blog/local_mcp.py` é um segundo transporte MCP, por **stdio**, destinado a um
assistente que roda neste computador. Ele lê os arquivos de histórico que o
usuário fornece e envia as matérias ao blog local pela API autenticada. Não
precisa de OAuth para a conexão local por stdio. A conexão do ChatGPT web com
o servidor HTTP continua sendo uma etapa diferente, descrita adiante.

O fluxo completo é:

1. O usuário disponibiliza resultados reais em `.local/history/` ou na pasta
   absoluta indicada por `BLOG_HISTORY_DIR`.
2. O assistente chama `list_history_entries` e seleciona os resultados dos
   agendamentos desejados.
3. `read_history_entry` busca o conteúdo daquele resultado no arquivo local.
4. O assistente transforma esse material em matéria, preservando fatos e fontes.
5. `create_history_article` verifica a identidade e o hash da fonte, deriva uma
   edição estável e envia a matéria ao blog local.

O MCP não possui um modelo de IA próprio. A redação é feita pelo assistente que
chama as ferramentas. O servidor não acessa a conta ChatGPT, não baixa seu
histórico online e não obtém acesso à conta apenas por estar instalado.
Uma tentativa de leitura pela interface em navegador separado ficou bloqueada
por CAPTCHA; não existe integração de navegador ativa neste código.

### Formatos de entrada

- `.md` ou `.txt`, UTF-8: um resultado por arquivo. Preserve o nome do arquivo
  nas novas tentativas para manter a identificação da edição.
- `.html` ou `.htm`: uma página de resultado salva pelo navegador normal. Lê o
  texto da área principal e preserva URLs de links; não executa scripts nem
  carrega recursos externos. Salve a execução já aberta e confira se o resultado
  está no arquivo: páginas que dependem de carregamento posterior podem não
  incluir os textos. Uma execução por arquivo permite deduplicação adequada.
- JSON com `runs`: resultados com identificadores explícitos, como abaixo.
- Conversas exportadas em uma lista com `mapping` e `current_node`: lê somente
  o texto das mensagens do assistente no ramo selecionado. O suporte ao formato
  **não garante** que uma exportação do ChatGPT inclua os históricos dos
  agendamentos. Confira a presença dos resultados antes da importação.

```json
{
  "runs": [
    {
      "id": "terca-2026-10-13",
      "task_name": "Pesquisa de terça",
      "run_at": "2026-10-13T09:00:00-03:00",
      "content_markdown": "Texto completo do resultado real, com as fontes originais."
    }
  ]
}
```

O servidor ignora links simbólicos e não segue subpastas. Arquivos estão
limitados a 25 MB, e cada resultado a 100.000 caracteres. Pastas vazias retornam
uma lista vazia; não há dados fictícios de substituição. Arquivos e sessões
privadas devem ficar fora do Git (`.local/` é ignorada).

### Iniciar o MCP local

Com o blog local rodando, configure a mesma credencial administrativa usada por
esse blog, além de `BLOG_LOCAL_URL` e `BLOG_HISTORY_DIR` quando necessário:

```sh
cd blog
uv run --env-file ../.env python local_mcp.py
```

Esse comando espera um cliente MCP por stdio; não abre uma página web. Configure
o cliente local para executar esse comando. A URL de destino deve ser apenas uma
origem loopback (`127.0.0.1`, `localhost` ou `::1`). Redirecionamentos e proxies de
ambiente não são usados, para manter o token no blog local configurado.

`create_history_article` recebe `entry_id`, `source_sha256` retornado pela
leitura e um objeto `article` com título, slug, resumo, conteúdo, categoria e
status. Não recebe `edition_key`: ela é derivada do resultado de origem.
Se a fonte mudar entre a leitura e a publicação, o envio é recusado. A deduplicação
do blog impede criar outra matéria para a mesma origem com conteúdo divergente.

### Teste completo sem dados reais

```sh
cd blog
uv run --env-file ../.env python tests/local_mcp_smoke.py
```

Com publicação automática habilitada **no blog de teste**, esse teste inicia um
servidor MCP stdio de verdade pelo SDK, lista e lê um histórico fictício
temporário, publica uma matéria rotulada como demonstração e verifica a página
HTML e o reenvio sem duplicação. Não lê a conta ChatGPT e não chama um modelo
de IA; usa formatação determinística apenas para validar o transporte.

Para testar dados reais, disponibilize o arquivo com os resultados e peça ao
assistente para executar o fluxo editorial pelas ferramentas. Não habilite a
conexão em produção antes de validar a seleção de fontes e as matérias locais.

