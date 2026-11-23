"""Follow-ups from the delta review: refresh tokens, flag flips, MCP error hygiene."""
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from starlette.testclient import TestClient  # noqa: E402
from test_hardening import ApiBase, McpBase, article  # noqa: E402

from app import create_app  # noqa: E402


class OfflineAccessIsAdvertisedNotRequired(McpBase):
    """Without offline_access Auth0 issues no refresh token and the first scheduled run (3-4 days
    after setup) would get a 401. The blog advertises it so the client requests it, but a token is
    valid with blog:write alone."""

    def test_metadata_advertises_both_scopes(self):
        for path in ("/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/mcp"):
            scopes = self.client.get(path).json()["scopes_supported"]
            self.assertEqual(scopes, ["blog:write", "offline_access"], path)

    def test_challenge_names_both_scopes(self):
        challenge = self.client.post("/mcp", json={}).headers["www-authenticate"]
        self.assertIn('scope="blog:write offline_access"', challenge)

    def test_token_with_only_blog_write_is_still_accepted(self):  # @covers-existing
        self.assertEqual(self.rpc("tools/list", token=self.token(scope="blog:write")).status_code, 200)

    def test_token_with_only_offline_access_is_refused(self):  # @covers-existing
        self.assertEqual(self.rpc("tools/list", token=self.token(scope="offline_access")).status_code, 401)


class FlagFlipRetry(ApiBase):
    auto_publish = True

    def test_published_while_flag_was_on_retried_identically_after_it_is_off_is_idempotent(self):
        self.assertEqual(self.create(status="published").status_code, 201)
        with TestClient(create_app(replace(self.settings, allow_auto_publish=False))) as off:
            retry = off.post("/api/blog/articles", headers=self.headers, json=article(status="published"))
            self.assertEqual(retry.status_code, 200, retry.text)
            body = retry.json()
            self.assertFalse(body["created"])
            self.assertEqual((body["status"], body["awaiting_approval"]), ("published", False))
            self.assertEqual(len(off.get("/api/blog/articles", headers=self.headers).json()["articles"]), 1)

    def test_a_different_payload_after_the_flip_still_conflicts(self):  # @covers-existing
        self.create(status="published")
        with TestClient(create_app(replace(self.settings, allow_auto_publish=False))) as off:
            changed = off.post("/api/blog/articles", headers=self.headers, json=article(status="published", title="Outro título aqui"))
            self.assertEqual(changed.status_code, 409)
            as_draft = off.post("/api/blog/articles", headers=self.headers, json=article(status="draft"))
            self.assertEqual(as_draft.status_code, 409)  # a draft is different content from a published row


class McpErrorsDoNotEchoInput(McpBase):
    def test_validation_error_names_the_field_but_not_the_submitted_value(self):
        response = self.rpc("tools/call", dict(name="create_article",
            arguments=dict(article=article(title="abc", excerpt="trecho-privado-curto"))))
        result = response.json()["result"]
        self.assertTrue(result["isError"])
        text = result["content"][0]["text"]
        self.assertIn("title", text)
        self.assertIn("at least 5 characters", text)
        self.assertNotIn("input_value", text)
        self.assertNotIn("abc'", text)
        self.assertNotIn("trecho-privado-curto", text)

    def test_control_character_error_does_not_echo_the_content(self):
        response = self.rpc("tools/call", dict(name="create_article",
            arguments=dict(article=article(title="Título com\x0bcontrole"))))
        text = response.json()["result"]["content"][0]["text"]
        self.assertIn("Caracteres de controle", text)
        self.assertNotIn("Título com", text)


class ToolDescription(McpBase):
    def test_docstring_tells_the_model_to_relay_the_response_not_to_claim_publication(self):
        tools = self.rpc("tools/list").json()["result"]["tools"]
        description = next(t for t in tools if t["name"] == "create_article")["description"]
        self.assertIn("status", description)
        self.assertIn("message", description)
        self.assertNotIn("nunca diga que foi publicada", description.lower())


class Auth0DocCarriesTheRefreshCheck(unittest.TestCase):
    def test_refresh_token_verification_is_a_required_step_and_the_gap_is_gone(self):
        doc = (Path(__file__).resolve().parents[2] / "docs" / "auth0-setup.md").read_text()
        self.assertIn("Required before the automation is called active", doc)
        self.assertIn("300", doc)
        self.assertIn("refresh-token exchange", doc)
        self.assertNotIn("## Known gap", doc)
        self.assertIn('"scopes_supported": ["blog:write", "offline_access"]', doc)


if __name__ == "__main__":
    unittest.main()
