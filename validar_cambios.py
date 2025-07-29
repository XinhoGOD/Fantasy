#!/usr/bin/env python3
"""
Script para Validar Cambios Específicos
Verifica si realmente hay cambios en los campos que nos importan
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

class ValidadorCambios:
    """Valida si los cambios detectados son reales."""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(self.url, self.key)
    
    def analizar_cambios_reales(self, jugador_nombre: str = None):
        """Analiza si hay cambios reales en los campos que monitoreamos."""
        print("🔍 ANÁLISIS DE CAMBIOS REALES EN CAMPOS ESPECÍFICOS")
        print("="*70)
        
        # Campos que monitoreamos
        campos_importantes = [
            'percent_rostered',
            'percent_rostered_change', 
            'percent_started',
            'percent_started_change'
        ]
        
        print(f"🎯 Campos monitoreados: {', '.join(campos_importantes)}")
        print(f"❌ Campos IGNORADOS: adds, drops (para evitar falsos positivos)")
        
        if jugador_nombre:
            # Analizar jugador específico
            response = self.supabase.table('nfl_fantasy_trends').select('*').ilike(
                'player_name', f'%{jugador_nombre}%'
            ).order('scraped_at', desc=True).limit(5).execute()
            
            if response.data and len(response.data) >= 2:
                jugador_data = response.data
                print(f"\n👤 ANÁLISIS DE: {jugador_data[0]['player_name']}")
                print(f"📊 Últimos {len(jugador_data)} registros:")
                
                for i in range(len(jugador_data) - 1):
                    registro_nuevo = jugador_data[i]
                    registro_anterior = jugador_data[i + 1]
                    
                    fecha_nuevo = registro_nuevo['scraped_at'][:19]
                    fecha_anterior = registro_anterior['scraped_at'][:19]
                    
                    print(f"\n🔄 Comparación {i+1}: {fecha_anterior} → {fecha_nuevo}")
                    
                    cambios_detectados = []
                    for campo in campos_importantes:
                        valor_anterior = registro_anterior.get(campo)
                        valor_nuevo = registro_nuevo.get(campo)
                        
                        if valor_anterior != valor_nuevo:
                            cambios_detectados.append({
                                'campo': campo,
                                'anterior': valor_anterior,
                                'nuevo': valor_nuevo
                            })
                    
                    if cambios_detectados:
                        print(f"   ✅ {len(cambios_detectados)} cambios detectados:")
                        for cambio in cambios_detectados:
                            print(f"      • {cambio['campo']}: {cambio['anterior']} → {cambio['nuevo']}")
                        print(f"   📝 RESULTADO: Se insertaría en BD")
                    else:
                        print(f"   ⏭️ Sin cambios en campos monitoreados")
                        print(f"   📝 RESULTADO: Se omitiría (no se inserta)")
        else:
            print(f"\n💡 Para analizar un jugador específico, proporciona su nombre")
    
    def contar_cambios_en_ultimos_registros(self):
        """Cuenta cuántos de los últimos registros realmente representan cambios."""
        print(f"\n📈 ANÁLISIS DE ÚLTIMOS REGISTROS VS CAMBIOS REALES")
        print("="*70)
        
        # Obtener últimos 50 registros
        response = self.supabase.table('nfl_fantasy_trends').select('*').order(
            'created_at', desc=True
        ).limit(50).execute()
        
        if not response.data:
            print("❌ No hay registros para analizar")
            return
        
        registros_recientes = response.data
        print(f"📊 Analizando {len(registros_recientes)} registros más recientes...")
        
        # Agrupar por jugador
        jugadores_recientes = {}
        for registro in registros_recientes:
            player_id = registro.get('player_id')
            if player_id and player_id not in jugadores_recientes:
                jugadores_recientes[player_id] = registro
        
        print(f"👥 {len(jugadores_recientes)} jugadores únicos en registros recientes")
        
        # Para cada jugador, verificar si su registro más reciente representa un cambio real
        cambios_reales = 0
        registros_innecesarios = 0
        
        campos_importantes = ['percent_rostered', 'percent_started', 'percent_rostered_change', 'percent_started_change']
        
        for player_id, registro_reciente in jugadores_recientes.items():
            # Obtener el registro anterior de este jugador
            response_anterior = self.supabase.table('nfl_fantasy_trends').select('*').eq(
                'player_id', player_id
            ).order('created_at', desc=True).limit(2).execute()
            
            if response_anterior.data and len(response_anterior.data) >= 2:
                registro_anterior = response_anterior.data[1]  # El segundo más reciente
                
                # Comparar campos importantes
                hay_cambios = False
                for campo in campos_importantes:
                    if registro_reciente.get(campo) != registro_anterior.get(campo):
                        hay_cambios = True
                        break
                
                if hay_cambios:
                    cambios_reales += 1
                else:
                    registros_innecesarios += 1
                    player_name = registro_reciente.get('player_name', 'Unknown')
                    print(f"   ⏭️ {player_name}: valores idénticos en campos monitoreados")
        
        print(f"\n📈 RESULTADOS:")
        print(f"   ✅ Registros con cambios reales: {cambios_reales}")
        print(f"   ⏭️ Registros innecesarios (sin cambios): {registros_innecesarios}")
        
        if (cambios_reales + registros_innecesarios) > 0:
            porcentaje_util = (cambios_reales / (cambios_reales + registros_innecesarios)) * 100
            print(f"   📊 Eficiencia del sistema: {porcentaje_util:.1f}% útil")
            
            if porcentaje_util < 50:
                print(f"   🚨 PROBLEMA: Demasiados registros innecesarios!")
            elif porcentaje_util > 80:
                print(f"   ✅ EXCELENTE: Sistema muy eficiente")
            else:
                print(f"   ⚠️ MEJORABLE: Sistema funciona pero puede optimizarse")
    
    def run_analysis(self):
        """Ejecuta análisis completo."""
        self.analizar_cambios_reales()
        self.contar_cambios_en_ultimos_registros()
        
        print(f"\n💡 CÓMO VERIFICAR SI EL SISTEMA FUNCIONA BIEN:")
        print("="*70)
        print("1. Ejecuta: python debug_comparacion.py")
        print("2. Si el porcentaje de cambios es 10-30%, es NORMAL")
        print("3. Si es >70%, hay un problema en la detección")
        print("4. Si es <5%, la web no está cambiando mucho")
        print()
        print("🎯 TU SISTEMA ESTÁ FUNCIONANDO CORRECTAMENTE si:")
        print("• Solo inserta 20-100 jugadores por scraping (de ~900 totales)")
        print("• Los jugadores insertados tienen cambios REALES en rostered/started")
        print("• Los logs muestran 'jugadores omitidos' con sin cambios")

def main():
    validador = ValidadorCambios()
    validador.run_analysis()

if __name__ == "__main__":
    main()
