import asyncio
import hmac
import json
import math
import mimetypes
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from xml.etree.ElementTree import Element, SubElement, tostring

import jwt
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown_it import MarkdownIt
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import ValidationError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from store import ArticleInput, Conflict, Store, xml_safe

ROOT = Path(__file__).parent
# python:3.12-slim has no /etc/mime.types and the built-in table lacks woff2: without this the
# fonts are served text/plain in production (and ignored by browsers under nosniff).
mimetypes.add_type("font/woff2", ".woff2")
templates = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape())
templates.filters["date_br"] = lambda value: datetime.fromisoformat(value).strftime("%d.%m.%Y")
markdown = MarkdownIt("commonmark", {"html": False, "linkify": False})
# Scopes advertised to clients (RFC 9728 scopes_supported and the 401 challenge). offline_access is
# asked for so the provider issues a refresh token: scheduled runs are days apart and an access
# token lasts minutes. It is NOT required of a token: verify_oauth demands blog:write only.
ADVERTISED_SCOPES = ["blog:write", "offline_access"]
SECURITY_SCHEMES = [{"type": "oauth2", "scopes": ADVERTISED_SCOPES}]


class BlogMCP(FastMCP):
    async def call_tool(self, name, arguments):
        try:
            return await super().call_tool(name, arguments)
        except ToolError as exc:
            if isinstance(exc.__cause__, ValidationError):
                # Pydantic's own text echoes input_value=<what was submitted>. Say which field
                # failed and why, never the content (it is the editor's unpublished draft).
                raise ToolError("Campos inválidos: " + "; ".join(
                    f"{'.'.join(str(part) for part in error['loc'])}: {error['msg'].removeprefix('Value error, ')}"
                    for error in exc.__cause__.errors(include_url=False, include_input=False, include_context=False))) from None
            raise

    async def list_tools(self):
        # ChatGPT uses the tool descriptor to offer account linking.
        tools = await super().list_tools()
        return [tool.model_validate(tool.model_dump(by_alias=True) | {
            "securitySchemes": SECURITY_SCHEMES,
            "_meta": {**(tool.meta or {}), "securitySchemes": SECURITY_SCHEMES},
        }) for tool in tools]


@dataclass(frozen=True)
class Settings:
    database: str = "/data/blog.sqlite3"
    base_url: str = "https://www.devboot.com.br"
    api_token: str = ""
    allow_auto_publish: bool = False
    oauth_issuer: str = ""
    oauth_jwks_url: str = ""

    @classmethod
    def from_env(cls):
        return cls(database=os.getenv("BLOG_DB", "/data/blog.sqlite3"),
            base_url=os.getenv("BLOG_BASE_URL", "https://www.devboot.com.br").rstrip("/"),
            api_token=os.getenv("BLOG_API_TOKEN", ""),
            allow_auto_publish=os.getenv("BLOG_ALLOW_AUTO_PUBLISH", "false").lower() == "true",
            oauth_issuer=os.getenv("BLOG_OAUTH_ISSUER", ""),
            oauth_jwks_url=os.getenv("BLOG_OAUTH_JWKS_URL", ""))


class Auth:
    def __init__(self, settings):
        self.settings = settings
        self.jwks = jwt.PyJWKClient(settings.oauth_jwks_url, timeout=5) if settings.oauth_jwks_url else None

    def verify_oauth(self, token):
        key = self.jwks.get_signing_key_from_jwt(token)
        claims = jwt.decode(token, key.key, algorithms=["RS256", "ES256"],
            issuer=self.settings.oauth_issuer, audience=self.settings.base_url + "/mcp",
            options={"require": ["exp", "iss", "aud", "sub"]})
        scope = claims.get("scope", "")
        # RFC 8693/9068: a space-delimited string. Any other type is a malformed token, not a crash.
        if not isinstance(scope, str) or "blog:write" not in scope.split():
            raise jwt.InvalidTokenError("Missing blog:write scope")


class Protection:
    """Separate manual API credentials from OAuth credentials used by ChatGPT."""
    def __init__(self, app, auth):
        self.app, self.auth = app, auth

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope["path"]
        private_api = path == "/api/blog" or path.startswith("/api/blog/")
        mcp = path == "/mcp" or path.startswith("/mcp/")
        settings = self.auth.settings
        if private_api or mcp:
            headers = dict(scope["headers"])
            authorization = headers.get(b"authorization", b"").decode("latin1")
            token = authorization[7:] if authorization.startswith("Bearer ") else ""
            if private_api:
                if len(settings.api_token) < 32:
                    return await JSONResponse({"error": "API de publicação não configurada"}, 503)(scope, receive, send)
                valid = bool(token) and hmac.compare_digest(token.encode(), settings.api_token.encode())
            else:
                if not self.auth.jwks or not settings.oauth_issuer:
                    return await JSONResponse({"error": "Conexão OAuth ainda não configurada"}, 503)(scope, receive, send)
                try:
                    await asyncio.to_thread(self.auth.verify_oauth, token)
                    valid = True
                except (jwt.PyJWTError, ValueError):
                    valid = False
            if not valid:
                challenge = 'Bearer realm="Devboot Blog"'
                if mcp:
                    challenge += f', resource_metadata="{settings.base_url}/.well-known/oauth-protected-resource/mcp", scope="{' '.join(ADVERTISED_SCOPES)}"'
                return await JSONResponse({"error": "Não autorizado"}, 401,
                    headers={"WWW-Authenticate": challenge, "Cache-Control": "no-store"})(scope, receive, send)

        async def secure_send(message):
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                response_headers.extend([
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"content-security-policy", b"default-src 'self'; script-src 'none'; style-src 'self'; img-src 'self' https:; font-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"),
                ])
                if private_api or mcp:
                    response_headers.append((b"cache-control", b"no-store"))
                message["headers"] = response_headers
            await send(message)
        await self.app(scope, receive, secure_send)


def create_app(settings=None):
    settings = settings or Settings.from_env()
    if urlparse(settings.base_url).scheme not in {"https", "http"} or not urlparse(settings.base_url).netloc:
        raise ValueError("BLOG_BASE_URL inválida")
    for endpoint in (settings.oauth_issuer, settings.oauth_jwks_url):
        if endpoint and urlparse(endpoint).scheme != "https":
            raise ValueError("OAuth exige HTTPS")
    store = Store(settings.database)
    auth = Auth(settings)
    base = urlparse(settings.base_url)
    host = base.netloc
    # Traefik routes both www and the bare domain to this service; accept both, whichever the
    # configured base URL names.
    bare = host.removeprefix("www.")
    hosts = [bare, "www." + bare]
    mcp = BlogMCP("Devboot Blog", stateless_http=True, json_response=True,
        streamable_http_path="/mcp", transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True, allowed_hosts=[*hosts, "testserver", "localhost:*", "127.0.0.1:*"],
            allowed_origins=[f"{base.scheme}://{h}" for h in hosts]))

    def outcome(saved, created):
        """Machine-readable result of a create request, in Portuguese for the scheduled task to relay."""
        awaiting = saved["status"] != "published"
        return {"created": created, "status": saved["status"], "awaiting_approval": awaiting,
                "message": "Recebida como rascunho; aguarda aprovação do editor." if awaiting else "Matéria publicada.",
                "article": presentation(saved)}

    def presentation(article):
        return {key: value for key, value in article.items() if key not in {"fingerprint", "id"}} | {
            "url": settings.base_url + "/blog/" + article["slug"] + "/" if article["status"] == "published" else None}

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=True))
    def create_article(article: ArticleInput) -> dict:
        """Cria uma matéria no blog Devboot. Use Markdown com fontes verificáveis.

        edition_key deve ser estável por agendamento e data (ex.: terca-2026-10-20).
        Com a publicação automática desligada, a matéria é guardada como rascunho mesmo com
        status=published e aguarda aprovação do editor. Relate ao usuário exatamente o `status`
        e a `message` devolvidos pela ferramenta, sem acrescentar nem presumir o que não constar
        na resposta.
        Reenvio idêntico devolve o artigo existente; divergências geram erro.
        Nunca invente uma nova edition_key para contornar um conflito.
        """
        saved, created = store.save(article, settings.allow_auto_publish)
        return outcome(saved, created)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
    def list_articles() -> list[dict]:
        """Lista títulos, edições, slugs, resumos e status para evitar pautas duplicadas."""
        return [{key: value for key, value in presentation(a).items() if key != "content_markdown"}
                for a in store.list(public=False)]

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
    def read_article(slug: str) -> dict:
        """Lê um artigo existente, inclusive rascunhos, para conferir conteúdo e edição."""
        article = store.get(slug, public=False)
        if not article:
            raise ValueError("Artigo não encontrado")
        return presentation(article)

    def render(name, status=200, **context):
        return HTMLResponse(templates.get_template(name).render(base_url=settings.base_url, **context), status_code=status)

    async def index(request):
        return render("index.html", articles=store.list(), title="Blog Devboot — Tecnologia aplicada a negócios",
            description="Software, automação e tecnologia: ideias e análises para transformar a operação do seu negócio.",
            canonical=settings.base_url + "/blog/")

    async def detail(request):
        article = store.get(request.path_params["slug"])
        if not article:
            return render("404.html", status=404, title="Artigo não encontrado — Devboot", description="Artigo não encontrado.", canonical=None)
        if not request.url.path.endswith("/"):
            return RedirectResponse("/blog/" + article["slug"] + "/", status_code=308)
        url = settings.base_url + "/blog/" + article["slug"] + "/"
        return render("article.html", article=article, content=markdown.render(article["content_markdown"]),
            reading_time=max(1, math.ceil(len(article["content_markdown"].split()) / 200)),
            title=article["title"] + " — Devboot", description=article["excerpt"], canonical=url,
            structured_data={"@context": "https://schema.org", "@type": "BlogPosting",
                "headline": article["title"], "description": article["excerpt"],
                "datePublished": article["published_at"], "mainEntityOfPage": url,
                "author": {"@type": "Organization", "name": "Devboot", "url": settings.base_url},
                "publisher": {"@type": "Organization", "name": "Devboot"}})

    async def feed(request):
        rss = Element("rss", version="2.0")
        channel = SubElement(rss, "channel")
        for key, value in {"title": "Blog Devboot", "link": settings.base_url + "/blog/", "description": "Tecnologia aplicada a negócios", "language": "pt-BR"}.items():
            SubElement(channel, key).text = value
        for article in store.list():
            item = SubElement(channel, "item")
            url = settings.base_url + "/blog/" + article["slug"] + "/"
            for key, value in {"title": article["title"], "link": url, "guid": url,
                "description": article["excerpt"], "pubDate": datetime.fromisoformat(article["published_at"]).strftime("%a, %d %b %Y %H:%M:%S GMT")}.items():
                SubElement(item, key).text = xml_safe(value)
        return Response(tostring(rss, encoding="utf-8", xml_declaration=True), media_type="application/rss+xml")

    async def sitemap(request):
        root = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        SubElement(SubElement(root, "url"), "loc").text = settings.base_url + "/blog/"
        for article in store.list():
            node = SubElement(root, "url")
            SubElement(node, "loc").text = settings.base_url + "/blog/" + article["slug"] + "/"
            SubElement(node, "lastmod").text = article["published_at"]
        return Response(tostring(root, encoding="utf-8", xml_declaration=True), media_type="application/xml")

    async def articles_api(request):
        if request.method == "GET":
            return JSONResponse({"articles": [presentation(a) for a in store.list(public=False)]})
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 256_000:
                return JSONResponse({"error": "Artigo excede o limite de envio"}, 413)
        try:
            article = ArticleInput.model_validate_json(body)
            saved, created = store.save(article, settings.allow_auto_publish)
            return JSONResponse(outcome(saved, created), 201 if created else 200)
        except ValidationError as exc:
            # Name each failing field and why, never the submitted values.
            fields = [{"field": ".".join(str(part) for part in error["loc"]) or "body",
                       "reason": error["msg"].removeprefix("Value error, ")}
                      for error in exc.errors(include_url=False, include_input=False, include_context=False)]
            return JSONResponse({"error": "JSON ou campos inválidos. Consulte docs/blog.md.", "fields": fields}, 422)
        except Conflict as exc:
            return JSONResponse({"error": str(exc)}, 409)

    async def publish_api(request):
        # Manual review endpoint: separate API credential, never exposed as an MCP tool.
        article = store.publish(request.path_params["slug"])
        return JSONResponse({"article": presentation(article)}) if article else JSONResponse({"error": "Artigo não encontrado"}, 404)

    async def metadata(request):
        if not settings.oauth_issuer:
            return JSONResponse({"error": "OAuth não configurado"}, 503)
        return JSONResponse({"resource": settings.base_url + "/mcp",
            "authorization_servers": [settings.oauth_issuer], "scopes_supported": ADVERTISED_SCOPES,
            "bearer_methods_supported": ["header"]})

    async def health(request):
        return JSONResponse({"status": "ok"})

    @asynccontextmanager
    async def lifespan(app):
        async with mcp.session_manager.run():
            yield

    app = Starlette(routes=[
        Route("/health", health), Route("/blog/", index),
        Route("/blog/feed.xml", feed), Route("/blog/sitemap.xml", sitemap),
        Mount("/blog/assets", app=StaticFiles(directory=ROOT / "static")),
        Route("/blog/{slug}/", detail), Route("/blog/{slug}", detail),
        Route("/api/blog/articles", articles_api, methods=["GET", "POST"]),
        Route("/api/blog/articles/{slug}/publish", publish_api, methods=["POST"]),
        Route("/.well-known/oauth-protected-resource", metadata),
        Route("/.well-known/oauth-protected-resource/mcp", metadata),
        # Root mount last preserves /mcp with no redirect to /mcp/.
        Mount("/", app=mcp.streamable_http_app()),
    ], lifespan=lifespan)
    app.state.store, app.state.auth = store, auth
    app.add_middleware(Protection, auth=auth)
    return app
