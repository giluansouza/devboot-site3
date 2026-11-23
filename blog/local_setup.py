"""Prepare the isolated ChatGPT -> HTTPS MCP -> local blog test environment.

Start the tunnel first, then pass its HTTPS origin here. Secrets stay in .local.
This does not log into ChatGPT or edit any scheduled task.
"""
import argparse
import json
import os
from pathlib import Path
import re
import secrets

ROOT = Path(__file__).resolve().parent.parent
DIRECTORY = ROOT / ".local" / "chatgpt"


def prepare(origin):
    if not re.fullmatch(r"https://[a-z0-9-]+\.trycloudflare\.com", origin):
        raise ValueError("Informe somente a origem HTTPS do túnel temporário trycloudflare.com")
    DIRECTORY.mkdir(parents=True, exist_ok=True, mode=0o700)
    credentials_path = DIRECTORY / "credentials.json"
    if credentials_path.exists():
        credentials = json.loads(credentials_path.read_text())
    else:
        credentials = {"username": "editor", "password": secrets.token_urlsafe(32),
                       "api_token": secrets.token_urlsafe(48), "client_secret": secrets.token_urlsafe(48)}
        credentials_path.write_text(json.dumps(credentials, indent=2) + "\n")
    credentials_path.chmod(0o600)
    client = {
        "clientId": "devboot-chatgpt", "name": "Devboot Blog local", "enabled": True,
        "protocol": "openid-connect", "publicClient": False,
        "secret": credentials["client_secret"], "standardFlowEnabled": True,
        "directAccessGrantsEnabled": False, "serviceAccountsEnabled": False,
        "redirectUris": ["https://chatgpt.com/connector_platform_oauth_redirect"],
        "attributes": {"pkce.code.challenge.method": "S256"},
        "defaultClientScopes": ["blog:write"], "optionalClientScopes": ["offline_access"],
        "protocolMappers": [{"name": "blog-audience", "protocol": "openid-connect",
            "protocolMapper": "oidc-audience-mapper", "config": {
                "included.custom.audience": origin + "/mcp", "access.token.claim": "true",
                "id.token.claim": "false"}},
            {"name": "editor-subject", "protocol": "openid-connect",
             "protocolMapper": "oidc-sub-mapper",
             "config": {"access.token.claim": "true", "introspection.token.claim": "true"}}],
    }
    # Separate local callback for the end-to-end smoke test, never the ChatGPT client.
    smoke = dict(client, clientId="devboot-smoke", name="Local OAuth smoke test",
                 redirectUris=["http://127.0.0.1:18977/callback"])
    realm = {
        "realm": "devboot", "enabled": True, "sslRequired": "external",
        "registrationAllowed": False, "resetPasswordAllowed": False,
        "rememberMe": False, "bruteForceProtected": True,
        "accessTokenLifespan": 300, "ssoSessionIdleTimeout": 604800,
        "ssoSessionMaxLifespan": 2592000, "revokeRefreshToken": True,
        "refreshTokenMaxReuse": 0,
        "roles": {"realm": [{"name": "offline_access"}]},
        "clientScopes": [{"name": "blog:write", "protocol": "openid-connect",
            "attributes": {"include.in.token.scope": "true", "display.on.consent.screen": "true"}}],
        "clients": [client, smoke],
        "users": [{"username": credentials["username"], "enabled": True,
            "realmRoles": ["offline_access"],
            "firstName": "Editor", "lastName": "Devboot",
            "email": "editor@devboot.invalid", "emailVerified": False,
            "credentials": [{"type": "password", "value": credentials["password"], "temporary": False}]}],
    }
    # Parent directory is private; the mounted file must be readable by Keycloak's UID.
    realm_path = DIRECTORY / "realm.json"
    realm_path.write_text(json.dumps(realm, indent=2) + "\n")
    realm_path.chmod(0o644)
    env_path = DIRECTORY / "local.env"
    env_path.write_text(f"BLOG_BASE_URL={origin}\nBLOG_API_TOKEN={credentials['api_token']}\n")
    env_path.chmod(0o600)
    (DIRECTORY / "connection.json").write_text(json.dumps({
        "url": origin + "/mcp", "client_id": "devboot-chatgpt", "auth": "OAuth",
        "issuer": origin + "/auth/realms/devboot", "local_blog": "http://127.0.0.1:18976/blog/",
    }, indent=2) + "\n")
    # This file is only for the owner to copy into the ChatGPT connection form.
    instructions = DIRECTORY / "conectar.txt"
    instructions.write_text(
        f"Devboot Blog — teste local\n\nURL MCP: {origin}/mcp\nAutenticação: OAuth\n"
        f"Client ID: devboot-chatgpt\nClient secret: {credentials['client_secret']}\n\n"
        f"Login Devboot: {credentials['username']}\nSenha Devboot: {credentials['password']}\n\n"
        "Estas são credenciais do blog de teste, não da sua conta ChatGPT.\n"
        "Cadastre a conexão em Configurações > Apps no ChatGPT.\n"
        "Conclua o login Devboot e habilite a ferramenta no chat do agendamento.\n"
        "Faça uma publicação de teste antes de ativar a recorrência.\n")
    instructions.chmod(0o600)
    for schedule in ("terca", "sabado"):
        (DIRECTORY / f"agendamento-{schedule}.txt").write_text(
            "Mantenha a pauta, o horário e a recorrência atuais deste agendamento. "
            "Use exatamente o resumo que este agendamento acabou de produzir; "
            "não escreva uma nova matéria nem transforme, revise, resuma, amplie ou "
            "parafraseie o texto. Preserve cada palavra, pontuação, parágrafo, título, "
            "marcadores, emojis e links na mesma ordem. Envie o resumo completo, "
            "sem remover nem acrescentar texto, em content_markdown. "
            "Use o título que já aparece no resumo como title; se não houver, use "
            "a primeira linha textual existente, sem inventar um título. "
            "Use como excerpt um trecho literal de até 350 caracteres retirado do próprio resumo. "
            "Defina category como Tecnologia. "
            "Use a conexão MCP Devboot Blog para publicar esse conteúdo automaticamente. "
            "Consulte list_articles antes de publicar para evitar duplicações. "
            f"Use edition_key {schedule}-AAAA-MM-DD com a data da execução em America/Recife. "
            "Se essa edição já existir, consulte read_article e informe seu status; "
            "não crie outra chave nem sobrescreva o conteúdo. "
            "Chame create_article com os campos edition_key, slug, title, excerpt, "
            "content_markdown, category e status=published dentro do argumento article. "
            "Publique ao final de cada execução usando as permissões concedidas à conexão. "
            "Só informe sucesso após a ferramenta confirmar e retornar a URL da matéria. "
            "Se a ferramenta falhar ou exigir autorização, informe isso claramente e "
            "preserve a matéria na conversa para uma nova tentativa.\n")
    print(f"MCP: {origin}/mcp\nDados da conexão: {instructions}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("origin")
    args = parser.parse_args()
    os.umask(0o077)
    prepare(args.origin)
