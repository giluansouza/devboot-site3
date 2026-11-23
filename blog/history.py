"""Read explicitly supplied history files; never access ChatGPT account cookies."""

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_CONTENT_CHARS = 100_000


class SavedPage(HTMLParser):
    """Read visible saved-page content without executing scripts or loading URLs."""
    ignored = {"head", "script", "style", "nav", "aside", "button", "form", "noscript"}
    blocks = {"p", "div", "section", "article", "h1", "h2", "h3", "h4", "li", "blockquote", "pre", "br"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.in_main = False
        self.main_found = False
        self.all_text, self.main_text = [], []
        self.links = []

    def append(self, text):
        if not self.skip:
            self.all_text.append(text)
            if self.in_main:
                self.main_text.append(text)

    def handle_starttag(self, tag, attrs):
        if tag in self.ignored:
            self.skip += 1
        if tag == "main":
            self.in_main = self.main_found = True
        if tag in self.blocks:
            self.append("\n")
        if tag == "a":
            href = dict(attrs).get("href", "")
            self.links.append(href if urlparse(href).scheme in {"https", "http"} else "")

    def handle_endtag(self, tag):
        if tag == "a" and self.links:
            href = self.links.pop()
            if href:
                self.append(" (" + href + ")")
        if tag in self.blocks:
            self.append("\n")
        if tag == "main":
            self.in_main = False
        if tag in self.ignored and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        self.append(data)

    def text(self):
        text = "".join(self.main_text if self.main_found else self.all_text)
        return re.sub(r"\n{3,}", "\n\n", re.sub(r"[^\S\n]+", " ", text)).strip()


class HistoryInbox:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()

    @staticmethod
    def _key(filename, source_id):
        return hashlib.sha256(f"{filename}\0{source_id}".encode()).hexdigest()[:32]

    def _entries(self):
        if not self.directory.is_dir():
            return
        for path in sorted(self.directory.iterdir()):
            # Symlinks and nested paths are never followed outside this inbox.
            if path.is_symlink() or not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".json", ".html", ".htm"}:
                continue
            if path.stat().st_size > MAX_FILE_BYTES:
                raise ValueError(f"Arquivo de histórico excede 25 MB: {path.name}")
            text = path.read_text(encoding="utf-8")
            if path.suffix.lower() in {".html", ".htm"}:
                parser = SavedPage()
                parser.feed(text)
                text = parser.text()
            if path.suffix.lower() != ".json":
                yield self._entry(path.name, "document", path.stem, text)
                continue
            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON de histórico inválido: {path.name}") from exc
            if isinstance(data, dict) and isinstance(data.get("runs"), list):
                seen = set()
                for run in data["runs"]:
                    if not isinstance(run, dict) or not isinstance(run.get("id"), str) or not run["id"]:
                        raise ValueError(f"Cada execução precisa de um id textual: {path.name}")
                    if run["id"] in seen:
                        raise ValueError(f"id de execução duplicado: {path.name}")
                    seen.add(run["id"])
                    yield self._entry(path.name, run["id"], run.get("task_name", path.stem),
                        run.get("content_markdown", ""), run.get("run_at"))
            elif isinstance(data, list):
                for conversation in data:
                    yield from self._conversation(path.name, conversation)
            else:
                raise ValueError(f"Formato não reconhecido: {path.name}. Use Markdown, texto ou um histórico JSON compatível.")

    def _entry(self, filename, source_id, title, content, run_at=None):
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"Resultado sem texto no histórico: {filename}")
        if len(content) > MAX_CONTENT_CHARS:
            raise ValueError(f"Resultado excede 100.000 caracteres: {filename}")
        return {"entry_id": self._key(filename, source_id), "filename": filename,
            "source_id": source_id, "title": title if isinstance(title, str) else filename,
            "run_at": run_at, "content_markdown": content,
            "content_sha256": hashlib.sha256(content.encode()).hexdigest()}

    def _conversation(self, filename, conversation):
        """Support exported conversations with mapping/current_node when available.

        Only assistant text from the selected branch is included, never tool or
        system messages. This does not assume task histories exist in an export.
        """
        if not isinstance(conversation, dict) or not isinstance(conversation.get("mapping"), dict):
            raise ValueError(f"Conversa exportada sem mapping: {filename}")
        mapping = conversation["mapping"]
        current = conversation.get("current_node")
        if not current:
            return
        branch, seen = [], set()
        while current:
            if current in seen or len(seen) >= 10_000:
                raise ValueError(f"Conversa exportada contém ciclo ou excesso de mensagens: {filename}")
            seen.add(current)
            node = mapping.get(current)
            if not isinstance(node, dict):
                raise ValueError(f"Conversa exportada contém referência inválida: {filename}")
            branch.append(node)
            current = node.get("parent")
        conversation_id = conversation.get("id") or conversation.get("conversation_id")
        if not isinstance(conversation_id, str) or not conversation_id:
            raise ValueError(f"Conversa exportada sem identificador: {filename}")
        for node in reversed(branch):
            message = node.get("message") or {}
            if (message.get("author") or {}).get("role") != "assistant":
                continue
            content = message.get("content") or {}
            parts = content.get("parts", [])
            if not isinstance(parts, list):
                continue
            text = "\n\n".join(part for part in parts if isinstance(part, str) and part.strip())
            if not text:
                continue
            message_id = message.get("id") or node.get("id")
            if not isinstance(message_id, str) or not message_id:
                raise ValueError(f"Mensagem exportada sem identificador: {filename}")
            yield self._entry(filename, conversation_id + ":" + message_id,
                conversation.get("title", "Conversa exportada"), text, message.get("create_time"))

    def list(self):
        return [{key: value for key, value in entry.items() if key != "content_markdown"} for entry in self._entries()]

    def read(self, entry_id):
        if len(entry_id) != 32 or any(char not in "0123456789abcdef" for char in entry_id):
            raise ValueError("Identificador de histórico inválido")
        for entry in self._entries():
            if entry["entry_id"] == entry_id:
                return entry
        raise ValueError("Resultado não encontrado na pasta de histórico configurada")
