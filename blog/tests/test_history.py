import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from history import HistoryInbox
from local_mcp import BlogAPI, create_local_mcp


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "inbox"
        self.root.mkdir()
        self.inbox = HistoryInbox(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_history_is_empty_not_fabricated(self):
        self.assertEqual(HistoryInbox(self.root / "absent").list(), [])
        self.assertEqual(self.inbox.list(), [])

    def test_lists_metadata_then_reads_text_without_following_symlinks(self):
        (self.root / "terca.md").write_text("# Uma pesquisa real\n\nTexto fornecido para importação.")
        private = Path(self.tmp.name) / "outside.txt"
        private.write_text("Do not read this unrelated file")
        (self.root / "outside.txt").symlink_to(private)
        entries = self.inbox.list()
        self.assertEqual(len(entries), 1)
        self.assertNotIn("content_markdown", entries[0])
        self.assertIn("Uma pesquisa real", self.inbox.read(entries[0]["entry_id"])["content_markdown"])
        with self.assertRaises(ValueError):
            self.inbox.read("../outside.txt")

    def test_stable_run_identity_detects_changed_content(self):
        source = self.root / "runs.json"
        data = {"runs": [{"id": "terca-2026-10-13", "task_name": "Pesquisa de terça", "content_markdown": "Primeiro conteúdo"}]}
        source.write_text(json.dumps(data))
        first = self.inbox.list()[0]
        data["runs"][0]["content_markdown"] = "Conteúdo corrigido"
        source.write_text(json.dumps(data))
        second = self.inbox.list()[0]
        self.assertEqual(first["entry_id"], second["entry_id"])
        self.assertNotEqual(first["content_sha256"], second["content_sha256"])
        data["runs"].append(data["runs"][0])
        source.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "duplicado"):
            self.inbox.list()

    def test_saved_html_reads_main_content_and_links_without_scripts_or_navigation(self):
        (self.root / "sabado.html").write_text('''<!doctype html><html><head><title>ChatGPT</title></head>
            <body><nav>Outra conversa privada</nav><main><h1>Resultado de sábado</h1>
            <p>Pesquisa com <a href="https://example.com/report">fonte original</a>.</p>
            <script>fetch('https://example.com/do-not-call')</script><button>Compartilhar</button>
            </main><aside>Outras conversas</aside></body></html>''')
        entry = self.inbox.read(self.inbox.list()[0]["entry_id"])
        self.assertIn("Resultado de sábado", entry["content_markdown"])
        self.assertIn("https://example.com/report", entry["content_markdown"])
        for unwanted in ("fetch", "Outra conversa privada", "Outras conversas", "Compartilhar"):
            self.assertNotIn(unwanted, entry["content_markdown"])

    def test_export_reads_only_assistant_text_on_selected_branch(self):
        data = [{"id": "conversation-1", "title": "Pesquisa de terça", "current_node": "selected", "mapping": {
            "root": {"parent": None, "message": {"author": {"role": "system"}, "content": {"parts": ["private system"]}}},
            "user": {"parent": "root", "message": {"author": {"role": "user"}, "content": {"parts": ["private user"]}}},
            "discarded": {"parent": "user", "message": {"id": "discarded", "author": {"role": "assistant"}, "content": {"parts": ["discarded branch"]}}},
            "selected": {"parent": "user", "message": {"id": "result-1", "author": {"role": "assistant"}, "content": {"parts": ["Resultado selecionado", {"image": "not text"}]}}},
        }}]
        path = self.root / "conversations.json"
        path.write_text(json.dumps(data))
        entry = self.inbox.read(self.inbox.list()[0]["entry_id"])
        self.assertEqual(entry["content_markdown"], "Resultado selecionado")
        data[0]["mapping"]["root"]["parent"] = "selected"
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "ciclo"):
            self.inbox.list()

    def test_local_publisher_cannot_target_remote_hosts_or_credentials_in_url(self):
        for url in ["https://www.devboot.com.br", "http://127.0.0.1.evil.test", "http://user:password@localhost:80", "http://localhost/path", "file:///tmp/test"]:
            with self.assertRaises(ValueError):
                BlogAPI(url, "x" * 40)


class LocalMCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_mcp_reads_source_checks_fingerprint_and_sends_validated_article(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "result.md"
            source.write_text("# Texto de uma pesquisa\n\n" + "Resultado fornecido pelo usuário. " * 5)
            api = Mock()
            api.request.return_value = {"created": True, "article": {"status": "draft"}}
            server = create_local_mcp(directory, api)
            entry = HistoryInbox(directory).list()[0]
            article = {"title": "Uma matéria para o blog", "slug": "materia-para-o-blog",
                "excerpt": "Resumo de uma matéria criada a partir do histórico fornecido.",
                "content_markdown": "## Resultado da pesquisa\n\n" + "Texto editado da pesquisa. " * 8}
            await server.call_tool("read_history_entry", {"entry_id": entry["entry_id"]})
            await server.call_tool("create_history_article", {"entry_id": entry["entry_id"],
                "source_sha256": entry["content_sha256"], "article": article})
            args = api.request.call_args.args
            self.assertEqual(args[0], "/api/blog/articles")
            self.assertEqual(args[1]["edition_key"], "history-" + entry["entry_id"])
            self.assertEqual(args[1]["status"], "draft")
            source.write_text("Texto alterado depois da leitura.")
            with self.assertRaisesRegex(Exception, "fonte mudou"):
                await server.call_tool("create_history_article", {"entry_id": entry["entry_id"],
                    "source_sha256": entry["content_sha256"], "article": article})
            self.assertEqual(api.request.call_count, 1)
