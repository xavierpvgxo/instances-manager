#!/usr/bin/env python3
"""
Convierte el Excel "Client ID list.xlsx" (hoja 'Client Info') a data/instances.json.

Uso:
  python scripts/excel_to_json.py "C:\\ruta\\Client ID list.xlsx"
  python scripts/excel_to_json.py data/instances.xlsx            # copia saneada en el repo
  python scripts/excel_to_json.py <input.xlsx> <output.json>

Genera tambien la version minificada (data/instances.min.json).

Mapeo de columnas (hoja 'Client Info'):
  A POC               -> contact.poc
  B Client ID         -> client_id
  C Client            -> client
  E NP Env            -> environments.np.code
  F Prod Env          -> environments.prod.code (display_id; se limpia para URLs)
  G Arch Env          -> environments.arch.code
  H Site Code         -> site
  I Instance          -> instance (tenant; define region)
  J NP BY Version     -> environments.np.version
  K Prod. BY Version  -> environments.prod.version
  L NP Realm          -> environments.np.realm
  M GIT Repo          -> extensions_repo (https://github.com/BYExternal/<M>)
  N Prod. Realm       -> environments.prod.realm
  O Location          -> location
  P Operating Hours   -> operating_hours
  Q SIte distribution -> contact.site_distribution
  R Site Contact      -> contact.site_contact
  Y Go-Live           -> go_live / live

Reglas:
  - live  = la columna Prod Env tiene un valor real (TBD no cuenta).
  - region: instance be40 -> AMAPAC, bh10 -> EUROPE, otro -> None.
  - URLs calculadas: https://<instance>-gxo-wms-<kind>-<env>.jdadelivers.com<suffix>
    kind -> suffix:  web -> /portal,  app -> /service,  con -> (sin path).
    NP usa NP Env; PROD usa Prod Env. Si falta instance o env -> None (boton no clickable).
  - "PR12 - NO SSO" -> code 'PR12' + flags ['NO SSO'].
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

SOURCE_SHEET = "Client Info"

# Entornos internos que no son clientes. Se publican igual, pero categorizados
# aparte para que no se mezclen con las instancias de cliente en la web.
DEV_SANDBOX_RE = re.compile(r"dev|test|sandbox", re.I)
QL_TEMPLATE_RE = re.compile(r"^\s*QL\b", re.I)


def classify(client):
    """'client' | 'dev-sandbox' | 'ql-template' segun el nombre de la fila."""
    if DEV_SANDBOX_RE.search(client):
        return "dev-sandbox"
    if QL_TEMPLATE_RE.match(client):
        return "ql-template"
    return "client"

REGION_BY_INSTANCE = {
    "be40": "AMAPAC",
    "bh10": "EUROPE",
}

URL_BASE = "https://{instance}-gxo-wms-{kind}-{env}.jdadelivers.com"
URL_SUFFIX = {"web": "/portal", "app": "/service", "con": ""}


def normalize_str(v):
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    # Algunas celdas traen saltos de linea (p.ej. Site Code "PIN\nJMS\nWTN"),
    # que romperian ids y maquetacion. Se colapsa todo el blanco a un espacio.
    s = " ".join(str(v).split())
    if not s or s.lower() == "nan" or s == "----":
        return None
    return s


def normalize_prod_env(raw):
    """'PR12 - NO SSO' -> ('PR12', ['NO SSO']); 'PR1' -> ('PR1', [])."""
    if not raw:
        return None, []
    parts = [p.strip() for p in str(raw).split("-")]
    head = parts[0].strip()
    flags = [p for p in parts[1:] if p]
    return head, flags


# Un codigo de entorno real es NP/PR + numero (+ sufijo de arch): NP5, PR26, PR18A.
# La columna trae tambien texto libre ('TBD', 'GXO funded', 'Not Setup') que NO es
# un entorno: si se cuela, se acaban construyendo URLs invalidas con espacios.
ENV_CODE_RE = re.compile(r"^(?:NP|PR)\d+[A-Za-z]?$", re.I)


def env_for_url(code):
    """Codigo de entorno valido para construir una URL, o None."""
    if not code:
        return None
    code = code.strip()
    return code if ENV_CODE_RE.match(code) else None


def build_url(instance, env_code, kind):
    inst = normalize_str(instance)
    env = env_for_url(env_code)
    if not inst or not env:
        return None
    return URL_BASE.format(instance=inst, kind=kind, env=env) + URL_SUFFIX.get(kind, "")


def fmt_date(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        ts = pd.to_datetime(v, errors="coerce")
    except Exception:
        return None
    if pd.isna(ts):
        return None
    return ts.date().isoformat()


def convert_excel_to_json(input_file, output_file="data/instances.json"):
    xl = pd.ExcelFile(input_file)
    sheet = SOURCE_SHEET if SOURCE_SHEET in xl.sheet_names else xl.sheet_names[0]
    df = pd.read_excel(input_file, sheet_name=sheet)
    df.columns = [str(c).strip() for c in df.columns]

    instances = []
    seen_ids = set()

    for _, row in df.iterrows():
        prod_env_raw = normalize_str(row.get("Prod Env"))
        client = normalize_str(row.get("Client"))
        site_code = normalize_str(row.get("Site Code"))
        # Basta con tener cliente: una instancia solo-NP (aun sin produccion) es
        # real y debe publicarse. Las filas hueco del Excel (IDs pre-reservados,
        # sin nombre) se descartan aqui.
        if not client:
            continue
        if client.lower().startswith("do not use"):
            continue

        display_prod, flags = normalize_prod_env(prod_env_raw)
        np_env = normalize_str(row.get("NP Env"))
        arch_env = normalize_str(row.get("Arch Env"))
        instance = normalize_str(row.get("Instance"))
        git_repo = normalize_str(row.get("GIT Repo"))
        go_live = fmt_date(row.get("Go-Live"))
        # En PROD si Prod Env tiene un valor real (TBD no cuenta como entorno).
        in_prod = env_for_url(display_prod) is not None

        # Sin Prod Env util el identificador cae al codigo NP (y de ahi al cliente),
        # para no acabar generando ids del tipo "None-WNL" o "TBD-GE1".
        base_code = env_for_url(display_prod) or env_for_url(np_env) or client
        unique_id = f"{base_code}-{site_code}" if site_code else base_code
        if unique_id in seen_ids:
            n = 2
            while f"{unique_id}-{n}" in seen_ids:
                n += 1
            unique_id = f"{unique_id}-{n}"
        seen_ids.add(unique_id)

        # Cabecera de tarjeta: "<Client> - <NP Env>" (fallback a Prod Env / Site Code)
        title_suffix = env_for_url(np_env) or env_for_url(display_prod) or site_code
        card_title = f"{client} - {title_suffix}" if title_suffix else client

        region = REGION_BY_INSTANCE.get((instance or "").lower())

        instances.append({
            "id": unique_id,
            "card_title": card_title,
            "client": client,
            "category": classify(client),
            "client_id": normalize_str(row.get("Client ID")),
            "instance": instance,
            "site": site_code,
            "region": region,
            "location": normalize_str(row.get("Location")),
            "operating_hours": normalize_str(row.get("Operating Hours")),
            "live": in_prod,
            "go_live": go_live,
            "flags": flags,

            "environments": {
                "np": {
                    "code": np_env,
                    "version": normalize_str(row.get("NP BY Version")),
                    "realm": normalize_str(row.get("NP Realm")),
                },
                "prod": {
                    "code": display_prod,
                    "version": normalize_str(row.get("Prod. BY Version")),
                    "realm": normalize_str(row.get("Prod. Realm")),
                },
                "arch": {
                    "code": arch_env,
                    "version": None,
                    "realm": None,
                },
            },

            "contact": {
                "poc": normalize_str(row.get("POC")),
                "site_contact": normalize_str(row.get("Site Contact")),
                "site_distribution": normalize_str(row.get("SIte distribution")),
            },

            "urls": {
                "web": {
                    "np": build_url(instance, np_env, "web"),
                    "prod": build_url(instance, display_prod, "web"),
                },
                "app": {
                    "np": build_url(instance, np_env, "app"),
                    "prod": build_url(instance, display_prod, "app"),
                },
                "console": {
                    "np": build_url(instance, np_env, "con"),
                    "prod": build_url(instance, display_prod, "con"),
                },
            },

            "extensions_repo": f"https://github.com/BYExternal/{git_repo}" if git_repo else None,

            "metadata": {
                "last_updated": datetime.now().isoformat(),
            },
        })

    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_instances": len(instances),
            "source_file": str(input_file),
            "source_sheet": sheet,
        },
        "instances": instances,
    }

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    min_path = output_path.with_name(output_path.stem + ".min.json")
    with min_path.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, separators=(",", ":"), ensure_ascii=False)

    print(f"OK - {len(instances)} instancias -> {output_path}")
    print(f"OK - minificado -> {min_path}")
    return instances


if __name__ == "__main__":
    in_f = sys.argv[1] if len(sys.argv) > 1 else "data/instances.xlsx"
    out_f = sys.argv[2] if len(sys.argv) > 2 else "data/instances.json"
    convert_excel_to_json(in_f, out_f)
