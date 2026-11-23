"""The landing header links to the shop, between Câmeras and Blog.

The landing has no test runner of its own; this is the one place its nav is pinned. The same
`.nav-links` list is the desktop bar and the phone menu, so one assertion covers both.
"""
import unittest
from html.parser import HTMLParser
from pathlib import Path

LANDING = Path(__file__).resolve().parents[2] / "public" / "index.html"


class NavLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._text = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and "nav-link" in (a.get("class") or "").split():
            self._href, self._text = a.get("href"), ""

    def handle_data(self, data):
        if self._href is not None:
            self._text += data

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.links.append((self._text.strip(), self._href))
            self._href = None


class LandingNav(unittest.TestCase):
    def test_loja_sits_between_cameras_and_blog(self):
        p = NavLinks()
        p.feed(LANDING.read_text(encoding="utf-8"))
        labels = [t for t, _ in p.links]
        self.assertEqual(
            labels, ["Desenvolvimento", "Produtos", "Câmeras", "Loja", "Blog", "Contato"])
        self.assertEqual(dict(p.links)["Loja"], "/loja/")


if __name__ == "__main__":
    unittest.main()
