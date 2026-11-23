"""The blog names Archivo and IBM Plex; the CSP (font-src 'self') blocks Google Fonts, so they must be self-hosted."""
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from starlette.testclient import TestClient  # noqa: E402
from test_hardening import ApiBase  # noqa: E402

BLOG = Path(__file__).resolve().parents[1]
STATIC = BLOG / "static"


class SelfHostedFonts(ApiBase):
    def faces(self):
        css = (STATIC / "blog.css").read_text()
        return re.findall(r"@font-face\{[^}]*\}", css.replace("\n", "").replace(" {", "{"))

    def test_css_declares_the_three_families_with_local_woff2_sources(self):
        faces = self.faces()
        families = {re.search(r"font-family:\s*['\"]?([^;'\"]+)", f).group(1) for f in faces}
        self.assertEqual(families, {"Archivo", "IBM Plex Sans", "IBM Plex Mono"})
        for face in faces:
            url = re.search(r"url\(['\"]?(/blog/assets/fonts/[^'\")]+\.woff2)", face)
            self.assertIsNotNone(url, face)
            self.assertIn("font-display:swap", face.replace(" ", ""))
            self.assertTrue((STATIC / "fonts" / Path(url.group(1)).name).exists(), url.group(1))

    def test_declared_fonts_are_served_as_woff2_under_the_csp(self):
        self.assertEqual(len(self.faces()), 4)
        for face in self.faces():
            path = re.search(r"url\(['\"]?(/blog/assets/fonts/[^'\")]+\.woff2)", face).group(1)
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertEqual(response.headers["content-type"], "font/woff2")
            self.assertEqual(response.content[:4], b"wOF2")
        self.assertIn("font-src 'self'", self.client.get("/blog/").headers["content-security-policy"])

    def test_pages_preload_the_display_and_body_fonts(self):
        html = self.client.get("/blog/").text
        preloads = re.findall(r'<link rel="preload" href="(/blog/assets/fonts/[^"]+)" as="font" type="font/woff2" crossorigin>', html)
        self.assertGreaterEqual(len(preloads), 2)
        for href in preloads:
            self.assertEqual(self.client.get(href).status_code, 200, href)
        self.assertNotIn("fonts.googleapis.com", html)

    def test_licence_notice_ships_with_the_fonts(self):
        self.assertIn("SIL Open Font License", (STATIC / "fonts" / "LICENSE.md").read_text())


if __name__ == "__main__":
    unittest.main()
