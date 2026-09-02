# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Two things glued together by a GitHub Actions workflow:

1. A Python scraper (`scraper/`) that pulls recent articles from a curated whitelist of Argentine
   news sources, keeps only ones matching "desalojo" (eviction) keywords, and writes each match as
   a Jekyll post.
2. A Jekyll static site (everything at the repo root) served via GitHub Pages, styled with a
   customized `minima` theme.

The whole point of the filtering design is to avoid publishing fake/unverified news: an article is
only published if it comes from a domain in `scraper/config/sources.yaml` **and** matches a keyword
in `scraper/config/keywords.yaml`. There is no AI classification or fact-checking step — trust comes
entirely from the source whitelist.

## Commands

Run the scraper (from repo root, needs a venv with `scraper/requirements.txt` installed):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r scraper/requirements.txt
python3 scraper/scrape.py
```

This fetches all sources, writes any new matching posts to `_posts/`, updates
`scraper/data/seen.json` (dedup) and `_data/status.yml` (last-run status shown on the homepage).
It's safe to re-run — already-seen article guids are skipped.

There is no test suite. Verify scraper changes by running it and inspecting the generated files in
`_posts/` and the console summary line (`Listo. N noticia(s) nueva(s)... de M revisadas.`).

Preview the Jekyll site locally (requires Ruby ≥ 3.0 + Bundler — the system Ruby on this machine has
been too old for the `github-pages` gem in past sessions, so this may need to be verified against the
live GitHub Pages build instead):

```bash
bundle install
bundle exec jekyll serve
```

## Architecture

### Scraper pipeline (`scraper/scrape.py` is the entrypoint)

`fetch_sources.py` → `scrape.py` (filter + dedup) → `generate_post.py` → `_posts/*.md`

- **`fetch_sources.py`** pulls raw articles from each configured source, trying methods in this
  order per source: `rss_url` (feedparser) → `news_sitemap_url` (Google News sitemap XML, for sites
  without RSS — parsed by hand with `xml.etree.ElementTree`) → `html_url` + `article_selector`
  (BeautifulSoup, last resort). Never extracts full article bodies, only title/summary/link, for
  copyright reasons.
- **`scrape.py`** loads `sources.yaml` + `keywords.yaml`, calls `fetch_all()`, then for each article:
  skips it if its guid is already in `scraper/data/seen.json`, skips it if it matches an
  `exclude_keywords` entry (added to filter out "desalojo" meaning *evacuation*, e.g. bomb-threat
  articles, not housing eviction), otherwise keeps it if it matches a `keywords` entry. Matching is
  accent/case-insensitive substring matching (see `normalize()`), not NLP.
- **`generate_post.py`** writes the Jekyll post file (`_posts/YYYY-MM-DD-slug.md`) with front matter
  (`title`, `date`, `source`, `original_url`) and a body of summary + "leer la nota completa" link.
- `scrape.py` always writes `_data/status.yml` (last-checked timestamp in UTC and Argentina time,
  sources/articles counts) — even when zero new articles are found. This exists specifically so the
  homepage can show "last checked" as a heartbeat independent of whether anything was published;
  don't make this conditional on finding new articles.

### `scraper/config/sources.yaml` conventions

Each entry needs exactly one of `rss_url` / `news_sitemap_url` / (`html_url` + `article_selector`).
Multiple entries can share the same `name` (e.g. Clarín has separate entries for its `policiales`
and `sociedad` section feeds) — sources intentionally point at **section-level** feeds, not homepage
feeds, because a single eviction rarely makes national front-page RSS. When adding a source, verify
the feed actually returns entries (`feedparser.parse(url).entries`) before committing — RSS URLs on
Argentine news sites move around and silently 404/redirect/hang. A comment block at the bottom of
the file lists sources that were evaluated and rejected (infra blocks bots, or feed was compromised
with spam) — check there before re-proposing a source that already failed vetting.

### GitHub Actions workflow (`.github/workflows/scrape.yml`)

Nominally runs hourly (`17 * * * *` — deliberately not `:00`, since GitHub Actions cron jobs
scheduled on the hour are more likely to be delayed under load) plus `workflow_dispatch` for manual
runs. Has a `concurrency` group with `cancel-in-progress: false` so overlapping runs queue instead of
racing on the `git push`. It commits `_posts/`, `scraper/data/seen.json`, and `_data/status.yml`
**every run**, not just when new posts are found — the commit message itself is derived from
`_data/status.yml`'s `new_articles` count. Because the bot commits directly to `main` on its own
schedule, expect `git push` to sometimes be rejected with "fetch first" during manual work; resolve
with `git pull --rebase origin main` (the bot's changes and local edits touch disjoint files in
practice, so this has rebased cleanly every time so far).

**GitHub's own `schedule` trigger turned out to be unreliable in practice** — checked empirically via
the Actions API, it fired only once in ~10 expected hourly windows over a day of observation (not
just delayed, mostly skipped outright). Because of that, the real trigger for regular runs is now
**external**: a free cron-job.org job calls `POST /repos/ezequielabregu/desalojos_bot/actions/workflows/scrape.yml/dispatches`
every hour with a fine-grained GitHub PAT (scoped to this repo only, `Actions: read/write` +
`Contents: read`) stored in cron-job.org's own header config — not anywhere in this repo or as a
GitHub Actions secret. The in-repo `schedule:` trigger is kept only as a zero-cost fallback in case it
occasionally fires; don't remove it, but don't rely on it either. If "last checked" on the homepage
stops advancing, the cron-job.org job (not GitHub Actions) is the first thing to check — GitHub's own
Actions run history only shows what GitHub knows about, which won't explain an external-trigger
outage. Debugging that integration once surfaced a red herring worth remembering: GitHub's dispatch
endpoint returns a generic-looking `400`/`404` for several unrelated causes (bad token, wrong repo
scope on the token, or a header value accidentally containing `"HeaderName: value"` instead of just
`value`) — the real cause is always in the JSON `message`/`errors` field of the response body, not the
status code alone.

### Jekyll site

- `_config.yml` sets `theme: minima` and excludes `scraper/` from the built site.
- `_layouts/home.html` **overrides** minima's default home layout: post titles and a "Fuente: X"
  line both link straight to `post.original_url` in a new tab, instead of to the post's own internal
  page. This was a deliberate choice so a reader never has to leave the homepage to reach an article.
  The post's own permalink page still gets built (with the full "leer la nota completa" link) but is
  no longer linked from anywhere in the UI.
- `assets/main.scss` is a standard Jekyll/minima override file (`@import "minima";` plus custom
  rules) — this is how theme CSS gets extended, not by editing the theme itself.
- `index.md` renders `site.data.status.*` (from `_data/status.yml`) in a banner showing when the bot
  last ran.
- `about.md` is user-facing documentation of the anti-fake-news methodology; keep it in sync if the
  filtering logic in `scrape.py`/`keywords.yaml` changes meaningfully.
