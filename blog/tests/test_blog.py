import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
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


def article(**changes):
    return dict(edition_key="terca-2026-10-20", slug="software-para-negocios",
        title="Software que transforma negócios",
        excerpt="Uma análise sobre tecnologia e os resultados que ela pode gerar para empresas.",
        category="Software", content_markdown="## Uma decisão importante\n\n" +
        "Tecnologia pode simplificar processos quando parte de um problema concreto. " * 4,
        status="draft") | changes


class BlogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Settings(database=self.tmp.name + "/blog.sqlite3", base_url="https://www.devboot.com.br",
            api_token="test-credential-" + "x" * 40, allow_auto_publish=True)
        self.app = create_app(self.settings)
        self.client = TestClient(self.app)
        self.client.__enter__()
        self.headers = {"Authorization": "Bearer " + self.settings.api_token}

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.tmp.cleanup()

    def create(self, **changes):
        return self.client.post("/api/blog/articles", headers=self.headers, json=article(**changes))

    def test_publication_is_visible_in_article_index_feed_and_sitemap(self):
        response = self.create(status="published")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["article"]["url"], "https://www.devboot.com.br/blog/software-para-negocios/")
        page = self.client.get("/blog/software-para-negocios/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("<h2>Uma decisão importante</h2>", page.text)
        self.assertIn('application/ld+json', page.text)
        self.assertIn('rel="canonical"', page.text)
        self.assertIn("Software que transforma negócios", self.client.get("/blog/").text)
        for path in ["/blog/feed.xml", "/blog/sitemap.xml"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            ElementTree.fromstring(response.content)
            self.assertIn("software-para-negocios", response.text)
        self.assertEqual(self.client.get("/blog/assets/blog.css").status_code, 200)

    def test_drafts_are_private_until_manually_published(self):
        self.assertEqual(self.create().status_code, 201)
        self.assertIsNone(self.create().json()["article"]["url"])
        self.assertEqual(self.client.get("/blog/software-para-negocios/").status_code, 404)
        for path in ["/blog/", "/blog/feed.xml", "/blog/sitemap.xml"]:
            self.assertNotIn("Software que transforma negócios", self.client.get(path).text)
        self.assertEqual(self.client.post("/api/blog/articles/software-para-negocios/publish").status_code, 401)
        self.assertEqual(self.client.post("/api/blog/articles/software-para-negocios/publish", headers=self.headers).status_code, 200)
        self.assertEqual(self.client.get("/blog/software-para-negocios/").status_code, 200)

    def test_both_read_and_write_api_require_authentication(self):
        for method in [self.client.get, self.client.post]:
            for headers in [{}, {"Authorization": "Bearer wrong"}]:
                response = method("/api/blog/articles", headers=headers)
                self.assertEqual(response.status_code, 401)
        self.assertEqual(self.client.get("/api/blog/articles", headers=self.headers).status_code, 200)
        self.assertIn("no-store", self.client.get("/api/blog/articles", headers=self.headers).headers["cache-control"])

    def test_retries_are_idempotent_but_cannot_overwrite_content(self):
        self.assertEqual(self.create(status="published").status_code, 201)
        first_date = self.create(status="published").json()["article"]["published_at"]
        retry = self.create(status="published")
        self.assertEqual(retry.status_code, 200)
        self.assertFalse(retry.json()["created"])
        self.assertEqual(retry.json()["article"]["published_at"], first_date)
        self.assertEqual(self.create(title="Outro título para a mesma edição", status="published").status_code, 409)
        self.assertEqual(self.create(edition_key="sabado-2026-10-24", status="published").status_code, 409)
        self.assertEqual(len(self.client.get("/api/blog/articles", headers=self.headers).json()["articles"]), 1)

    def test_concurrent_delivery_creates_only_one_article_and_persists(self):
        store = self.app.state.store
        with ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(lambda _: store.save(ArticleInput(**article()), True), range(5)))
        self.assertEqual(sum(created for _, created in results), 1)
        self.assertEqual(len(Store(self.settings.database).list(public=False)), 1)

    def test_html_and_script_urls_are_not_executable(self):
        self.create(status="published", title='Título com <script>alert(1)</script>',
            content_markdown=article()["content_markdown"] + '\n<script>alert(1)</script>\n\n[link](javascript:alert(1))')
        response = self.client.get("/blog/software-para-negocios/")
        self.assertNotIn("<script>alert(1)</script>", response.text)
        self.assertNotIn('href="javascript:', response.text)
        self.assertIn("&lt;script&gt;", response.text)
        self.assertIn("script-src 'none'", response.headers["content-security-policy"])

    def test_invalid_payloads_reserved_slugs_and_large_bodies(self):
        for changes in [dict(slug="../escape"), dict(slug="assets"), dict(title=""), dict(status="unknown"), dict(content_markdown="short"), dict(unknown="field")]:
            self.assertEqual(self.create(**changes).status_code, 422)
        self.assertEqual(self.client.post("/api/blog/articles", content="{", headers=self.headers).status_code, 422)
        self.assertEqual(self.client.post("/api/blog/articles", content="x" * 256001, headers=self.headers).status_code, 413)

    def test_publication_disabled_still_allows_manual_review(self):
        app = create_app(replace(self.settings, allow_auto_publish=False))
        with TestClient(app) as client:
            self.assertEqual(client.post("/api/blog/articles", headers=self.headers, json=article(status="published")).status_code, 403)
            self.assertEqual(client.post("/api/blog/articles", headers=self.headers, json=article()).status_code, 201)
            self.assertEqual(client.post("/api/blog/articles/software-para-negocios/publish", headers=self.headers).status_code, 200)

    def test_missing_credentials_fail_closed(self):
        with TestClient(create_app(replace(self.settings, api_token=""))) as client:
            self.assertEqual(client.post("/api/blog/articles", json=article()).status_code, 503)
            self.assertEqual(client.get("/blog/").status_code, 200)
            self.assertEqual(client.post("/mcp", headers=self.headers, json={}).status_code, 503)

    def test_not_found_and_trailing_slash_redirect(self):
        self.assertEqual(self.client.get("/blog/unknown/").status_code, 404)
        self.create(status="published")
        response = self.client.get("/blog/software-para-negocios", follow_redirects=False)
        self.assertEqual(response.status_code, 308)
        self.assertEqual(response.headers["location"], "/blog/software-para-negocios/")


class OAuthAndMCPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Settings(database=self.tmp.name + "/blog.sqlite3", api_token="x" * 40,
            allow_auto_publish=True, oauth_issuer="https://auth.example.com/",
            oauth_jwks_url="https://auth.example.com/.well-known/jwks.json")
        self.app = create_app(self.settings)
        self.client = TestClient(self.app)
        self.client.__enter__()
        self.jwks_patch = patch.object(self.app.state.auth.jwks, "get_signing_key_from_jwt", return_value=SimpleNamespace(key=self.key.public_key()))
        self.jwks_patch.start()

    def tearDown(self):
        self.jwks_patch.stop()
        self.client.__exit__(None, None, None)
        self.tmp.cleanup()

    def token(self, **changes):
        return jwt.encode(dict(sub="devboot-editor", iss=self.settings.oauth_issuer,
            aud=self.settings.base_url + "/mcp", exp=datetime.now(timezone.utc) + timedelta(minutes=5),
            scope="blog:write") | changes, self.key, algorithm="RS256", headers={"kid": "test-key"})

    def rpc(self, method, params=None, token=None):
        return self.client.post("/mcp", headers={"Authorization": "Bearer " + (token or self.token()),
            "Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-06-18"},
            json=dict(jsonrpc="2.0", id=1, method=method, params=params or {}))

    def test_metadata_and_auth_challenge(self):
        response = self.client.get("/.well-known/oauth-protected-resource/mcp")
        self.assertEqual(response.json()["resource"], self.settings.base_url + "/mcp")
        response = self.client.post("/mcp", json={})
        self.assertEqual(response.status_code, 401)
        self.assertIn("resource_metadata", response.headers["www-authenticate"])

    def test_expiry_audience_issuer_scope_and_signature_are_verified(self):
        for claims in [dict(exp=1), dict(aud="https://wrong.example.com"), dict(iss="https://wrong.example.com"), dict(scope="blog:read")]:
            self.assertEqual(self.rpc("tools/list", token=self.token(**claims)).status_code, 401)
        self.assertEqual(self.rpc("tools/list", token="x" * 40).status_code, 401)
        other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        claims = jwt.decode(self.token(), options={"verify_signature": False})
        self.assertEqual(self.rpc("tools/list", token=jwt.encode(claims, other_key, algorithm="RS256")).status_code, 401)

    def test_mcp_initialize_list_create_read_and_retry(self):
        response = self.rpc("initialize", dict(protocolVersion="2025-06-18", capabilities={}, clientInfo=dict(name="test", version="1")))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("serverInfo", response.json()["result"])
        listing = self.rpc("tools/list")
        self.assertEqual(listing.status_code, 200, listing.text)
        self.assertEqual({tool["name"] for tool in listing.json()["result"]["tools"]}, {"create_article", "list_articles", "read_article"})
        for tool in listing.json()["result"]["tools"]:
            self.assertEqual(tool["securitySchemes"], [{"type": "oauth2", "scopes": ["blog:write"]}])
            self.assertEqual(tool["_meta"]["securitySchemes"], tool["securitySchemes"])
        response = self.rpc("tools/call", dict(name="create_article", arguments=dict(article=article(status="published"))))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertFalse(response.json()["result"].get("isError", False), response.text)
        self.assertEqual(self.client.get("/blog/software-para-negocios/").status_code, 200)
        response = self.rpc("tools/call", dict(name="read_article", arguments=dict(slug="software-para-negocios")))
        self.assertIn("Software que transforma negócios", response.text)
        response = self.rpc("tools/call", dict(name="create_article", arguments=dict(article=article(status="published"))))
        self.assertFalse(response.json()["result"].get("isError", False), response.text)
        self.assertEqual(len(self.app.state.store.list()), 1)


if __name__ == "__main__":
    unittest.main()
