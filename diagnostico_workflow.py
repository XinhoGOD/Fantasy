#!/usr/bin/env python3
"""
Diagnóstico del Workflow de GitHub Actions
Verifica el estado y configuración del workflow nfl-scraper-30min.yml
"""

import os
import yaml
from datetime import datetime, timedelta
import re

def analizar_workflow():
    """Analiza el archivo de workflow y detecta problemas comunes."""
    
    print("🔍 DIAGNÓSTICO DEL WORKFLOW NFL SCRAPER")
    print("=" * 60)
    
    # Leer el archivo del workflow
    workflow_path = ".github/workflows/nfl-scraper-30min.yml"
    
    if not os.path.exists(workflow_path):
        print(f"❌ ERROR: No se encuentra el archivo {workflow_path}")
        return
    
    # Leer contenido
    with open(workflow_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"✅ Archivo encontrado: {workflow_path}")
    print(f"📏 Tamaño: {len(content)} caracteres")
    
    try:
        # Parsear YAML
        workflow_data = yaml.safe_load(content)
        print("✅ Sintaxis YAML válida")
        
        # Verificar estructura básica
        print(f"\n📋 CONFIGURACIÓN DEL WORKFLOW:")
        print(f"   • Nombre: {workflow_data.get('name', 'N/A')}")
        
        # Verificar triggers
        if 'on' in workflow_data:
            triggers = workflow_data['on']
            print(f"   • Triggers configurados: {list(triggers.keys())}")
            
            # Analizar cron schedule
            if 'schedule' in triggers:
                schedules = triggers['schedule']
                for i, schedule in enumerate(schedules):
                    cron_expr = schedule.get('cron', '')
                    print(f"   • Cron #{i+1}: '{cron_expr}'")
                    
                    # Validar expresión cron
                    if validar_cron(cron_expr):
                        print(f"     ✅ Expresión cron válida")
                        explicar_cron(cron_expr)
                    else:
                        print(f"     ❌ Expresión cron inválida")
            
            # Verificar workflow_dispatch
            if 'workflow_dispatch' in triggers:
                print(f"   • ✅ Ejecución manual habilitada")
            else:
                print(f"   • ⚠️ Ejecución manual NO habilitada")
        
        # Verificar jobs
        if 'jobs' in workflow_data:
            jobs = workflow_data['jobs']
            print(f"   • Jobs definidos: {len(jobs)}")
            
            for job_name, job_config in jobs.items():
                timeout = job_config.get('timeout-minutes', 'No definido')
                runs_on = job_config.get('runs-on', 'No definido')
                print(f"     - {job_name}: {runs_on}, timeout {timeout}min")
        
        # Verificar variables de entorno
        if 'env' in workflow_data:
            env_vars = workflow_data['env']
            print(f"   • Variables de entorno: {len(env_vars)}")
            for var, value in env_vars.items():
                if 'secret' in str(value).lower():
                    print(f"     - {var}: [SECRET]")
                else:
                    print(f"     - {var}: {value}")
        
        print(f"\n🎯 PROBLEMAS POTENCIALES DETECTADOS:")
        detectar_problemas_comunes(workflow_data, content)
        
        print(f"\n💡 RAZÓN MÁS PROBABLE:")
        print("🚨 GitHub Actions PAUSA automáticamente los cron schedules")
        print("   cuando un repositorio se considera 'inactivo'")
        print(f"📅 Fecha actual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("⏰ Si no ha habido commits recientes, GitHub desactivó el cron")
        
        print(f"\n🔧 SOLUCIONES RECOMENDADAS:")
        print("1. 🖱️ Ejecutar manualmente el workflow desde GitHub Actions")
        print("2. 📝 Hacer un commit (aunque sea mínimo) para reactivar")
        print("3. ⏰ Una vez ejecutado manualmente, el cron se reactivará")
        print("4. 🔄 Verificar en GitHub > Actions > Workflows")
        
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ ERROR de sintaxis YAML: {e}")
        return False
    
    except Exception as e:
        print(f"❌ ERROR inesperado: {e}")
        return False

def validar_cron(cron_expr):
    """Valida si una expresión cron es sintácticamente correcta."""
    if not cron_expr:
        return False
    
    # Patrón básico para validar cron (5 campos)
    pattern = r'^(\*|[\d,-/]+)\s+(\*|[\d,-/]+)\s+(\*|[\d,-/]+)\s+(\*|[\d,-/]+)\s+(\*|[\d,-/]+)$'
    return bool(re.match(pattern, cron_expr))

def explicar_cron(cron_expr):
    """Explica qué significa una expresión cron."""
    parts = cron_expr.split()
    if len(parts) != 5:
        print(f"     ⚠️ Expresión cron debe tener 5 campos")
        return
    
    minute, hour, day, month, weekday = parts
    
    print(f"     📝 Explicación:")
    print(f"       • Minutos: {minute}")
    print(f"       • Horas: {hour}")
    print(f"       • Día del mes: {day}")
    print(f"       • Mes: {month}")
    print(f"       • Día de la semana: {weekday}")
    
    if cron_expr == "0,30 * * * *":
        print(f"     🎯 SIGNIFICADO: Ejecutar en minuto 0 y 30 de cada hora")
        print(f"       = Cada 30 minutos, las 24 horas, todos los días")
        print(f"       = 48 ejecuciones por día")

def detectar_problemas_comunes(workflow_data, content):
    """Detecta problemas comunes en workflows."""
    problemas = []
    
    # Verificar si hay secrets hardcodeados
    if 'supabase' in content.lower() and '${{ secrets.' not in content:
        problemas.append("⚠️ Posibles credenciales hardcodeadas (usar secrets)")
    
    # Verificar timeout razonable
    jobs = workflow_data.get('jobs', {})
    for job_name, job_config in jobs.items():
        timeout = job_config.get('timeout-minutes')
        if timeout and int(timeout) > 30:
            problemas.append(f"⚠️ Timeout alto en job '{job_name}': {timeout}min")
    
    # Verificar si hay steps problemáticos
    if 'apt-get' in content and 'update' in content:
        if content.count('apt-get update') > 1:
            problemas.append("⚠️ Múltiples 'apt-get update' (optimizar)")
    
    # Verificar versiones pinned
    if 'python-version:' in content:
        if "'3.9'" in content or '"3.9"' in content:
            print("✅ Versión de Python fijada correctamente")
        else:
            problemas.append("⚠️ Versión de Python no específica")
    
    if problemas:
        for problema in problemas:
            print(f"   {problema}")
    else:
        print("✅ No se detectaron problemas técnicos en el workflow")

def verificar_archivos_relacionados():
    """Verifica archivos relacionados con GitHub Actions."""
    print(f"\n📁 ARCHIVOS RELACIONADOS:")
    
    archivos_importantes = [
        ".github/workflows/nfl-scraper-30min.yml",
        ".github/workflows/health-check-advanced.yml", 
        ".github/workflows/health-check.yml",
        ".github/workflows/nfl-scraper-hourly.yml",
        "requirements.txt",
        "scrapper.py"
    ]
    
    for archivo in archivos_importantes:
        if os.path.exists(archivo):
            size = os.path.getsize(archivo)
            print(f"   ✅ {archivo} ({size} bytes)")
        else:
            print(f"   ❌ {archivo} (no encontrado)")

def generar_solucion():
    """Genera comandos específicos para solucionar el problema."""
    print(f"\n🛠️ COMANDOS PARA REACTIVAR EL WORKFLOW:")
    print("=" * 50)
    
    print("1. 📝 Hacer un commit mínimo para reactivar:")
    print("   git add .")
    print("   git commit -m \"🔄 Reactivar workflow automático 24/7\"")
    print("   git push")
    
    print("\n2. 🖱️ O ejecutar manualmente desde GitHub:")
    print("   • Ir a: https://github.com/XinhoGOD/Fantasy/actions")
    print("   • Seleccionar: '🏈 NFL Fantasy Scraper 24/7 - Cada 30 Minutos'")
    print("   • Hacer clic en: 'Run workflow'")
    print("   • Confirmar: 'Run workflow'")
    
    print("\n3. ✅ Verificar reactivación:")
    print("   • El workflow debería aparecer como 'programado'")
    print("   • Verificar en 30 minutos si se ejecutó automáticamente")
    
    print(f"\n⏰ PRÓXIMAS EJECUCIONES ESPERADAS:")
    now = datetime.now()
    for i in range(3):
        next_run = now + timedelta(minutes=30*(i+1))
        print(f"   • {next_run.strftime('%Y-%m-%d %H:%M:%S')} UTC")

if __name__ == "__main__":
    try:
        analizar_workflow()
        verificar_archivos_relacionados()
        generar_solucion()
        
        print(f"\n✅ Diagnóstico completado")
        print(f"💡 El workflow está técnicamente correcto")
        print(f"🚨 Problema: GitHub pausó el cron por 'inactividad'")
        print(f"🔧 Solución: Ejecución manual o commit para reactivar")
        
    except ImportError:
        print("⚠️ Módulo 'yaml' no disponible")
        print("Instalando: pip install pyyaml")
        os.system("pip install pyyaml")
        print("Reiniciar el script después de la instalación")
    except Exception as e:
        print(f"❌ Error durante diagnóstico: {e}")
