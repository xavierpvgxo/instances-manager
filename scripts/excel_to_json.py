#!/usr/bin/env python3
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

def convert_excel_to_json(input_file, output_file='data/instances.json'):
    if input_file.endswith('.csv'):
        df = pd.read_csv(input_file)
    else:
        df = pd.read_excel(input_file)

    # REGLA DE ORO: Normalizar nombres de columnas
    # Quitamos espacios extra y convertimos a minúsculas para comparar fácil
    original_cols = df.columns
    normalized_cols = {str(c).strip().replace("  ", " ").lower(): c for c in original_cols}
    
    def get_val(row, target_name):
        """Busca una columna por nombre aproximado si el exacto falla"""
        target = target_name.lower()
        real_col_name = normalized_cols.get(target)
        if real_col_name:
            val = row.get(real_col_name)
            return str(val).strip() if pd.notna(val) else ""
        return ""

    instances = []
    
    for index, row in df.iterrows():
        # Extraemos la cuenta usando el nombre normalizado
        account_val = get_val(row, "gxo account") # Esto capturará "GXO  Account" o "GXO Account"
        client_val = get_val(row, "gxo sites")
        instance_id = get_val(row, "instance")

        instance = {
            'id': instance_id,
            'account': account_val, # <--- AQUÍ SE ASIGNA
            'client': client_val,
            'site': get_val(row, "site name"),
            'whid': get_val(row, "whid"),
            'live': get_val(row, "live").lower() == 'yes',
            'wgs': get_val(row, "wgs"),
            
            'location': {
                'country': get_val(row, "country"),
                'address': get_val(row, "address name")
            },
            
            'products': [p.strip() for p in get_val(row, "product").split('/') if p.strip()],
            
            'versions': {
                'wms': get_val(row, "wms"),
                'oms': get_val(row, "oms"),
                'pdc': get_val(row, "pdc"),
                'tms': get_val(row, "tms")
            },
            
            'urls': {
                'np': {
                    'web': get_val(row, "web non-prod"),
                    'app': get_val(row, "app non-prod"),
                    'config': get_val(row, "console non-prod")
                },
                'prod': {
                    'web': get_val(row, "web prod"),
                    'app': get_val(row, "app prod"),
                    'config': get_val(row, "console prod")
                }
            },
            
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                'repository': f"https://github.com/gxo-instances/{instance_id.lower()}-extensions" if instance_id else None
            }
        }
        
        if client_val or instance_id:
            instances.append(instance)
    
    # ... (resto del código de guardado igual que antes)
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
    
    print(f"✅ Conversión completada: {len(instances)} filas. Account detectado: {'Sí' if account_val else 'No'}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        convert_excel_to_json(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'data/instances.json')