# Deploying the blog to production

Until now the site shipped by `git pull` alone: nginx serves `public/` through a bind mount. The
blog changes that. It is a container with a **build**, a **volume**, a **`.env`** and an **nginx
config mount**, so a bare `git pull` is no longer the whole deploy. Order matters; follow it.

The owner runs everything below. The VPS account is `vps222` (deploys need `docker`).

## What is already true on the VPS (read-only check, 23/11/2026)

- `/opt/apps/devboot-site3` is a git checkout at `fda8d47`, clean, with a tracked
  `docker-compose.yml` (no `restart:` on `web`, no nginx conf mount).
- There is **no `.env`** there yet.
- `sudo -n /opt/infra/bin/status devboot-site3 <env>` answers `proj desconhecido: devboot-site3`
  for `prod` and `production`. The project is not registered with the status wrapper, and the env
  name is **unknown**. Registering it belongs to the foundation project, not to this repo.

## 1. The compose file

Production runs `/opt/apps/devboot-site3/docker-compose.yml`. The reference copy lives in
`~/dev/foundation/host/apps/devboot-site3/docker-compose.yml` (another project — do not edit it
from here). The `docker-compose.yml` on branch `blog` is that file plus the diff below, so a
`git pull` of master brings production's compose to the intended state. **The foundation copy
needs the same diff**, applied by whoever owns that repo, or the next sync-config will revert it.

```diff
@@ -7,6 +7,8 @@
     restart: unless-stopped
     volumes:
       - ./public:/usr/share/nginx/html:ro
+      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
+    # The landing must start even when the blog is down or unhealthy: no depends_on.
     labels:
       - traefik.enable=true
       - traefik.docker.network=debnet
@@ -22,7 +24,36 @@
       - traefik.http.services.devboot.loadbalancer.server.port=80
     networks:
         - debnet
+        - blog-internal
+
+  blog:
+    build: ./blog
+    restart: unless-stopped
+    environment:
+      BLOG_API_TOKEN: ${BLOG_API_TOKEN:?Configure BLOG_API_TOKEN no arquivo .env}
+      BLOG_BASE_URL: ${BLOG_BASE_URL:-https://www.devboot.com.br}
+      BLOG_ALLOW_AUTO_PUBLISH: ${BLOG_ALLOW_AUTO_PUBLISH:-false}
+      BLOG_OAUTH_ISSUER: ${BLOG_OAUTH_ISSUER:-}
+      BLOG_OAUTH_JWKS_URL: ${BLOG_OAUTH_JWKS_URL:-}
+    volumes:
+      - blog-data:/data
+    healthcheck:
+      test: ["CMD", "/app/.venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]
+      interval: 15s
+      timeout: 5s
+      retries: 3
+      start_period: 15s
+    security_opt:
+      - no-new-privileges:true
+    cap_drop:
+      - ALL
+    networks:
+      - blog-internal
 
 networks:
   debnet:
     external: true
+  blog-internal:
+
+volumes:
+  blog-data:
```

`web` has **no** `depends_on` on the blog: the landing starts and stays up whether the blog is
absent, stopped or unhealthy. `web` keeps `restart: unless-stopped` — do not drop it (a `no`
policy once left a site down for 96 days).

The `${BLOG_API_TOKEN:?...}` check makes **every** `docker compose` command fail, `web` included,
while `.env` has no token. So `.env` comes first.

## 2. Ordered commands (on the VPS, as `vps222`)

```sh
cd /opt/apps/devboot-site3

# 0. Remember where to roll back to.
PREV=$(git rev-parse HEAD); echo "$PREV"        # currently fda8d47...

# 1. .env with a token generated here. It never leaves the VPS and is never printed.
#    The umask is confined to this subshell. Set for the whole shell it makes `git pull`
#    create every new file 0600: the blog crash-looped (PermissionError: /app/app.py) and
#    nginx answered 403 for public/blog-down.html. Never `umask 077` outside the parentheses.
( umask 077; printf 'BLOG_API_TOKEN=%s\nBLOG_BASE_URL=https://www.devboot.com.br\n' "$(openssl rand -hex 32)" > .env )
ls -l .env                                       # -rw------- , owned by vps222
umask                                            # must print 0022 (or 0002), never 0077

# 2. Code: blog/, nginx/default.conf, the new compose, public/blog-down.html.
#    (master must already contain branch `blog`. The nav link is NOT in it — see §5.)
git pull --ff-only

#    Nothing the web server serves may be unreadable. This must print nothing:
find public nginx -type f ! -perm -o+r

# 3. Build and start the blog first; wait until it is healthy.
#    The image build fails (instead of the container crash-looping) if the runtime user cannot
#    read /app, and normalises file modes itself.
docker compose up -d --build --wait blog

# 4. Recreate web so it mounts nginx/default.conf and joins blog-internal (a second or two).
docker compose up -d --no-deps web
docker compose logs --tail 20 web                # no "[emerg]"
```

`BLOG_OAUTH_ISSUER` / `BLOG_OAUTH_JWKS_URL` stay empty here: publishing through the API with the
token works; the OAuth-protected MCP endpoint is **not** usable until those are configured. That is
a separate decision and not part of this deploy.

## 3. Verify

Container states (the owner's brief asked for the status wrapper; today it does not know this
project, so the env is `unknown`):

```sh
ssh vps222-claude 'sudo -n /opt/infra/bin/status devboot-site3 <env>'   # <env> = unknown
# until the wrapper knows the project, from vps222:
docker compose -f /opt/apps/devboot-site3/docker-compose.yml ps         # blog: healthy, web: running
```

Probes, from any machine:

```sh
for p in / /blog/ /blog/sitemap.xml /blog/feed.xml; do
  printf '%s ' "$p"; curl -s -o /dev/null -w '%{http_code}\n' "https://www.devboot.com.br$p"
done                                              # expect 200 four times

for p in sitemap.xml feed.xml; do                  # well-formed XML
  curl -s "https://www.devboot.com.br/blog/$p" | python3 -c 'import sys,xml.dom.minidom as m; m.parseString(sys.stdin.buffer.read()); print("well-formed")'
done
```

The first `/blog/` before any article is published should still be `200` (an empty index).

## 4. Rollback

Fastest, keeps everything: the landing is independent of the blog.

```sh
docker compose stop blog        # /blog/ now shows the "O blog está fora do ar" page; / stays 200
```

Full rollback to the previous release:

```sh
cd /opt/apps/devboot-site3
git checkout --detach "$PREV"                    # the sha from step 0
docker compose up -d --remove-orphans web        # removes the now-undeclared blog container
                                                 # and recreates web without the conf mount
```

`blog-data` is a named volume: it **survives** `stop`, `rm` and `--remove-orphans`, so the articles
are kept. **Never** `docker compose down -v` — that deletes it. When fixed, return with
`git switch master && git pull --ff-only` and repeat §2 from step 3. `.env` stays on disk.

Whether `blog-data` is covered by the VPS nightly backup is **unknown** (out of scope here; see
`docs/blog.md` for the SQLite backup command).

## 5. The "Blog" nav link and `Sitemap:` line ship last

Branch `blog-link` (one commit, off `blog`) adds the nav link in `public/index.html` and
`public/robots.txt` with `Sitemap: https://www.devboot.com.br/blog/sitemap.xml`. Because `public/`
is a live bind mount, those go public the moment the pull finishes. Merge and pull `blog-link`
**only after** `/blog/` answers 200 in production (step 3 above).
