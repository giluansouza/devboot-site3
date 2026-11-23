# Blog Devboot e publicação pelo ChatGPT

O site principal continua em `public/`, servido por Nginx. O novo serviço
`blog` serve páginas HTML em `/blog/`, recebe artigos por API e disponibiliza
ferramentas MCP em `/mcp`. Os artigos ficam em SQLite no volume Docker
`blog-data`; recriar o container não apaga as matérias.

Não há gerador de texto nem chamadas à API da OpenAI neste serviço. O conteúdo
é produzido no ChatGPT e enviado por uma ferramenta conectada. Este projeto
não lê nem altera automaticamente os agendamentos da conta do usuário.

## Fluxo automático dos agendamentos

ChatGPT executa a pesquisa → gera o resumo → envia esse mesmo resumo, sem edição,
à ferramenta `create_article` pelo MCP
→ o blog publica e retorna a URL. Não há exportação de histórico, cópia de
matérias, captura de navegador ou login automatizado na conta ChatGPT.

Para novas execuções, a tarefa deve usar a conexão Devboot Blog e enviar
`status=published`. A instalação e a autorização da conexão são feitas uma vez.
As permissões de escrita do ChatGPT precisam permitir essa ação recorrente;
se a plataforma exigir aprovação por execução, a automação ficará pendente.
O teste com um cliente MCP valida o servidor, mas não substitui o teste de
uma execução real na conta ChatGPT.

### Teste local com HTTPS e OAuth

O Compose separado `docker-compose.blog-local.yml` inicia um blog de teste,
Keycloak para OAuth e um túnel HTTPS temporário Cloudflare. Não usa Traefik,
a rede de produção nem o banco de produção. A API administrativa e o console
Keycloak não são expostos pelo túnel. O blog de teste pode ser visto pela URL
pública; não use conteúdo privado nessa instalação.

```sh
docker compose -f docker-compose.blog-local.yml up -d tunnel
docker compose -f docker-compose.blog-local.yml logs tunnel
```

Copie a origem `https://...trycloudflare.com` exibida nos logs para:

```sh
python blog/local_setup.py https://SEU-TUNEL.trycloudflare.com
docker compose -f docker-compose.blog-local.yml --env-file .local/chatgpt/local.env up -d --build auth blog web
```

O preparo gera credenciais aleatórias em `.local/chatgpt/`, fora do Git.
Abra `.local/chatgpt/conectar.txt` para cadastrar a conexão OAuth no ChatGPT:
a URL MCP, Client ID e Client secret estão no arquivo, seguidos pelo login
**do blog de teste**. Não use sua senha ChatGPT nesse formulário Devboot.
O cliente exige PKCE S256 e usa o callback estável
`https://chatgpt.com/connector_platform_oauth_redirect`, pois o provedor
anuncia e retorna identificação do issuer. Se a interface exibir outro callback,
cadastre exatamente aquele endereço; não use curingas.

Acesse o blog em `http://127.0.0.1:18976/blog/`.
Os arquivos `.local/chatgpt/agendamento-terca.txt` e
`.local/chatgpt/agendamento-sabado.txt` contêm o complemento editorial a aplicar
uma vez às tarefas existentes. Preserve suas pautas e horários originais.
O teste de integração real usa um cliente OAuth separado e cria somente uma
matéria identificada como demonstração:

```sh
cd blog
uv run python tests/remote_mcp_smoke.py
```

Ele verifica login, PKCE, código de uso único, renovação offline, MCP via HTTPS,
publicação, leitura, repetição sem duplicação e recusa de acesso anônimo.
Não acessa nem altera a conta ChatGPT. Depois de conectar a ferramenta, execute
uma tarefa de teste no ChatGPT e confirme a matéria no blog. Só então valide
uma execução agendada e habilite a publicação recorrente dos dois agendamentos.

O computador e os containers precisam permanecer ligados durante o teste.
Um novo túnel pode receber outro endereço; nesse caso, prepare novamente e
recrie `auth`, `blog` e `web`, preservando o volume `articles`. O Keycloak de
teste é efêmero: recriá-lo invalida as conexões e requer novo login. Esse Compose
usa `start-dev` e não deve ser levado à produção; o ambiente definitivo precisa
de domínio estável e provedor OAuth persistente.

Para encerrar o teste sem apagar artigos:

```sh
docker compose -f docker-compose.blog-local.yml stop
```

## Executar localmente

```sh
cd blog
uv sync --frozen
BLOG_DB=/tmp/devboot-blog-preview.sqlite3 uv run uvicorn app:create_app --factory --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000/blog/`. Esse comando executa apenas o serviço do blog;
as imagens da marca e os links para a landing são servidos pelo Nginx na
configuração completa. Para testar:

```sh
cd blog
uv run python -m unittest discover -s tests -v
```

## Instalação no servidor atual

1. Copie `.env.example` para `.env`. Gere `BLOG_API_TOKEN` com
   `openssl rand -hex 32` e coloque o resultado somente em `.env`.
2. Mantenha `BLOG_BASE_URL=https://www.devboot.com.br`, ou defina o domínio
   canônico desejado. Configure OAuth antes de conectar o MCP.
3. No servidor que já usa Traefik e a rede `debnet`, execute:

   ```sh
   docker compose config --quiet
   docker compose up -d --build
   ```

4. Confirme a landing, `/blog/`, `/blog/feed.xml` e `/blog/sitemap.xml`.
   Não foi incluído artigo de exemplo no banco de produção.

`BLOG_ALLOW_AUTO_PUBLISH=false` é o padrão inicial: aceita rascunhos e impede
que as ferramentas publiquem diretamente. Para permitir publicação automática,
configure `BLOG_ALLOW_AUTO_PUBLISH=true` e recrie o serviço `blog`. O endpoint
manual de aprovação continua disponível com a credencial administrativa da API.

## Conectar o ChatGPT

Os agendamentos precisam ter acesso ao plugin/ferramenta no chat em que rodam.
Verifique a disponibilidade na conta: um agendamento antigo pode precisar ser
recriado em um chat com as ferramentas habilitadas. Não basta fornecer a URL de
compartilhamento de uma tarefa para este servidor.

O MCP é implementado com o SDK oficial e usa Streamable HTTP. Há três ferramentas:

- `list_articles`: consulta edições e títulos para evitar repetição de pautas;
- `read_article`: consulta o conteúdo de uma matéria ou rascunho existente;
- `create_article`: recebe o objeto `article` descrito abaixo e retorna status e URL.

### Autenticação OAuth

A conexão autenticada com o ChatGPT requer um provedor OAuth 2.1. Este serviço
implementa a verificação dos tokens e o documento de descoberta do recurso;
não implementa um servidor próprio de login, autorização ou refresh tokens.
Use um provedor existente, como Auth0, e restrinja o acesso ao editor autorizado.

Configure o provedor com:

- audience/resource: `https://www.devboot.com.br/mcp`;
- scope: `blog:write`, concedido apenas ao editor do blog; solicite também
  `offline_access` no cliente para renovação offline quando o provedor o usar;
- authorization code com PKCE S256 e refresh tokens para acesso recorrente;
- descoberta OAuth/OIDC e registro de cliente compatível com ChatGPT (CIMD,
  DCR ou cliente predefinido);
- tokens de acesso JWT assinados com RS256 ou ES256, com `sub`, `iss`, `aud`,
  `exp` e o scope `blog:write` no campo `scope`.

Preencha `BLOG_OAUTH_ISSUER` com o issuer exato do provedor (inclusive a barra
final, quando houver) e `BLOG_OAUTH_JWKS_URL` com a URL HTTPS do JWKS.
O provedor deve autorizar esse audience e scope somente para as contas que
podem publicar na Devboot. A API key administrativa **não** é uma credencial MCP.

No ChatGPT, adicione uma conexão MCP personalizada apontando para
`https://www.devboot.com.br/mcp`, escolha OAuth e conclua o login.
Instale/habilite a ferramenta no chat dos agendamentos e faça um teste manual
com `status=draft`. Após conferir, teste uma publicação e a primeira execução
agendada. As permissões da conta/workspace podem exigir confirmação de escrita:
valide o funcionamento sem intervenção antes de considerar a automação ativa.

Sem OAuth configurado, `/mcp` retorna 503. Tokens sem assinatura válida, issuer,
audience, validade ou scope corretos são recusados. Nunca desative a
autenticação para conectar o ChatGPT.

Referências oficiais:

- [Agendamentos e ferramentas conectadas](https://learn.chatgpt.com/docs/automations)
- [Conectar um MCP personalizado](https://developers.openai.com/plugins/quickstart)
- [Autenticação de plugins](https://developers.openai.com/plugins/build/auth)

## Contrato de publicação

`POST /api/blog/articles`, autenticado com `Authorization: Bearer <BLOG_API_TOKEN>`.
No MCP, envie o mesmo objeto dentro do argumento `article` de `create_article`.

```json
{
  "edition_key": "terca-2026-10-20",
  "slug": "automacao-na-gestao-de-frotas",
  "title": "Automação na gestão de frotas: por onde começar",
  "excerpt": "Um resumo curto da matéria, com pelo menos vinte caracteres, para a listagem e os buscadores.",
  "content_markdown": "## O problema antes da ferramenta\n\nEscreva aqui a matéria completa em Markdown, com pelo menos cem caracteres, subtítulos e links para as fontes consultadas.",
  "category": "Automação",
  "status": "draft"
}
```

Limites: título de 5 a 180 caracteres, resumo de 20 a 350, conteúdo de 100 a
100.000, categoria de 2 a 60, slug de 3 a 120. O slug aceita letras minúsculas
sem acentos, números e hífens. A edição aceita letras minúsculas, números,
pontos, hífens e underscores. Campos desconhecidos são recusados.
Markdown renderiza títulos, parágrafos, listas, links, citações e blocos de código;
HTML embutido é escapado. Scripts e links `javascript:` não são executados.

A `edition_key` identifica a execução editorial: nome estável do agendamento
mais a data em `America/Recife`. Use identificadores diferentes se os dois
agendamentos rodarem no mesmo dia. Reenvios idênticos retornam a matéria
existente (HTTP 200); a primeira criação retorna 201. Conteúdo diferente com a
mesma edição, ou um slug já usado, retorna 409. Nada é sobrescrito.

Uma matéria publicada recebe URL canônica, metadados sociais, dados estruturados,
RSS e sitemap. Um rascunho não aparece nessas páginas e não tem URL pública.
As listagens estão limitadas às 500 matérias mais recentes nesta versão.

## Rascunhos e aprovação manual

`GET /api/blog/articles` lista matérias e seus conteúdos, incluindo rascunhos.
`POST /api/blog/articles/{slug}/publish` aprova um artigo existente.
Ambos exigem a credencial administrativa. Não há painel de administração nesta
versão; a revisão é feita pelo cliente da API, ou consultando os rascunhos pelo
MCP. A aprovação exige a API administrativa e não é oferecida como ferramenta
MCP para preservar a opção de revisão manual.

## Instrução para acrescentar aos dois agendamentos

Preserve a pauta original e acrescente o texto abaixo. Ajuste `terca` para o
identificador fixo de cada agendamento e use `published` para o fluxo automático autorizado. Os horários e as pautas originais precisam ser
informados pelo usuário; este projeto não os conhece.

> Ao terminar a pesquisa e gerar o resumo desta execução, publique no blog da
> Devboot exatamente esse mesmo texto. Não escreva uma matéria nova, não reescreva,
> resuma, amplie, corrija ou parafraseie. Preserve palavras, pontuação, parágrafos,
> títulos, listas e links, na ordem original. Envie o texto integral em
> content_markdown. Use o título já existente como title; use como excerpt um
> trecho literal do próprio resumo. Consulte list_articles para evitar duplicação
> e verificar se a edição de
> hoje já existe. Use edition_key terca-AAAA-MM-DD, com a data de America/Recife.
> Se a edição já existir, consulte-a e informe seu status; não crie outra chave
> para a mesma execução. Envie o resumo à ferramenta create_article com
> status=published. Só informe que foi salva ou publicada após a ferramenta confirmar.
> Para publicação, informe a URL retornada. Se houver erro, reporte-o claramente
> e preserve o conteúdo nesta conversa para nova tentativa.

Uma execução avulsa usa a mesma edição da data se for uma repetição daquela
pauta. Para uma matéria extra intencional, use uma edição explicitamente
distinta, como `extra-2026-10-20-automacao`.

## Backup e recuperação

Inclua o volume `blog-data` no backup do servidor. Para um backup consistente,
use a operação SQLite `backup` (o serviço usa WAL; copiar somente o arquivo
principal com o banco ativo pode perder dados). Exemplo dentro do container:

```sh
docker compose exec -T blog .venv/bin/python -c 'import sqlite3; source=sqlite3.connect("/data/blog.sqlite3"); target=sqlite3.connect("/data/blog-backup.sqlite3"); source.backup(target); target.close(); source.close()'
docker compose cp blog:/data/blog-backup.sqlite3 ./blog-backup.sqlite3
```

Guarde o backup fora do servidor. Para restaurar, pare o serviço, substitua o
banco no volume por uma cópia consistente e preserve o dono UID 10001.
Não use `docker compose down -v` em produção: ele remove os artigos.
