"""Owner decision: auto-publish is OFF and every scheduled article arrives as a draft.

A `published` request with BLOG_ALLOW_AUTO_PUBLISH=false used to be refused and lost. It is now
stored as a draft with a machine-readable outcome. Branch table: flag off/on x MCP/API x new/existing.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_hardening import ApiBase, McpBase, article  # noqa: E402

def decode(result):
    """The tool answers with its dict serialised as JSON text content."""
    if result.get("isError"):
        return {}
    return json.loads(result["content"][0]["text"])


AWAITING = "Recebida como rascunho; aguarda aprovação do editor."


class ApiFlagOff(ApiBase):
    auto_publish = False

    def stored(self):
        return self.client.get("/api/blog/articles", headers=self.headers).json()["articles"]

    def assertNotPublished(self):
        """The point of the rule: whatever was retried, nothing went public."""
        self.assertEqual(self.client.get("/blog/software-para-negocios/").status_code, 404)
        self.assertEqual([a["status"] for a in self.stored()], ["draft"])

    def test_published_request_is_stored_as_a_draft_with_a_clear_outcome(self):
        response = self.create(status="published")
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body["created"])
        self.assertEqual(body["status"], "draft")
        self.assertTrue(body["awaiting_approval"])
        self.assertEqual(body["message"], AWAITING)
        self.assertEqual(body["article"]["status"], "draft")
        self.assertIsNone(body["article"]["url"])
        self.assertEqual(self.client.get("/blog/software-para-negocios/").status_code, 404)
        self.assertNotIn("software-para-negocios", self.client.get("/blog/feed.xml").text)

    def test_retry_of_the_same_edition_is_idempotent(self):
        self.assertEqual(self.create(status="published").status_code, 201)
        retry = self.create(status="published")
        self.assertEqual(retry.status_code, 200)
        self.assertFalse(retry.json()["created"])
        self.assertTrue(retry.json()["awaiting_approval"])
        self.assertEqual(len(self.stored()), 1)
        self.assertNotPublished()

    def test_published_request_after_a_draft_of_the_same_content_is_idempotent(self):
        self.assertEqual(self.create(status="draft").status_code, 201)
        again = self.create(status="published")
        self.assertEqual(again.status_code, 200)
        self.assertFalse(again.json()["created"])
        self.assertTrue(again.json()["awaiting_approval"])
        self.assertEqual(len(self.stored()), 1)
        self.assertNotPublished()

    def test_retry_after_manual_publish_returns_the_honest_published_response(self):  # @covers-existing
        self.create(status="published")
        self.client.post("/api/blog/articles/software-para-negocios/publish", headers=self.headers)
        retry = self.create(status="published")
        self.assertEqual(retry.status_code, 200)
        body = retry.json()
        self.assertFalse(body["created"])
        self.assertEqual((body["status"], body["awaiting_approval"]), ("published", False))
        self.assertTrue(body["article"]["url"])
        self.assertEqual(len(self.stored()), 1)

    def test_different_content_for_an_existing_edition_still_conflicts(self):
        self.create(status="published")
        self.assertEqual(self.create(status="published", title="Outro título para a edição").status_code, 409)
        self.assertEqual(len(self.stored()), 1)

    def test_draft_request_has_the_same_outcome_shape(self):
        body = self.create().json()
        self.assertEqual((body["status"], body["awaiting_approval"], body["message"]), ("draft", True, AWAITING))

    def test_manual_publish_endpoint_still_publishes(self):
        self.create(status="published")
        response = self.client.post("/api/blog/articles/software-para-negocios/publish", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/blog/software-para-negocios/").status_code, 200)


class ApiFlagOn(ApiBase):
    auto_publish = True

    def test_published_request_publishes(self):
        body = self.create(status="published").json()
        self.assertEqual((body["status"], body["awaiting_approval"]), ("published", False))
        self.assertTrue(body["article"]["url"])
        self.assertEqual(self.client.get("/blog/software-para-negocios/").status_code, 200)

    def test_retry_is_idempotent(self):
        self.create(status="published")
        retry = self.create(status="published")
        self.assertEqual((retry.status_code, retry.json()["created"]), (200, False))

    def test_draft_request_stays_a_draft_and_awaits_approval(self):
        body = self.create().json()
        self.assertEqual((body["status"], body["awaiting_approval"]), ("draft", True))

    def test_published_request_after_a_draft_conflicts(self):  # @covers-existing
        self.create()
        self.assertEqual(self.create(status="published").status_code, 409)


class McpFlagOff(McpBase):
    auto_publish = False

    def assertNotPublished(self):
        self.assertEqual(self.client.get("/blog/software-para-negocios/").status_code, 404)
        self.assertEqual([a["status"] for a in self.app.state.store.list(public=False)], ["draft"])

    def call(self, **changes):
        response = self.rpc("tools/call", dict(name="create_article", arguments=dict(article=article(**changes))))
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()["result"]
        return result, decode(result)

    def test_published_request_is_stored_as_a_draft_with_a_clear_outcome(self):
        result, body = self.call(status="published")
        self.assertFalse(result.get("isError", False), result)
        self.assertTrue(body["created"])
        self.assertEqual(body["status"], "draft")
        self.assertTrue(body["awaiting_approval"])
        self.assertEqual(body["message"], AWAITING)
        self.assertIsNone(body["article"]["url"])
        self.assertEqual(len(self.app.state.store.list(public=False)), 1)
        self.assertEqual(self.app.state.store.list(), [])

    def test_retry_is_idempotent(self):
        self.call(status="published")
        result, body = self.call(status="published")
        self.assertFalse(result.get("isError", False), result)
        self.assertFalse(body["created"])
        self.assertTrue(body["awaiting_approval"])
        self.assertEqual(len(self.app.state.store.list(public=False)), 1)
        self.assertNotPublished()

    def test_published_request_after_a_draft_of_the_same_content_is_idempotent(self):
        self.call(status="draft")
        result, body = self.call(status="published")
        self.assertFalse(result.get("isError", False), result)
        self.assertFalse(body["created"])
        self.assertTrue(body["awaiting_approval"])
        self.assertEqual(len(self.app.state.store.list(public=False)), 1)
        self.assertNotPublished()

    def test_retry_after_manual_publish_returns_the_honest_published_response(self):  # @covers-existing
        self.call(status="published")
        self.app.state.store.publish("software-para-negocios")
        result, body = self.call(status="published")
        self.assertFalse(result.get("isError", False), result)
        self.assertFalse(body["created"])
        self.assertEqual((body["status"], body["awaiting_approval"]), ("published", False))
        self.assertTrue(body["article"]["url"])

    def test_different_content_for_an_existing_edition_is_a_tool_error(self):
        self.call(status="published")
        result, _ = self.call(status="published", title="Outro título para a edição")
        self.assertTrue(result["isError"])
        self.assertEqual(len(self.app.state.store.list(public=False)), 1)


class McpFlagOn(McpBase):
    auto_publish = True

    def call(self, **changes):
        response = self.rpc("tools/call", dict(name="create_article", arguments=dict(article=article(**changes))))
        result = response.json()["result"]
        return result, decode(result)

    def test_published_request_publishes(self):
        result, body = self.call(status="published")
        self.assertEqual((body["status"], body["awaiting_approval"]), ("published", False))
        self.assertTrue(body["article"]["url"])

    def test_retry_is_idempotent(self):
        self.call(status="published")
        result, body = self.call(status="published")
        self.assertFalse(result.get("isError", False))
        self.assertFalse(body["created"])

    def test_draft_request_awaits_approval(self):
        _, body = self.call()
        self.assertEqual((body["status"], body["awaiting_approval"]), ("draft", True))


if __name__ == "__main__":
    unittest.main()
