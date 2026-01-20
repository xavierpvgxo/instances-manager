#!/usr/bin/env python3
"""
scripts/auto_sync.py
Detecta cambios en archivos Excel y los sincroniza automáticamente con GitHub
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ExcelChangeHandler(FileSystemEventHandler):
    """Maneja cambios en archivos Excel"""
    
    def __init__(self):
        self.last_sync = {}
        self.cooldown = 10  # Segundos de espera entre syncs del mismo archivo
        
    def on_modified(self, event):
        """Se ejecuta cuando se modifica un archivo"""
        if event.is_directory:
            return
            
        file_path = event.src_path
        
        # Solo procesar archivos Excel/CSV en data/
        if not (file_path.endswith(('.xlsx', '.csv', '.xls')) and 'data' in file_path):
            return
        
        # Evitar múltiples ejecuciones (Excel guarda varias veces)
        current_time = time.time()
        if file_path in self.last_sync:
            if current_time - self.last_sync[file_path] < self.cooldown:
                return
        
        self.last_sync[file_path] = current_time
        
        print(f"\n{'='*60}")
        print(f"🔔 Cambio detectado: {os.path.basename(file_path)}")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        self.process_change(file_path)
    
    def process_change(self, file_path):
        """Procesa el cambio y sincroniza con GitHub"""
        
        filename = os.path.basename(file_path)
        
        try:
            # 1. Ejecutar script de conversión correspondiente
            if 'instances' in filename.lower():
                print("📊 Convirtiendo instances a JSON...")
                result = subprocess.run(
                    ['python', 'scripts/excel_to_json.py', file_path, 'data/instances.json'],
                    capture_output=True,
                    text=True
                )
                    
            elif 'extensions' in filename.lower():
                print("🔧 Convirtiendo extensions a JSON...")
                result = subprocess.run(
                    ['python', 'scripts/extensions_to_json.py', file_path, 'data/extensions.json'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print("✅ extensions.json actualizado")
                else:
                    print(f"❌ Error: {result.stderr}")
                    return
            
            # 2. Git add
            print("\n📦 Añadiendo archivos a Git...")
            subprocess.run(['git', 'add', 'data/', 'data/'], check=True)
            
            # 3. Git commit
            commit_msg = f"🤖 Auto-sync: Updated {filename} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            print(f"💾 Haciendo commit: {commit_msg}")
            
            result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 or 'nothing to commit' in result.stdout:
                # 4. Git push
                print("🚀 Subiendo a GitHub...")
                push_result = subprocess.run(
                    ['git', 'push', 'origin', 'main'],
                    capture_output=True,
                    text=True
                )
                
                if push_result.returncode == 0:
                    print("✅ ¡Cambios sincronizados con GitHub exitosamente!")
                else:
                    print(f"❌ Error en push: {push_result.stderr}")
            else:
                if 'nothing to commit' in result.stdout:
                    print("ℹ️  No hay cambios que commitear")
                else:
                    print(f"❌ Error en commit: {result.stderr}")
            
            print(f"\n{'='*60}\n")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print(f"\n{'='*60}\n")

def daily_sync():
    """Sincronización diaria automática"""
    print("\n" + "="*60)
    print("📅 Sincronización diaria automática")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    try:
        # Convertir archivos
        if Path('data/instances.xlsx').exists():
            print("📊 Convirtiendo instances.xlsx...")
            subprocess.run(['python', 'scripts/excel_to_json.py', 'data/instances.xlsx'])
        
        if Path('data/extensions.xlsx').exists():
            print("🔧 Convirtiendo extensions.xlsx...")
            subprocess.run(['python', 'scripts/extensions_to_json.py', 'data/extensions.xlsx'])
        
        # Git operations
        subprocess.run(['git', 'add', 'data/', 'data/'])
        
        commit_msg = f"🤖 Daily auto-sync - {datetime.now().strftime('%Y-%m-%d')}"
        result = subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            subprocess.run(['git', 'push', 'origin', 'main'])
            print("✅ Sincronización diaria completada")
        else:
            print("ℹ️  No hay cambios que sincronizar")
            
    except Exception as e:
        print(f"❌ Error en sincronización diaria: {str(e)}")
    
    print("\n" + "="*60 + "\n")

def watch_files():
    """Observa cambios en archivos en tiempo real"""
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         🔄 GXO Auto-Sync Service - ACTIVO                   ║
║                                                              ║
║  Monitoreando cambios en archivos Excel...                   ║
║  Presiona Ctrl+C para detener                                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Configurar observador
    event_handler = ExcelChangeHandler()
    observer = Observer()
    
    # Observar carpeta data/
    data_path = str(Path('data').absolute())
    observer.schedule(event_handler, data_path, recursive=False)
    observer.start()
    
    print(f"👀 Observando: {data_path}")
    print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    last_daily_sync = datetime.now().date()
    
    try:
        while True:
            time.sleep(60)  # Revisar cada minuto
            
            # Sincronización diaria a las 00:00
            current_date = datetime.now().date()
            if current_date > last_daily_sync:
                daily_sync()
                last_daily_sync = current_date
                
    except KeyboardInterrupt:
        print("\n\n⏹️  Deteniendo servicio...")
        observer.stop()
        print("✅ Servicio detenido correctamente")
    
    observer.join()

if __name__ == '__main__':
    # Verificar que estamos en el directorio correcto
    if not Path('data').exists():
        print("❌ Error: Debes ejecutar este script desde la raíz del proyecto")
        print("💡 Navega a la carpeta del proyecto y ejecuta: python scripts/auto_sync.py")
        sys.exit(1)
    
    # Verificar que Git está configurado
    try:
        subprocess.run(['git', 'status'], capture_output=True, check=True)
    except:
        print("❌ Error: No se detectó un repositorio Git")
        print("💡 Asegúrate de estar en un repositorio Git válido")
        sys.exit(1)
    
    watch_files()