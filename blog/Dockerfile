FROM ghcr.io/astral-sh/uv:0.12.10 AS uv
FROM python:3.12-slim
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
# Normalise modes: a build context checked out under a restrictive umask (0600 files) would
# otherwise land root-owned and unreadable by the runtime user.
COPY --chmod=u=rwX,go=rX . .
RUN useradd --uid 10001 --create-home blog && mkdir /data && chown blog:blog /data
USER blog
# Fail the build, not the container, if the runtime user cannot read the app tree.
RUN bad="$(find /app \( -not -readable -o \( -type d -not -executable \) \) -print)"; \
    [ -z "$bad" ] || { echo "unreadable by the runtime user:" >&2; echo "$bad" >&2; exit 1; }
ENV BLOG_DB=/data/blog.sqlite3
EXPOSE 8000
CMD [".venv/bin/uvicorn", "app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
