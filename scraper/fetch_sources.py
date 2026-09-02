"""Obtiene artículos crudos de las fuentes confiables configuradas.

Para cada fuente se intenta primero RSS (feedparser). Si la fuente no tiene
`rss_url` pero sí `html_url` + `article_selector`, se usa scraping HTML como
respaldo. Nunca se extrae el cuerpo completo del artículo, solo metadata y un
resumen corto.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone

import feedparser
import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "desalojos-bot/1.0 (+https://github.com/; "
    "recopilador de noticias sobre desalojos en Argentina)"
)
REQUEST_TIMEOUT = 15


@dataclass
class Article:
    source: str
    title: str
    link: str
    summary: str
    published: datetime
    guid: str


def fetch_all(sources: list[dict]) -> list[Article]:
    articles: list[Article] = []
    for source in sources:
        try:
            if source.get("rss_url"):
                articles.extend(_fetch_rss(source))
            elif source.get("html_url") and source.get("article_selector"):
                articles.extend(_fetch_html(source))
            else:
                print(f"[WARN] Fuente '{source.get('name')}' sin rss_url ni html_url, se omite.")
        except Exception as exc:
            # Una fuente caída o que cambió de estructura no debe frenar al resto.
            print(f"[WARN] Fallo al obtener '{source.get('name')}': {exc}")
    return articles


def _fetch_rss(source: dict) -> list[Article]:
    feed = feedparser.parse(source["rss_url"])
    articles = []
    for entry in feed.entries:
        link = getattr(entry, "link", None)
        title = getattr(entry, "title", None)
        if not link or not title:
            continue
        summary = _clean_html(getattr(entry, "summary", ""))
        guid = getattr(entry, "id", None) or link
        articles.append(
            Article(
                source=source["name"],
                title=title,
                link=link,
                summary=summary,
                published=_parse_published(entry),
                guid=guid,
            )
        )
    return articles


def _fetch_html(source: dict) -> list[Article]:
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(source["html_url"], headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    articles = []
    for link_tag in soup.select(source["article_selector"]):
        href = link_tag.get("href")
        title = link_tag.get_text(strip=True)
        if not href or not title:
            continue
        if href.startswith("/"):
            href = source["homepage"].rstrip("/") + href
        articles.append(
            Article(
                source=source["name"],
                title=title,
                link=href,
                summary="",
                published=datetime.now(timezone.utc),
                guid=href,
            )
        )
    return articles


def _parse_published(entry) -> datetime:
    for field in ("published_parsed", "updated_parsed"):
        value = getattr(entry, field, None)
        if value:
            return datetime.fromtimestamp(time.mktime(value), tz=timezone.utc)
    return datetime.now(timezone.utc)


def _clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    if "<" not in raw_html:
        return raw_html.strip()
    return BeautifulSoup(raw_html, "html.parser").get_text(separator=" ", strip=True)
