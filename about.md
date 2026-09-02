---
layout: page
title: Acerca de
permalink: /about/
---

## Qué es este sitio

Un bot recorre automáticamente, una vez al día, los feeds RSS (y en algunos
casos el HTML) de un conjunto **fijo y curado de medios argentinos
reconocidos**. De cada fuente extrae únicamente título, fecha, un resumen
breve y el enlace a la nota original — nunca el artículo completo, para
respetar los derechos de autor de cada medio.

## Cómo se decide qué se publica acá

Una noticia se publica en este blog solo si se cumplen **dos condiciones** a
la vez:

1. **Proviene de una fuente en la lista de medios confiables** definida en
   [`scraper/config/sources.yaml`](https://github.com/) del repositorio. No se
   scrapea ni se publica contenido de sitios fuera de esa lista.
2. **El título o el resumen contiene alguna palabra clave** relacionada con
   desalojos (definidas en `scraper/config/keywords.yaml`), para descartar
   noticias no relevantes.

Este enfoque de "whitelist + palabras clave" busca minimizar el riesgo de
difundir información falsa o no verificada, priorizando medios con
trayectoria periodística reconocida por sobre la cobertura exhaustiva de
absolutamente todas las fuentes posibles.

## Limitaciones

- No es un sistema de verificación de hechos (fact-checking): confía en la
  credibilidad general de cada medio incluido en la whitelist, no valida cada
  noticia individualmente.
- Si un medio de la lista publica información incorrecta, ese error se
  reflejará acá también. Ante cualquier duda, siempre conviene leer la nota
  completa en la fuente original (el link está en cada post).
- La lista de fuentes es editable y puede ampliarse o corregirse con el
  tiempo; se puede consultar su estado actual directamente en el repositorio.
