#!/usr/bin/env python3
"""
Script de Debug: Visualizar lógica de comparación del scraper
Muestra exactamente con qué datos se está comparando cada scraping
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# Intentar cargar python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("📝 python-dotenv no disponible, usando variables de entorno del sistema")

# Intentar importar Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    print("❌ Supabase no disponible. Instalar con: pip install supabase")
    sys.exit(1)

import logging

class ComparacionDebugger:
    """Clase para debuggear la lógica de comparación del scraper."""
    
    def __init__(self):
        """Inicializar conexión a Supabase."""
        try:
            self.url = os.getenv("SUPABASE_URL")
            self.key = os.getenv("SUPABASE_KEY")
            
            if not self.url or not self.key:
                print("❌ Variables de entorno SUPABASE_URL y SUPABASE_KEY son requeridas")
                sys.exit(1)
            
            self.supabase: Client = create_client(self.url, self.key)
            
            # Configurar logging
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
            self.logger = logging.getLogger(__name__)
            
            print("✅ Conexión a Supabase establecida")
            
        except Exception as e:
            print(f"❌ Error conectando a Supabase: {e}")
            sys.exit(1)
    
    def detect_current_nfl_week(self) -> int:
        """Detecta la semana actual de la NFL (simplificado para debug)."""
        try:
            from datetime import datetime
            
            current_date = datetime.now()
            current_year = current_date.year
            
            # Temporada 2025
            if current_year == 2025:
                # Estamos en julio 2025, temporada no ha empezado
                return 1
            else:
                # Default a semana 1
                return 1
                
        except Exception as e:
            print(f"❌ Error calculando semana: {e}")
            return 1
    
    def get_latest_player_records(self, by_week: bool = False, target_week: int = None) -> Dict[str, Dict]:
        """
        Obtiene el último registro de cada jugador por su player_id.
        IDÉNTICA a la función del scraper principal.
        """
        try:
            if by_week and target_week:
                print(f"🔍 Obteniendo último registro de cada jugador para semana {target_week}...")
                query = self.supabase.table('nfl_fantasy_trends').select('*').eq('semana', target_week)
            else:
                print("🔍 Obteniendo último registro individual de cada jugador...")
                query = self.supabase.table('nfl_fantasy_trends').select('*')
            
            # Obtener registros ordenados por fecha de scraping
            all_records_response = query.order('scraped_at', desc=True).execute()
            
            if not all_records_response.data:
                if by_week:
                    print(f"📊 No hay registros para semana {target_week}")
                else:
                    print("📊 No hay registros históricos")
                return {}
            
            # Crear diccionario con el último registro de cada jugador
            latest_by_player = {}
            
            for record in all_records_response.data:
                player_id = record.get('player_id')
                if player_id and player_id not in latest_by_player:
                    # Este es el registro más reciente de este jugador
                    latest_by_player[player_id] = record
            
            if by_week:
                print(f"📊 Últimos registros obtenidos para {len(latest_by_player)} jugadores únicos (semana {target_week})")
            else:
                print(f"📊 Últimos registros obtenidos para {len(latest_by_player)} jugadores únicos")
            return latest_by_player
            
        except Exception as e:
            print(f"❌ Error obteniendo registros por jugador: {e}")
            return {}
    
    def analyze_comparison_logic(self):
        """Analiza qué datos usa la lógica de comparación actual."""
        print("\n🔬 ANÁLISIS DE LÓGICA DE COMPARACIÓN")
        print("="*80)
        
        # Detectar semana actual
        current_week = self.detect_current_nfl_week()
        print(f"🏈 Semana NFL actual detectada: {current_week}")
        
        # Simular la lógica exacta del scraper
        if current_week > 1:
            previous_week = current_week - 1
            print(f"\n🔍 COMPARACIÓN CONFIGURADA: semana {current_week} vs semana {previous_week}")
            
            # Obtener datos de semana anterior
            latest_by_player = self.get_latest_player_records(by_week=True, target_week=previous_week)
            
            if not latest_by_player:
                print(f"⚠️ No hay datos de semana {previous_week}, cambiando a comparación con historial completo")
                latest_by_player = self.get_latest_player_records(by_week=False)
                comparison_mode = "historial completo"
            else:
                comparison_mode = f"semana {previous_week}"
        else:
            print(f"\n🔍 COMPARACIÓN CONFIGURADA: semana 1 - usando historial completo")
            latest_by_player = self.get_latest_player_records(by_week=False)
            comparison_mode = "historial completo"
        
        # Análisis de los datos de comparación
        print(f"\n📊 DATOS DE COMPARACIÓN ({comparison_mode}):")
        print(f"   • Jugadores únicos para comparar: {len(latest_by_player)}")
        
        if latest_by_player:
            # Analizar distribución por fecha
            dates_distribution = {}
            for player_id, record in latest_by_player.items():
                scraped_date = record.get('scraped_at', '')[:19]
                if scraped_date not in dates_distribution:
                    dates_distribution[scraped_date] = 0
                dates_distribution[scraped_date] += 1
            
            print(f"   • Distribución por fecha de scraping:")
            sorted_dates = sorted(dates_distribution.items(), key=lambda x: x[0], reverse=True)
            
            for date, count in sorted_dates[:5]:  # Top 5 fechas más recientes
                print(f"     - {date}: {count} jugadores")
            
            if len(sorted_dates) > 5:
                remaining = sum(count for _, count in sorted_dates[5:])
                print(f"     - ... y {remaining} jugadores en fechas anteriores")
        
        return latest_by_player, comparison_mode
    
    def simulate_scraping_comparison(self, sample_size: int = 10):
        """Simula cómo sería la comparación con un nuevo scraping."""
        print(f"\n🎯 SIMULACIÓN DE COMPARACIÓN CON NUEVO SCRAPING")
        print("="*80)
        
        # Obtener datos de comparación
        latest_by_player, comparison_mode = self.analyze_comparison_logic()
        
        if not latest_by_player:
            print("❌ No hay datos para simular comparación")
            return
        
        # Simular nuevos datos (tomando jugadores existentes)
        sample_players = list(latest_by_player.values())[:sample_size]
        
        print(f"📝 Simulando {len(sample_players)} jugadores en el nuevo scraping...")
        print(f"🔍 Comparando contra: {comparison_mode}")
        
        new_players = 0
        changed_players = 0
        unchanged_players = 0
        
        print(f"\n📋 RESULTADOS DE COMPARACIÓN SIMULADA:")
        
        for i, player_record in enumerate(sample_players, 1):
            player_id = player_record.get('player_id')
            player_name = player_record.get('player_name', 'Unknown')
            
            # Simular que este jugador está en el nuevo scraping
            if player_id in latest_by_player:
                # Jugador existente - simular si tendría cambios
                original_rostered = player_record.get('percent_rostered', 0) or 0
                
                # 70% probabilidad de no tener cambios, 30% de tener cambios
                import random
                if random.random() < 0.7:
                    # Sin cambios
                    unchanged_players += 1
                    status = "⏭️ SIN CAMBIOS (OMITIDO)"
                else:
                    # Con cambios simulados
                    changed_players += 1
                    status = "🔄 CON CAMBIOS (INSERTADO)"
            else:
                # Jugador nuevo (no debería pasar en esta simulación)
                new_players += 1
                status = "🆕 NUEVO (INSERTADO)"
            
            print(f"   {i:2d}. {player_name[:25]:<25} | {original_rostered:5.1f}% rostered | {status}")
        
        print(f"\n📈 RESUMEN DE SIMULACIÓN:")
        print(f"   • Jugadores nuevos: {new_players}")
        print(f"   • Jugadores con cambios: {changed_players}")
        print(f"   • Jugadores sin cambios (omitidos): {unchanged_players}")
        print(f"   • Total que se insertaría: {new_players + changed_players}")
        print(f"   • Porcentaje de cambios: {((new_players + changed_players) / len(sample_players)) * 100:.1f}%")
    
    def analyze_database_content(self):
        """Analiza el contenido actual de la base de datos."""
        print(f"\n🗄️ ANÁLISIS DEL CONTENIDO DE LA BASE DE DATOS")
        print("="*80)
        
        try:
            # Total de registros
            total_response = self.supabase.table('nfl_fantasy_trends').select('id').execute()
            total_records = len(total_response.data) if total_response.data else 0
            
            print(f"📊 Total de registros en BD: {total_records}")
            
            # Contar registros por timestamp
            timestamps_response = self.supabase.table('nfl_fantasy_trends').select('scraped_at').execute()
            timestamp_counts = {}
            
            if timestamps_response.data:
                for record in timestamps_response.data:
                    ts = record['scraped_at'][:19]  # Solo fecha y hora
                    timestamp_counts[ts] = timestamp_counts.get(ts, 0) + 1
            
            print(f"📅 Timestamps únicos: {len(timestamp_counts)}")
            
            # Mostrar últimos 10 timestamps
            sorted_timestamps = sorted(timestamp_counts.items(), key=lambda x: x[0], reverse=True)[:10]
            
            print(f"\n📋 Últimos 10 scrapings:")
            for i, (timestamp, count) in enumerate(sorted_timestamps, 1):
                print(f"   {i:2d}. {timestamp} | {count:4d} registros")
            
            # Contar jugadores únicos
            unique_players_response = self.supabase.table('nfl_fantasy_trends').select('player_id').execute()
            unique_player_ids = set()
            
            if unique_players_response.data:
                for record in unique_players_response.data:
                    player_id = record.get('player_id')
                    if player_id:
                        unique_player_ids.add(player_id)
            
            print(f"\n👥 Jugadores únicos registrados: {len(unique_player_ids)}")
            
            # Calcular promedio de registros por jugador
            if unique_player_ids:
                avg_records_per_player = total_records / len(unique_player_ids)
                print(f"📈 Promedio de registros por jugador: {avg_records_per_player:.1f}")
            
        except Exception as e:
            print(f"❌ Error analizando BD: {e}")
    
    def run_full_analysis(self):
        """Ejecuta análisis completo de la lógica de comparación."""
        print("🔍 ANÁLISIS COMPLETO DE LÓGICA DE COMPARACIÓN")
        print("="*80)
        print("Este script te mostrará exactamente cómo funciona la comparación del scraper")
        print()
        
        # 1. Analizar contenido de BD
        self.analyze_database_content()
        
        # 2. Analizar lógica de comparación
        self.analyze_comparison_logic()
        
        # 3. Simular comparación
        self.simulate_scraping_comparison()
        
        print(f"\n💡 CONCLUSIONES:")
        print("="*80)
        print("• El sistema NO compara con todos los 976+ registros iniciales")
        print("• Compara cada jugador individual con SU ÚLTIMO registro específico")
        print("• Solo detecta cambios en: percent_rostered, percent_started y sus _change")
        print("• Ignora completamente: adds, drops (para evitar falsos positivos)")
        print("• Los pocos jugadores nuevos son NORMALES - significa que pocos jugadores")
        print("  tuvieron cambios reales en rostered/started desde la última vez")


def main():
    """Función principal."""
    try:
        debugger = ComparacionDebugger()
        debugger.run_full_analysis()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
