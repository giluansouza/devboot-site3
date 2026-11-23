"""Integration test against the isolated local stack through its HTTPS tunnel.

Uses the real OAuth provider (authorization code + PKCE), no ChatGPT session.
Creates one explicitly labelled demo article; never points at production.
"""
import asyncio
import base64
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import secrets
from urllib.parse import parse_qs, urlparse

import httpx
import jwt
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

LOCAL = Path(__file__).resolve().parents[2] / ".local" / "chatgpt"


class LoginForm(HTMLParser):
    action = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form" and attrs.get("id") == "kc-form-login":
            self.action = attrs["action"]


def tokens(origin, credentials):
    issuer = origin + "/auth/realms/devboot"
    with httpx.Client(timeout=30, trust_env=False) as client:
        metadata = client.get(issuer + "/.well-known/openid-configuration")
        metadata.raise_for_status()
        config = metadata.json()
        assert config["issuer"] == issuer
        for discovery in ["oauth-authorization-server", "openid-configuration"]:
            discovered = client.get(origin + "/.well-known/" + discovery + "/auth/realms/devboot")
            assert discovered.status_code == 200
            assert discovered.json()["issuer"] == issuer
        assert config["authorization_response_iss_parameter_supported"] is True
        verifier, state = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        redirect = "http://127.0.0.1:18977/callback"
        response = client.get(config["authorization_endpoint"], params={
            "client_id": "devboot-smoke", "response_type": "code", "redirect_uri": redirect,
            "scope": "blog:write offline_access", "state": state, "resource": origin + "/mcp",
            "code_challenge": challenge, "code_challenge_method": "S256"})
        response.raise_for_status()
        form = LoginForm()
        form.feed(response.text)
        assert form.action, "OAuth não apresentou o formulário de login"
        assert form.action.startswith(issuer + "/login-actions/"), "Destino de login inesperado"
        response = client.post(form.action, data={
            "username": credentials["username"], "password": credentials["password"], "credentialId": ""})
        assert response.status_code == 302, f"Login OAuth retornou {response.status_code}"
        callback = response.headers["location"]
        assert callback.startswith(redirect + "?"), "OAuth redirecionou para " + urlparse(callback).path
        query = parse_qs(urlparse(callback).query)
        assert query["state"] == [state]
        assert query["iss"] == [issuer]
        assert "code" in query, "OAuth não retornou um código"
        data = {"grant_type": "authorization_code", "code": query["code"][0],
            "redirect_uri": redirect, "client_id": "devboot-smoke",
            "client_secret": credentials["client_secret"], "code_verifier": verifier,
            "resource": origin + "/mcp"}
        response = client.post(config["token_endpoint"], data=data)
        assert response.status_code == 200, f"Token OAuth retornou {response.status_code}: {response.json().get('error_description', response.json().get('error'))}"
        token = response.json()
        assert "refresh_token" in token
        assert "offline_access" in token["scope"], "Renovação offline não concedida"
        # Provider may return an idle timeout, renewed on each use.
        assert token.get("refresh_expires_in", 0) == 0 or token["refresh_expires_in"] > 4 * 86400
        print("PASS OAuth real: login, PKCE, issuer e acesso offline", flush=True)
        renewed = client.post(config["token_endpoint"], data={
            "grant_type": "refresh_token", "refresh_token": token["refresh_token"],
            "client_id": "devboot-smoke", "client_secret": credentials["client_secret"],
            "resource": origin + "/mcp"})
        assert renewed.status_code == 200, f"Refresh retornou {renewed.status_code}"
        print("PASS renovação de acesso sem novo login", flush=True)
        # Check replay only after refresh: a rejected replay may revoke the session.
        assert client.post(config["token_endpoint"], data=data).status_code == 400
        print("PASS código de autorização de uso único", flush=True)
        claims = jwt.decode(renewed.json()["access_token"], options={"verify_signature": False})
        assert all(name in claims for name in ["sub", "iss", "aud", "exp", "scope"]), "Claims presentes: " + ", ".join(claims)
        assert "blog:write" in claims["scope"].split()
        assert claims["aud"] == origin + "/mcp" or origin + "/mcp" in claims["aud"]
        return renewed.json()["access_token"]


async def check_mcp(origin, access_token):
    async with httpx.AsyncClient(timeout=30, trust_env=False,
                                 headers={"Authorization": "Bearer " + access_token}) as http:
        async with streamable_http_client(origin + "/mcp", http_client=http) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listing = await session.list_tools()
                assert {tool.name for tool in listing.tools} == {"list_articles", "read_article", "create_article"}
                payload = {"edition_key": "teste-oauth-mcp-local", "slug": "teste-oauth-mcp-local",
                    "title": "Demonstração: publicação pelo MCP autenticado",
                    "excerpt": "Matéria de teste para verificar OAuth, publicação via MCP e proteção contra duplicações.",
                    "category": "Demonstração", "status": "published",
                    "content_markdown": "## Teste da integração\n\nEsta matéria demonstrativa foi enviada por um cliente MCP de teste, autenticado por OAuth com PKCE, ao blog local. Não é resultado de um agendamento do ChatGPT.\n\nO teste também verifica a renovação do acesso sem novo login e o reenvio da mesma edição sem duplicá-la."}
                for _ in range(2):
                    result = await session.call_tool("create_article", {"article": payload})
                    assert not result.isError, "MCP recusou a publicação"
                result = await session.call_tool("read_article", {"slug": payload["slug"]})
                assert not result.isError
    with httpx.Client(timeout=30, trust_env=False) as client:
        assert client.get(origin + "/blog/teste-oauth-mcp-local/").status_code == 200
        assert client.post(origin + "/mcp", json={}).status_code == 401
        for path in ["/api/blog/articles", "/auth/admin/", "/auth/realms/master/",
                     "/auth/realms/devboot/clients-registrations/openid-connect"]:
            assert client.get(origin + path).status_code == 404, path
    print("PASS MCP HTTP real: descoberta, publicação, leitura, reenvio e página HTML", flush=True)
    print("PASS acesso sem credencial recusado; administração inacessível pelo túnel", flush=True)


if __name__ == "__main__":
    connection = json.loads((LOCAL / "connection.json").read_text())
    origin = connection["url"].removesuffix("/mcp")
    assert urlparse(origin).hostname.endswith(".trycloudflare.com")
    credential = json.loads((LOCAL / "credentials.json").read_text())
    asyncio.run(check_mcp(origin, tokens(origin, credential)))
