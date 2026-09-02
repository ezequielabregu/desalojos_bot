"""Punto de entrada del bot.

Obtiene noticias de las fuentes confiables, filtra por palabras clave de
desalojo, descarta duplicados ya publicados y genera un post Jekyll por cada
noticia nueva.
"""

from __future__ import annotations

import json
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))

from fetch_sources import Article, fetch_all
from generate_post import write_post

BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
SEEN_PATH = BASE_DIR / "data" / "seen.json"
POSTS_DIR = BASE_DIR.parent / "_posts"
STATUS_PATH = BASE_DIR.parent / "_data" / "status.yml"
ARGENTINA_UTC_OFFSET = timedelta(hours=-3)


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()


def load_yaml_list(path: Path, key: str) -> list:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get(key, [])


def load_seen() -> set[str]:
    if not SEEN_PATH.exists():
        return set()
    with SEEN_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("seen_ids", []))


def save_seen(seen_ids: set[str]) -> None:
    SEEN_PATH.write_text(
        json.dumps({"seen_ids": sorted(seen_ids)}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def save_status(sources_count: int, articles_count: int, new_count: int) -> None:
    """Registra que el bot corrió, incluso si no encontró noticias nuevas.

    Esto es lo que permite monitorear en el sitio si el cron de GitHub
    Actions se sigue ejecutando (ver /about/): una fecha de "última
    verificación" muy vieja indica que el cron dejó de dispararse, algo
    que no se notaría mirando solo la fecha del último post publicado.
    """
    now_utc = datetime.now(timezone.utc)
    now_ar = now_utc + ARGENTINA_UTC_OFFSET

    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    content = (
        f'last_checked_utc: "{now_utc.strftime("%Y-%m-%d %H:%M UTC")}"\n'
        f'last_checked_ar: "{now_ar.strftime("%d/%m/%Y %H:%M")} hs (Argentina)"\n'
        f"sources_checked: {sources_count}\n"
        f"articles_reviewed: {articles_count}\n"
        f"new_articles: {new_count}\n"
    )
    STATUS_PATH.write_text(content, encoding="utf-8")


def matches_keywords(article: Article, keywords: list[str], exclude_keywords: list[str]) -> bool:
    haystack = normalize(f"{article.title} {article.summary}")
    if any(normalize(keyword) in haystack for keyword in exclude_keywords):
        return False
    return any(normalize(keyword) in haystack for keyword in keywords)


def main() -> None:
    sources = load_yaml_list(CONFIG_DIR / "sources.yaml", "sources")
    keywords = load_yaml_list(CONFIG_DIR / "keywords.yaml", "keywords")
    exclude_keywords = load_yaml_list(CONFIG_DIR / "keywords.yaml", "exclude_keywords")

    if not sources:
        print("[ERROR] No hay fuentes configuradas en sources.yaml")
        return
    if not keywords:
        print("[ERROR] No hay palabras clave configuradas en keywords.yaml")
        return

    seen_ids = load_seen()
    articles = fetch_all(sources)

    new_count = 0
    for article in articles:
        if article.guid in seen_ids:
            continue
        if not matches_keywords(article, keywords, exclude_keywords):
            continue

        write_post(article, POSTS_DIR)
        seen_ids.add(article.guid)
        new_count += 1

    save_seen(seen_ids)
    save_status(len(sources), len(articles), new_count)
    print(f"Listo. {new_count} noticia(s) nueva(s) publicada(s) de {len(articles)} revisadas.")


if __name__ == "__main__":
    main()
