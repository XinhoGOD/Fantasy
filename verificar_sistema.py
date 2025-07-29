#!/usr/bin/env python3
"""
🔍 Script de Verificación Final - NFL Fantasy Scraper 24/7
Verifica que todo esté configurado correctamente antes del despliegue.
"""

import os
import sys
from pathlib import Path

def check_files():
    """Verificar que todos los archivos necesarios existan."""
    print("📁 VERIFICANDO ARCHIVOS...")
    
    required_files = [
        "scrapper.py",
        "requirements.txt", 
        ".github/workflows/nfl-scraper-30min.yml",
        ".github/workflows/health-check.yml",
        ".github/workflows/nfl-scraper-hourly.yml",
        "add_week_column.sql",
        "GITHUB_ACTIONS_24_7.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f"❌ Falta: {file_path}")
        else:
            print(f"✅ Existe: {file_path}")
    
    if missing_files:
        print(f"\n🚨 FALTAN {len(missing_files)} ARCHIVOS REQUERIDOS")
        return False
    else:
        print(f"\n✅ TODOS LOS ARCHIVOS REQUERIDOS ESTÁN PRESENTES")
        return True

def check_environment():
    """Verificar variables de entorno."""
    print("\n🌍 VERIFICANDO VARIABLES DE ENTORNO...")
    
    # Verificar variables de Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if supabase_url:
        print(f"✅ SUPABASE_URL: Configurada ({supabase_url[:30]}...)")
    else:
        print("⚠️ SUPABASE_URL: No configurada localmente (OK para GitHub)")
    
    if supabase_key:
        print(f"✅ SUPABASE_KEY: Configurada ({supabase_key[:20]}...)")
    else:
        print("⚠️ SUPABASE_KEY: No configurada localmente (OK para GitHub)")
    
    return True

def check_python_dependencies():
    """Verificar que las dependencias estén disponibles."""
    print("\n📦 VERIFICANDO DEPENDENCIAS PYTHON...")
    
    required_packages = [
        "selenium", "beautifulsoup4", "supabase", "requests"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: Instalado")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}: No instalado")
    
    if missing_packages:
        print(f"\n⚠️ FALTAN {len(missing_packages)} DEPENDENCIAS")
        print("💡 Ejecuta: pip install -r requirements.txt")
        return False
    else:
        print(f"\n✅ TODAS LAS DEPENDENCIAS ESTÁN INSTALADAS")
        return True

def check_scraper_functionality():
    """Verificar funcionalidad básica del scraper."""
    print("\n🧪 VERIFICANDO FUNCIONALIDAD DEL SCRAPER...")
    
    try:
        # Importar el scraper
        from scrapper import SupabaseManager
        print("✅ Importación del scraper: OK")
        
        # Verificar conexión a Supabase (si las variables están configuradas)
        if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
            try:
                sm = SupabaseManager()
                print("✅ Conexión a Supabase: OK")
                
                # Probar detección de semana
                current_week = sm.detect_current_nfl_week()
                print(f"✅ Detección de semana NFL: {current_week}")
                
                return True
            except Exception as e:
                print(f"❌ Error de Supabase: {e}")
                return False
        else:
            print("⚠️ Variables de Supabase no configuradas - omitiendo pruebas de BD")
            return True
            
    except Exception as e:
        print(f"❌ Error importando scraper: {e}")
        return False

def check_github_workflows():
    """Verificar configuración de workflows."""
    print("\n⚙️ VERIFICANDO WORKFLOWS DE GITHUB...")
    
    workflows = {
        ".github/workflows/nfl-scraper-30min.yml": "Principal (30 min)",
        ".github/workflows/health-check.yml": "Health Check (2h)",
        ".github/workflows/nfl-scraper-hourly.yml": "Backup (4h)"
    }
    
    all_good = True
    for workflow_path, description in workflows.items():
        if Path(workflow_path).exists():
            # Verificar contenido básico
            with open(workflow_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if "schedule:" in content and "cron:" in content:
                print(f"✅ {description}: Configurado correctamente")
            else:
                print(f"❌ {description}: Falta configuración de schedule")
                all_good = False
        else:
            print(f"❌ {description}: Archivo no encontrado")
            all_good = False
    
    return all_good

def main():
    """Función principal de verificación."""
    print("🔍 VERIFICACIÓN FINAL - NFL FANTASY SCRAPER 24/7")
    print("=" * 60)
    print("Verificando que todo esté listo para ejecución automática...")
    print()
    
    # Ejecutar todas las verificaciones
    checks = [
        check_files(),
        check_environment(), 
        check_python_dependencies(),
        check_scraper_functionality(),
        check_github_workflows()
    ]
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VERIFICACIÓN:")
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"✅ Verificaciones pasadas: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ¡SISTEMA LISTO PARA DESPLIEGUE!")
        print("🚀 Pasos siguientes:")
        print("   1. Configura SUPABASE_URL y SUPABASE_KEY en GitHub Secrets")
        print("   2. Ejecuta add_week_column.sql en tu base de datos Supabase")
        print("   3. Haz commit y push para activar los workflows")
        print("   4. El sistema iniciará automáticamente cada 30 minutos")
        print("\n💡 Monitorea la primera ejecución en GitHub Actions")
        return True
    else:
        print(f"\n⚠️ HAY {total - passed} PROBLEMAS QUE RESOLVER")
        print("🔧 Revisa los errores arriba y corrígelos antes del despliegue")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
