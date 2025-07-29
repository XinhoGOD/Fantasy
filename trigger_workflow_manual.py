#!/usr/bin/env python3
"""
Activador manual de workflow GitHub Actions para reactivar cron schedules
"""
import requests
import json
import os

def trigger_workflow_manually():
    """Ejecuta manualmente el workflow para reactivar el cron schedule"""
    
    # Configuración
    repo = "XinhoGOD/Fantasy"
    workflow_file = "nfl-scraper-30min.yml"
    
    print("🔄 REACTIVACIÓN MANUAL DE GITHUB ACTIONS")
    print("=" * 50)
    print(f"📂 Repositorio: {repo}")
    print(f"⚙️ Workflow: {workflow_file}")
    print()
    
    # GitHub requiere un token para trigger workflows
    # Por seguridad, esto se hace mejor desde la UI de GitHub
    print("💡 INSTRUCCIONES PARA REACTIVACIÓN MANUAL:")
    print()
    print("1️⃣ Ve a GitHub.com")
    print(f"2️⃣ Navega a: https://github.com/{repo}")
    print("3️⃣ Ve a la pestaña 'Actions'")
    print("4️⃣ Busca el workflow: '🏈 NFL Fantasy Scraper 24/7 - Cada 30 Minutos'")
    print("5️⃣ Haz click en 'Run workflow' (botón azul)")
    print("6️⃣ Deja las opciones por defecto y haz click en 'Run workflow'")
    print()
    print("✅ RESULTADO ESPERADO:")
    print("   • El workflow se ejecutará inmediatamente")
    print("   • Los cron schedules se reactivarán automáticamente")  
    print("   • Empezará a ejecutarse cada 30 minutos de nuevo")
    print()
    print("🔍 VERIFICACIÓN:")
    print("   • Espera 30-60 minutos")
    print("   • Verifica que aparezcan nuevas ejecuciones automáticas")
    print("   • Las ejecuciones tendrán 'Event: schedule' en lugar de 'workflow_dispatch'")
    print()
    print("📋 ALTERNATIVA DESDE URL DIRECTA:")
    print(f"   https://github.com/{repo}/actions/workflows/{workflow_file}")

if __name__ == "__main__":
    trigger_workflow_manually()
