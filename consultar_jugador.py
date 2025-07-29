#!/usr/bin/env python3
"""
Consulta Interactiva de Jugadores NFL Fantasy
Permite buscar jugadores por nombre y ver todo su historial en la base de datos
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


class PlayerConsultation:
    """Clase para consultar jugadores en la base de datos."""
    
    def __init__(self):
        """Inicializar conexión a Supabase."""
        try:
            self.url = os.getenv("SUPABASE_URL")
            self.key = os.getenv("SUPABASE_KEY")
            
            if not self.url or not self.key:
                print("❌ Variables de entorno SUPABASE_URL y SUPABASE_KEY son requeridas")
                print("💡 Asegúrate de tener un archivo .env con estas variables")
                sys.exit(1)
            
            self.supabase: Client = create_client(self.url, self.key)
            print("✅ Conexión a Supabase establecida")
            
        except Exception as e:
            print(f"❌ Error conectando a Supabase: {e}")
            sys.exit(1)
    
    def search_player_by_name(self, player_name: str) -> List[Dict[str, Any]]:
        """
        Busca jugadores por nombre (búsqueda flexible).
        
        Args:
            player_name: Nombre del jugador a buscar
            
        Returns:
            Lista de todos los registros del jugador encontrado
        """
        try:
            print(f"🔍 Buscando jugador: '{player_name}'...")
            
            # Búsqueda case-insensitive y flexible
            response = self.supabase.table('nfl_fantasy_trends').select('*').ilike(
                'player_name', f'%{player_name}%'
            ).order('scraped_at', desc=True).execute()
            
            if response.data:
                print(f"✅ Encontrados {len(response.data)} registros")
                return response.data
            else:
                print(f"❌ No se encontraron registros para '{player_name}'")
                return []
                
        except Exception as e:
            print(f"❌ Error buscando jugador: {e}")
            return []
    
    def display_player_info(self, records: List[Dict[str, Any]]):
        """Muestra la información del jugador de forma organizada."""
        if not records:
            print("📝 No hay datos para mostrar")
            return
        
        # Obtener información básica del jugador (del registro más reciente)
        latest_record = records[0]
        player_name = latest_record.get('player_name', 'N/A')
        position = latest_record.get('position', 'N/A')
        team = latest_record.get('team', 'N/A')
        player_id = latest_record.get('player_id', 'N/A')
        
        print("\n" + "="*80)
        print(f"🏈 INFORMACIÓN DEL JUGADOR")
        print("="*80)
        print(f"👤 Nombre: {player_name}")
        print(f"📍 Posición: {position}")
        print(f"🏟️  Equipo: {team}")
        print(f"🆔 ID: {player_id}")
        print(f"📊 Total de registros: {len(records)}")
        
        # Agrupar por semana
        records_by_week = {}
        for record in records:
            week = record.get('semana', 'N/A')
            if week not in records_by_week:
                records_by_week[week] = []
            records_by_week[week].append(record)
        
        print(f"📅 Semanas con datos: {sorted(records_by_week.keys()) if 'N/A' not in records_by_week else list(records_by_week.keys())}")
        
        print("\n" + "="*80)
        print(f"📈 HISTORIAL COMPLETO ({len(records)} registros)")
        print("="*80)
        
        # 🔍 DETECCIÓN DE DUPLICADOS
        duplicate_groups = []
        current_group = []
        
        for i, record in enumerate(records):
            if i == 0:
                current_group.append(record)
                continue
            
            # Comparar valores clave con el registro anterior
            prev_record = records[i-1]
            
            key_fields = ['percent_rostered', 'percent_started', 'percent_rostered_change', 'percent_started_change']
            is_duplicate = True
            
            for field in key_fields:
                if record.get(field) != prev_record.get(field):
                    is_duplicate = False
                    break
            
            if is_duplicate:
                # Es parte del mismo grupo de duplicados
                if len(current_group) == 1:
                    current_group.insert(0, prev_record)  # Agregar el anterior si es el primer duplicado
                current_group.append(record)
            else:
                # No es duplicado, cerrar grupo anterior si había
                if len(current_group) > 1:
                    duplicate_groups.append(current_group)
                current_group = [record]
        
        # Cerrar último grupo si es duplicado
        if len(current_group) > 1:
            duplicate_groups.append(current_group)
        
        # 🚨 ALERTA DE DUPLICADOS
        if duplicate_groups:
            print(f"🚨 ALERTA: Se detectaron {len(duplicate_groups)} grupos de registros duplicados:")
            for group_idx, group in enumerate(duplicate_groups, 1):
                print(f"   📋 Grupo {group_idx}: {len(group)} registros idénticos")
                first_record = group[0]
                last_record = group[-1]
                
                try:
                    first_date = datetime.fromisoformat(first_record['scraped_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
                    last_date = datetime.fromisoformat(last_record['scraped_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
                    print(f"      📅 Período: {last_date} → {first_date}")
                except:
                    print(f"      📅 Registros duplicados consecutivos")
                
                print(f"      📊 Valores idénticos: {first_record.get('percent_rostered')}% rostered, {first_record.get('percent_started')}% started")
            print()
        
        # Mostrar registros organizados
        for i, record in enumerate(records, 1):
            scraped_date = record.get('scraped_at', 'N/A')
            semana = record.get('semana', 'N/A')
            percent_rostered = record.get('percent_rostered', 'N/A')
            percent_rostered_change = record.get('percent_rostered_change', 'N/A')
            percent_started = record.get('percent_started', 'N/A')
            percent_started_change = record.get('percent_started_change', 'N/A')
            adds = record.get('adds', 'N/A')
            drops = record.get('drops', 'N/A')
            opponent = record.get('opponent', 'N/A')
            
            # Formatear fecha
            try:
                if scraped_date != 'N/A':
                    dt = datetime.fromisoformat(scraped_date.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%Y-%m-%d %H:%M')
                else:
                    formatted_date = 'N/A'
            except:
                formatted_date = scraped_date
            
            # 🔍 Marcar si es parte de un grupo duplicado
            is_in_duplicate_group = False
            for group in duplicate_groups:
                if record in group:
                    is_in_duplicate_group = True
                    break
            
            duplicate_marker = " 🔄 DUPLICADO" if is_in_duplicate_group else ""
            
            print(f"\n📋 Registro #{i}{duplicate_marker}")
            print(f"   📅 Fecha: {formatted_date}")
            print(f"   🏈 Semana NFL: {semana}")
            print(f"   🆚 Oponente: {opponent}")
            print(f"   📊 % Rostered: {percent_rostered}% (cambio: {percent_rostered_change})")
            print(f"   🎯 % Started: {percent_started}% (cambio: {percent_started_change})")
            print(f"   ➕ Adds: {adds}")
            print(f"   ➖ Drops: {drops}")
            print(f"   {'-'*60}")
        
        # 💡 RECOMENDACIÓN
        if duplicate_groups:
            total_duplicates = sum(len(group) - 1 for group in duplicate_groups)  # -1 porque uno debe quedarse
            print(f"\n💡 RECOMENDACIÓN: Considera limpiar {total_duplicates} registros duplicados")
            print(f"   Los registros duplicados no aportan información nueva y ocupan espacio innecesario")
    
    def show_player_summary(self, records: List[Dict[str, Any]]):
        """Muestra un resumen estadístico del jugador."""
        if not records:
            return
        
        print("\n" + "="*80)
        print("📊 RESUMEN ESTADÍSTICO")
        print("="*80)
        
        # Extraer valores numéricos válidos
        rostered_values = []
        started_values = []
        adds_values = []
        drops_values = []
        
        for record in records:
            if record.get('percent_rostered') is not None:
                rostered_values.append(record['percent_rostered'])
            if record.get('percent_started') is not None:
                started_values.append(record['percent_started'])
            if record.get('adds') is not None:
                adds_values.append(record['adds'])
            if record.get('drops') is not None:
                drops_values.append(record['drops'])
        
        # Calcular estadísticas
        if rostered_values:
            print(f"📈 % Rostered - Máximo: {max(rostered_values)}% | Mínimo: {min(rostered_values)}% | Promedio: {sum(rostered_values)/len(rostered_values):.1f}%")
        
        if started_values:
            print(f"🎯 % Started - Máximo: {max(started_values)}% | Mínimo: {min(started_values)}% | Promedio: {sum(started_values)/len(started_values):.1f}%")
        
        if adds_values:
            print(f"➕ Adds - Máximo: {max(adds_values)} | Mínimo: {min(adds_values)} | Total: {sum(adds_values)}")
        
        if drops_values:
            print(f"➖ Drops - Máximo: {max(drops_values)} | Mínimo: {min(drops_values)} | Total: {sum(drops_values)}")
        
        # Mostrar tendencias
        if len(rostered_values) >= 2:
            trend = "📈 Subiendo" if rostered_values[0] > rostered_values[-1] else "📉 Bajando" if rostered_values[0] < rostered_values[-1] else "➡️ Estable"
            print(f"📊 Tendencia Rostered: {trend}")
    
    def suggest_similar_players(self, search_term: str):
        """Sugiere jugadores similares si no se encuentra una coincidencia exacta."""
        try:
            print(f"\n🔍 Buscando jugadores similares a '{search_term}'...")
            
            # Buscar por palabras individuales
            words = search_term.lower().split()
            all_suggestions = []
            
            for word in words:
                if len(word) >= 3:  # Solo buscar palabras de 3+ caracteres
                    response = self.supabase.table('nfl_fantasy_trends').select(
                        'player_name'
                    ).ilike('player_name', f'%{word}%').execute()
                    
                    if response.data:
                        for record in response.data:
                            player_name = record['player_name']
                            if player_name not in all_suggestions:
                                all_suggestions.append(player_name)
            
            # Obtener jugadores únicos y limitar a 10
            unique_suggestions = list(set(all_suggestions))[:10]
            
            if unique_suggestions:
                print(f"💡 Jugadores similares encontrados:")
                for i, suggestion in enumerate(unique_suggestions, 1):
                    print(f"   {i}. {suggestion}")
                print(f"\n💭 Intenta buscar alguno de estos nombres")
            else:
                print(f"❌ No se encontraron jugadores similares")
                
        except Exception as e:
            print(f"⚠️ Error buscando sugerencias: {e}")
    
    def run_interactive_consultation(self):
        """Ejecuta la consulta interactiva principal."""
        print("\n🏈 CONSULTA DE JUGADORES NFL FANTASY")
        print("="*50)
        print("💡 Puedes buscar por nombre completo o parcial")
        print("💡 Ejemplo: 'josh allen', 'mahomes', 'justin jefferson'")
        print("💡 Escribe 'salir' o 'exit' para terminar")
        print("="*50)
        
        while True:
            try:
                # Solicitar nombre del jugador
                player_input = input("\n🔍 Ingresa el nombre del jugador: ").strip()
                
                # Verificar comando de salida
                if player_input.lower() in ['salir', 'exit', 'quit', '']:
                    print("👋 ¡Hasta luego!")
                    break
                
                # Buscar jugador
                records = self.search_player_by_name(player_input)
                
                if records:
                    # Mostrar información completa
                    self.display_player_info(records)
                    self.show_player_summary(records)
                    
                    # Preguntar si quiere ver más detalles
                    while True:
                        action = input("\n❓ ¿Qué quieres hacer? (n)ueva búsqueda / (s)alir: ").lower().strip()
                        if action in ['n', 'nueva', 'nuevo']:
                            break
                        elif action in ['s', 'salir', 'exit']:
                            print("👋 ¡Hasta luego!")
                            return
                        else:
                            print("💡 Responde 'n' para nueva búsqueda o 's' para salir")
                else:
                    # No se encontró el jugador, mostrar sugerencias
                    self.suggest_similar_players(player_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                print("🔄 Intenta de nuevo...")


def main():
    """Función principal."""
    try:
        consultation = PlayerConsultation()
        consultation.run_interactive_consultation()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
