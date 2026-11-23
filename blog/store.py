"""Persistent articles. Retries never overwrite an existing editorial edition."""

import hashlib
import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Characters XML 1.0 cannot carry (C0 controls except tab/newline/CR, surrogates, U+FFFE/FFFF).
XML_INVALID = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")


def xml_safe(value):
    """Drop what XML cannot carry. Used when rendering feeds, for rows stored before validation."""
    return XML_INVALID.sub("", value) if isinstance(value, str) else value


class ArticleInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    edition_key: str = Field(min_length=3, max_length=120, pattern=r"^[a-z0-9][a-z0-9._-]+$")
    slug: str = Field(min_length=3, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=5, max_length=180)
    excerpt: str = Field(min_length=20, max_length=350)
    content_markdown: str = Field(min_length=100, max_length=100_000)
    category: str = Field(default="Tecnologia", min_length=2, max_length=60)
    status: Literal["draft", "published"] = "draft"

    @field_validator("title", "excerpt", "category")
    @classmethod
    def no_control_characters(cls, value):
        # A C0 control in a title made /blog/feed.xml unparseable for every article.
        if XML_INVALID.search(value):
            raise ValueError("Caracteres de controle não são permitidos")
        return value

    @field_validator("slug")
    @classmethod
    def reserved_slug(cls, value):
        if value in {"feed", "sitemap", "assets"}:
            raise ValueError("Slug reservado")
        return value


class Conflict(ValueError):
    pass


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY, edition_key TEXT NOT NULL UNIQUE,
                slug TEXT NOT NULL UNIQUE, title TEXT NOT NULL, excerpt TEXT NOT NULL,
                content_markdown TEXT NOT NULL, category TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('draft','published')),
                created_at TEXT NOT NULL, published_at TEXT, fingerprint TEXT NOT NULL
            )""")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def save(self, article: ArticleInput, allow_auto_publish: bool):
        data = article.model_dump()
        fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if data["status"] == "published" and not allow_auto_publish:
            raise PermissionError("Publicação automática desativada. Envie status=draft e revise antes de publicar.")
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT * FROM articles WHERE edition_key = ?", (article.edition_key,)).fetchone()
            if existing:
                if existing["fingerprint"] != fingerprint:
                    raise Conflict("Esta edição já existe com outro conteúdo. Consulte-a antes de tentar novamente.")
                return dict(existing), False
            try:
                row = db.execute("""INSERT INTO articles
                    (edition_key,slug,title,excerpt,content_markdown,category,status,created_at,published_at,fingerprint)
                    VALUES (:edition_key,:slug,:title,:excerpt,:content_markdown,:category,:status,:created_at,:published_at,:fingerprint)
                    RETURNING *""", {**data, "created_at": now,
                        "published_at": now if article.status == "published" else None,
                        "fingerprint": fingerprint}).fetchone()
            except sqlite3.IntegrityError as exc:
                raise Conflict("Este slug já pertence a outro artigo. Escolha um slug diferente.") from exc
            return dict(row), True

    def get(self, slug, public=True):
        with self.connect() as db:
            row = db.execute("SELECT * FROM articles WHERE slug = ?" +
                (" AND status = 'published'" if public else ""), (slug,)).fetchone()
        return dict(row) if row else None

    def list(self, public=True):
        with self.connect() as db:
            rows = db.execute("SELECT * FROM articles" + (" WHERE status = 'published'" if public else "") +
                " ORDER BY COALESCE(published_at, created_at) DESC, id DESC LIMIT 500").fetchall()
        return [dict(row) for row in rows]

    def publish(self, slug):
        with self.connect() as db:
            db.execute("UPDATE articles SET status = 'published', published_at = COALESCE(published_at, ?) WHERE slug = ?",
                (datetime.now(timezone.utc).isoformat(), slug))
        return self.get(slug, public=False)
