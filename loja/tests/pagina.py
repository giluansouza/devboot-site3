"""A small strict HTML reader for the tests: well-formedness plus what a page declares."""
import json
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source",
        "track", "wbr"}


class Pagina(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.problemas = []
        self.pilha = []
        self.ids = []
        self.meta = {}
        self.links = []        # (tag, attrs)
        self.jsonld = []
        self.titulo = ""
        self.texto = []
        self.classes = []
        self.html_attrs = {}
        self.doctype = False
        self.ordem = []        # ("script"|"stylesheet", index) as met in <head>
        self._em = None
        self._buf = ""
        self._silencio = 0
        self.feed(html)
        self.close()
        if self.pilha:
            self.problemas.append(f"unclosed tags: {self.pilha}")

    def handle_decl(self, decl):
        if decl.lower().startswith("doctype html"):
            self.doctype = True

    def _abrir(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if a.get("class"):
            self.classes += a["class"].split()
        if tag == "html":
            self.html_attrs = a
        if tag == "meta":
            k = a.get("name") or a.get("property")
            if k:
                self.meta[k] = a.get("content", "")
        if tag in ("a", "link", "img", "script", "use", "source") or "href" in a or "src" in a:
            self.links.append((tag, a))
        if tag == "link" and a.get("rel") == "stylesheet":
            self.ordem.append(("stylesheet", a.get("href")))
        if tag == "script":
            if a.get("type") == "application/ld+json":
                self._em, self._buf = "ld", ""
            elif not a.get("src"):
                self._em, self._buf = "script", ""
            else:
                self.ordem.append(("script-src", a["src"]))
        if tag == "title":
            self._em, self._buf = "title", ""
        if tag in ("script", "style"):
            self._silencio += 1

    def handle_starttag(self, tag, attrs):
        self._abrir(tag, attrs)
        if tag not in VOID:
            self.pilha.append(tag)

    def handle_startendtag(self, tag, attrs):
        self._abrir(tag, attrs)
        if tag in ("script", "style"):
            self._silencio -= 1

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.pilha or self.pilha[-1] != tag:
            self.problemas.append(f"</{tag}> closes {self.pilha[-1:] or 'nothing'}")
            if tag in self.pilha:
                while self.pilha and self.pilha.pop() != tag:
                    pass
            return
        self.pilha.pop()
        if tag in ("script", "style"):
            self._silencio -= 1
        if tag == "title" and self._em == "title":
            self.titulo, self._em = self._buf.strip(), None
        if tag == "script" and self._em == "ld":
            try:
                self.jsonld.append(json.loads(self._buf))
            except json.JSONDecodeError as e:
                self.problemas.append(f"invalid JSON-LD: {e}")
            self._em = None
        elif tag == "script" and self._em == "script":
            self.ordem.append(("script", self._buf))
            self._em = None

    def handle_data(self, data):
        if self._em:
            self._buf += data
        elif not self._silencio:
            self.texto.append(data)

    @property
    def visivel(self):
        return " ".join(" ".join(self.texto).split())

    def hrefs(self, tag="a"):
        return [a.get("href") for t, a in self.links if t == tag and a.get("href") is not None]
