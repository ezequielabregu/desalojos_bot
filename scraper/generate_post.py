"""Genera un post Jekyll (_posts/YYYY-MM-DD-slug.md) a partir de un Article."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from fetch_sources import Article


def slugify(text: str, max_words: int = 12) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()
    ascii_text = re.sub(r"[^a-z0-9\s-]", "", ascii_text)
    words = ascii_text.split()[:max_words]
    return "-".join(words).strip("-") or "noticia"


def escape_yaml_string(value: str) -> str:
    return value.replace('"', '\\"')


def write_post(article: Article, posts_dir: Path) -> Path:
    posts_dir.mkdir(parents=True, exist_ok=True)

    date_str = article.published.strftime("%Y-%m-%d")
    slug = slugify(article.title)
    path = posts_dir / f"{date_str}-{slug}.md"

    suffix = 2
    while path.exists():
        path = posts_dir / f"{date_str}-{slug}-{suffix}.md"
        suffix += 1

    front_matter = (
        "---\n"
        "layout: post\n"
        f'title: "{escape_yaml_string(article.title)}"\n'
        f"date: {article.published.strftime('%Y-%m-%d %H:%M:%S %z')}\n"
        f'source: "{escape_yaml_string(article.source)}"\n'
        f'original_url: "{article.link}"\n'
        "---\n\n"
    )

    body_parts = []
    if article.summary:
        body_parts.append(article.summary.strip())
    body_parts.append(f"**Leer la nota completa en [{article.source}]({article.link}).**")

    path.write_text(front_matter + "\n\n".join(body_parts) + "\n", encoding="utf-8")
    return path
