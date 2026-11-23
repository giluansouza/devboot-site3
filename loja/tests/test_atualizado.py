"""public/loja/ is generated output. Nobody edits it by hand, and the committed copy is the one
that serves production (a `git pull`, no build on the VPS), so it must equal what the generator
produces from produtos.json today."""
import unittest
from pathlib import Path

import gerar

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "public" / "loja"
LEMBRETE = "Run `cd loja && uv run python gerar.py` and commit public/loja/. Never edit it by hand."


def gerado():
    dados, tokens = gerar.carregar(RAIZ)
    return gerar.renderizar(dados, tokens, RAIZ / "loja" / "static", SAIDA / "img")


class DadosReais(unittest.TestCase):
    def test_the_committed_data_is_publishable(self):
        dados, _ = gerar.carregar(RAIZ)
        self.assertEqual(gerar.validar(dados, SAIDA / "img"), [])

    def test_no_price_anywhere_in_the_data_file(self):
        texto = (RAIZ / "loja" / "produtos.json").read_text(encoding="utf-8")
        self.assertNotIn("R$", texto)
        for campo in ('"preco"', '"preço"', '"price"', '"valor"'):
            self.assertNotIn(campo, texto)

    def test_every_listing_is_on_mercadolivre_and_every_product_has_a_source(self):
        dados, _ = gerar.carregar(RAIZ)
        for p in dados["produtos"]:
            self.assertTrue(gerar.link_do_mercado_livre(p["link_ml"]), p["slug"])
            self.assertTrue(p["fonte"], p["slug"])


class SaidaAtualizada(unittest.TestCase):
    def test_every_generated_file_equals_the_committed_one(self):
        for rel, esperado in gerado().items():
            with self.subTest(file=rel):
                arq = SAIDA / rel
                self.assertTrue(arq.is_file(), f"public/loja/{rel} is missing. {LEMBRETE}")
                self.assertEqual(arq.read_bytes(), esperado, f"public/loja/{rel} is stale or was edited. {LEMBRETE}")

    def test_no_file_in_public_loja_that_the_generator_does_not_produce(self):
        dados, _ = gerar.carregar(RAIZ)
        self.assertEqual(gerar.arquivos_estranhos(SAIDA, gerado(), dados), [], f"stray files. {LEMBRETE}")


class ArquivosEstranhos(unittest.TestCase):
    """The stray-file check also looks under img/: only the photos the JSON names are allowed there."""

    def setUp(self):
        import tempfile
        self.saida = Path(tempfile.mkdtemp())
        self.dados = {"produtos": [
            {"slug": "camera-um", "fotos": [{"arquivo": "1.webp"}, {"arquivo": "2.webp"}], "og": "og.jpg"},
            {"slug": "camera-dois", "fotos": []}]}
        self.gerados = {"index.html": b"x", "camera-um/index.html": b"x", "loja.css": b"x"}
        for rel in ("index.html", "camera-um/index.html", "loja.css"):
            self.poe(rel)
        for rel in ("img/camera-um/1.webp", "img/camera-um/2.webp", "img/camera-um/og.jpg"):
            self.poe(rel)

    def poe(self, rel):
        arq = self.saida / rel
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_bytes(b"x")

    def estranhos(self):
        return gerar.arquivos_estranhos(self.saida, self.gerados, self.dados)

    def test_the_expected_tree_is_clean(self):
        self.assertEqual(self.estranhos(), [])

    def test_a_page_dropped_into_img_is_flagged(self):
        self.poe("img/promo.html")
        self.assertEqual(self.estranhos(), ["img/promo.html"])

    def test_an_unlisted_file_inside_a_product_folder_is_flagged(self):
        self.poe("img/camera-um/3.webp")
        self.poe("img/camera-um/promo.html")
        self.assertEqual(self.estranhos(), ["img/camera-um/3.webp", "img/camera-um/promo.html"])

    def test_a_folder_for_an_unknown_slug_is_flagged(self):
        self.poe("img/outro/1.webp")
        self.assertEqual(self.estranhos(), ["img/outro/1.webp"])

    def test_a_folder_of_a_product_without_photos_is_flagged(self):
        self.poe("img/camera-dois/1.webp")
        self.assertEqual(self.estranhos(), ["img/camera-dois/1.webp"])

    def test_a_stray_file_outside_img_is_still_flagged(self):
        self.poe("promo.html")
        self.assertEqual(self.estranhos(), ["promo.html"])

    def test_a_file_in_the_root_of_img_is_flagged(self):
        self.poe("img/x.webp")
        self.assertEqual(self.estranhos(), ["img/x.webp"])


class MarcaIgualALanding(unittest.TestCase):
    def test_brand_fragment_is_the_landings_header_markup(self):
        landing = (RAIZ / "public" / "index.html").read_text(encoding="utf-8")
        for linha in (RAIZ / "loja" / "static" / "marca.html").read_text(encoding="utf-8").splitlines():
            self.assertIn(linha.strip(), landing)



class RobotsListaOSitemapDaLoja(unittest.TestCase):
    def test_robots_txt_points_to_the_shop_sitemap(self):
        robots = (RAIZ / "public" / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("Sitemap: https://www.devboot.com.br/loja/sitemap.xml", robots.splitlines())


if __name__ == "__main__":
    unittest.main()
