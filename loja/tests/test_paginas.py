"""What the generated pages say, branch by branch (docs/loja-flow.md)."""
import json
import tempfile
import unittest
from pathlib import Path

import gerar
from tests.dados import ML, dados, produto
from tests.pagina import Pagina

RAIZ = Path(__file__).resolve().parents[2]
TOKENS = json.loads((RAIZ / "design" / "tokens.json").read_text())
ESTATICOS = Path(__file__).resolve().parents[1] / "static"
SITE = "https://www.devboot.com.br"


def gerar_paginas(d, fotos=None):
    fotos = fotos or Path(tempfile.mkdtemp())
    return gerar.renderizar(d, TOKENS, ESTATICOS, fotos)


def pg(arquivos, caminho):
    return Pagina(arquivos[caminho].decode("utf-8"))


def cat(slug, **o):
    return produto(slug, **o)


def acesso(slug, **o):
    return produto(slug, linha="controle-de-acesso", tipo="controladores faciais", pictograma="face", **o)


class TodasAsPaginas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = gerar_paginas(dados(
            cat("camera-um", destaque=True), cat("camera-dois", status="pausado"),
            cat("camera-tres", status="encerrado", tipo="kits"), acesso("controlador-um")))
        cls.html = sorted(k for k in cls.f if k.endswith(".html"))

    def test_the_expected_files_are_generated(self):
        self.assertEqual(sorted(self.f), sorted([
            "index.html", "404.html", "cameras-e-gravadores/index.html", "controle-de-acesso/index.html",
            "camera-um/index.html", "camera-dois/index.html", "camera-tres/index.html",
            "controlador-um/index.html", "loja.css", "loja.js", "sprite.svg", "sitemap.xml"]))

    def test_every_page_is_well_formed(self):
        for k in self.html:
            with self.subTest(page=k):
                p = pg(self.f, k)
                self.assertEqual(p.problemas, [])
                self.assertTrue(p.doctype)
                self.assertEqual(p.html_attrs.get("lang"), "pt-BR")
                self.assertEqual(len(p.ids), len(set(p.ids)), "duplicate ids")
                self.assertEqual(p.visivel.count("<"), 0)

    def test_every_page_has_title_description_and_open_graph(self):
        for k in self.html:
            with self.subTest(page=k):
                p = pg(self.f, k)
                self.assertTrue(p.titulo)
                self.assertTrue(p.meta.get("description"))
                self.assertLessEqual(len(p.meta["description"]), 160)
                for og in ("og:title", "og:description", "og:image", "og:type", "og:locale", "og:site_name"):
                    self.assertTrue(p.meta.get(og), og)
                self.assertTrue(p.meta["og:image"].startswith(SITE + "/"))
                self.assertEqual(p.meta.get("twitter:card"), "summary_large_image")
                self.assertEqual(p.meta.get("viewport"), "width=device-width, initial-scale=1, viewport-fit=cover")
                self.assertEqual(p.meta.get("theme-color"), "#0a0d12")

    def test_indexable_pages_have_an_absolute_canonical_equal_to_og_url(self):
        for k in self.html:
            if k == "404.html":
                continue
            with self.subTest(page=k):
                p = pg(self.f, k)
                canon = [a["href"] for t, a in p.links if t == "link" and a.get("rel") == "canonical"]
                self.assertEqual(len(canon), 1)
                self.assertTrue(canon[0].startswith(SITE + "/loja/") and canon[0].endswith("/"))
                self.assertEqual(canon[0], p.meta["og:url"])

    def test_breadcrumb_json_ld_on_every_page_but_the_404(self):
        for k in self.html:
            with self.subTest(page=k):
                p = pg(self.f, k)
                bc = [x for x in p.jsonld if x.get("@type") == "BreadcrumbList"]
                if k == "404.html":
                    self.assertEqual(bc, [])
                    continue
                self.assertEqual(len(bc), 1)
                itens = bc[0]["itemListElement"]
                self.assertEqual([i["position"] for i in itens], list(range(1, len(itens) + 1)))
                self.assertEqual(itens[0]["item"], SITE + "/loja/")
                for i in itens[:-1]:
                    self.assertTrue(i["item"].startswith(SITE + "/loja/"))

    def test_breadcrumb_depth_follows_the_page(self):
        n = lambda k: len([x for x in pg(self.f, k).jsonld if x["@type"] == "BreadcrumbList"][0]["itemListElement"])
        self.assertEqual(n("index.html"), 1)
        self.assertEqual(n("cameras-e-gravadores/index.html"), 2)
        self.assertEqual(n("camera-um/index.html"), 3)

    def test_noindex_exactly_where_the_flow_map_says(self):
        noindex = {k for k in self.html if "noindex" in pg(self.f, k).meta.get("robots", "")}
        # the 404 and the ended product; the access line has a product so it is indexable
        self.assertEqual(noindex, {"404.html", "camera-tres/index.html"})

    def test_theme_script_runs_before_the_stylesheet_and_guards_storage(self):
        for k in self.html:
            with self.subTest(page=k):
                p = pg(self.f, k)
                kinds = [o[0] for o in p.ordem]
                self.assertLess(kinds.index("script"), kinds.index("stylesheet"))
                js = [o[1] for o in p.ordem if o[0] == "script"][0]
                for trecho in ("try", "catch", "devboot-tema", "escuro", "data-tema", "classList.add('js')"):
                    self.assertIn(trecho, js)
                self.assertNotIn("prefers-color-scheme", js)
                self.assertNotIn("data-tema", p.html_attrs)

    def test_the_stylesheet_never_follows_the_phone_colour_scheme(self):
        self.assertNotIn("prefers-color-scheme", self.f["loja.css"].decode())

    def test_no_page_shows_a_price(self):
        for k, v in self.f.items():
            with self.subTest(file=k):
                self.assertNotIn("R$", v.decode("utf-8"))

    def test_internal_links_resolve(self):
        for k in self.html:
            p = pg(self.f, k)
            ids = set(p.ids)
            for tag, a in p.links:
                ref = a.get("href") or a.get("src")
                if not ref or ref.startswith(("http", "mailto:", "tel:", "javascript:")):
                    continue
                with self.subTest(page=k, ref=ref):
                    if ref.startswith("#"):
                        self.assertIn(ref[1:], ids)
                    elif ref.startswith("/loja/"):
                        alvo = ref[len("/loja/"):].split("#")[0].split("?")[0]
                        arq = alvo + "index.html" if alvo.endswith("/") or alvo == "" else alvo
                        self.assertIn(arq, self.f)
                    elif ref.startswith("/img/"):
                        self.assertTrue((RAIZ / "public" / ref.lstrip("/")).is_file())
                    else:
                        self.assertTrue(ref.startswith(("/#", "/blog/")), ref)

    def test_stylesheet_and_script_are_the_generated_files(self):
        for k in self.html:
            p = pg(self.f, k)
            self.assertIn("/loja/loja.css", [h.split("?")[0] for h in p.hrefs("link")])
            self.assertIn("/loja/loja.js", [a["src"].split("?")[0] for t, a in p.links if t == "script" and a.get("src")])

    def test_generation_is_deterministic(self):
        again = gerar_paginas(dados(
            cat("camera-um", destaque=True), cat("camera-dois", status="pausado"),
            cat("camera-tres", status="encerrado", tipo="kits"), acesso("controlador-um")))
        self.assertEqual(self.f, again)

    def test_the_nav_has_loja_between_cameras_and_blog_and_marks_it_current(self):
        p = pg(self.f, "index.html")
        nav = [(a.get("href"), a.get("aria-current")) for t, a in p.links
               if t == "a" and "nlink" in (a.get("class") or "").split()]
        self.assertEqual([h for h, _ in nav], ["/#desenvolvimento", "/#produtos", "/#cftv", "/loja/", "/blog/", "/#contato"])
        self.assertEqual([h for h, c in nav if c == "page"], ["/loja/"])

    def test_the_brand_is_the_landings_own_markup(self):
        landing = (RAIZ / "public" / "index.html").read_text(encoding="utf-8")
        import re
        paths = re.findall(r'<path fill="#(?:d1d5db|e10600)" d="([^"]+)"', landing)[:4]
        page = self.f["index.html"].decode()
        for d in paths:
            self.assertIn(d, page)
        self.assertNotIn('<use href="#brand', page)
        self.assertIn('viewBox="75 221 874 583"', page)
        self.assertIn('viewBox="123 556 1007 115"', page)


class Inicio(unittest.TestCase):
    def test_lines_destaques_and_steps(self):
        f = gerar_paginas(dados(
            cat("camera-um", destaque=True), cat("camera-dois", destaque=True, status="pausado"),
            cat("camera-tres", destaque=True, status="encerrado"), acesso("controlador-um", destaque=True)))
        p = pg(f, "index.html")
        t = p.visivel
        self.assertIn("Câmeras e gravadores", t)
        self.assertIn("Controle de acesso", t)
        self.assertIn("Destaques", t)
        dest = [h for h in p.hrefs() if h.startswith("/loja/") and h.count("/") == 3
                and h not in ("/loja/cameras-e-gravadores/", "/loja/controle-de-acesso/")]
        # only active, featured products: the paused and the ended one stay out
        self.assertEqual(sorted(dest), ["/loja/camera-um/", "/loja/controlador-um/"])
        self.assertIn("Como a compra funciona", t)
        self.assertIn("Revenda autorizada Intelbras", t)
        self.assertIn("Petrolina, Juazeiro, Dormentes e região", t)

    def test_no_featured_product_omits_the_section(self):
        f = gerar_paginas(dados(cat("camera-um"), acesso("controlador-um")))
        self.assertNotIn("Destaques", pg(f, "index.html").visivel)

    def test_line_with_no_product_stays_with_a_coming_soon_stamp_and_no_count(self):
        f = gerar_paginas(dados(cat("camera-um", destaque=True)))
        t = pg(f, "index.html").visivel
        self.assertIn("Chegando à vitrine", t)
        self.assertIn("Pedir orçamento", t)

    def test_featured_come_only_from_lines_that_have_products(self):
        f = gerar_paginas(dados(cat("camera-um", destaque=True)))
        self.assertIn("/loja/camera-um/", pg(f, "index.html").hrefs())

    def test_ended_products_do_not_count_toward_a_line(self):
        f = gerar_paginas(dados(cat("camera-um"), acesso("controlador-um", status="encerrado")))
        p = pg(f, "index.html")
        self.assertIn("Chegando à vitrine", p.visivel)  # access line is empty once the ended one is out
        self.assertIn("1 produto", p.visivel)


class Categoria(unittest.TestCase):
    def test_groups_chips_anchor_to_groups_and_paused_goes_last(self):
        f = gerar_paginas(dados(
            cat("camera-pausada", status="pausado", nome="Câmera pausada"),
            cat("camera-ativa", nome="Câmera ativa"),
            cat("camera-saiu", status="encerrado", nome="Câmera que saiu"),
            cat("gravador-um", tipo="gravadores", nome="Gravador um"), acesso("controlador-um")))
        p = pg(f, "cameras-e-gravadores/index.html")
        chips = [a["href"] for t, a in p.links if t == "a" and "chip" in (a.get("class") or "").split()]
        self.assertEqual(chips, ["#g-cameras", "#g-gravadores"])
        for c in chips:
            self.assertIn(c[1:], p.ids)
        t = p.visivel
        self.assertLess(t.index("Câmera ativa"), t.index("Câmera pausada"))
        self.assertIn("Sob consulta", t)
        self.assertNotIn("Câmera que saiu", t)
        self.assertNotIn("/loja/camera-saiu/", p.hrefs())
        self.assertNotIn("noindex", p.meta.get("robots", ""))

    def test_a_single_group_has_no_chips(self):
        f = gerar_paginas(dados(cat("camera-um"), acesso("controlador-um")))
        p = pg(f, "cameras-e-gravadores/index.html")
        self.assertNotIn("chip", p.classes)

    def test_empty_line_explains_offers_quote_links_the_other_line_and_is_noindex(self):
        f = gerar_paginas(dados(cat("camera-um")))
        p = pg(f, "controle-de-acesso/index.html")
        self.assertIn("noindex", p.meta["robots"])
        t = p.visivel
        self.assertIn("Chegando à vitrine", t)
        self.assertIn("Texto da linha vazia de acesso.", t)
        self.assertTrue(any(h.startswith("https://wa.me/5587991402037?text=") for h in p.hrefs()))
        self.assertIn("/loja/cameras-e-gravadores/", p.hrefs())
        self.assertNotIn("Nenhum resultado", t)

    def test_long_names_are_never_truncated_in_the_markup(self):
        nome = "Câmera " + "x" * 33
        f = gerar_paginas(dados(cat("camera-um", nome=nome), acesso("controlador-um")))
        self.assertIn(nome, pg(f, "cameras-e-gravadores/index.html").visivel)


class Produto(unittest.TestCase):
    def pagina(self, p, *outros, **kw):
        f = gerar_paginas(dados(p, *outros, acesso("controlador-um")), **kw)
        return pg(f, f"{p['slug']}/index.html"), f

    def test_active_has_ml_primary_whatsapp_secondary_and_the_seller(self):
        p, _ = self.pagina(cat("camera-um"))
        ml = [a for t, a in p.links if t == "a" and a.get("href") == ML]
        self.assertGreaterEqual(len(ml), 1)
        for a in ml:
            self.assertEqual(a.get("target"), "_blank")
            self.assertIn("noopener", a.get("rel"))
        t = p.visivel
        self.assertIn("Ver no Mercado Livre", t)
        self.assertIn("Pedir orçamento no WhatsApp", t)
        self.assertIn("Vendido por VENDEDOR_TESTE no Mercado Livre", t)
        self.assertIn("Preço, pagamento e entrega ficam no anúncio", t)
        self.assertIn("Revenda autorizada Intelbras", t)
        self.assertIn("Precisa instalar?", t)
        self.assertIn("Petrolina, Juazeiro, Dormentes e região", t)
        self.assertIn("https://perfil.mercadolivre.com.br/VENDEDOR_TESTE", p.hrefs())

    def test_the_whatsapp_link_carries_the_product(self):
        p, _ = self.pagina(cat("camera-um"))
        from urllib.parse import parse_qs, urlparse
        textos = [parse_qs(urlparse(h).query)["text"][0] for h in p.hrefs()
                  if h.startswith("https://wa.me/5587991402037?text=")]
        do_produto = [t for t in textos if "Câmera de teste camera-um" in t]
        self.assertTrue(do_produto, textos)
        self.assertIn("T-100", do_produto[0])
        self.assertIn("quero um orçamento", do_produto[0])

    def test_the_sticky_bar_exists_only_for_active_products_and_starts_hidden(self):
        p, _ = self.pagina(cat("camera-um"))
        self.assertIn("sticky", p.classes)
        self.assertIn("sticky", p.ids)
        for st in ("pausado", "encerrado"):
            p2, _ = self.pagina(cat("camera-um", status=st))
            self.assertNotIn("sticky", p2.classes)

    def test_paused_has_no_ml_button_at_all_a_stamp_and_whatsapp_as_primary(self):
        p, f = self.pagina(cat("camera-um", status="pausado"))
        self.assertNotIn("mercadolivre", f["camera-um/index.html"].decode())
        t = p.visivel
        self.assertIn("Indisponível no Mercado Livre no momento", t)
        self.assertIn("Perguntar no WhatsApp", t)
        self.assertNotIn("Ver no Mercado Livre", t)
        self.assertNotIn("Vendido por", t)
        self.assertNotIn("noindex", p.meta.get("robots", ""))

    def test_ended_says_so_puts_similars_before_the_spec_sheet_and_is_noindex(self):
        p, _ = self.pagina(cat("camera-um", status="encerrado"), cat("camera-dois", nome="Outra câmera"))
        t = p.visivel
        self.assertIn("Saiu de linha", t)
        self.assertIn("Similares à venda", t)
        self.assertLess(t.index("Similares à venda"), t.index("Ficha técnica"))
        self.assertIn("/loja/camera-dois/", p.hrefs())
        self.assertNotIn("Ver no Mercado Livre", t)
        self.assertIn("noindex", p.meta["robots"])

    def test_ended_page_with_no_similar_still_offers_whatsapp(self):
        f = gerar_paginas(dados(cat("camera-um", status="encerrado")))
        p = pg(f, "camera-um/index.html")
        self.assertNotIn("Similares à venda", p.visivel)
        self.assertTrue(any(h.startswith("https://wa.me/") for h in p.hrefs()))

    def test_related_products_prefer_the_same_type_and_never_list_the_product_itself(self):
        p, _ = self.pagina(cat("camera-um"), cat("camera-dois"), cat("gravador-um", tipo="gravadores"))
        h = p.hrefs()
        self.assertIn("/loja/camera-dois/", h)
        self.assertEqual(h.count("/loja/camera-um/"), 0)
        self.assertNotIn("/loja/gravador-um/", h)

    def test_no_photo_draws_the_pictogram_and_says_it_is_illustrative(self):
        p, f = self.pagina(cat("camera-um"))
        self.assertIn("Imagem ilustrativa", p.visivel)
        self.assertEqual(p.meta["og:image"], SITE + "/img/devboot-share-light-1200x630.png")
        self.assertNotIn("count", p.ids)
        self.assertEqual([a for t, a in p.links if t == "img"], [])

    def test_one_photo_has_no_counter_and_is_the_og_image(self):
        fotos = Path(tempfile.mkdtemp())
        (fotos / "camera-um").mkdir()
        (fotos / "camera-um" / "1.webp").write_bytes(b"x")
        (fotos / "camera-um" / "og.jpg").write_bytes(b"x")
        d = dados(cat("camera-um", fotos=[{"arquivo": "1.webp", "fonte": "https://www.intelbras.com/a"}],
                      og="og.jpg"), acesso("controlador-um"))
        f = gerar_paginas(d, fotos)
        p = pg(f, "camera-um/index.html")
        self.assertNotIn("count", p.ids)
        self.assertNotIn("Imagem ilustrativa", p.visivel)
        imgs = [a for t, a in p.links if t == "img"]
        self.assertTrue(imgs)
        self.assertEqual(imgs[0]["src"], "/loja/img/camera-um/1.webp")
        self.assertTrue(imgs[0].get("alt"))
        self.assertTrue(imgs[0].get("width") and imgs[0].get("height"))
        self.assertEqual(p.meta["og:image"], SITE + "/loja/img/camera-um/og.jpg")

    def test_several_photos_have_counter_and_first_is_og_when_no_og_given(self):
        fotos = Path(tempfile.mkdtemp())
        (fotos / "camera-um").mkdir()
        fs = []
        for i in (1, 2, 3):
            (fotos / "camera-um" / f"{i}.webp").write_bytes(b"x")
            fs.append({"arquivo": f"{i}.webp", "fonte": "https://www.intelbras.com/a"})
        f = gerar_paginas(dados(cat("camera-um", fotos=fs), acesso("controlador-um")), fotos)
        p = pg(f, "camera-um/index.html")
        self.assertIn("count", p.ids)
        self.assertIn("1 / 3", p.visivel)
        self.assertEqual(p.meta["og:image"], SITE + "/loja/img/camera-um/1.webp")

    def test_benefits_and_every_spec_row_are_rendered(self):
        p, _ = self.pagina(cat("camera-um"))
        t = p.visivel
        for x in ("Primeiro benefício", "Segundo benefício", "Terceiro benefício", "Resolução", "2 MP",
                  "Lente", "2,8 mm", "Proteção", "IP67"):
            self.assertIn(x, t)
        self.assertIn("Intelbras T-100", t)

    def test_title_names_the_product_the_brand_and_the_model(self):
        p, _ = self.pagina(cat("camera-um"))
        self.assertEqual(p.titulo, "Câmera de teste camera-um Intelbras T-100 | Loja Devboot")
        self.assertEqual(p.meta["description"], "Resumo curto do produto de teste.")

    def test_text_from_data_is_escaped(self):
        p, f = self.pagina(cat("camera-um", nome="A <b>&\"'", resumo="<script>alert(1)</script>"))
        self.assertNotIn("<script>alert(1)</script>", f["camera-um/index.html"].decode())
        self.assertIn("A <b>&\"'", p.visivel)


class NaoEncontrado(unittest.TestCase):
    def test_the_404_page_says_what_happened_and_offers_both_lines_and_whatsapp(self):
        f = gerar_paginas(dados())
        p = pg(f, "404.html")
        t = p.visivel
        self.assertIn("Esse produto não está na vitrine", t)
        self.assertIn("/loja/cameras-e-gravadores/", p.hrefs())
        self.assertIn("/loja/controle-de-acesso/", p.hrefs())
        self.assertIn("/loja/", p.hrefs())
        self.assertTrue(any(h.startswith("https://wa.me/5587991402037?text=") for h in p.hrefs()))
        self.assertIn("noindex", p.meta["robots"])

    def test_the_404_page_only_uses_absolute_paths_because_nginx_serves_it_at_any_url(self):
        f = gerar_paginas(dados())
        p = pg(f, "404.html")
        for tag, a in p.links:
            ref = a.get("href") or a.get("src")
            if ref and not ref.startswith(("http", "#")):
                self.assertTrue(ref.startswith("/"), ref)


class Sitemap(unittest.TestCase):
    def test_lists_only_indexable_pages(self):
        f = gerar_paginas(dados(
            cat("camera-um"), cat("camera-dois", status="pausado"), cat("camera-tres", status="encerrado")))
        xml = f["sitemap.xml"].decode()
        import re
        urls = sorted(re.findall(r"<loc>([^<]+)</loc>", xml))
        self.assertEqual(urls, sorted([
            SITE + "/loja/", SITE + "/loja/cameras-e-gravadores/",
            SITE + "/loja/camera-um/", SITE + "/loja/camera-dois/"]))
        # access line is empty: noindex, so out of the sitemap


class DadosInvalidos(unittest.TestCase):
    def test_rendering_refuses_invalid_data_instead_of_publishing_it(self):
        with self.assertRaises(gerar.ErroDeDados) as c:
            gerar_paginas(dados(cat("camera-um", link_ml="https://example.com/x")))
        self.assertIn("link_ml", str(c.exception))



class JsonLdNaoQuebraOScript(unittest.TestCase):
    """json.dumps does not escape `<`: a name containing </script> would end the JSON-LD block."""
    ATAQUE = "</script><img src=x onerror=alert(1)>"

    def paginas(self, d):
        return gerar_paginas(d)

    def confere(self, f, nome_esperado):
        for k, v in f.items():
            if not k.endswith(".html"):
                continue
            with self.subTest(page=k):
                texto = v.decode("utf-8")
                self.assertNotIn("</script><img", texto)
                p = Pagina(texto)
                self.assertEqual(p.problemas, [])
                self.assertFalse([a for t, a in p.links if t == "img" and "onerror" in a])
                for ld in p.jsonld:
                    for item in ld["itemListElement"]:
                        self.assertNotIn("<", item["name"].replace(self.ATAQUE, ""))
        return f

    def test_a_product_name_with_a_closing_script_tag(self):
        self.assertLessEqual(len(self.ATAQUE), 40)
        f = self.confere(self.paginas(dados(cat("camera-um", nome=self.ATAQUE), acesso("controlador-um"))), self.ATAQUE)
        nomes = [i["name"] for x in pg(f, "camera-um/index.html").jsonld for i in x["itemListElement"]]
        self.assertIn(self.ATAQUE, nomes)  # still the same name once the JSON is parsed

    def test_a_line_name_with_a_closing_script_tag(self):
        d = dados(cat("camera-um"), acesso("controlador-um"))
        d["linhas"]["cameras-e-gravadores"]["nome"] = self.ATAQUE
        f = self.confere(self.paginas(d), self.ATAQUE)
        nomes = [i["name"] for x in pg(f, "cameras-e-gravadores/index.html").jsonld for i in x["itemListElement"]]
        self.assertIn(self.ATAQUE, nomes)

    def test_angle_brackets_and_ampersands_leave_the_json_ld_as_escapes(self):
        f = self.paginas(dados(cat("camera-um", nome="A <b> & C"), acesso("controlador-um")))
        bloco = f["camera-um/index.html"].decode().split('application/ld+json">')[1].split("</script>")[0]
        for ch in "<>&":
            self.assertNotIn(ch, bloco)
        self.assertIn("\\u003c", bloco)


if __name__ == "__main__":
    unittest.main()
