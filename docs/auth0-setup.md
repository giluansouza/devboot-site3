# Auth0 for the blog MCP endpoint

The blog verifies OAuth tokens; it does not issue them. Auth0 is the provider (owner decision,
2026-11-23). This is what the owner configures, in order, and the two values that go into the
VPS `.env`.

**How to read this page.** Setting names in quotes were read on Auth0's and OpenAI's documentation
on 2026-11-23. Anything that page did not state is marked `unknown` and has a way to check it. No
dashboard label here is guessed: where I could not confirm one, the step names the *intent* and says
`unknown`. Replace `TENANT_DOMAIN` below with the tenant's own domain (shown in the dashboard).

## What the blog checks (so you know what Auth0 must produce)

Every request to `/mcp` needs a bearer token that is a JWT with:

| Claim | Must be | Source in Auth0 |
|---|---|---|
| signature | RS256 (ES256 also accepted), key from `BLOG_OAUTH_JWKS_URL` | API signing algorithm |
| `iss` | **exactly** `BLOG_OAUTH_ISSUER` | tenant |
| `aud` | contains `https://www.devboot.com.br/mcp` | API identifier |
| `exp`, `sub` | present | default |
| `scope` | a **space-delimited string** containing `blog:write` | API permission |

A `scope` that is not a string (for example a list) is refused with 401. Anything else wrong is 401
too. With the two env vars empty `/mcp` answers 503 ("not configured") — that is the state today.

## 1. The API (the MCP resource)

1. Create an API (Dashboard → Applications → APIs). Fields:
   - **Identifier** (the audience): `https://www.devboot.com.br/mcp` — exactly, no trailing slash.
     Auth0 states the Identifier cannot be changed after creation.
   - **Signing algorithm**: `RS256`. Also fixed at creation.
   - Name: anything (`Devboot Blog MCP`). The exact form fields and button labels of the *create*
     dialog: `unknown` (the page I read describes the settings screen, not the creation dialog).
2. Open the API → **Settings** tab (names as Auth0 documents them):
   - "JSON Web Token (JWT) Profile": leave `Auth0` unless there is a reason. After the first real
     token, decode it and confirm `scope` is a string (see §6); if the `RFC 9068` profile is ever
     chosen, re-check that.
   - "Maximum Access Token Lifetime (Seconds)": default 86400. Suggested: `3600`. Not required by
     the blog.
   - "Allow Offline Access": **on** (lets the client obtain refresh tokens, which recurring
     scheduled tasks need).
3. **Permissions** tab: add the permission `blog:write` (description: "Create blog drafts"). The
   exact add-permission field labels: `unknown`.
4. Only the owner may hold that permission — use RBAC:
   - API Settings → RBAC Settings → toggle "Enable RBAC". Leave "Add Permissions in the Access
     Token" optional: the blog reads the `scope` claim, not `permissions`.
   - With RBAC on, Auth0 documents that the token's `scope` is the intersection of what was
     requested and what the *user* is permitted. Create a role (e.g. `blog-editor`) carrying
     `blog:write` and assign it **only to the owner's user**. Anyone else who somehow logs in gets
     a token without `blog:write`, and the blog answers 401. The role/user screens' labels:
     `unknown`.

## 2. Tenant settings required by MCP clients

Dashboard → Settings → Advanced (Auth0 documents both toggles on this screen):

- **"Resource Parameter Compatibility Profile"**: **on**. ChatGPT sends the MCP server as the RFC 8707
  `resource` parameter, not Auth0's `audience`; without this profile Auth0 does not set the token
  audience from `resource` and the login fails with an audience error. Limitation stated by Auth0:
  if a request carries both parameters, `audience` wins; and `resource` is not forwarded to upstream
  identity providers (we use none).
- **"Include Issuer in Authorization Responses"**: **on**. This is what lets ChatGPT use its stable
  callback `https://chatgpt.com/connector_platform_oauth_redirect`. OpenAI requires every response,
  errors included, to carry an `iss` that matches the issuer exactly.

## 3. How ChatGPT registers — choose the predefined client

OpenAI documents three ways: CIMD (preferred by ChatGPT when the server advertises it), Dynamic
Client Registration (DCR, when the server has a `registration_endpoint`), and a **predefined
OAuth client**. Findings today:

- **CIMD with Auth0**: a public Auth0 community report says Auth0's registration endpoint rejects
  ChatGPT's metadata document while its preview validates it; no fix was confirmed. Treat as not
  working (`unknown` whether fixed since).
- **DCR with Auth0**: works (reported) but opens client registration to anyone who can reach the
  tenant's registration endpoint; Auth0 lists the mitigations (tenant ACL, a reverse proxy) as
  Enterprise features. DCR clients are third-party apps, which needs extra setup Auth0's DCR page
  does not spell out (promotion to first-party, domain-level connections): `unknown`.
- **Predefined client** (recommended): keeps DCR off, so nobody can register clients against the
  tenant, and the blog's owner-only rule is easy to reason about.

Steps for the predefined client:

1. Create an Application of the "Regular Web Application" kind (the exact name of the type in
   today's dashboard: `unknown`). Note its Client ID and Client Secret.
2. Allowed Callback URLs: `https://chatgpt.com/connector_platform_oauth_redirect`. If ChatGPT's
   connector page shows a different URL (`https://chatgpt.com/connector/oauth/{callback_id}`), add
   **exactly** the one it shows; OpenAI says the management page displays the URI to allowlist. No
   wildcards.
3. Grant types: authorization code and refresh token only. PKCE S256 is enforced by ChatGPT; Auth0
   supports it. The field names for grant types: `unknown`.
4. Authorise this application to access the API of §1 with the permission `blog:write`
   (Application → APIs tab, or the API's Machine/Application access settings — which one today:
   `unknown`).
5. Keep "DCR" (Settings → Advanced → "Dynamic Client Registration (DCR)") **off**. It is off by
   default.
6. In ChatGPT's custom-connector form enter the MCP URL `https://www.devboot.com.br/mcp`, choose
   OAuth, and give the Client ID/Secret. Whether today's ChatGPT UI accepts a predefined client for
   a custom MCP connector, and its field labels: `unknown` — if it does not, fall back to DCR and
   note that §3 mitigations apply.

### Restricting sign-in to the owner

Defence in depth, any one of these is enough *because* §1.4 already withholds `blog:write` from
everyone else:

- Create the owner's user and nobody else; turn off public sign-ups on the login connection
  (the setting's exact name: `unknown`).
- Optionally a post-login Action that denies anyone but the owner's email. Auth0 supports Actions;
  the exact `api.access.deny` call and trigger name were not verified here: `unknown`.

## 4. The two values for the VPS `.env`

Read them from the tenant's discovery document — do not type them from memory:

```sh
curl -s https://TENANT_DOMAIN/.well-known/openid-configuration \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); print("issuer:", repr(d["issuer"])); print("jwks_uri:", d["jwks_uri"])'
```

```
BLOG_OAUTH_ISSUER=<the issuer value, character for character>
BLOG_OAUTH_JWKS_URL=<the jwks_uri value>
```

- Auth0 issuers normally end with `/` (`https://TENANT_DOMAIN/`) and the JWKS is normally at
  `https://TENANT_DOMAIN/.well-known/jwks.json`. The pages I read do not state either (`unknown`),
  which is why you copy them from the document above. The blog compares `iss` with
  `BLOG_OAUTH_ISSUER` byte for byte; a missing slash makes every token 401.
- Both must be `https://` (the app refuses to start otherwise).
- A custom domain on the tenant changes the issuer; use whatever `issuer` prints.

After editing `.env` on the VPS, recreate only the blog (env changes are not picked up by a restart):

```sh
cd /opt/apps/devboot-site3
docker compose up -d --no-deps --force-recreate blog
```

## 5. The approval page (later)

The phone page where the owner approves drafts will use the **same Auth0 tenant** for the owner's
login, as a separate Application and the same user. Nothing to configure now; the details come
with that page's design.

## 6. Verification

From any machine, in this order:

```sh
# a. MCP is configured (no longer 503) and challenges correctly:
curl -si -X POST https://www.devboot.com.br/mcp | head -n 5      # expect 401, www-authenticate: Bearer ... resource_metadata=...

# b. The blog advertises the right resource and authorization server:
curl -s https://www.devboot.com.br/.well-known/oauth-protected-resource/mcp
#    expect "resource": "https://www.devboot.com.br/mcp", "authorization_servers": [<your issuer>]
#    and "scopes_supported": ["blog:write", "offline_access"]

# c. The authorization server meets ChatGPT's needs:
curl -s https://TENANT_DOMAIN/.well-known/openid-configuration | python3 -c 'import sys,json; d=json.load(sys.stdin); print({k:d.get(k) for k in ("code_challenge_methods_supported","authorization_response_iss_parameter_supported","registration_endpoint")})'
#    expect S256 in the list, iss parameter True, and registration_endpoint absent while DCR is off
```

Then connect ChatGPT (§3) and run `list_articles`. A successful connection is the only complete
check. To inspect a real token once, decode its payload (never share it) and confirm:
`iss` equals `BLOG_OAUTH_ISSUER`, `aud` contains `https://www.devboot.com.br/mcp`, `scope` is a
string containing `blog:write`. A token with `scope` as a list, or without `blog:write`, is refused
with 401 by design.

If the connection fails with an audience error → §2, "Resource Parameter Compatibility Profile".
If every call is 401 though login worked → compare `iss` (trailing slash) and `aud` as above.

## 7. Required before the automation is called active: the refresh-token check

Scheduled runs are 3–4 days apart and an access token lasts minutes. If the provider issued no
refresh token, the first run after setup gets a 401 and the article is lost for that run. The blog
advertises `offline_access` next to `blog:write` — in `scopes_supported` and in the 401
challenge's `scope` — so the client asks for it. It does **not** require it: a token is accepted
with `blog:write` alone. (RFC 6750 reads a challenge's `scope` as what the *token* needs; the blog
lists `offline_access` there only so MCP clients, which treat the challenge as authoritative, request
a refresh token. The token check is unchanged.) Whether ChatGPT then actually requests it and keeps
the refresh token is the thing to prove:

1. Make the test fast: API → Settings → "Maximum Access Token Lifetime (Seconds)" = `300`.
   Remember to set it back afterwards (the value to keep: your choice, §1).
2. Connect ChatGPT (§3) and call `list_articles` once from the chat the scheduled task uses.
3. Wait more than 300 seconds.
4. Call `list_articles` again from the **scheduled task's chat** (not a fresh connection). It must
   succeed without asking to log in again.
5. Confirm in the Auth0 dashboard (Monitoring → Logs) that the second call was a **refresh-token
   exchange**, not a new login. The log entry's exact type code and wording: `unknown` — look for
   the entry between the two calls that is not a user login.

If step 4 asks you to log in again, or step 5 shows no refresh-token exchange, the automation is
**not** active: check "Allow Offline Access" on the API (§1.2), that the application is allowed to
use refresh tokens, and that the connector requested the `offline_access` scope. Do not enable the
schedules until this passes.

## Sources

- Auth0: [Dynamic Client Registration for MCP](https://auth0.com/ai/docs/mcp/guides/registering-your-mcp-client-application/dynamic-client-registration), [Resource Parameter Compatibility Profile](https://auth0.com/ai/docs/mcp/guides/resource-param-compatibility-profile), [API settings](https://auth0.com/docs/get-started/apis/api-settings), [RBAC for APIs](https://auth0.com/docs/get-started/apis/enable-role-based-access-control-for-apis)
- OpenAI: [Authentication for apps/connectors](https://developers.openai.com/apps-sdk/build/auth)
- Community report on Auth0 CIMD vs ChatGPT: [community.auth0.com thread](https://community.auth0.com/t/auth0-cimd-registration-appears-incompatible-with-the-current-chatgpt-client-id-metadata-document/203817) (anecdotal, unresolved)
