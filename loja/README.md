# loja/

Source of `devboot.com.br/loja/`. A static showcase: nothing is sold here, every product hands off
to the Mercado Livre listing or to a WhatsApp quote. Screens, states and branch tables:
[`docs/loja-flow.md`](../docs/loja-flow.md).

```bash
cd loja
uv run python gerar.py                              # produtos.json + design/tokens.json -> public/loja/
uv run python gerar.py --texto > ../docs/loja-texto.md   # every visitor-facing line, for review
uv run python -m unittest discover -s tests -v       # the whole suite (nginx probe needs Docker)
```

`public/loja/` is **output and is committed** (production deploys with `git pull`, no build on the
VPS). Never edit it by hand: `tests/test_atualizado.py` regenerates and diffs. The only hand-placed
files there are the photos in `public/loja/img/<slug>/`.

## Add or change a product

Edit `produtos.json` and run the generator. It refuses, naming the field and the product: a link off
`mercadolivre.com.br`, an `ativo` product without `link_ml`, a `nome` over 40 characters, a repeated
or reserved slug, a listed photo with no file, an unknown line/type/status, any price field, and
copy outside the limits (resumo 155, 3 benefícios of at most 70, 3 to 10 specs, at most 4 destaques).

- Specs and benefits come from the manufacturer's datasheet. `fonte` lists the URLs they were checked
  against (not shown on the site). **Never store or show a price.**
- `status`: `ativo` (Mercado Livre button), `pausado` (no ML button, WhatsApp is the action),
  `encerrado` (page kept as "Saiu de linha", `noindex`, out of the catalog and the sitemap).
- Colours live in `design/tokens.json` (owner-approved); the generator writes them into `loja.css`.

## Photos

Put source photos (at least 1000 px) through the helper, then list them:

```bash
uv run --with pillow python preparar_foto.py <slug> photo1.png photo2.png ...
```

It writes `public/loja/img/<slug>/1.webp ... n.webp` (800 px, padded onto white, about 10 KB each) and
`og.jpg` (1200 x 630 preview). Add `"fotos": [{"arquivo": "1.webp", "fonte": "<where it came from>"}]`
and `"og": "og.jpg"` to the product. The first photo is the cover; up to 6.

Each line also has a **scene photo** for its tile on the shop home: an official Intelbras photo of
one of its products installed in a real setting, 700 px wide at the 700:478 ratio (never padded or
cropped). It goes through the same helper, then is described in `produtos.json`:

```bash
uv run --with pillow python preparar_foto.py --ambiente <line-slug> scene.jpg
```

```json
"ambiente": {"produto": "<slug of the product shown>", "fonte": "<image URL>", "alt": "<scene, in Portuguese>"}
```

It writes `public/loja/img/_linhas/<line-slug>/480.webp` and `700.webp` (about 15 and 25 KB). The
generator refuses a line without `ambiente`, without either file, or without `fonte` or `alt`.
