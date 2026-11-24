"""Category tiles on the shop home carry a real photo of a product installed in a real setting.
Each test is one row of the branch table "Home category tile photo" in docs/loja-flow.md,
written before the code that satisfies it."""
import re
import struct
import unittest
from pathlib import Path

import gerar
from tests.dados import ambiente, dados, pasta_de_fotos, produto
from tests.pagina import Pagina
from tests.test_paginas import acesso, cat, gerar_paginas, pg

RAIZ = Path(__file__).resolve().parents[2]
CAM, ACE = "cameras-e-gravadores", "controle-de-acesso"
ESTILO = (Path(__file__).resolve().parents[1] / "static" / "loja.css").read_text(encoding="utf-8")


def azulejos(html):
    """The <li class="line ..."> blocks of a page, by line slug."""
    achados = re.findall(r'<li class="line[^"]*">.*?</li>', html, re.S)
    return {re.search(r'href="/loja/([a-z-]+)/"', a).group(1): a for a in achados}


class Validacao(unittest.TestCase):
    def setUp(self):
        self.fotos = pasta_de_fotos()

    def erros(self, d):
        return gerar.validar(d, self.fotos)

    def assertRecusa(self, d, *trechos):
        erros = self.erros(d)
        self.assertTrue(erros, "the generator accepted data it must refuse")
        for t in trechos:
            self.assertIn(t, "\n".join(erros))

    # @covers-existing: the positive control of the refusals below; master accepted this data too
    def test_a_line_with_photo_file_source_and_alt_is_accepted(self):
        self.assertEqual(self.erros(dados()), [])

    def test_a_line_without_a_scene_photo_is_refused(self):
        d = dados()
        del d["linhas"][CAM]["ambiente"]
        self.assertRecusa(d, f"linhas.{CAM}.ambiente", "missing")

    def test_a_missing_source_is_refused(self):
        for valor in (None, "", "   "):
            with self.subTest(fonte=valor):
                d = dados()
                d["linhas"][CAM]["ambiente"]["fonte"] = valor
                self.assertRecusa(d, f"linhas.{CAM}.ambiente.fonte")
        d = dados()
        del d["linhas"][CAM]["ambiente"]["fonte"]
        self.assertRecusa(d, f"linhas.{CAM}.ambiente.fonte")

    def test_a_source_that_is_not_an_https_url_is_refused(self):
        for url in ("http://backend.intelbras.com/x.jpg", "backend.intelbras.com/x.jpg",
                    "javascript:alert(1)", "https://evil.com\\@backend.intelbras.com/x.jpg"):
            with self.subTest(url=url):
                d = dados()
                d["linhas"][CAM]["ambiente"]["fonte"] = url
                self.assertRecusa(d, f"linhas.{CAM}.ambiente.fonte")

    def test_a_missing_alt_is_refused(self):
        for valor in (None, "", "  "):
            with self.subTest(alt=valor):
                d = dados()
                d["linhas"][CAM]["ambiente"]["alt"] = valor
                self.assertRecusa(d, f"linhas.{CAM}.ambiente.alt")

    def test_a_missing_file_is_refused_naming_the_file_and_the_line(self):
        for nome in ("480.webp", "700.webp"):
            with self.subTest(arquivo=nome):
                (self.fotos / "_linhas" / CAM / nome).unlink()
                self.assertRecusa(dados(), f"linhas.{CAM}.ambiente", f"_linhas/{CAM}/{nome}")
                (self.fotos / "_linhas" / CAM / nome).write_bytes(b"RIFF")

    def test_a_line_whose_folder_is_missing_is_refused(self):
        self.fotos = pasta_de_fotos(ACE)
        self.assertRecusa(dados(), f"linhas.{CAM}.ambiente", f"_linhas/{CAM}/480.webp")

    def test_the_product_shown_must_be_a_product_of_that_line(self):
        d = dados(cat("camera-um"), acesso("controlador-um"))
        d["linhas"][CAM]["ambiente"]["produto"] = "camera-um"
        self.assertEqual(self.erros(d), [])
        for slug in ("controlador-um", "nao-existe", 7):
            with self.subTest(produto=slug):
                d["linhas"][CAM]["ambiente"]["produto"] = slug
                self.assertRecusa(d, f"linhas.{CAM}.ambiente.produto")

    def test_an_unknown_field_or_a_non_object_is_refused(self):
        d = dados()
        d["linhas"][CAM]["ambiente"]["preco"] = "R$ 1"
        self.assertRecusa(d, f"linhas.{CAM}.ambiente", "preco")
        d = dados()
        d["linhas"][CAM]["ambiente"] = "foto.webp"
        self.assertRecusa(d, f"linhas.{CAM}.ambiente")


class TileDaInicio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = gerar_paginas(dados(cat("camera-um"), acesso("controlador-um")))
        cls.html = cls.f["index.html"].decode("utf-8")
        cls.tiles = azulejos(cls.html)

    def test_each_home_tile_is_a_photo_with_both_widths_and_the_reserved_ratio(self):
        self.assertEqual(sorted(self.tiles), sorted([CAM, ACE]))
        for slug, t in self.tiles.items():
            with self.subTest(linha=slug):
                img = re.search(r"<img\b[^>]*>", t).group(0)
                self.assertIn(f'src="/loja/img/_linhas/{slug}/700.webp"', img)
                self.assertIn(f'srcset="/loja/img/_linhas/{slug}/480.webp 480w, '
                              f'/loja/img/_linhas/{slug}/700.webp 700w"', img)
                self.assertIn('sizes="', img)
                self.assertIn('width="700" height="478"', img)
                self.assertIn('decoding="async"', img)

    def test_the_alt_is_the_portuguese_description_of_the_scene(self):
        self.assertIn('alt="Câmera instalada na fachada de uma casa, com jardim ao fundo"', self.tiles[CAM])
        self.assertIn('alt="Controlador facial na parede de uma portaria"', self.tiles[ACE])

    def test_the_line_icons_are_gone_from_the_home_tiles(self):
        for slug, t in self.tiles.items():
            with self.subTest(linha=slug):
                self.assertNotIn("<svg", t)
                self.assertNotIn("sprite.svg#p-", t)

    def test_the_label_sits_below_the_photo_never_on_it(self):
        for slug, t in self.tiles.items():
            with self.subTest(linha=slug):
                foto = re.search(r'<div class="amb">(.*?)</div>', t, re.S).group(1)
                self.assertTrue(foto.startswith("<img") and foto.endswith(">"), foto)
                self.assertNotIn("<h3", foto)
                self.assertNotIn("class=\"go\"", foto)
        self.assertIn(".amb {", ESTILO)

    def test_the_photo_box_reserves_its_ratio_so_nothing_jumps(self):
        regra = re.search(r"\.amb\s*\{([^}]*)\}", ESTILO).group(1)
        self.assertRegex(regra, r"aspect-ratio:\s*700\s*/\s*478")

    def test_no_photo_above_the_fold_is_lazy(self):
        for slug, t in self.tiles.items():
            with self.subTest(linha=slug):
                self.assertNotIn('loading="lazy"', t)
                self.assertIn('loading="eager"', t)
        primeiro = self.tiles[CAM]
        self.assertIn('fetchpriority="high"', primeiro)
        self.assertNotIn("fetchpriority", self.tiles[ACE])

    def test_a_line_with_no_product_keeps_the_stamp_and_shows_its_photo(self):
        f = gerar_paginas(dados(cat("camera-um")))
        t = azulejos(f["index.html"].decode("utf-8"))[ACE]
        self.assertIn("Chegando à vitrine", t)
        self.assertIn("Pedir orçamento", t)
        self.assertIn(f"/loja/img/_linhas/{ACE}/700.webp", t)
        self.assertNotIn("<svg", t)
        self.assertEqual(Pagina(f["index.html"].decode("utf-8")).problemas, [])

    def test_text_from_the_data_is_escaped_in_the_alt(self):
        d = dados(cat("camera-um"), acesso("controlador-um"))
        d["linhas"][CAM]["ambiente"]["alt"] = 'Câmera "externa" <script>x</script> & jardim'
        f = gerar_paginas(d)
        html = f["index.html"].decode("utf-8")
        self.assertNotIn("<script>x", html)
        self.assertIn("&quot;externa&quot; &lt;script&gt;x&lt;/script&gt; &amp; jardim", html)
        self.assertEqual(Pagina(html).problemas, [])


class OsIconesDaLinhaFicamOndeEstao(unittest.TestCase):
    """The owner is asked about the other places before they change: today they keep the icon."""

    @classmethod
    def setUpClass(cls):
        cls.f = gerar_paginas(dados(cat("camera-um"), acesso("controlador-um")))

    # @covers-existing: pins what the tile photos must NOT change
    def test_the_404_page_keeps_the_pictogram_tiles(self):
        t = self.f["404.html"].decode("utf-8")
        self.assertIn("sprite.svg#p-bullet", t)
        self.assertIn("sprite.svg#p-face", t)
        self.assertNotIn("_linhas", t)

    # @covers-existing: pins what the tile photos must NOT change
    def test_the_other_line_tile_on_a_category_page_keeps_the_pictogram(self):
        t = self.f[f"{CAM}/index.html"].decode("utf-8")
        self.assertIn("sprite.svg#p-face", t)
        self.assertNotIn("_linhas", t)

    # @covers-existing: pins what the tile photos must NOT change
    def test_product_pages_do_not_carry_the_scene_photos(self):
        for k in ("camera-um/index.html", "controlador-um/index.html"):
            self.assertNotIn("_linhas", self.f[k].decode("utf-8"), k)


class ArquivosEstranhosDasLinhas(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.saida = Path(tempfile.mkdtemp())
        self.dados = dados()
        self.gerados = {"index.html": b"x"}
        self.poe("index.html")
        for linha in (CAM, ACE):
            for nome in ("480.webp", "700.webp"):
                self.poe(f"img/_linhas/{linha}/{nome}")

    def poe(self, rel):
        arq = self.saida / rel
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_bytes(b"x")

    def estranhos(self):
        return gerar.arquivos_estranhos(self.saida, self.gerados, self.dados)

    def test_the_two_files_of_each_line_are_expected(self):
        self.assertEqual(self.estranhos(), [])

    def test_an_extra_file_in_a_line_folder_is_flagged(self):
        self.poe(f"img/_linhas/{CAM}/1000.webp")
        self.poe(f"img/_linhas/{CAM}/promo.html")
        self.assertEqual(self.estranhos(), [f"img/_linhas/{CAM}/1000.webp", f"img/_linhas/{CAM}/promo.html"])

    def test_a_folder_of_an_unknown_line_is_flagged(self):
        self.poe("img/_linhas/outra/480.webp")
        self.assertEqual(self.estranhos(), ["img/_linhas/outra/480.webp"])

    def test_a_file_loose_in_the_scene_root_is_flagged(self):
        self.poe("img/_linhas/480.webp")
        self.assertEqual(self.estranhos(), ["img/_linhas/480.webp"])


def dimensoes_webp(arquivo):
    """(width, height) of a lossy WebP (the 'VP8 ' chunk), standard library only."""
    b = Path(arquivo).read_bytes()
    assert b[:4] == b"RIFF" and b[8:12] == b"WEBP", f"{arquivo} is not a WebP"
    assert b[12:16] == b"VP8 ", f"{arquivo}: expected a lossy WebP, got chunk {b[12:16]!r}"
    larg, alt = struct.unpack("<HH", b[26:30])
    return larg & 0x3FFF, alt & 0x3FFF


class FotosReais(unittest.TestCase):
    """The committed shop: the scene photos are official, name their product and weigh what 4G allows."""

    @classmethod
    def setUpClass(cls):
        cls.dados, _ = gerar.carregar(RAIZ)
        cls.img = RAIZ / "public" / "loja" / "img"

    def test_every_real_scene_photo_is_official_declares_its_product_and_has_both_files(self):
        for slug, linha in self.dados["linhas"].items():
            a = linha["ambiente"]
            with self.subTest(linha=slug):
                self.assertTrue(a["fonte"].startswith("https://backend.intelbras.com/"), a["fonte"])
                self.assertIn(a["produto"], [p["slug"] for p in self.dados["produtos"] if p["linha"] == slug])
                self.assertEqual(dimensoes_webp(self.img / "_linhas" / slug / "700.webp"), (700, 478))
                self.assertEqual(dimensoes_webp(self.img / "_linhas" / slug / "480.webp"), (480, 328))

    def test_each_scene_file_stays_light(self):
        for slug in self.dados["linhas"]:
            for nome, teto in (("480.webp", 30), ("700.webp", 50)):
                with self.subTest(linha=slug, arquivo=nome):
                    kb = (self.img / "_linhas" / slug / nome).stat().st_size / 1024
                    self.assertLessEqual(kb, teto, f"{nome} is {kb:.1f} KB, the budget is {teto} KB")


if __name__ == "__main__":
    unittest.main()
