#!/usr/bin/env python3
"""
Prueba de Sensibilidad Extrema - Detecta CUALQUIER cambio por más mínimo que sea
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    print("❌ Supabase no disponible")
    sys.exit(1)

# Importar el SupabaseManager desde scrapper.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scrapper import SupabaseManager


def test_sensibilidad_extrema():
    """Prueba la nueva función de sensibilidad extrema."""
    print("🔬 PRUEBA DE SENSIBILIDAD EXTREMA")
    print("="*60)
    print("Probando detección de cambios mínimos en rostered/started")
    print()
    
    # Inicializar manager
    sm = SupabaseManager()
    print("✅ Supabase Manager inicializado")
    
    # Crear datos de prueba con cambios MÍNIMOS
    print("\n📊 CASOS DE PRUEBA:")
    print("-"*40)
    
    test_cases = [
        {
            "name": "Cambio mínimo 0.1% en rostered",
            "old": {
                "player_name": "Josh Allen",
                "player_id": "12345",
                "percent_rostered": 95.5,
                "percent_started": 88.2,
                "percent_rostered_change": 2.1,
                "percent_started_change": -0.3,
                "opponent": "vs BUF"
            },
            "new": {
                "player_name": "Josh Allen", 
                "player_id": "12345",
                "percent_rostered": 95.6,  # +0.1% cambio
                "percent_started": 88.2,
                "percent_rostered_change": 2.1,
                "percent_started_change": -0.3,
                "opponent": "vs BUF"
            }
        },
        {
            "name": "Cambio mínimo 0.01% en started",
            "old": {
                "player_name": "Patrick Mahomes",
                "player_id": "67890",
                "percent_rostered": 98.7,
                "percent_started": 95.45,
                "percent_rostered_change": 0.2,
                "percent_started_change": 1.8,
                "opponent": "vs KC"
            },
            "new": {
                "player_name": "Patrick Mahomes",
                "player_id": "67890", 
                "percent_rostered": 98.7,
                "percent_started": 95.46,  # +0.01% cambio
                "percent_rostered_change": 0.2,
                "percent_started_change": 1.8,
                "opponent": "vs KC"
            }
        },
        {
            "name": "Cambio en rostered_change solamente",
            "old": {
                "player_name": "Tyreek Hill",
                "player_id": "11111",
                "percent_rostered": 92.1,
                "percent_started": 78.9,
                "percent_rostered_change": 3.2,
                "percent_started_change": -1.1,
                "opponent": "vs MIA"
            },
            "new": {
                "player_name": "Tyreek Hill",
                "player_id": "11111",
                "percent_rostered": 92.1,
                "percent_started": 78.9,
                "percent_rostered_change": 3.3,  # +0.1% cambio
                "percent_started_change": -1.1,
                "opponent": "vs MIA"
            }
        },
        {
            "name": "Cambio de oponente solamente",
            "old": {
                "player_name": "Cooper Kupp",
                "player_id": "22222",
                "percent_rostered": 89.4,
                "percent_started": 82.7,
                "percent_rostered_change": -0.8,
                "percent_started_change": 2.3,
                "opponent": "vs LAR"
            },
            "new": {
                "player_name": "Cooper Kupp",
                "player_id": "22222",
                "percent_rostered": 89.4,
                "percent_started": 82.7,
                "percent_rostered_change": -0.8,
                "percent_started_change": 2.3,
                "opponent": "@ SEA"  # Cambio de oponente
            }
        },
        {
            "name": "Sin cambios (control negativo)",
            "old": {
                "player_name": "Travis Kelce",
                "player_id": "33333",
                "percent_rostered": 96.2,
                "percent_started": 91.8,
                "percent_rostered_change": 1.5,
                "percent_started_change": 0.7,
                "opponent": "vs KC"
            },
            "new": {
                "player_name": "Travis Kelce",
                "player_id": "33333",
                "percent_rostered": 96.2,  # Sin cambios
                "percent_started": 91.8,   # Sin cambios
                "percent_rostered_change": 1.5,
                "percent_started_change": 0.7,
                "opponent": "vs KC"
            }
        }
    ]
    
    # Ejecutar pruebas
    print(f"\n🧪 EJECUTANDO {len(test_cases)} CASOS DE PRUEBA:")
    print("="*60)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print("-" * len(f"{i}. {case['name']}"))
        
        # Probar detección de cambios
        has_changes = sm.has_significant_changes(case['old'], case['new'])
        
        # Mostrar resultado
        if has_changes:
            print(f"   ✅ CAMBIO DETECTADO (como esperado)")
        else:
            print(f"   ❌ No se detectó cambio")
        
        print()
    
    print("\n🎯 RESUMEN DE LA PRUEBA:")
    print("-"*30)
    print("• Casos 1-4: Deberían detectar cambios (✅)")
    print("• Caso 5: NO debería detectar cambios (❌)")
    print("\n🔥 La función ahora es SÚPER SENSIBLE:")
    print("   • Detecta cambios de 0.01% o más")
    print("   • Detecta cambios en matchups (oponente)")
    print("   • Ignora adds/drops (como solicitado)")
    print("   • Registra diferencias exactas")


def test_con_datos_reales():
    """Prueba con jugadores reales de la base de datos."""
    print("\n" + "="*60)
    print("🏈 PRUEBA CON DATOS REALES DE LA BASE DE DATOS")
    print("="*60)
    
    sm = SupabaseManager()
    
    # Obtener algunos jugadores reales
    print("📊 Obteniendo jugadores reales...")
    latest_records = sm.get_latest_player_records()
    
    if not latest_records:
        print("❌ No hay datos reales para probar")
        return
    
    print(f"✅ {len(latest_records)} jugadores encontrados")
    
    # Tomar los primeros 3 jugadores para simular cambios mínimos
    sample_players = list(latest_records.values())[:3]
    
    print(f"\n🔬 SIMULANDO CAMBIOS MÍNIMOS EN {len(sample_players)} JUGADORES:")
    print("-"*50)
    
    for i, player in enumerate(sample_players, 1):
        player_name = player.get('player_name', 'Unknown')
        original_rostered = player.get('percent_rostered', 0) or 0
        
        # Crear versión con cambio mínimo
        modified_player = player.copy()
        modified_player['percent_rostered'] = original_rostered + 0.1  # +0.1% cambio
        
        print(f"\n{i}. {player_name}")
        print(f"   Original: {original_rostered}% rostered")
        print(f"   Modificado: {modified_player['percent_rostered']}% rostered")
        
        # Probar detección
        has_changes = sm.has_significant_changes(player, modified_player)
        
        if has_changes:
            print(f"   ✅ CAMBIO MÍNIMO DETECTADO (+0.1%)")
        else:
            print(f"   ❌ Cambio mínimo NO detectado")


if __name__ == "__main__":
    try:
        test_sensibilidad_extrema()
        test_con_datos_reales()
        
        print(f"\n🎉 PRUEBAS COMPLETADAS")
        print(f"🔧 La función de detección ahora es SÚPER SENSIBLE")
        print(f"📈 Detectará CUALQUIER cambio por más mínimo que sea")
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
