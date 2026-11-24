# Loja — flow map

Status: **approved by the owner on 23/11/2026** (navigable prototype). Built by `loja/gerar.py`;
the tests in `loja/tests/` are the executable form of the tables below.

The shop is a showcase. Nothing is sold on devboot.com.br: every product hands off to the
company's own Mercado Livre listing (price, payment, delivery) or to a WhatsApp quote.
The pages are static HTML generated from one data file; there is no server-side search.

## URLs

| Page | URL | Why |
|---|---|---|
| Shop home | `/loja/` | storefront: the two lines, featured products, how buying works |
| Category | `/loja/<categoria>/` | `cameras-e-gravadores`, `controle-de-acesso` |
| Product | `/loja/<slug>/` | **not** `/loja/<categoria>/<slug>/`: the URL survives a product moving line or belonging to both (a video intercom fits either), links already shared on WhatsApp and indexed by Google keep working, and it is shorter to share. The hierarchy reaches Google through the breadcrumb and `BreadcrumbList` JSON-LD, not the path |
| Not found | any unknown `/loja/...` | nginx today has no `error_page`, so it serves its default 404. Needs `error_page 404 /loja/404.html` in a `location /loja/` block, which is a server config change |

Cost of the flat product URL: product slugs and category slugs share one namespace, so **the build
must refuse a product slug equal to a category slug**.

## Screens

| Screen | Arrives from | States | Goes to |
|---|---|---|---|
| **Shop home** `/loja/` | header nav "Loja" (every page), landing CFTV section, Google, a shared link | content · **a line has zero products** (tile stays, stamped "Chegando à vitrine", no count; Destaques draws from non-empty lines only) · **no featured products** (Destaques section omitted, not an empty grid) · loading: n/a (static; the line tiles carry a scene photo that reserves its 700:478 box, product tiles their square, so nothing jumps) · error: n/a (no data fetch at runtime) · not permitted: n/a (public) | Category, Product (Destaques), WhatsApp (general quote), CamSeek |
| **Category** `/loja/<categoria>/` | Shop home, header nav, product breadcrumb, 404 page, Google | content (grouped by type, anchor chips jump to each group; no JS filter) · **zero products** (explains the line, offers a WhatsApp quote, links to the other line; `noindex` while empty) · product paused (stays in the list, last in its group, stamped "Sob consulta") · product ended (left out) · long name (wraps to 2 lines, never truncated) · no photo (line pictogram) · loading/error/not permitted: n/a as above | Product, other Category, WhatsApp |
| **Product** `/loja/<slug>/` | Category, Shop home, related products, Google, WhatsApp/ML shares | content (status `ativo`: ML primary, WhatsApp secondary) · **paused** (`pausado`: no ML button at all; a stamp explains; WhatsApp becomes the primary action) · **ended** (`encerrado`: "Saiu de linha", similars first, WhatsApp; `noindex`, out of catalog and sitemap) · **one photo** (no counter, no swipe hint) · **no photo** (line pictogram, "Imagem ilustrativa"; OG image falls back to a generated brand card) · long name (data refuses >40 chars) · loading: photo squares reserved · error: ML link is outside our control; the owner flags `pausado` | Mercado Livre (new tab), WhatsApp (prefilled with the product), Category (breadcrumb), related Product |
| **Not found** `/loja/nao-existe/` | a mistyped or retired URL | single state: says what happened, the two lines, WhatsApp prefilled with the address that failed (script enhances; the link works without it) | Shop home, Category, WhatsApp |

No screen is orphaned (every one is reachable from the nav or a link) and none is a dead end
(every one offers at least one line, one product, or WhatsApp).

## Branch table — product page (rendered by the build, per product)

| Input | Condition | Response |
|---|---|---|
| `status: ativo`, valid ML link | normal | "Ver no Mercado Livre" (primary, new tab) + "Pedir orçamento no WhatsApp" |
| `status: pausado` | owner paused the listing | no ML button; stamp "Indisponível no Mercado Livre no momento"; WhatsApp primary, text "Perguntar no WhatsApp"; stays in catalog, last, "Sob consulta" |
| `status: encerrado` | listing ended for good | page kept with "Saiu de linha", similars above the fold, WhatsApp; `noindex`; out of catalog, home and sitemap |
| `link_ml` host not `mercadolivre.com.br` | data error | **build refuses** |
| `status: ativo` without `link_ml` | data error | **build refuses** |
| `fotos` empty | no photo yet | pictogram of the type + "Imagem ilustrativa"; OG = brand card with the name |
| `fotos` has 1 | single photo | one image, no counter |
| photo file listed but missing | data error | **build refuses** |
| `nome` > 40 chars | ML title pasted as name | **build refuses** with the field and the length |
| `slug` equals a category slug, or repeats | collision | **build refuses** |
| line has 0 products (after removing `encerrado`) | empty line | category empty state, `noindex`; home tile stamped "Chegando à vitrine" |
| URL not generated | unknown slug | `/loja/404.html` via nginx `error_page` |

## Branch table — scene photo of each line (home tiles)

Each line shows, on the shop home only, an official Intelbras photo of one of its products installed
in a real setting (`linhas.<linha>.ambiente`: `fonte`, `alt`, optional `produto`; files
`img/_linhas/<linha>/480.webp` and `700.webp`). The label sits below the photo, never on it. The 404
page and the "other line" tile at the bottom of a category page keep the line pictogram.

| Input | Condition | Response |
|---|---|---|
| line with `ambiente`, both files, https `fonte`, `alt` | normal | tile = photo (`srcset` 480w/700w, `width`/`height` set, `aspect-ratio: 700/478`) + name, count, "Ver a linha"; no pictogram |
| line without `ambiente` | data error | **build refuses**, naming the line |
| `fonte` missing, blank or not https | data error | **build refuses** |
| `alt` missing or blank | data error | **build refuses** |
| `480.webp` or `700.webp` missing | data error | **build refuses**, naming the file |
| `produto` not a product of that line | data error | **build refuses** |
| unknown field in `ambiente` | data error | **build refuses** |
| line has 0 visible products | empty line | tile keeps the photo; stamp "Chegando à vitrine", "Pedir orçamento" |
| first tile on the page | above the fold | `loading="eager"` + `fetchpriority="high"`; the others eager, never lazy |
| file under `img/_linhas/` the data does not name | stray | the generator and the freshness test flag it |
| alt text contains `"`, `<`, `&` | hostile text | escaped; markup stays well formed |

Every "build refuses" row is a test for the generator, written before it.
