"""The committed shop: every product shows a real, official photo, so no page draws the
illustrative pictogram. Where each photo came from is recorded per photo in produtos.json."""
import unittest
from pathlib import Path

import gerar

RAIZ = Path(__file__).resolve().parents[2]


class FotosDosProdutos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados, _ = gerar.carregar(RAIZ)

    def test_every_real_product_has_a_photo_so_no_page_shows_the_illustrative_pictogram(self):
        sem = [p["slug"] for p in self.dados["produtos"] if not p.get("fotos")]
        self.assertEqual(sem, [], "these products still draw the pictogram")

    # @covers-existing: the four photos already in the shop were all taken from that server
    def test_every_real_photo_comes_from_intelbras_s_own_file_server(self):
        for p in self.dados["produtos"]:
            for f in p["fotos"]:
                with self.subTest(produto=p["slug"], foto=f["arquivo"]):
                    self.assertTrue(f["fonte"].startswith("https://backend.intelbras.com/"), f["fonte"])


if __name__ == "__main__":
    unittest.main()
