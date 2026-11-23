"""Static generator for devboot.com.br/loja/.

    uv run python gerar.py            regenerate public/loja/ from produtos.json
    uv run python gerar.py --texto    print every visitor-facing line, for the owner's review

`produtos.json` + `design/tokens.json` are the source. `public/loja/` (HTML, CSS, JS, sprite,
sitemap) is output and is committed, because production deploys with `git pull` and nothing is
built on the VPS. Never edit it by hand: tests/test_atualizado.py regenerates and diffs.
Photos are the one exception: they are put in public/loja/img/<slug>/ and only referenced.

Standard library only.
"""
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parents[1]

STATUS = ("ativo", "pausado", "encerrado")
PICTOGRAMAS = ("bullet", "dome", "kit", "nvr", "hd", "face", "lock", "door")
RESERVADOS = ("img", "404", "loja", "sitemap")  # would shadow a file or folder of the shop
MAX_NOME, MAX_RESUMO, MAX_BENEFICIO, MAX_FOTOS, MAX_DESTAQUES = 40, 155, 70, 6, 4
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SITE_PUBLICO = "https://www.devboot.com.br"
WHATSAPP_RE = re.compile(r"^55[0-9]{10,11}$")

CAMPOS_PRODUTO = {
    "slug", "nome", "marca", "modelo", "linha", "tipo", "status", "link_ml", "resumo", "beneficios",
    "specs", "pictograma", "fotos", "og", "destaque", "fonte"}
OBRIGATORIOS = ("slug", "nome", "marca", "linha", "tipo", "status", "resumo", "beneficios", "specs",
                "pictograma", "fonte")
CAMPOS_PRECO = {"preco", "preço", "price", "valor", "precos", "preços"}


class ErroDeDados(Exception):
    def __init__(self, erros):
        super().__init__("\n".join(erros))
        self.erros = list(erros)


def url_limpa(url):
    """No backslash, whitespace or control/format character anywhere: a browser reads `\\` as `/`
    (https://evil.com\\.mercadolivre.com.br/ goes to evil.com) and strips tabs and newlines, so
    the parser here and the browser would disagree about the host."""
    return (isinstance(url, str) and "\\" not in url
            and not any(c.isspace() or unicodedata.category(c) in ("Cc", "Cf", "Zl", "Zp") for c in url))


def link_do_mercado_livre(url):
    """True only for https://mercadolivre.com.br or any of its subdomains, with no userinfo."""
    if not url_limpa(url):
        return False
    try:
        u = urlparse(url)
        host = u.hostname or ""
        has_user = u.username is not None or u.password is not None
    except ValueError:
        return False
    return (u.scheme == "https" and not has_user
            and (host == "mercadolivre.com.br" or host.endswith(".mercadolivre.com.br")))


def link_https(url):
    if not url_limpa(url):
        return False
    try:
        u = urlparse(url)
        return u.scheme == "https" and bool(u.hostname) and "." in u.hostname
    except (ValueError, AttributeError):
        return False


def _texto(v):
    return isinstance(v, str) and v.strip() != ""


def validar(dados, pasta_fotos):
    """Every reason the data is not publishable, each naming the field and the product."""
    e = []
    loja = dados.get("loja") or {}
    linhas = dados.get("linhas") or {}
    produtos = dados.get("produtos") or []

    for campo in ("site", "whatsapp", "vendedor_ml", "perfil_ml", "revenda", "instalacao", "ano"):
        if not loja.get(campo):
            e.append(f"loja.{campo}: missing")
    if loja.get("site") and loja["site"] != SITE_PUBLICO:
        e.append(f"loja.site: {loja['site']!r} must be exactly {SITE_PUBLICO!r} (canonical, OG and sitemap use it)")
    if loja.get("whatsapp") and not (isinstance(loja["whatsapp"], str) and WHATSAPP_RE.match(loja["whatsapp"])):
        e.append(f"loja.whatsapp: {loja['whatsapp']!r} must be digits only with the country code, "
                 "e.g. 5587991402037 (no +, spaces or dashes)")
    if loja.get("perfil_ml") and not link_do_mercado_livre(loja["perfil_ml"]):
        e.append(f"loja.perfil_ml: {loja['perfil_ml']!r} is not an https link on mercadolivre.com.br")

    for ls, l in linhas.items():
        if not SLUG_RE.match(ls):
            e.append(f"linhas.{ls}: malformed slug")
        for campo in ("nome", "descricao", "vazio", "pictograma", "tipos"):
            if not l.get(campo):
                e.append(f"linhas.{ls}.{campo}: missing")
        if l.get("pictograma") and l["pictograma"] not in PICTOGRAMAS:
            e.append(f"linhas.{ls}.pictograma: {l['pictograma']!r} unknown (one of {', '.join(PICTOGRAMAS)})")

    vistos = {}
    destaques = 0
    for i, p in enumerate(produtos):
        slug = p.get("slug")
        ref = f"produtos[{i}] ({slug})" if _texto(slug) else f"produtos[{i}]"

        for campo in sorted(set(p) - CAMPOS_PRODUTO):
            if campo.lower() in CAMPOS_PRECO:
                e.append(f"{ref}: field {campo!r}: prices are never published and never stored here")
            else:
                e.append(f"{ref}: unknown field {campo!r}")
        for campo in OBRIGATORIOS:
            if campo not in p or p[campo] in (None, "", [], {}):
                e.append(f"{ref}: {campo} is required")

        if "slug" in p:
            if not (_texto(slug) and SLUG_RE.match(slug)):
                e.append(f"{ref}: slug {slug!r} must be lowercase letters, digits and single hyphens")
            elif slug in linhas:
                e.append(f"{ref}: slug {slug!r} equals the category slug /loja/{slug}/")
            elif slug in RESERVADOS:
                e.append(f"{ref}: slug {slug!r} is reserved (it would shadow a file or folder of /loja/)")
            elif slug in vistos:
                e.append(f"{ref}: slug {slug!r} repeats produtos[{vistos[slug]}]")
            else:
                vistos[slug] = i

        nome = p.get("nome")
        if nome is not None:
            if not _texto(nome):
                e.append(f"{ref}: nome is empty")
            elif len(nome) > MAX_NOME:
                e.append(f"{ref}: nome has {len(nome)} characters, the limit is {MAX_NOME}: {nome!r}")

        linha, tipo, status = p.get("linha"), p.get("tipo"), p.get("status")
        if linha is not None and linha not in linhas:
            e.append(f"{ref}: linha {linha!r} unknown (one of {', '.join(linhas)})")
        elif linha is not None and tipo is not None and tipo not in linhas[linha].get("tipos", []):
            e.append(f"{ref}: tipo {tipo!r} is not a type of {linha} "
                     f"(one of {', '.join(linhas[linha].get('tipos', []))})")
        if status is not None and status not in STATUS:
            e.append(f"{ref}: status {status!r} unknown (one of {', '.join(STATUS)})")
        if p.get("pictograma") is not None and p["pictograma"] not in PICTOGRAMAS:
            e.append(f"{ref}: pictograma {p['pictograma']!r} unknown (one of {', '.join(PICTOGRAMAS)})")

        link = p.get("link_ml")
        if status == "ativo" and not _texto(link):
            e.append(f"{ref}: link_ml is required while status is 'ativo'")
        elif _texto(link) and not link_do_mercado_livre(link):
            e.append(f"{ref}: link_ml {link!r} is not an https link on mercadolivre.com.br")
        elif link is not None and not isinstance(link, str):
            e.append(f"{ref}: link_ml must be a string")

        resumo = p.get("resumo")
        if isinstance(resumo, str) and len(resumo) > MAX_RESUMO:
            e.append(f"{ref}: resumo has {len(resumo)} characters, the limit is {MAX_RESUMO}")

        b = p.get("beneficios")
        if b is not None and "beneficios" in p and b != []:
            if not isinstance(b, list) or len(b) != 3:
                e.append(f"{ref}: beneficios must be exactly 3 items, got "
                         f"{len(b) if isinstance(b, list) else b!r}")
            else:
                for k, x in enumerate(b):
                    if not _texto(x) or len(x) > MAX_BENEFICIO:
                        e.append(f"{ref}: beneficios[{k}] must be 1 to {MAX_BENEFICIO} characters")

        s = p.get("specs")
        if isinstance(s, list) and s:
            if not 3 <= len(s) <= 10:
                e.append(f"{ref}: specs must have 3 to 10 rows, got {len(s)}")
            for k, par in enumerate(s):
                if not (isinstance(par, list) and len(par) == 2 and _texto(par[0]) and _texto(par[1])):
                    e.append(f"{ref}: specs[{k}] must be [label, value], both non-empty")

        f = p.get("fonte")
        if isinstance(f, list) and f and not all(link_https(x) for x in f):
            e.append(f"{ref}: fonte must be a list of https URLs (where the data was checked)")

        fotos = p.get("fotos", [])
        if not isinstance(fotos, list):
            e.append(f"{ref}: fotos must be a list")
            fotos = []
        if len(fotos) > MAX_FOTOS:
            e.append(f"{ref}: fotos has {len(fotos)} items, the limit is {MAX_FOTOS}")
        nomes = [x.get("arquivo") if isinstance(x, dict) else None for x in fotos]
        for k, x in enumerate(fotos):
            arq = nomes[k]
            if not isinstance(x, dict) or not _texto(arq):
                e.append(f"{ref}: fotos[{k}] must be {{arquivo, fonte}}")
                continue
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*\.(webp|jpg|jpeg|png)", arq):
                e.append(f"{ref}: fotos[{k}].arquivo {arq!r} must be a plain file name (.webp, .jpg or .png)")
            elif not (Path(pasta_fotos) / str(slug) / arq).is_file():
                e.append(f"{ref}: fotos[{k}].arquivo {arq!r} is listed but img/{slug}/{arq} does not exist")
            if not link_https(x.get("fonte")):
                e.append(f"{ref}: fotos[{k}].fonte must be the https URL the photo came from")
        if p.get("og") and not (Path(pasta_fotos) / str(slug) / str(p["og"])).is_file():
            e.append(f"{ref}: og {p['og']!r} is listed but img/{slug}/{p['og']} does not exist")

        if p.get("destaque"):
            destaques += 1

    if destaques > MAX_DESTAQUES:
        e.append(f"destaque: {destaques} featured products, the limit is {MAX_DESTAQUES}")
    return e


# --------------------------------------------------------------------------- rendering

import hashlib
import html as _html
import json
import sys
from html.parser import HTMLParser
from urllib.parse import quote

SITE_IMG_PADRAO = "/img/devboot-share-light-1200x630.png"
FONTES = ("https://fonts.googleapis.com/css2?family=Archivo:wght@700;800;900"
          "&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap")
TEMA_JS = ("try { if (localStorage.getItem('devboot-tema') === 'escuro') "
           "document.documentElement.setAttribute('data-tema', 'escuro'); } catch (e) {}\n"
           "document.documentElement.classList.add('js');")
LANDING = (("Desenvolvimento", "/#desenvolvimento"), ("Produtos", "/#produtos"),
           ("Câmeras", "/#cftv"), ("Loja", "/loja/"), ("Blog", "/blog/"), ("Contato", "/#contato"))
CAMSEEK = "https://camseek.devboot.com.br"


def e(s):
    return _html.escape(str(s), quote=True)


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def kebab(nome):
    return re.sub(r"(?<!^)(?=[A-Z])", "-", nome).lower()


def plural(n, um, varios):
    return f"{n} {um if n == 1 else varios}"


def bloco_tokens(tokens):
    """The approved tokens (design/tokens.json) as CSS: light on :root, dark on [data-tema]."""
    def decls(cores):
        return [f"  --{kebab(k)}: {v};" for k, v in cores.items()]
    return "\n".join([
        "/* BEGIN tokens: generated from design/tokens.json by loja/gerar.py. Edit the JSON. */",
        ":root {", "  color-scheme: light;", *decls(tokens["color"]), "}",
        ':root[data-tema="escuro"] {', "  color-scheme: dark;",
        *decls(tokens["themes"]["dark"]["color"]), "}",
        "/* END tokens */"])


class Contexto:
    """Everything a page needs to know about the shop, computed once."""

    def __init__(self, dados, estaticos, css, js):
        self.loja = dados["loja"]
        self.linhas = dados["linhas"]
        self.todos = dados["produtos"]
        self.site = self.loja["site"].rstrip("/")
        self.marca = (Path(estaticos) / "marca.html").read_text(encoding="utf-8").strip()
        self.css_url = "/loja/loja.css?v=" + hashlib.sha1(css).hexdigest()[:8]
        self.js_url = "/loja/loja.js?v=" + hashlib.sha1(js).hexdigest()[:8]

    def visiveis(self, linha):
        """What the catalog shows for a line: everything but the ended products."""
        return [p for p in self.todos if p["linha"] == linha and p["status"] != "encerrado"]

    def por_slug(self, slug):
        return next(p for p in self.todos if p["slug"] == slug)

    def wa(self, texto):
        return f"https://wa.me/{self.loja['whatsapp']}?text={quote(texto, safe='')}"

    def modelo(self, p):
        return f"{p['marca']} {p['modelo']}" if p.get("modelo") else p["marca"]

    def rotulo(self, p):
        return f"{p['nome']} ({self.modelo(p)})"

    def foto(self, p, i=0):
        return f"/loja/img/{p['slug']}/{p['fotos'][i]['arquivo']}"

    def og_imagem(self, p=None):
        if p and p.get("og"):
            return f"{self.site}/loja/img/{p['slug']}/{p['og']}", None
        if p and p.get("fotos"):
            return self.site + self.foto(p), None
        return self.site + SITE_IMG_PADRAO, (1200, 630)


def icone(id_, extra=""):
    return f'<svg aria-hidden="true"{extra}><use href="/loja/sprite.svg#{id_}"/></svg>'


def ph(c, p, pict, v=0, ilustrativa=False, eager=False, i=0, total=1):
    """A square on the `photo` background: the photo (padded, never cropped) or the pictogram."""
    if p and p.get("fotos"):
        n = len(p["fotos"])
        carga = ' loading="eager" fetchpriority="high"' if eager else ' loading="lazy"'
        alt = f"{p['nome']}, foto {i + 1} de {n}" if n > 1 else p["nome"]
        return (f'<div class="ph"><img src="{e(c.foto(p, i))}" alt="{e(alt)}" width="800" height="800"'
                f'{carga} decoding="async"></div>')
    return (f'<div class="ph" data-v="{v}">{icone("p-" + pict)}'
            + ('<span class="ilus">Imagem ilustrativa</span>' if ilustrativa else "") + "</div>")


def carimbo_pausado():
    return '<span class="stamp">Sob consulta</span>'


def item(c, p):
    chave = " · ".join(v for _, v in p["specs"][:2])
    return (f'<li class="item"><a href="/loja/{p["slug"]}/">'
            f'{ph(c, p, p["pictograma"], 0, not p.get("fotos"), i=0)}'
            f'<div class="txt"><span class="name">{e(p["nome"])}</span>'
            f'<span class="model">{e(c.modelo(p))}</span><span class="key">{e(chave)}</span>'
            + (carimbo_pausado() if p["status"] == "pausado" else "") + "</div></a></li>")


def tile_da_linha(c, slug):
    L, ps = c.linhas[slug], c.visiveis(slug)
    if ps:
        tipos = [t for t in L["tipos"] if any(p["tipo"] == t for p in ps)]
        meta = f'<span class="model">{plural(len(ps), "produto", "produtos")} · {e(", ".join(tipos))}</span>'
        ir = "Ver a linha"
    else:
        meta = '<span class="stamp stamp--dot">Chegando à vitrine</span>'
        ir = "Pedir orçamento"
    return (f'<li class="line"><a href="/loja/{slug}/"><div class="stack g45"><h3>{e(L["nome"])}</h3>{meta}'
            f'<span class="go">{ir} <span aria-hidden="true">→</span></span></div>'
            f'{ph(c, None, L["pictograma"])}</a></li>')


def lista_de_linhas(c):
    return '<ul class="lines">' + "".join(tile_da_linha(c, s) for s in c.linhas) + "</ul>"


# ------------------------------------------------------------------------------ page shell

def cabecalho(c, atual):
    links = "".join(
        f'<a class="nlink" href="{h}"' + (f' aria-current="{"page" if atual == "inicio" else "true"}"'
                                          if h == "/loja/" and atual else "") + f'>{t}</a>'
        for t, h in LANDING)
    wa = c.wa("Olá, vim pelo site da Devboot e quero conversar.")
    return (
        '<a class="skip" href="#app">Pular para o conteúdo</a>\n'
        '<header class="nav" id="nav"><div class="wrap gut">'
        f'<a class="brand" href="/loja/" aria-label="Loja Devboot, início da loja">{c.marca}</a>'
        f'<nav class="links" id="links" aria-label="Navegação principal">{links}'
        f'<a class="btn" href="{e(wa)}" target="_blank" rel="noopener noreferrer">{icone("wa")}Falar no WhatsApp</a></nav>'
        '<div class="navr"><button class="iconbtn theme-btn" type="button" id="themeBtn" '
        'aria-label="Mudar para o tema escuro" title="Mudar para o tema escuro">'
        f'<span class="to-dark">{icone("moon")}<span class="t-txt">Escuro</span></span>'
        f'<span class="to-light">{icone("sun")}<span class="t-txt">Claro</span></span></button>'
        '<button class="iconbtn burger" type="button" id="burger" aria-expanded="false" '
        'aria-controls="links">Menu</button></div></div></header>')


def rodape(c):
    l = c.loja
    return (f'<footer class="foot"><div class="wrap gut"><span>© {e(l["ano"])} Devboot Tecnologia</span>'
            f'<span>Dormentes, PE</span><span>{e(l["revenda"])}</span>'
            '<span>Loja: vitrine dos anúncios da Devboot no Mercado Livre</span></div></footer>')


def breadcrumb_ld(c, itens):
def json_para_script(obj, **kw):
    """JSON that is safe inside <script>: json.dumps leaves `<` alone, so a name containing
    </script> would end the block and the rest would be parsed as HTML. \\u003c and friends mean
    the same thing to a JSON parser and nothing to the HTML parser."""
    return (json.dumps(obj, ensure_ascii=False, **kw)
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


    return json_para_script({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": nome, "item": c.site + caminho}
                            for i, (nome, caminho) in enumerate(itens)]},
        indent=2)


def pagina(c, *, titulo, descricao, caminho, corpo, atual, noindex=False, og=None, migalhas=None,
           depois_do_rodape="", canonical=True):
    og_url, dim = og or c.og_imagem()
    meta = [
        f'<title>{e(titulo)}</title>',
        f'<meta name="description" content="{e(descricao)}">',
    ]
    if noindex:
        meta.append('<meta name="robots" content="noindex">')
    if canonical:
        meta.append(f'<link rel="canonical" href="{e(c.site + caminho)}">')
    meta += [
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Devboot">',
        '<meta property="og:locale" content="pt_BR">',
        f'<meta property="og:title" content="{e(titulo)}">',
        f'<meta property="og:description" content="{e(descricao)}">',
        f'<meta property="og:image" content="{e(og_url)}">',
    ]
    if canonical:
        meta.append(f'<meta property="og:url" content="{e(c.site + caminho)}">')
    if dim:
        meta += [f'<meta property="og:image:width" content="{dim[0]}">',
                 f'<meta property="og:image:height" content="{dim[1]}">']
    meta += [
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{e(titulo)}">',
        f'<meta name="twitter:description" content="{e(descricao)}">',
        f'<meta name="twitter:image" content="{e(og_url)}">',
    ]
    ld = (f'<script type="application/ld+json">\n{breadcrumb_ld(c, migalhas)}\n</script>\n'
          if migalhas else "")
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<script>
{TEMA_JS}
</script>
{chr(10).join(meta)}
<meta name="theme-color" content="#0a0d12">
<link rel="icon" href="/img/favicon/favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="/img/favicon/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/img/favicon/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/img/favicon/favicon-16x16.png">
<link rel="apple-touch-icon" href="/img/favicon/apple-touch-icon.png">
<link rel="mask-icon" href="/img/favicon/safari-pinned-tab.svg" color="#e10600">
<link rel="manifest" href="/img/favicon/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTES}">
<link rel="stylesheet" href="{c.css_url}">
{ld}<script src="{c.js_url}" defer></script>
</head>
<body>
{cabecalho(c, atual)}
<main id="app">
{corpo}
</main>
{rodape(c)}
{depois_do_rodape}
</body>
</html>
"""


# ------------------------------------------------------------------------------------ pages

PASSOS = (
    ("Escolha aqui", "Cada produto tem foto, ficha técnica e para que serve."),
    ("Compre no Mercado Livre",
     "O botão abre o anúncio da Devboot no ML. Preço, pagamento e entrega ficam por lá."),
)


def pagina_inicial(c):
    l = c.loja
    dest = [p for p in c.todos if p.get("destaque") and p["status"] == "ativo"][:MAX_DESTAQUES]
    sec_dest = ""
    if dest:
        sec_dest = (f'<section class="group" aria-labelledby="h-dest"><div class="ghead"><h2 id="h-dest">Destaques</h2>'
                    f'<span>{plural(len(dest), "produto", "produtos")}</span></div><ul class="items">'
                    + "".join(item(c, p) for p in dest) + "</ul></section>")
    passos = "".join(
        f'<li class="step"><b>PASSO {i}</b><h3>{e(t)}</h3><p>{e(d)}</p></li>'
        for i, (t, d) in enumerate(PASSOS, 1))
    passos += (f'<li class="step"><b>PASSO 3</b><h3>Precisa instalar?</h3>'
               f'<p>Chame no WhatsApp. Instalamos em {e(l["instalacao"])}.</p></li>')
    corpo = f"""<div class="wrap gut page">
<div class="stack"><span class="eyebrow">Loja Devboot</span>
<h1 class="h1">Equipamento que a gente instala.<span class="snd">Compra segura no Mercado Livre.</span></h1>
<p class="lede">Câmeras, gravadores e controle de acesso escolhidos por quem projeta e instala segurança no sertão. Você compra no Mercado Livre; se quiser, a instalação é com a gente.</p>
<p class="model">{e(l["revenda"])} · Instalamos em {e(l["instalacao"])}</p></div>
{lista_de_linhas(c)}
{sec_dest}
<section class="stack" aria-labelledby="h-como"><h2 class="h2" id="h-como">Como a compra funciona</h2><ol class="steps">{passos}</ol></section>
<div class="band"><div class="stack g4"><h2>Precisa de um projeto completo?</h2><p class="lede">Calculamos a cobertura de cada câmera antes de instalar, com o CamSeek.</p></div>
<div class="cta"><a class="btn" href="{e(c.wa("Olá, vim pela loja da Devboot e quero um orçamento de projeto completo."))}" target="_blank" rel="noopener noreferrer">{icone("wa")}Pedir orçamento</a><a class="btn btn--ghost" href="{CAMSEEK}" target="_blank" rel="noopener noreferrer">Abrir o CamSeek <span aria-hidden="true">↗</span><span class="vh">(abre em nova aba)</span></a></div></div>
</div>"""
    return pagina(
        c, titulo="Loja Devboot: câmeras, gravadores e controle de acesso",
        descricao=f"Câmeras, gravadores e controle de acesso Intelbras. Compre no Mercado Livre; instalamos em {l['instalacao']}.",
        caminho="/loja/", corpo=corpo, atual="inicio",
        migalhas=[("Loja", "/loja/")])


def pagina_da_linha(c, slug):
    L, ps = c.linhas[slug], c.visiveis(slug)
    outra = next(s for s in c.linhas if s != slug) if len(c.linhas) > 1 else None
    topo = (f'<nav class="crumb" aria-label="Você está em"><a href="/loja/">Loja</a><span aria-hidden="true">/</span>'
            f'<span aria-current="page">{e(L["nome"])}</span></nav>'
            f'<div class="stack g75"><h1 class="h1 h1--md">{e(L["nome"])}</h1><p class="lede">{e(L["descricao"])}</p></div>')
    outra_html = f'<ul class="lines">{tile_da_linha(c, outra)}</ul>' if outra and c.visiveis(outra) else ""
    if not ps:
        corpo = (f'<div class="empty"><span class="stamp stamp--dot">Chegando à vitrine</span>'
                 f'<h2>Os produtos desta linha ainda não estão na loja.</h2><p class="lede">{e(L["vazio"])}</p>'
                 f'<div class="cta"><a class="btn" href="{e(c.wa("Olá, vim pela loja da Devboot e procuro um equipamento de " + L["nome"].lower() + "."))}" '
                 f'target="_blank" rel="noopener noreferrer">{icone("wa")}Pedir orçamento no WhatsApp</a></div></div>' + outra_html)
    else:
        grupos = []
        for t in L["tipos"]:
            g = [p for p in ps if p["tipo"] == t]
            g.sort(key=lambda p: p["status"] == "pausado")  # stable: paused last, owner's order otherwise
            if g:
                grupos.append((t, g))
        chips = ""
        if len(grupos) > 1:
            chips = ('<div class="chips" role="group" aria-label="Ir para o grupo">'
                     + "".join(f'<a class="chip" href="#g-{slugify(t)}">{e(t[:1].upper() + t[1:])}<b>{len(g)}</b></a>'
                               for t, g in grupos) + "</div>")
        blocos = "".join(
            f'<section class="group" id="g-{slugify(t)}" aria-labelledby="gh-{slugify(t)}"><div class="ghead">'
            f'<h2 id="gh-{slugify(t)}">{e(t)}</h2><span>{len(g)}</span></div><ul class="items">'
            + "".join(item(c, p) for p in g) + "</ul></section>" for t, g in grupos)
        mais = (f'<div class="band"><div class="stack g4"><h2>Não achou o que precisa?</h2>'
                f'<p class="lede">Trabalhamos com outros modelos sob encomenda.</p></div><div class="cta">'
                f'<a class="btn btn--ghost" href="{e(c.wa("Olá, vim pela loja da Devboot e procuro um equipamento de " + L["nome"].lower() + "."))}" '
                f'target="_blank" rel="noopener noreferrer">{icone("wa")}Perguntar no WhatsApp</a></div></div>')
        corpo = chips + blocos + mais + outra_html
    return pagina(
        c, titulo=f'{L["nome"]} | Loja Devboot', descricao=L["descricao"], caminho=f"/loja/{slug}/",
        corpo=f'<div class="wrap gut page">{topo}{corpo}</div>', atual="linha", noindex=not ps,
        migalhas=[("Loja", "/loja/"), (L["nome"], f"/loja/{slug}/")])


def texto_whatsapp(c, p):
    n = c.rotulo(p)
    if p["status"] == "pausado":
        return f"Olá, vi o {n} no site da Devboot. O anúncio está pausado: tem previsão ou um equivalente?"
    if p["status"] == "encerrado":
        return f"Olá, vi o {n} no site da Devboot, mas saiu de linha. Podem me indicar um similar?"
    return f"Olá, vi o {n} no site da Devboot e quero um orçamento."


def pagina_do_produto(c, p):
    L, l = c.linhas[p["linha"]], c.loja
    wa = e(c.wa(texto_whatsapp(c, p)))
    n = len(p.get("fotos", []))
    if not n:
        gal = f'<div class="galwrap">{ph(c, p, p["pictograma"], 0, True)}</div>'
    else:
        slides = "".join(
            ph(c, p, p["pictograma"], i, False, eager=(i == 0), i=i).replace(
                '<div class="ph"', f'<div class="ph" role="group" aria-label="Foto {i + 1} de {n}"', 1)
            for i in range(n))
        miniaturas = "".join(
            f'<button type="button" data-shot="{i}" aria-label="Ver foto {i + 1} de {n}"'
            + (' aria-current="true"' if i == 0 else "") + f'>{ph(c, p, p["pictograma"], i, False, i=i)}</button>'
            for i in range(n))
        gal = (f'<div class="galwrap"><div class="gal" id="gal" tabindex="0" role="region" '
               f'aria-label="Fotos de {e(p["nome"])}">{slides}</div>'
               + (f'<span class="count" id="count" aria-hidden="true">1 / {n}</span>' if n > 1 else "")
               + "</div>" + (f'<div class="thumbs">{miniaturas}</div>' if n > 1 else ""))
    zap = f'{icone("wa")}'
    sticky, flag = "", ""
    if p["status"] == "ativo":
        ml = e(p["link_ml"])
        cta = (f'<div class="cta" id="ctaMain"><a class="btn" href="{ml}" target="_blank" rel="noopener noreferrer">'
               f'Ver no Mercado Livre <span aria-hidden="true">↗</span><span class="vh">(abre o Mercado Livre em nova aba)</span></a>'
               f'<a class="btn btn--ghost" href="{wa}" target="_blank" rel="noopener noreferrer">{zap}Pedir orçamento no WhatsApp</a></div>'
               f'<p class="seller"><span>Vendido por <a href="{e(l["perfil_ml"])}" target="_blank" rel="noopener noreferrer">{e(l["vendedor_ml"])}</a> no Mercado Livre.</span>'
               f'<span>Preço, pagamento e entrega ficam no anúncio.</span><span>{e(l["revenda"])}.</span></p>')
        sticky = (f'<div class="sticky" id="sticky" hidden><a class="btn" href="{ml}" target="_blank" rel="noopener noreferrer">'
                  f'Ver no Mercado Livre <span aria-hidden="true">↗</span><span class="vh">(abre o Mercado Livre em nova aba)</span></a>'
                  f'<a class="btn btn--ghost" href="{wa}" target="_blank" rel="noopener noreferrer" '
                  f'aria-label="Pedir orçamento no WhatsApp">{zap}WhatsApp</a></div>')
    elif p["status"] == "pausado":
        flag = '<span class="stamp stamp--dot">Indisponível no Mercado Livre no momento</span>'
        cta = ('<div class="note"><b>Anúncio pausado</b><span>Pergunte no WhatsApp: confirmamos o prazo ou indicamos um equivalente.</span></div>'
               f'<div class="cta"><a class="btn" href="{wa}" target="_blank" rel="noopener noreferrer">{zap}Perguntar no WhatsApp</a></div>')
    else:
        flag = '<span class="stamp">Saiu de linha</span>'
        cta = ('<div class="note"><b>Este produto não é mais vendido</b><span>Veja os similares abaixo ou peça uma indicação.</span></div>'
               f'<div class="cta"><a class="btn btn--ghost" href="{wa}" target="_blank" rel="noopener noreferrer">{zap}Pedir indicação no WhatsApp</a></div>')

    pool = [x for x in c.visiveis(p["linha"]) if x["slug"] != p["slug"]]
    ativos = [x for x in pool if x["status"] == "ativo"]
    mesmo_tipo = [x for x in pool if x["tipo"] == p["tipo"]]
    rel = ativos if p["status"] == "encerrado" else mesmo_tipo
    if not rel:
        rel = ativos
    rel = rel[:4]
    if p["status"] == "encerrado":
        titulo_rel = "Similares à venda"
    else:
        titulo_rel = f'Mais {p["tipo"]}' if mesmo_tipo else f'Mais em {L["nome"]}'
    rel_html = (f'<section class="group" aria-labelledby="h-rel"><div class="ghead"><h2 id="h-rel">{e(titulo_rel)}</h2></div>'
                f'<ul class="items">{"".join(item(c, x) for x in rel)}</ul></section>' if rel else "")
    specs = ('<section class="stack g5" aria-labelledby="h-ficha"><h2 class="label" id="h-ficha">Ficha técnica</h2><dl class="specs">'
             + "".join(f'<div class="spec"><dt>{e(r)}</dt><dd>{e(v)}</dd></div>' for r, v in p["specs"]) + "</dl></section>")
    instalar = (f'<div class="note"><b>Precisa instalar?</b><span>Instalamos em {e(l["instalacao"])}. Chame no WhatsApp.</span></div>'
                if p["status"] == "ativo" else "")
    info = (f'<div class="info">{flag}<div class="stack g4"><h1 class="h1">{e(p["nome"])}</h1>'
            f'<span class="model">{e(c.modelo(p))}</span></div><p class="lede">{e(p["resumo"])}</p>{cta}'
            + (rel_html if p["status"] == "encerrado" else "")
            + '<ul class="checks">' + "".join(f"<li>{e(b)}</li>" for b in p["beneficios"]) + "</ul>"
            + specs + instalar + "</div>")
    corpo = (f'<div class="wrap gut page"><nav class="crumb" aria-label="Você está em"><a href="/loja/">Loja</a>'
             f'<span aria-hidden="true">/</span><a href="/loja/{p["linha"]}/">{e(L["nome"])}</a></nav>'
             f'<div class="pdp"><div class="galcol">{gal}</div>{info}</div>'
             + ("" if p["status"] == "encerrado" else rel_html) + "</div>")
    return pagina(
        c, titulo=f'{p["nome"]} {c.modelo(p)} | Loja Devboot', descricao=p["resumo"],
        caminho=f'/loja/{p["slug"]}/', corpo=corpo, atual="produto", noindex=p["status"] == "encerrado",
        og=c.og_imagem(p), depois_do_rodape=sticky,
        migalhas=[("Loja", "/loja/"), (L["nome"], f'/loja/{p["linha"]}/'), (p["nome"], f'/loja/{p["slug"]}/')])


def pagina_404(c):
    base = c.wa("")  # ".../?text=" : the script appends the address that failed
    texto = "Olá, tentei abrir uma página da loja no site da Devboot e não encontrei."
    corpo = f"""<div class="wrap gut page"><div class="stack"><span class="eyebrow">404 · produto não encontrado</span>
<h1 class="h1 h1--md">Esse produto não está na vitrine.</h1>
<p class="lede">O endereço pode ter mudado, ou o produto saiu da loja. Veja as linhas abaixo ou pergunte direto.</p></div>
{lista_de_linhas(c)}
<div class="cta cta--narrow"><a class="btn btn--ghost" id="wa404" data-wa-base="{e(base)}" href="{e(c.wa(texto))}" target="_blank" rel="noopener noreferrer">{icone("wa")}Procurando um modelo? Pergunte</a></div>
<p><a class="go go--lone" href="/loja/">Ir para o início da loja</a></p></div>"""
    return pagina(c, titulo="Produto não encontrado | Loja Devboot",
                  descricao="Esse endereço não está na vitrine da Devboot. Veja as linhas da loja ou pergunte no WhatsApp.",
                  caminho="/loja/404.html", corpo=corpo, atual="404", noindex=True, canonical=False)


def sitemap(c):
    urls = ["/loja/"] + [f"/loja/{s}/" for s in c.linhas if c.visiveis(s)] \
        + [f'/loja/{p["slug"]}/' for p in c.todos if p["status"] != "encerrado"]
    corpo = "".join(f"<url><loc>{e(c.site + u)}</loc></url>\n" for u in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + corpo + "</urlset>\n")


def renderizar(dados, tokens, estaticos, pasta_fotos):
    """The whole shop as {path under public/loja/: bytes}. Pure: the same input, the same bytes."""
    erros = validar(dados, pasta_fotos)
    if erros:
        raise ErroDeDados(erros)
    estaticos = Path(estaticos)
    css = (estaticos / "loja.css").read_text(encoding="utf-8").replace("/*TOKENS*/", bloco_tokens(tokens))
    css, js = css.encode("utf-8"), (estaticos / "loja.js").read_bytes()
    c = Contexto(dados, estaticos, css, js)
    f = {"index.html": pagina_inicial(c), "404.html": pagina_404(c), "sitemap.xml": sitemap(c)}
    for s in c.linhas:
        f[f"{s}/index.html"] = pagina_da_linha(c, s)
    for p in c.todos:
        f[f'{p["slug"]}/index.html'] = pagina_do_produto(c, p)
    out = {k: v.encode("utf-8") for k, v in f.items()}
    out["loja.css"], out["loja.js"] = css, js
    out["sprite.svg"] = (estaticos / "sprite.svg").read_bytes()
    return out


# ------------------------------------------------------------------------------------- CLI

class _Texto(HTMLParser):
    BLOCOS = {"p", "div", "li", "h1", "h2", "h3", "section", "header", "footer", "nav", "span", "dt", "dd",
              "a", "button", "b", "ol", "ul", "dl", "main"}

    def __init__(self):
        super().__init__()
        self.partes, self.pula = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "svg"):
            self.pula += 1
        elif tag == "dd":
            self.partes.append(" : ")
        elif tag in ("h1", "h2", "h3", "li", "p", "div", "section", "dt", "span", "a", "b", "button"):
            self.partes.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg"):
            self.pula -= 1

    def handle_data(self, d):
        if not self.pula:
            self.partes.append(d)


def texto_para_revisao(arquivos):
    """Every visitor-facing line, page by page, for the owner to read before merge."""
    saida = ["# Loja: texto de todas as páginas", "",
             "Gerado por `loja/gerar.py --texto`. Para o dono revisar; não é fonte, não edite.", ""]
    for k in sorted(arquivos, key=lambda k: (k != "index.html", k)):
        if not k.endswith(".html"):
            continue
        h = arquivos[k].decode("utf-8")
        titulo = re.search(r"<title>(.*?)</title>", h, re.S).group(1)
        desc = re.search(r'<meta name="description" content="(.*?)">', h, re.S).group(1)
        corpo = h[h.index("<main"):h.index("</main>")]
        p = _Texto()
        p.feed(corpo)
        linhas = [" ".join(x.split()) for x in "".join(p.partes).split("\n")]
        linhas = [x for x in linhas if x not in ("↗", "→")]
        saida += [f"## /loja/{k[:-len('index.html')] if k.endswith('index.html') else k}",
                  f"- Título: {_html.unescape(titulo)}", f"- Descrição (Google): {_html.unescape(desc)}", "",
                  *[f"- {_html.unescape(x)}" for x in linhas if x], ""]
    return "\n".join(saida)


def escrever(saida, arquivos):
    """Write the generated files and delete generated files that are no longer produced.
    img/ (the photos) is never touched."""
    saida = Path(saida)
    for k, v in arquivos.items():
        alvo = saida / k
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_bytes(v)
    for arq in sorted(saida.rglob("*"), reverse=True):
        rel = arq.relative_to(saida).as_posix()
        if rel == "img" or rel.startswith("img/"):
            continue
        if arq.is_file() and rel not in arquivos:
            arq.unlink()
        elif arq.is_dir() and not any(arq.iterdir()):
            arq.rmdir()


def carregar(raiz=RAIZ):
    dados = json.loads((raiz / "loja" / "produtos.json").read_text(encoding="utf-8"))
    tokens = json.loads((raiz / "design" / "tokens.json").read_text(encoding="utf-8"))
    return dados, tokens


def main(argv):
    dados, tokens = carregar()
    saida = RAIZ / "public" / "loja"
    try:
        arquivos = renderizar(dados, tokens, RAIZ / "loja" / "static", saida / "img")
    except ErroDeDados as ex:
        print(f"produtos.json refused ({len(ex.erros)} problem(s)):", file=sys.stderr)
        for m in ex.erros:
            print(f"  - {m}", file=sys.stderr)
        return 1
    if "--texto" in argv:
        print(texto_para_revisao(arquivos))
        return 0
    escrever(saida, arquivos)
    print(f"{len(arquivos)} files written to {saida.relative_to(RAIZ)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
def fotos_nomeadas(dados):
    """Every photo the data names, as paths under public/loja/ (fotos and og)."""
    nomes = set()
    for p in dados["produtos"]:
        for f in p.get("fotos", []):
            nomes.add(f"img/{p['slug']}/{f['arquivo']}")
        if p.get("og"):
            nomes.add(f"img/{p['slug']}/{p['og']}")
    return nomes


def arquivos_estranhos(saida, gerados, dados):
    """Files in public/loja/ that nothing explains: not generated, and not a photo the data names.
    The photo folders are not exempt: anything else under img/ (a page, an unlisted file, a folder
    of an unknown slug) would be served from the shop's own address."""
    esperados = set(gerados) | fotos_nomeadas(dados)
    saida = Path(saida)
    existentes = {a.relative_to(saida).as_posix() for a in saida.rglob("*") if a.is_file()}
    return sorted(existentes - esperados)


    estranhos = arquivos_estranhos(saida, arquivos, dados)
    if estranhos:
        print("files under public/loja/ that nothing explains (not generated, not a listed photo):",
              file=sys.stderr)
        for a in estranhos:
            print(f"  - {a}", file=sys.stderr)
        return 1
