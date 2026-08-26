# design/

Duas variações de landing exploradas antes da troca visual de 2026-08-26.

| Arquivo | O que é |
| --- | --- |
| `v2-sinal.html` | Variação monocromática: instrumento e ação no mesmo `#E10600`. **Não escolhida.** |
| `v2-sinal-duplo.html` | Variação escolhida: instrumento em `#2563EB`, vermelho reservado para ação. |

As duas diferem em um único token (`--data`) no bloco `.page[data-palette=...]`.

## Relação com produção

`v2-sinal-duplo.html` **é derivada de `public/index.html`**: mesmo CSS, mesmo
markup, mesmo script — o que muda é só o envelope. A produção é a fonte; o
arquivo daqui existe para dar um link de preview (útil para abrir no celular). O arquivo daqui é um
fragmento (sem `<!DOCTYPE>`, `<head>` ou `<body>`) porque é publicado como
Artifact, que injeta o próprio envelope; a versão de produção recebe um `<head>`
completo com favicons, Open Graph e canonical.

**Cuidado com a divergência:** editar `public/index.html` não atualiza o preview,
e vice-versa. Ao mexer no visual, decida qual é a fonte e refaça a outra ponta.
Hoje a fonte de verdade é `public/index.html`.

## Formulário

O envio usa Web3Forms (`CHAVE_WEB3FORMS` no script). A chave é pública por
natureza — ela é servida ao navegador. Quem define o destinatário é a conta, não
a chave: os envios chegam em `comercial@devboot.com.br`.

O plano grátis **recusa requisição feita de servidor**; só aceita do navegador.
Teste sempre pela página, nunca por `curl`.
