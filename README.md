# Desalojos en Argentina — bot + blog estático

Bot que recopila diariamente noticias sobre desalojos en Argentina desde un
conjunto curado de medios confiables, y las publica como posts en un blog
Jekyll servido con GitHub Pages.

## Cómo funciona

1. GitHub Actions corre `scraper/scrape.py` una vez al día (cron) o cuando se
   dispara manualmente.
2. El script lee `scraper/config/sources.yaml` (fuentes confiables) y
   `scraper/config/keywords.yaml` (palabras clave de desalojo).
3. Para cada fuente, obtiene sus últimos artículos (RSS o HTML de respaldo).
4. Descarta lo que no tenga alguna palabra clave y lo que ya se haya
   publicado antes (registrado en `scraper/data/seen.json`).
5. Por cada noticia nueva, genera un post en `_posts/` con título, fecha,
   fuente, resumen breve y link a la nota original.
6. El workflow commitea y pushea los cambios; GitHub Pages reconstruye el
   sitio automáticamente.

## Metodología anti fake-news

Solo se publica contenido que cumpla **ambas** condiciones:

- Proviene de un medio en la whitelist (`sources.yaml`) — no se scrapea nada
  fuera de esa lista.
- El título o resumen contiene una palabra clave relacionada a desalojos
  (`keywords.yaml`).

Ver [`about.md`](about.md) para el detalle publicado en el sitio, incluyendo
limitaciones de este enfoque.

## Correr el scraper localmente

```bash
cd scraper
pip install -r requirements.txt
python scrape.py
```

Esto genera posts nuevos en `_posts/` (en la raíz del repo) y actualiza
`scraper/data/seen.json`.

## Previsualizar el blog localmente

Requiere Ruby y Bundler instalados.

```bash
bundle install
bundle exec jekyll serve
```

Abrir `http://localhost:4000`.

## Agregar o quitar una fuente

Editar `scraper/config/sources.yaml`. Cada entrada necesita `name`,
`homepage` y, preferentemente, `rss_url`. Si el medio no tiene RSS, se puede
usar el fallback de scraping HTML con `html_url` + `article_selector` (ver
comentarios en el propio archivo).

Las URLs de RSS cambian con el tiempo: antes de dar por buena una fuente
nueva, conviene verificar el feed abriéndolo en el navegador o corriendo el
scraper localmente y revisando la salida.

## Ajustar palabras clave

Editar `scraper/config/keywords.yaml`. La comparación ignora mayúsculas y
acentos.

## Publicar el sitio en GitHub Pages

1. Crear el repositorio en GitHub y pushear la rama `main`.
2. En **Settings → Pages**, elegir **Source: Deploy from a branch**, rama
   `main`, carpeta `/ (root)`.
3. Disparar el workflow manualmente la primera vez desde la pestaña
   **Actions → Scrape noticias de desalojos → Run workflow**, para generar
   los primeros posts sin esperar al cron diario.

## Nota sobre derechos de autor

El bot nunca extrae el cuerpo completo de un artículo: solo título, un
resumen corto (el que provee el propio RSS del medio) y el link a la nota
original, con atribución explícita a la fuente.
