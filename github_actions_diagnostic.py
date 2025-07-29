#!/usr/bin/env python3
"""
Verificador completo de GitHub Actions - Diagnóstico de problemas con cron
"""
import requests
import json
from datetime import datetime, timedelta

def check_github_workflow_detailed():
    """Verificación detallada del estado de workflows"""
    repo = "XinhoGOD/Fantasy"
    
    print("🔍 DIAGNÓSTICO COMPLETO DE GITHUB ACTIONS")
    print("=" * 60)
    
    try:
        # 1. Verificar workflows disponibles
        print("\n1️⃣ WORKFLOWS DISPONIBLES:")
        workflows_url = f"https://api.github.com/repos/{repo}/actions/workflows"
        workflows_response = requests.get(workflows_url)
        
        if workflows_response.status_code == 200:
            workflows = workflows_response.json()
            for workflow in workflows['workflows']:
                name = workflow['name']
                state = workflow['state']
                path = workflow['path']
                print(f"   • {name}")
                print(f"     Estado: {state}")
                print(f"     Archivo: {path}")
                print()
        
        # 2. Verificar ejecuciones recientes con más detalle
        print("2️⃣ EJECUCIONES RECIENTES (últimas 20):")
        runs_url = f"https://api.github.com/repos/{repo}/actions/runs?per_page=20"
        runs_response = requests.get(runs_url)
        
        if runs_response.status_code == 200:
            runs = runs_response.json()
            
            print(f"   Total de ejecuciones encontradas: {runs['total_count']}")
            print("   Últimas 20 ejecuciones:")
            
            now = datetime.now()
            cron_executions = []
            manual_executions = []
            
            for run in runs['workflow_runs']:
                name = run['name']
                status = run['status']
                conclusion = run['conclusion']
                created_at = run['created_at']
                event = run['event']
                
                # Calcular tiempo transcurrido
                try:
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    time_diff = now - created_dt.replace(tzinfo=None)
                    hours_ago = int(time_diff.total_seconds() // 3600)
                    minutes_ago = int((time_diff.total_seconds() % 3600) // 60)
                    time_str = f"{hours_ago}h {minutes_ago}m ago"
                except:
                    time_str = "unknown"
                
                status_emoji = "✅" if conclusion == "success" else "❌" if conclusion == "failure" else "🔄"
                event_emoji = "⏰" if event == "schedule" else "👤" if event == "workflow_dispatch" else "🔀"
                
                print(f"   {status_emoji} {event_emoji} {name[:50]}")
                print(f"       {status}/{conclusion} - {time_str} - Evento: {event}")
                
                # Categorizar ejecuciones
                if event == "schedule":
                    cron_executions.append((created_dt, time_str))
                elif event == "workflow_dispatch":
                    manual_executions.append((created_dt, time_str))
            
            # 3. Análisis de ejecuciones programadas
            print(f"\n3️⃣ ANÁLISIS DE EJECUCIONES PROGRAMADAS:")
            print(f"   📅 Ejecuciones por cron: {len(cron_executions)}")
            print(f"   👤 Ejecuciones manuales: {len(manual_executions)}")
            
            if cron_executions:
                latest_cron = min(cron_executions, key=lambda x: x[0])
                print(f"   ⏰ Última ejecución automática: {latest_cron[1]}")
                
                # Verificar si debería haber habido más ejecuciones
                latest_cron_dt = latest_cron[0]
                expected_executions = int((now - latest_cron_dt.replace(tzinfo=None)).total_seconds() // 1800)  # cada 30min
                print(f"   🤔 Ejecuciones esperadas desde entonces: ~{expected_executions}")
                
                if expected_executions > 1:
                    print(f"   🚨 PROBLEMA DETECTADO: Faltan ~{expected_executions-1} ejecuciones automáticas")
                    print(f"   💡 Posibles causas:")
                    print(f"      • Repositorio inactivo (GitHub pausa crons en repos sin actividad)")
                    print(f"      • Límites de GitHub Actions alcanzados")
                    print(f"      • Configuración de cron incorrecta")
                    print(f"      • Fallos recurrentes que pausaron el workflow")
                else:
                    print(f"   ✅ Frecuencia de ejecución normal")
            else:
                print(f"   🚨 NO HAY EJECUCIONES AUTOMÁTICAS RECIENTES")
                print(f"   💡 El cron schedule NO se está ejecutando")
        
        # 4. Verificar límites y cuotas
        print(f"\n4️⃣ VERIFICACIÓN DE LÍMITES:")
        print(f"   💡 GitHub Actions en repos públicos:")
        print(f"      • Minutos ilimitados para repos públicos")
        print(f"      • Cron jobs pueden pausarse en repos inactivos")
        print(f"      • Máximo 20 workflows concurrentes")
        
        # 5. Recomendaciones
        print(f"\n5️⃣ RECOMENDACIONES:")
        if len(cron_executions) == 0:
            print(f"   🔧 SOLUCIÓN INMEDIATA:")
            print(f"      1. Ejecutar workflow manualmente para reactivar")
            print(f"      2. Hacer un push/commit para generar actividad")
            print(f"      3. Verificar que el archivo .yml esté en la branch main")
            print(f"      4. Revisar sintaxis del cron en el archivo YAML")
        else:
            latest_cron_dt = min(cron_executions, key=lambda x: x[0])[0]
            hours_since = (now - latest_cron_dt.replace(tzinfo=None)).total_seconds() // 3600
            if hours_since > 2:
                print(f"   ⚠️ REACTIVACIÓN NECESARIA:")
                print(f"      • Última ejecución automática hace {int(hours_since)} horas")
                print(f"      • Ejecutar manualmente para reactivar el cron")
                print(f"      • GitHub puede pausar crons en repos 'inactivos'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        return False

if __name__ == "__main__":
    check_github_workflow_detailed()
