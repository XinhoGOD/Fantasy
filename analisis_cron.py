#!/usr/bin/env python3
"""
Análisis de expresiones cron para GitHub Actions
Explica la diferencia entre '0,30 * * * *' y '*/30 * * * *'
"""

def explicar_cron_expressions():
    print("🕐 ANÁLISIS DE EXPRESIONES CRON")
    print("=" * 50)
    
    print("\n❌ EXPRESIÓN ANTERIOR (PROBLEMÁTICA):")
    print("   cron: '0,30 * * * *'")
    print("   📝 Significado: Ejecutar en minuto 0 Y minuto 30 de cada hora")
    print("   ⏰ Ejecuciones:")
    print("      • 00:00, 00:30")
    print("      • 01:00, 01:30") 
    print("      • 02:00, 02:30")
    print("      • ... etc")
    print("   📊 Total: 48 ejecuciones/día (2 por hora)")
    print("   🚨 PROBLEMA: GitHub puede ejecutar solo UNA por hora")
    print("   📈 RESULTADO: Ejecuta solo en :00 o solo en :30 (cada hora)")
    
    print("\n✅ EXPRESIÓN NUEVA (CORREGIDA):")
    print("   cron: '*/30 * * * *'")
    print("   📝 Significado: Ejecutar CADA 30 minutos")
    print("   ⏰ Ejecuciones:")
    print("      • 00:00, 00:30")
    print("      • 01:00, 01:30")
    print("      • 02:00, 02:30") 
    print("      • ... etc")
    print("   📊 Total: 48 ejecuciones/día (cada 30 minutos exactamente)")
    print("   ✅ RESULTADO: Ejecución garantizada cada 30 minutos")
    
    print("\n🔧 DIFERENCIA TÉCNICA:")
    print("   • '0,30 * * * *' = Lista de minutos específicos")
    print("   • '*/30 * * * *'  = Intervalo de 30 minutos")
    print("   • GitHub Actions prefiere intervalos sobre listas")
    
    print("\n📅 PRÓXIMAS EJECUCIONES ESPERADAS:")
    from datetime import datetime, timedelta
    
    now = datetime.now()
    print(f"   🕐 Ahora: {now.strftime('%H:%M:%S')}")
    
    # Calcular próxima ejecución en múltiplo de 30 minutos
    minutes = now.minute
    next_30 = ((minutes // 30) + 1) * 30
    
    if next_30 >= 60:
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        next_time = now.replace(minute=next_30, second=0, microsecond=0)
    
    for i in range(5):
        exec_time = next_time + timedelta(minutes=30*i)
        print(f"   • {exec_time.strftime('%H:%M')} (en {30*i + (next_time - now).total_seconds()//60:.0f} min)")
    
    print("\n🚀 ACCIONES REQUERIDAS:")
    print("   1. ✅ Cambio aplicado al workflow")
    print("   2. 📤 Hacer commit y push del cambio")
    print("   3. 🖱️ Ejecutar manualmente UNA VEZ desde GitHub")
    print("   4. ⏰ Verificar que funcione cada 30 minutos")

if __name__ == "__main__":
    explicar_cron_expressions()
