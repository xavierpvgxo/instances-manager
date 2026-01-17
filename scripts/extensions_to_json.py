#!/usr/bin/env python3
"""
scripts/extensions_to_json.py
Convierte el Excel de extensiones a JSON
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

def parse_date(date_str):
    """Convierte fecha de Excel a formato ISO"""
    if pd.isna(date_str) or str(date_str).strip() == '':
        return None
    
    try:
        # Intentar parsear diferentes formatos
        if isinstance(date_str, str):
            # Formato DD/MM/YYYY
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return str(date_str)
    except:
        return None

def parse_boolean(value):
    """Convierte YES/NO a booleano"""
    if pd.isna(value):
        return False
    value_str = str(value).strip().upper()
    return value_str in ['YES', 'Y', 'TRUE', '1', 'SI', 'SÍ']

def convert_extensions_to_json(input_file='data/extensions.xlsx', output_file='data/extensions.json'):
    """
    Convierte archivo Excel de extensiones a JSON
    
    Columnas esperadas:
    - Rollout Name
    - Description
    - Instance
    - NP (YES/NO)
    - NP Installation Date
    - PRD (YES/NO)
    - PRD Installation Date
    """
    
    print(f"📖 Leyendo {input_file}...")
    
    # Leer Excel
    if input_file.endswith('.csv'):
        df = pd.read_csv(input_file)
    else:
        df = pd.read_excel(input_file)
    
    print(f"📊 Encontradas {len(df)} extensiones")
    
    extensions = []
    instances_map = {}  # Para agrupar por instancia
    
    for index, row in df.iterrows():
        rollout_name = str(row.get('Rollout Name', '')).strip()
        description = str(row.get('Description', '')).strip()
        instance_id = str(row.get('Instance', '')).strip()
        client_id = str(row.get('Client', '')).strip()
        
        # Parsear datos de NP
        np_deployed = parse_boolean(row.get('NP'))
        np_date = parse_date(row.get('NP Installation Date'))
        
        # Parsear datos de PRD
        prd_deployed = parse_boolean(row.get('PRD'))
        prd_date = parse_date(row.get('PRD Installation Date'))
        
        if not rollout_name or not instance_id:
            continue
        
        extension = {
            'id': rollout_name,
            'name': rollout_name,
            'description': description if description else 'No description available',
            'instance_id': instance_id,
            'client_id': client_id,
            'environments': {
                'np': {
                    'deployed': np_deployed,
                    'installation_date': np_date,
                    'status': 'active' if np_deployed else 'not_deployed'
                },
                'prod': {
                    'deployed': prd_deployed,
                    'installation_date': prd_date,
                    'status': 'active' if prd_deployed else 'not_deployed'
                }
            },
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                'source_row': index + 2  # +2 porque Excel empieza en 1 y tiene header
            }
        }
        
        extensions.append(extension)
        
        # Agrupar por instancia
        if instance_id not in instances_map:
            instances_map[instance_id] = []
        instances_map[instance_id].append(extension)
    
    # Crear estructura final
    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_extensions': len(extensions),
            'total_instances': len(instances_map),
            'source_file': str(input_file)
        },
        'extensions': extensions,
        'by_instance': instances_map,
        'statistics': {
            'total': len(extensions),
            'deployed_np': sum(1 for e in extensions if e['environments']['np']['deployed']),
            'deployed_prod': sum(1 for e in extensions if e['environments']['prod']['deployed']),
            'instances_with_extensions': len(instances_map)
        }
    }
    
    # Crear directorio si no existe
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Guardar JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Conversión completada!")
    print(f"📊 Estadísticas:")
    print(f"   - Total extensiones: {len(extensions)}")
    print(f"   - Desplegadas en NP: {output_data['statistics']['deployed_np']}")
    print(f"   - Desplegadas en PROD: {output_data['statistics']['deployed_prod']}")
    print(f"   - Instancias con extensiones: {len(instances_map)}")
    print(f"💾 Archivo guardado en: {output_file}")
    
    # Generar versión compacta
    compact_file = output_file.replace('.json', '.min.json')
    with open(compact_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, separators=(',', ':'))
    print(f"💾 Versión compacta: {compact_file}")
    
    return extensions

def generate_sample_extensions():
    """Genera un Excel de ejemplo"""
    sample_data = [
        ['CT_REPORT_00303_V.001.ta', 'KUMHO Packing List', 'PR3', 'YES', '09/01/2025', 'NO', ''],
        ['CT_SHIPPING_00145_V.002', 'Custom Shipping Rules', 'PR1', 'YES', '15/12/2024', 'YES', '20/12/2024'],
        ['CT_INVENTORY_00267_V.001', 'Advanced Inventory Management', 'PR1', 'YES', '01/11/2024', 'YES', '10/11/2024'],
        ['CT_LABEL_00089_V.003', 'Custom Label Printing', 'PR2', 'YES', '20/01/2025', 'NO', ''],
        ['CT_PICKING_00156_V.001', 'Wave Picking Optimization', 'PR3', 'YES', '05/01/2025', 'YES', '12/01/2025'],
    ]
    
    df = pd.DataFrame(sample_data, columns=[
        'Rollout Name', 'Description', 'Instance', 'NP', 
        'NP Installation Date', 'PRD', 'PRD Installation Date'
    ])
    
    df.to_excel('sample_extensions.xlsx', index=False)
    df.to_csv('sample_extensions.csv', index=False)
    print("✅ Archivos de ejemplo generados: sample_extensions.xlsx y sample_extensions.csv")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("📖 Uso: python extensions_to_json.py <archivo_excel_o_csv>")
        print("\nEjemplo:")
        print("  python extensions_to_json.py data/extensions.xlsx")
        print("  python extensions_to_json.py data/extensions.csv")
        print("\n💡 Generando archivos de ejemplo...")
        generate_sample_extensions()
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else 'data/extensions.json'
        convert_extensions_to_json(input_file, output_file)