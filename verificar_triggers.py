#!/usr/bin/env python3
"""
Script rápido para verificar triggers del workflow
"""

import yaml

def verificar_triggers():
    with open('.github/workflows/nfl-scraper-30min.yml', 'r', encoding='utf-8') as f:
        workflow = yaml.safe_load(f)
    
    print("🔍 ANÁLISIS DE TRIGGERS DEL WORKFLOW")
    print("=" * 50)
    
    if 'on' in workflow:
        triggers = workflow['on']
        print(f"✅ Sección 'on' encontrada")
        print(f"📝 Triggers configurados: {list(triggers.keys())}")
        
        if 'schedule' in triggers:
            print(f"✅ Schedule configurado:")
            schedules = triggers['schedule']
            for i, schedule in enumerate(schedules):
                cron = schedule.get('cron', 'NO ENCONTRADO')
                print(f"   Cron #{i+1}: {cron}")
                
                if cron == '0,30 * * * *':
                    print(f"   ✅ Configuración correcta: cada 30 minutos")
                    print(f"   📊 Esto ejecuta 48 veces por día")
                else:
                    print(f"   ❌ Configuración inesperada")
        else:
            print(f"❌ NO HAY SCHEDULE CONFIGURADO")
        
        if 'workflow_dispatch' in triggers:
            print(f"✅ Ejecución manual habilitada")
        else:
            print(f"❌ Ejecución manual NO disponible")
    else:
        print(f"❌ NO HAY SECCIÓN 'on' EN EL WORKFLOW")

if __name__ == "__main__":
    verificar_triggers()
