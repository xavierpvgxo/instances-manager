---
name: verify
description: Launch and drive the Instance Manager page in a real browser to verify UI/data changes.
---

# Verify — instances-manager

Sitio estático. No hay build: `index.html` hace `fetch` de `data/instances.json`,
así que hay que servirlo por HTTP (abrirlo con `file://` rompe el fetch por CORS).

## Servir

```bash
cd "C:/Users/xavier.parro/OneDrive - GXO/Documentos/GitHub/GXO/instances-manager"
python -m http.server 8777 --bind 127.0.0.1 &
# http://127.0.0.1:8777/index.html   y   /extensions.html
```

## Pilotar el navegador

**La descarga del Chromium de Playwright está bloqueada por la red corporativa**
(`npx playwright install chromium` -> `Download failure, code=1`). No pierdas tiempo:
usa el Edge ya instalado.

```js
const browser = await chromium.launch({ channel: 'msedge' });
```

El módulo `playwright` no está en el repo; instálalo en el scratchpad (`npm install playwright`)
y ejecuta el script desde ahí.

## Qué conviene ejercitar

- Nº de tarjetas renderizadas (`#grid .card`) contra `metadata.total_instances` del JSON.
- Filtros: `#filterRegion`, `#filterCategory` (`client` / `ql-template` / `dev-sandbox`),
  pestañas de estado (`.tab[data-status]`) y `#searchInput`. Combínalos: los contadores
  de las pestañas (`#badgeAll/#badgeLive/#badgeDown`) se recalculan sobre búsqueda+región+categoría.
- Instancia solo-NP (p.ej. buscar "Kumho"): debe salir el chip `Not live` y los botones
  PROD **visibles pero deshabilitados** (`.conn-btn.disabled`), no ocultos.
- Errores de consola (`page.on('pageerror')`).

## Regenerar los datos

```bash
python scripts/excel_to_json.py "C:/Users/xavier.parro/GXO/GXO Blue Yonder - Documentos/BY Client Tracker/Client ID list.xlsx"
```

El sync completo (`scripts/sync_from_sharepoint.py`) commitea y pushea: para probar sin
publicar nada, usa `--dry-run`.
