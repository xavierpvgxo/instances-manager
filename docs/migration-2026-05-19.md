# Migración a `Client ID list.xlsx` (BY Client Tracker)

Inicio: 2026-05-19 · Última revisión: 2026-05-20
Origen: `...\BY Client Tracker\Client ID list.xlsx` (SharePoint, hoja `Client Info`).

## Resultado

34 instancias. Una tarjeta por fila de la hoja `Client Info`.

## `scripts/excel_to_json.py`

Lee la hoja `Client Info` y genera `data/instances.json` + `data/instances.min.json`.

Mapeo de columnas:

| Col | Campo Excel | Campo JSON |
|-----|-------------|------------|
| A | POC | `contact.poc` |
| B | Client ID | `client_id` |
| C | Client | `client` |
| E | NP Env | `environments.np.code` |
| F | Prod Env | `environments.prod.code` |
| G | Arch Env | `environments.arch.code` |
| H | Site Code | `site` |
| I | Instance | `instance` (tenant; define `region`) |
| J | NP BY Version | `environments.np.version` |
| K | Prod. BY Version | `environments.prod.version` |
| L | NP Realm | `environments.np.realm` |
| M | GIT Repo | `extensions_repo` |
| N | Prod. Realm | `environments.prod.realm` |
| O | Location | `location` |
| P | Operating Hours | `operating_hours` |
| Q | SIte distribution | `contact.site_distribution` |
| R | Site Contact | `contact.site_contact` |
| Y | Go-Live | `go_live` / `live` |

Reglas:
- `card_title` = `<Client> - <NP Env>` (fallback a Prod Env / Site Code).
- `live` = la columna Prod Env tiene un valor real (TBD no cuenta). No depende de Go-Live.
- `region` = `instance` `be40` → `AMAPAC`, `bh10` → `EUROPE`, otro → `null`.
- `"PR12 - NO SSO"` → code `PR12` + `flags: ["NO SSO"]`.
- URLs **calculadas**: `https://<instance>-gxo-wms-<kind>-<env>.jdadelivers.com<suffix>`
  — `web → /portal`, `app → /service`, `con → (sin path)`. NP usa NP Env, PROD usa Prod Env.
  Si falta `instance` o el env, o el env es `TBD` → `null`.
- `extensions_repo` = `https://github.com/BYExternal/<GIT Repo>`; `null` si no hay GIT Repo.
- El script ya **no crea** carpetas `repositories/<id>-extensions/`.

## Esquema JSON

```jsonc
{
  "id": "PR1-RI3",                    // clave única interna
  "card_title": "Hasbro - NP2",
  "client": "Hasbro",
  "client_id": "1722",
  "instance": "be40",
  "site": "RI3",
  "region": "AMAPAC",
  "location": "1551 Normantown Rd, Romeoville, IL",
  "operating_hours": "6:30am - 12:30am M-F CST",
  "live": true,
  "go_live": "2023-03-20",            // null si no hay fecha
  "flags": [],
  "environments": {
    "np":   { "code": "NP2",  "version": "2021.1.1.28.1", "realm": null },
    "prod": { "code": "PR1",  "version": "2021.1.1.28.1", "realm": null },
    "arch": { "code": "PR1A", "version": null, "realm": null }
  },
  "contact": { "poc": null, "site_contact": "...", "site_distribution": "..." },
  "urls": {
    "web":     { "np": "https://...", "prod": "https://..." },
    "app":     { "np": "https://...", "prod": "https://..." },
    "console": { "np": "https://...", "prod": "https://..." }
  },
  "extensions_repo": "https://github.com/BYExternal/exec-wms-gxo-hasbro-romeoville-les",
  "metadata": { "last_updated": "..." }
}
```

## `index.html`

CSS/branding GXO intactos. Tarjeta reestructurada:
- Cabecera: `card_title` + badges de `flags` + badge LIVE/NO LIVE (parpadea si LIVE).
- Datos: Instance, Client ID, Site, Region, Location, Operating Hours, Go-Live (solo si hay valor).
- Sección **Environments**: tabla NP / PR / ARCH con Code · Version · Realm.
- Sección **Contact**: POC, Site Contact, Site Distribution.
- Sección **Connectivity**: WEB / APP / CONSOLE × NP / PROD.
  - WEB y CONSOLE → enlaces directos.
  - APP → copia la URL al portapapeles + toast `APP URL copied`.
  - Botón sin URL → no clickable.
- Botón **Extensions repository** → `extensions_repo` (no clickable si falta).
- Filtro `Country` sustituido por `Region`.

## `data/instances.xlsx` (saneado)

Solo hoja `Client Info`, 20 columnas. El `Client ID list.xlsx` completo (facturas, T&E, Raw Users…) **no se sube** al repo.

## Métricas (2026-05-20)

- Total: **34 instancias** · Live: **30** · No-live: **4** (las 4 filas TBD)
- Region: AMAPAC 28 · EUROPE 6
- Sin `extensions_repo`: 4 (sin GIT Repo) · Sin URL PROD: 4 (filas TBD)
- Con flag `NO SSO`: 1 (Food52)

## Pendiente

1. Carpetas `repositories/pr3-extensions/` y `pr10-extensions/` conservan contenido real de extensions; el resto se eliminaron (vacías). El botón Extensions ahora apunta a `github.com/BYExternal`, así que la carpeta local `repositories/` queda como histórico.
2. Render visual de `index.html` pendiente de revisión en navegador.
3. Auto-sync desde SharePoint (opciones A/B/C descritas en la conversación) sin decidir.

## Regenerar

```bash
python scripts/excel_to_json.py "C:\ruta\Client ID list.xlsx"   # desde SharePoint
python scripts/excel_to_json.py data/instances.xlsx              # desde copia saneada
```
