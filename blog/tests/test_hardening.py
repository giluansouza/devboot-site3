"""Review findings F2-F4 and F9: each test is one row of the branch table.

Tests marked `characterization` cover behaviour that already held when they were written
(they pass on the base by definition); the others failed before the fix they accompany.
"""
import json
import re
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch
from xml.etree import ElementTree

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from starlette.testclient import TestClient

from app import Settings, create_app
from store import ArticleInput, Store

BODY = "## Uma decisão importante\n\n" + "Tecnologia pode simplificar processos quando parte de um problema concreto. " * 4


def article(**changes):
    return dict(edition_key="terca-2026-10-20", slug="software-para-negocios",
        title="Software que transforma negócios",
        excerpt="Uma análise sobre tecnologia e os resultados que ela pode gerar para empresas.",
        category="Software", content_markdown=BODY, status="draft") | changes


class ApiBase(unittest.TestCase):
    auto_publish = True

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Settings(database=self.tmp.name + "/blog.sqlite3", base_url="https://www.devboot.com.br",
            api_token="test-credential-" + "x" * 40, allow_auto_publish=self.auto_publish)
        self.app = create_app(self.settings)
        self.client = TestClient(self.app)
        self.client.__enter__()
        self.headers = {"Authorization": "Bearer " + self.settings.api_token}

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.tmp.cleanup()

    def create(self, **changes):
        return self.client.post("/api/blog/articles", headers=self.headers, json=article(**changes))


class FeedStaysWellFormed(ApiBase):
    """F2: a C0 control character in a text field made /blog/feed.xml unparseable for every article."""

    def test_control_characters_are_refused_at_input(self):
        n = 0
        for field in ("title", "excerpt", "category"):
            for char in ("\x0b", "\x00", "\x1f", "\x0c", "￾"):
                with self.subTest(field=field, char=repr(char)):
                    value = {"title": "Título com" + char + "controle",
                             "excerpt": "Resumo longo o bastante" + char + "para validar",
                             "category": "Cat" + char + "egoria"}[field]
                    n += 1  # a fresh edition and slug each time, so a 409 cannot mask a missing 422
                    self.assertEqual(self.create(**{field: value, "edition_key": f"ed-{n}", "slug": f"slug-{n}"}).status_code, 422)

    def test_published_feed_and_sitemap_parse_after_such_a_title(self):
        self.create(status="published", title="Título com\x0bcontrole")
        self.create(status="published", edition_key="sabado-2026-10-24", slug="segundo-artigo")
        for path in ("/blog/feed.xml", "/blog/sitemap.xml"):
            ElementTree.fromstring(self.client.get(path).content)

    def test_feed_survives_a_control_character_already_stored(self):
        # Defense in depth for rows written before input was validated: bypass the model.
        store = self.app.state.store
        saved, _ = store.save(ArticleInput(**article(status="published")), True)
        with store.connect() as db:
            db.execute("UPDATE articles SET title = ?, excerpt = ? WHERE id = ?",
                       ("Título com\x0bcontrole", "Resumo com\x08controle de feed", saved["id"]))
        feed = self.client.get("/blog/feed.xml")
        root = ElementTree.fromstring(feed.content)
        self.assertIn("Título comcontrole", [e.text for e in root.iter("title")])

    def test_tab_newline_and_accents_are_still_accepted(self):  # characterization
        self.assertEqual(self.create(excerpt="Resumo com acentuação e\nquebra de linha válida aqui").status_code, 201)


class BranchTableRows(ApiBase):
    """F9, API side."""

    def test_xss_in_excerpt_category_and_json_ld(self):  # characterization
        self.create(status="published", title="Título comum aqui",
            excerpt='</script><script>alert(1)</script> "><img src=x onerror=alert(2)> resumo',
            category='"><img src=x onerror=alert(3)>')
        for path in ("/blog/software-para-negocios/", "/blog/"):
            html = self.client.get(path).text
            self.assertNotIn("<script>alert(1)", html, path)
            self.assertNotIn("<img src=x", html, path)
        page = self.client.get("/blog/software-para-negocios/").text
        data = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S).group(1)
        self.assertIn("alert(1)", json.loads(data)["description"])  # kept as data, inert inside JSON
        self.assertNotIn("</script>", data)

    def test_paths_variants_do_not_bypass_authentication(self):  # characterization
        self.create(status="published")
        self.create(edition_key="rascunho-2026-10-24", slug="rascunho-secreto", title="Rascunho secreto aqui")
        for path in ("//mcp", "/mcp/", "/api//blog/articles", "//api/blog/articles", "/api/blog/articles/",
                     "/api/blog//articles", "/API/blog/articles", "/api/blog/%61rticles", "/%6dcp",
                     "/api/blog/articles/rascunho-secreto/publish", "/api/blog/articles/../articles",
                     "/mcp%2f", "/api/blog/articles%2f"):
            for method in (self.client.get, self.client.post):
                with self.subTest(path=path, method=method.__name__):
                    response = method(path, follow_redirects=False)
                    self.assertNotIn(response.status_code, (200, 201), response.text[:200])
                    self.assertNotIn("rascunho-secreto", response.text)

    def test_publish_unknown_slug_is_404(self):  # characterization
        response = self.client.post("/api/blog/articles/nao-existe/publish", headers=self.headers)
        self.assertEqual(response.status_code, 404)

    def test_publishing_twice_keeps_the_first_published_at(self):  # characterization
        self.create()
        first = self.client.post("/api/blog/articles/software-para-negocios/publish", headers=self.headers).json()["article"]
        second = self.client.post("/api/blog/articles/software-para-negocios/publish", headers=self.headers).json()["article"]
        self.assertTrue(first["published_at"])
        self.assertEqual(first["published_at"], second["published_at"])

    def test_empty_blog_renders_index_feed_and_sitemap(self):  # characterization
        response = self.client.get("/blog/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Boas ideias estão a caminho", response.text)
        for path in ("/blog/feed.xml", "/blog/sitemap.xml"):
            self.assertEqual(self.client.get(path).status_code, 200)
            ElementTree.fromstring(self.client.get(path).content)


class AutoPublishOff(ApiBase):
    auto_publish = False

    def test_resubmitting_a_draft_as_published_is_refused(self):  # characterization
        self.assertEqual(self.create().status_code, 201)
        response = self.create(status="published")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get("/blog/software-para-negocios/").status_code, 404)
        stored = self.client.get("/api/blog/articles", headers=self.headers).json()["articles"]
        self.assertEqual([a["status"] for a in stored], ["draft"])


class AutoPublishOnResubmit(ApiBase):
    def test_resubmitting_a_draft_as_published_conflicts_instead_of_overwriting(self):  # characterization
        self.assertEqual(self.create().status_code, 201)
        self.assertEqual(self.create(status="published").status_code, 409)
        self.assertEqual(self.client.get("/blog/software-para-negocios/").status_code, 404)


class McpBase(unittest.TestCase):
    auto_publish = True

    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Settings(database=self.tmp.name + "/blog.sqlite3", api_token="x" * 40,
            allow_auto_publish=self.auto_publish, oauth_issuer="https://auth.example.com/",
            oauth_jwks_url="https://auth.example.com/.well-known/jwks.json")
        self.app = create_app(self.settings)
        self.client = TestClient(self.app)
        self.client.__enter__()
        self.jwks_patch = patch.object(self.app.state.auth.jwks, "get_signing_key_from_jwt",
            return_value=SimpleNamespace(key=self.key.public_key()))
        self.jwks_patch.start()

    def tearDown(self):
        self.jwks_patch.stop()
        self.client.__exit__(None, None, None)
        self.tmp.cleanup()

    def token(self, **changes):
        return jwt.encode(dict(sub="devboot-editor", iss=self.settings.oauth_issuer,
            aud=self.settings.base_url + "/mcp", exp=datetime.now(timezone.utc) + timedelta(minutes=5),
            scope="blog:write") | changes, self.key, algorithm="RS256", headers={"kid": "test-key"})

    def rpc(self, method, params=None, token=None, headers=None):
        return self.client.post("/mcp", headers={"Authorization": "Bearer " + (token or self.token()),
            "Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-06-18"} | (headers or {}),
            json=dict(jsonrpc="2.0", id=1, method=method, params=params or {}))


class McpHardening(McpBase):
    def test_list_valued_scope_claim_is_401_not_500(self):
        response = self.rpc("tools/list", token=self.token(scope=["blog:write"]))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.rpc("tools/list", token=self.token(scope=None)).status_code, 401)
        self.assertEqual(self.rpc("tools/list", token=self.token(scope=7)).status_code, 401)

    def test_string_scope_with_several_values_still_works(self):  # characterization
        self.assertEqual(self.rpc("tools/list", token=self.token(scope="openid blog:write")).status_code, 200)

    def test_bare_domain_host_is_accepted_alongside_www(self):
        for host in ("www.devboot.com.br", "devboot.com.br"):
            with self.subTest(host=host):
                response = self.rpc("tools/list", headers={"Host": host})
                self.assertEqual(response.status_code, 200, response.text)

    def test_foreign_host_is_still_refused(self):  # characterization
        for host in ("evil.example.com", "devboot.com.br.evil.example.com", "wwwdevboot.com.br"):
            with self.subTest(host=host):
                self.assertEqual(self.rpc("tools/list", headers={"Host": host}).status_code, 421)

    def test_jwks_unreachable_is_401(self):  # characterization
        self.jwks_patch.stop()
        try:
            app = create_app(replace(self.settings, oauth_jwks_url="https://127.0.0.1:1/jwks.json"))
            with TestClient(app) as client:
                response = client.post("/mcp", headers={"Authorization": "Bearer " + self.token(),
                    "Accept": "application/json, text/event-stream"}, json=dict(jsonrpc="2.0", id=1, method="tools/list"))
            self.assertEqual(response.status_code, 401)
        finally:
            self.jwks_patch.start()


class McpAutoPublishOff(McpBase):
    auto_publish = False

    def test_create_published_is_refused_by_the_tool_and_stores_nothing(self):  # characterization
        response = self.rpc("tools/call", dict(name="create_article", arguments=dict(article=article(status="published"))))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["result"]["isError"], response.text)
        self.assertEqual(self.app.state.store.list(public=False), [])
        draft = self.rpc("tools/call", dict(name="create_article", arguments=dict(article=article())))
        self.assertFalse(draft.json()["result"].get("isError", False), draft.text)
        self.assertEqual(len(self.app.state.store.list(public=False)), 1)


if __name__ == "__main__":
    unittest.main()
