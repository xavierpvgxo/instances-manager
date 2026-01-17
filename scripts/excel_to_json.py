#!/usr/bin/env python3
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime

def clean_url(url):
    if pd.isna(url) or str(url).strip() == '' or str(url).strip() == '----':
        return None
    return str(url).strip()

def parse_products(products_str):
    if pd.isna(products_str):
        return []
    return [p.strip() for p in str(products_str).split('/') if p.strip()]

def convert_excel_to_json(input_file, output_file='data/instances.json'):
    # Leer el archivo
    if input_file.endswith('.csv'):
        df = pd.read_csv(input_file)
    else:
        df = pd.read_excel(input_file)

    # Limpiar nombres de columnas
    df.columns = [str(c).strip() for c in df.columns]
    
    instances = []
    # Carpeta raíz donde colgarán todos los repositorios
    repo_base_dir = Path('repositories')
    
    for index, row in df.iterrows():
        instance_id = str(row.get('Instance', '')).strip()
        
        # --- LÓGICA DE CREACIÓN DE CARPETAS (MODIFICADA: SIN SUB-CARPETAS) ---
        if instance_id and instance_id.lower() != 'nan':
            repo_name = f"{instance_id.lower()}-extensions"
            # Creamos la ruta directamente: repositories/[id]-extensions/
            instance_repo_path = repo_base_dir / repo_name
            
            # Crear la carpeta de la instancia
            instance_repo_path.mkdir(parents=True, exist_ok=True)
            
            # Crear .gitkeep en la raíz de la carpeta de la instancia
            (instance_repo_path / '.gitkeep').touch()
        # --------------------------------------------------------------------

        instance = {
            'id': instance_id,
            'account': str(row.get('GXO Account', '')).strip(),
            'client': str(row.get('GXO Sites', '')).strip(),
            'site': str(row.get('Site Name', '')).strip(),
            'whid': str(row.get('WhID', '')).strip() if not pd.isna(row.get('WhID')) else None,
            'live': str(row.get('LIVE', 'No')).strip().lower() == 'yes',
            'wgs': str(row.get('WGS', '')).strip() if not pd.isna(row.get('WGS')) else None,
            
            'location': {
                'country': str(row.get('Country', '')).strip() if not pd.isna(row.get('Country')) else None,
                'address': str(row.get('Address Name', '')).strip() if not pd.isna(row.get('Address Name')) else None
            },
            
            'contact': {
                'name': str(row.get('Person of Contact', '')).strip() if not pd.isna(row.get('Person of Contact')) else None,
                'email': None,
                'phone': None
            },
            
            'products': parse_products(row.get('Product')),
            'versions': {
                'wms': str(row.get('WMS', '')).strip() if not pd.isna(row.get('WMS')) else None,
                'oms': str(row.get('OMS', '')).strip() if not pd.isna(row.get('OMS')) else None,
                'pdc': str(row.get('PDC', '')).strip() if not pd.isna(row.get('PDC')) else None
            },
            
            'urls': {
                'np': {
                    'web': clean_url(row.get('WEB NON-PROD')),
                    'app': clean_url(row.get('APP NON-PROD')),
                    'config': clean_url(row.get('CONSOLE NON-PROD'))
                },
                'prod': {
                    'web': clean_url(row.get('WEB PROD')),
                    'app': clean_url(row.get('APP PROD')),
                    'config': clean_url(row.get('CONSOLE PROD'))
                }
            },
            
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                # URL corregida para apuntar a la subcarpeta dentro de tu repo principal
                'repository': f"https://github.com/xavierpvgxo/instances-manager/tree/main/repositories/{instance_id.lower()}-extensions" if instance_id else None
            }
        }
        
        if instance['client'] and instance['client'] != 'nan':
            instances.append(instance)
    
    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_instances': len(instances),
            'source_file': str(input_file)
        },
        'instances': instances
    }
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Proceso finalizado.")
    print(f"📂 Carpetas creadas en /repositories: {len(instances)}")
    return instances

if __name__ == '__main__':
    import sys
    input_f = sys.argv[1] if len(sys.argv) > 1 else 'data/instances.xlsx'
    output_f = sys.argv[2] if len(sys.argv) > 2 else 'data/instances.json'
    convert_excel_to_json(input_f, output_f)