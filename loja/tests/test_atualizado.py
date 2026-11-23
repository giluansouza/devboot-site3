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
        esperados = set(gerado())
        existentes = {a.relative_to(SAIDA).as_posix() for a in SAIDA.rglob("*")
                      if a.is_file() and a.relative_to(SAIDA).parts[0] != "img"}
        self.assertEqual(existentes - esperados, set(), f"stray files. {LEMBRETE}")


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
