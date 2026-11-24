"""The generator refuses bad data. Each test is one row of docs/loja-flow.md's branch table,
written before the code that satisfies it."""
import unittest
from pathlib import Path

import gerar
from tests.dados import ML, dados, pasta_de_fotos, produto


class Base(unittest.TestCase):
    def setUp(self):
        self.fotos = pasta_de_fotos()

    def erros(self, d):
        return gerar.validar(d, self.fotos)

    def assertRecusa(self, d, *trechos):
        erros = self.erros(d)
        self.assertTrue(erros, "the generator accepted data it must refuse")
        texto = "\n".join(erros)
        for t in trechos:
            self.assertIn(t, texto)

    def assertAceita(self, d):
        self.assertEqual(self.erros(d), [])


class LinkDoMercadoLivre(Base):
    def test_valid_listing_is_accepted(self):
        self.assertAceita(dados())

    def test_link_outside_mercadolivre_is_refused(self):
        for url in ("https://example.com/x",
                    "https://www.amazon.com.br/dp/B000",
                    "https://mercadolivre.com.br.evil.com/x",
                    "https://evilmercadolivre.com.br/x",
                    "https://mercadolivre.com.br@evil.com/x",
                    "http://www.mercadolivre.com.br/x",
                    "javascript:alert(1)",
                    "www.mercadolivre.com.br/x",
                    # a browser reads the backslash as a slash: this one goes to evil.com
                    "https://evil.com\\.mercadolivre.com.br/x",
                    "https://evil.com\\@www.mercadolivre.com.br/x",
                    "https://www.mercadolivre.com.br/x y",
                    "https://www.mercadolivre.com.br/x\ty",
                    "https://www.mercadolivre.com.br/x\ny",
                    "https://www.mercadolivre.com.br/x\x00y",
                    "https://www.mercadolivre.com.br/x\x7fy",
                    " https://www.mercadolivre.com.br/x",
                    "https://www.mercadolivre.com.br/x\u2028y"):
            with self.subTest(url=url):
                self.assertRecusa(dados(produto("camera-um", link_ml=url)), "link_ml", "camera-um")

    def test_mercadolivre_subdomains_and_the_bare_domain_are_accepted(self):
        for url in ("https://mercadolivre.com.br/x", "https://produto.mercadolivre.com.br/x",
                    "https://www.mercadolivre.com.br/x/up/MLBU1"):
            with self.subTest(url=url):
                self.assertAceita(dados(produto("camera-um", link_ml=url)))

    def test_seller_profile_must_also_be_on_mercadolivre(self):
        d = dados()
        d["loja"]["perfil_ml"] = "https://example.com/perfil"
        self.assertRecusa(d, "perfil_ml")

    def test_a_paused_or_ended_listing_with_a_bad_link_is_still_refused(self):
        for st in ("pausado", "encerrado"):
            with self.subTest(status=st):
                self.assertRecusa(
                    dados(produto("camera-um", status=st, link_ml="https://example.com/x")), "link_ml")


class AjustesDaLoja(Base):
    """loja.whatsapp and loja.site are published in every link and canonical: check their shape."""

    def com(self, campo, valor):
        d = dados()
        d["loja"][campo] = valor
        return d

    def test_the_real_values_are_accepted(self):
        self.assertAceita(self.com("whatsapp", "5587991402037"))
        self.assertAceita(self.com("site", "https://www.devboot.com.br"))

    def test_whatsapp_is_digits_only_with_the_country_code(self):
        for n in ("+5587991402037", "55 87 99140-2037", "(87) 99140-2037", "87991402037",
                  "5587", "55879914020371234", "55879914020a7", "", "wa.me/5587991402037"):
            with self.subTest(whatsapp=n):
                self.assertRecusa(self.com("whatsapp", n), "whatsapp")

    def test_whatsapp_accepts_landline_and_mobile_lengths(self):
        for n in ("558733211234", "5587991402037"):
            with self.subTest(whatsapp=n):
                self.assertAceita(self.com("whatsapp", n))

    def test_site_is_exactly_the_public_address(self):
        for u in ("https://www.devboot.com.br/", "http://www.devboot.com.br", "https://devboot.com.br",
                  "https://www.devboot.com.br.evil.com", "https://evil.com", "https://www.devboot.com.br/loja",
                  "HTTPS://www.devboot.com.br", " https://www.devboot.com.br"):
            with self.subTest(site=u):
                self.assertRecusa(self.com("site", u), "site")


class AtivoSemLink(Base):
    def test_active_product_without_link_is_refused(self):
        p = produto("camera-um")
        del p["link_ml"]
        self.assertRecusa(dados(p), "camera-um", "link_ml")

    def test_empty_link_counts_as_missing(self):
        self.assertRecusa(dados(produto("camera-um", link_ml="")), "camera-um", "link_ml")

    def test_paused_and_ended_products_need_no_link(self):
        for st in ("pausado", "encerrado"):
            with self.subTest(status=st):
                p = produto("camera-um", status=st)
                del p["link_ml"]
                self.assertAceita(dados(p, produto("camera-dois")))


class Nome(Base):
    def test_name_of_41_characters_is_refused_with_field_and_length(self):
        nome = "x" * 41
        self.assertRecusa(dados(produto("camera-um", nome=nome)), "nome", "camera-um", "41", "40")

    def test_name_of_40_characters_is_accepted(self):
        self.assertAceita(dados(produto("camera-um", nome="x" * 40)))

    def test_length_counts_characters_not_bytes(self):
        self.assertAceita(dados(produto("camera-um", nome="ã" * 40)))

    def test_empty_name_is_refused(self):
        self.assertRecusa(dados(produto("camera-um", nome="  ")), "nome")


class Slug(Base):
    def test_two_products_with_the_same_slug_are_refused(self):
        self.assertRecusa(dados(produto("camera-um"), produto("camera-um")), "camera-um", "slug")

    def test_product_slug_equal_to_a_category_slug_is_refused(self):
        for s in ("cameras-e-gravadores", "controle-de-acesso"):
            with self.subTest(slug=s):
                self.assertRecusa(dados(produto(s)), s, "slug")

    def test_slugs_that_would_shadow_a_file_or_folder_of_the_shop_are_refused(self):
        for s in ("img", "404", "loja", "sitemap"):
            with self.subTest(slug=s):
                self.assertRecusa(dados(produto(s)), s, "slug")

    def test_malformed_slug_is_refused(self):
        for s in ("Camera Um", "camera_um", "camera-um/", "-camera", "camera--um", "câmera", ""):
            with self.subTest(slug=s):
                self.assertRecusa(dados(produto(s)), "slug")


class Fotos(Base):
    def test_photo_listed_but_missing_is_refused(self):
        p = produto("camera-um", fotos=[{"arquivo": "1.webp", "fonte": "https://www.intelbras.com/x.webp"}])
        self.assertRecusa(dados(p), "camera-um", "1.webp")

    def test_photo_present_is_accepted(self):
        (self.fotos / "camera-um").mkdir()
        (self.fotos / "camera-um" / "1.webp").write_bytes(b"RIFF")
        p = produto("camera-um", fotos=[{"arquivo": "1.webp", "fonte": "https://www.intelbras.com/x.webp"}])
        self.assertAceita(dados(p))

    def test_photo_name_cannot_climb_out_of_the_product_folder(self):
        p = produto("camera-um", fotos=[{"arquivo": "../x.webp", "fonte": "https://www.intelbras.com/x"}])
        self.assertRecusa(dados(p), "arquivo")

    def test_more_than_six_photos_are_refused(self):
        (self.fotos / "camera-um").mkdir()
        fs = []
        for i in range(7):
            (self.fotos / "camera-um" / f"{i}.webp").write_bytes(b"x")
            fs.append({"arquivo": f"{i}.webp", "fonte": "https://www.intelbras.com/x"})
        self.assertRecusa(dados(produto("camera-um", fotos=fs)), "fotos", "6")

    def test_every_photo_records_its_source(self):
        (self.fotos / "camera-um").mkdir()
        (self.fotos / "camera-um" / "1.webp").write_bytes(b"x")
        self.assertRecusa(dados(produto("camera-um", fotos=[{"arquivo": "1.webp"}])), "fonte")


class Desconhecidos(Base):
    def test_unknown_line_is_refused(self):
        self.assertRecusa(dados(produto("camera-um", linha="alarmes")), "linha", "alarmes")

    def test_unknown_type_is_refused(self):
        self.assertRecusa(dados(produto("camera-um", tipo="drones")), "tipo", "drones")

    def test_type_of_another_line_is_refused(self):
        self.assertRecusa(dados(produto("camera-um", tipo="fechaduras")), "tipo", "fechaduras")

    def test_unknown_status_is_refused(self):
        self.assertRecusa(dados(produto("camera-um", status="esgotado")), "status", "esgotado")

    def test_unknown_pictogram_is_refused(self):
        self.assertRecusa(dados(produto("camera-um", pictograma="foguete")), "pictograma")

    def test_missing_required_field_is_refused_by_name(self):
        for campo in ("nome", "marca", "linha", "tipo", "status", "resumo", "beneficios", "specs",
                      "pictograma", "fonte"):
            with self.subTest(campo=campo):
                p = produto("camera-um")
                del p[campo]
                self.assertRecusa(dados(p), campo)


class NuncaPreco(Base):
    def test_a_price_field_is_refused(self):
        for campo in ("preco", "preço", "price", "valor"):
            with self.subTest(campo=campo):
                self.assertRecusa(dados(produto("camera-um", **{campo: 1299.9})), campo)

    def test_any_unknown_field_is_refused(self):
        self.assertRecusa(dados(produto("camera-um", cor="preto")), "cor")


class RegrasDeConteudo(Base):
    def test_summary_over_155_characters_is_refused(self):
        self.assertRecusa(dados(produto("camera-um", resumo="x" * 156)), "resumo", "156")

    def test_summary_of_155_characters_is_accepted(self):
        self.assertAceita(dados(produto("camera-um", resumo="x" * 155)))

    def test_exactly_three_benefits(self):
        for n in (0, 2, 4):
            with self.subTest(n=n):
                self.assertRecusa(dados(produto("camera-um", beneficios=["b"] * n)), "beneficios")

    def test_benefit_over_70_characters_is_refused(self):
        self.assertRecusa(dados(produto("camera-um", beneficios=["a", "b", "x" * 71])), "beneficios")

    def test_specs_between_3_and_10(self):
        for n in (0, 2, 11):
            with self.subTest(n=n):
                self.assertRecusa(
                    dados(produto("camera-um", specs=[["R", "V"]] * n)), "specs")

    def test_a_spec_needs_label_and_value(self):
        self.assertRecusa(dados(produto("camera-um", specs=[["R", "V"], ["R", ""], ["R", "V"]])), "specs")

    def test_at_most_four_featured_products(self):
        ps = [produto(f"camera-{i}", destaque=True) for i in range(5)]
        self.assertRecusa(dados(*ps), "destaque", "4")

    def test_every_product_records_where_its_data_came_from(self):
        self.assertRecusa(dados(produto("camera-um", fonte=[])), "fonte")
        self.assertRecusa(dados(produto("camera-um", fonte=["não é url"])), "fonte")


if __name__ == "__main__":
    unittest.main()
