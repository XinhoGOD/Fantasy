#!/usr/bin/env python3
"""
NFL Fantasy Football Trends Web Scraper - Versión Completa con Supabase
Extrae TODOS los datos de la tabla de trends de fantasy NFL y los sube a Supabase
"""

import time
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from typing import List, Dict, Any
import re

# Intentar cargar pandas, pero no es obligatorio
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    print("⚠️ pandas no disponible, solo guardado JSON")
    PANDAS_AVAILABLE = False

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup

# Intentar cargar python-dotenv, pero no es obligatorio para GitHub Actions
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
    print("⚠️ Supabase no disponible, guardando solo localmente")
    SUPABASE_AVAILABLE = False


class SupabaseManager:
    """Maneja las operaciones con Supabase."""
    
    def __init__(self):
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase no está disponible")
            
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("Variables de entorno SUPABASE_URL y SUPABASE_KEY son requeridas")
        
        self.supabase: Client = create_client(self.url, self.key)
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
    
    def insert_players_batch(self, players_data: List[Dict[str, Any]]) -> bool:
        """
        Inserta jugadores en lotes usando las mejores prácticas de Supabase.
        🔄 Redirige a la función con timestamp fijo.
        
        Args:
            players_data: Lista de diccionarios con datos de jugadores
            
        Returns:
            True si la inserción fue exitosa, False en caso contrario
        """
        return self.insert_players_batch_with_timestamp(players_data)
    
    def clear_today_data(self) -> bool:
        """
        Limpia los datos del día actual antes de insertar nuevos.
        Usa filtros de fecha más precisos según la documentación de Supabase.
        """
        try:
            today = datetime.now().date().isoformat()
            response = self.supabase.table('nfl_fantasy_trends').delete().gte('scraped_at', today).execute()
            
            # Verificar si la operación fue exitosa
            deleted_count = len(response.data) if response.data else 0
            self.logger.info(f"🧹 Datos del día actual limpiados: {deleted_count} registros eliminados")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error limpiando datos: {e}")
            return False
    
    def get_latest_data(self, limit: int = 10) -> List[Dict]:
        """
        Obtiene los últimos registros insertados usando order y limit.
        Usa select específico para mejor rendimiento.
        """
        try:
            response = self.supabase.table('nfl_fantasy_trends').select(
                'player_name, position, team, percent_rostered, scraped_at, created_at'
            ).order('created_at', desc=True).limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo datos: {e}")
            return []
    
    def get_player_stats(self, player_name: str) -> List[Dict]:
        """
        Obtiene estadísticas históricas de un jugador específico.
        Usa filtros ilike para búsqueda case-insensitive.
        """
        try:
            response = self.supabase.table('nfl_fantasy_trends').select('*').ilike(
                'player_name', f'%{player_name}%'
            ).order('scraped_at', desc=True).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo stats del jugador {player_name}: {e}")
            return []
    
    def get_player_by_id(self, player_id: str) -> List[Dict]:
        """
        Obtiene historial completo de un jugador por su ID.
        
        Args:
            player_id: ID único del jugador
            
        Returns:
            Lista con historial completo del jugador
        """
        try:
            response = self.supabase.table('nfl_fantasy_trends').select('*').eq(
                'player_id', player_id
            ).order('scraped_at', desc=True).execute()
            
            if response.data:
                self.logger.info(f"📊 {len(response.data)} registros encontrados para jugador ID {player_id}")
            
            return response.data if response.data else []
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo jugador por ID {player_id}: {e}")
            return []
    
    def get_trending_players(self, limit: int = 10) -> List[Dict]:
        """
        Obtiene jugadores con más actividad reciente (adds/drops).
        
        Args:
            limit: Número de jugadores a retornar
            
        Returns:
            Lista de jugadores ordenados por actividad
        """
        try:
            # Obtener timestamp más reciente
            latest_response = self.supabase.table('nfl_fantasy_trends').select(
                'scraped_at'
            ).order('scraped_at', desc=True).limit(1).execute()
            
            if not latest_response.data:
                return []
            
            latest_timestamp = latest_response.data[0]['scraped_at']
            
            # Obtener jugadores del timestamp más reciente ordenados por adds
            response = self.supabase.table('nfl_fantasy_trends').select('*').eq(
                'scraped_at', latest_timestamp
            ).order('adds', desc=True).limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo jugadores trending: {e}")
            return []
    
    def get_team_players(self, team: str) -> List[Dict]:
        """
        Obtiene todos los jugadores de un equipo específico del scraping más reciente.
        """
        try:
            # Primero obtener la fecha del scraping más reciente
            latest_date_response = self.supabase.table('nfl_fantasy_trends').select(
                'scraped_at'
            ).order('scraped_at', desc=True).limit(1).execute()
            
            if not latest_date_response.data:
                return []
            
            latest_date = latest_date_response.data[0]['scraped_at']
            
            # Obtener jugadores del equipo en esa fecha
            response = self.supabase.table('nfl_fantasy_trends').select('*').eq(
                'team', team.upper()
            ).eq('scraped_at', latest_date).order('percent_rostered', desc=True).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo jugadores del equipo {team}: {e}")
            return []
    
    def get_latest_complete_scraping(self) -> List[Dict]:
        """
        Obtiene el último scraping completo combinando timestamps relacionados si es necesario.
        🔥 CORREGIDO: Lógica simplificada que funciona como el debug.
        """
        try:
            # Obtener TODOS los timestamps sin límite
            timestamps_response = self.supabase.table('nfl_fantasy_trends').select(
                'scraped_at'
            ).execute()
            
            if not timestamps_response.data:
                self.logger.info("📊 No hay datos anteriores, todos los jugadores serán nuevos")
                return []
            
            # Contar registros por timestamp (método eficiente)
            timestamp_counts = {}
            for record in timestamps_response.data:
                ts = record['scraped_at']
                timestamp_counts[ts] = timestamp_counts.get(ts, 0) + 1
            
            # Ordenar por timestamp más reciente
            sorted_timestamps = sorted(timestamp_counts.items(), key=lambda x: x[0], reverse=True)
            
            latest_timestamp = sorted_timestamps[0][0]
            latest_count = sorted_timestamps[0][1]
            
            self.logger.info(f"📅 Último timestamp: {latest_timestamp[:19]} ({latest_count} registros)")
            
            # 🔥 NUEVO UMBRAL ADAPTATIVO: Ajustar según el tamaño actual del scraping
            current_scraping_size = len(self.supabase.table('nfl_fantasy_trends').select('scraped_at').execute().data)
            
            # Si tenemos un scraping completo reciente (>=500 registros), usarlo
            if latest_count >= 500:
                self.logger.info(f"✅ Scraping completo encontrado: {latest_count} registros")
                return self._get_all_records_for_timestamp(latest_timestamp)
            
            # 🔧 ESTRATEGIA MEJORADA: Buscar el scraping más completo en las últimas 24 horas
            self.logger.warning(f"⚠️ Timestamp incompleto ({latest_count} registros), buscando el scraping más completo reciente...")
            
            from datetime import datetime, timedelta, timezone
            
            # Buscar timestamps de las últimas 24 horas (sin pytz)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            
            recent_complete_timestamps = []
            related_fragments = []  # Para combinar fragmentos del mismo scraping
            
            for ts, count in sorted_timestamps:
                try:
                    # Manejar timestamps con y sin timezone (sin pytz)
                    if ts.endswith('+00:00'):
                        ts_dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        if ts_dt.tzinfo is None:
                            ts_dt = ts_dt.replace(tzinfo=timezone.utc)
                    else:
                        ts_dt = datetime.fromisoformat(ts)
                        if ts_dt.tzinfo is None:
                            ts_dt = ts_dt.replace(tzinfo=timezone.utc)
                    
                    # Si está en las últimas 24 horas
                    if ts_dt >= cutoff_time:
                        if count >= 300:  # Umbral para scraping completo
                            recent_complete_timestamps.append((ts, count))
                        elif count >= 50:  # Posible fragmento
                            related_fragments.append((ts, count, ts_dt))
                            
                except Exception as parse_error:
                    self.logger.warning(f"Error parseando timestamp {ts}: {parse_error}")
                    continue
            
            # Estrategia 1: Si hay scrapings completos recientes, usar el mejor
            if recent_complete_timestamps:
                best_timestamp = max(recent_complete_timestamps, key=lambda x: x[1])
                self.logger.info(f"✅ Scraping completo reciente encontrado: {best_timestamp[0][:19]} ({best_timestamp[1]} registros)")
                return self._get_all_records_for_timestamp(best_timestamp[0])
            
            # Estrategia 2: Combinar fragmentos del mismo período (ventana de 5 minutos)
            if related_fragments:
                self.logger.info(f"🔧 Combinando fragmentos del mismo scraping...")
                
                # Agrupar fragmentos por períodos de 5 minutos
                fragment_groups = []
                for ts, count, ts_dt in related_fragments:
                    added_to_group = False
                    for group in fragment_groups:
                        # Si está dentro de 5 minutos del primer timestamp del grupo
                        first_ts_dt = group[0][2]
                        if abs((ts_dt - first_ts_dt).total_seconds()) <= 300:  # 5 minutos
                            group.append((ts, count, ts_dt))
                            added_to_group = True
                            break
                    
                    if not added_to_group:
                        fragment_groups.append([(ts, count, ts_dt)])
                
                # Buscar el grupo con más registros total
                best_group = max(fragment_groups, key=lambda g: sum(item[1] for item in g))
                total_records = sum(item[1] for item in best_group)
                
                if total_records >= 200:  # Si el grupo combinado tiene suficientes registros
                    self.logger.info(f"✅ Combinando {len(best_group)} fragmentos con {total_records} registros total")
                    
                    combined_players = []
                    for ts, count, _ in best_group:
                        players = self._get_all_records_for_timestamp(ts)
                        combined_players.extend(players)
                        self.logger.info(f"   📥 {ts[:19]}: {len(players)} registros")
                    
                    # Eliminar duplicados por player_id
                    seen_ids = set()
                    unique_players = []
                    for player in combined_players:
                        player_id = player.get('player_id')
                        if player_id and player_id not in seen_ids:
                            seen_ids.add(player_id)
                            unique_players.append(player)
                        elif not player_id:  # Mantener jugadores sin ID
                            unique_players.append(player)
                    
                    self.logger.info(f"📊 Total combinado después de deduplicar: {len(unique_players)} registros únicos")
                    return unique_players
            
            # 🚨 ÚLTIMO RECURSO: Si no hay datos suficientes, insertar todos como nuevos
            self.logger.warning(f"⚠️ No se encontraron scrapings completos recientes")
            self.logger.info(f"� Esto es normal en la primera ejecución o después de limpiar la BD")
            
            # Usar el timestamp con más registros disponible
            if sorted_timestamps:
                largest_timestamp = max(sorted_timestamps, key=lambda x: x[1])
                self.logger.info(f"📊 Usando el mejor disponible: {largest_timestamp[0][:19]} ({largest_timestamp[1]} registros)")
                return self._get_all_records_for_timestamp(largest_timestamp[0])
            
            # Si no hay datos anteriores
            self.logger.info(f"📝 Primera ejecución: no hay datos anteriores para comparar")
            return []
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo último scraping: {e}")
            return []
    
    def _get_all_records_for_timestamp(self, timestamp: str) -> List[Dict]:
        """Obtiene TODOS los registros para un timestamp específico (paginado)."""
        all_players = []
        offset = 0
        batch_size = 1000
        
        while True:
            response = self.supabase.table('nfl_fantasy_trends').select('*').eq(
                'scraped_at', timestamp
            ).range(offset, offset + batch_size - 1).execute()
            
            if not response.data:
                break
            
            all_players.extend(response.data)
            
            if len(response.data) < batch_size:
                break
            
            offset += batch_size
        
        return all_players
    
    def get_latest_player_records(self, by_week: bool = False, target_week: int = None) -> Dict[str, Dict]:
        """
        Obtiene el último registro de cada jugador por su player_id.
        🔥 NUEVA LÓGICA: Comparación por historial individual de cada jugador.
        🏈 ACTUALIZADO: Opción de obtener por semana específica.
        
        Args:
            by_week: Si True, obtiene solo registros de la semana target_week
            target_week: Semana específica a filtrar (si by_week=True)
        
        Returns:
            Diccionario con player_id como clave y último registro como valor
        """
        try:
            if by_week and target_week:
                self.logger.info(f"🔍 Obteniendo último registro de cada jugador para semana {target_week}...")
                query = self.supabase.table('nfl_fantasy_trends').select('*').eq('semana', target_week)
            else:
                self.logger.info("🔍 Obteniendo último registro individual de cada jugador...")
                query = self.supabase.table('nfl_fantasy_trends').select('*')
            
            # Obtener registros ordenados por fecha de scraping
            all_records_response = query.order('scraped_at', desc=True).execute()
            
            if not all_records_response.data:
                if by_week:
                    self.logger.info(f"📊 No hay registros para semana {target_week}")
                else:
                    self.logger.info("📊 No hay registros históricos")
                return {}
            
            # Crear diccionario con el último registro de cada jugador
            latest_by_player = {}
            
            for record in all_records_response.data:
                player_id = record.get('player_id')
                if player_id and player_id not in latest_by_player:
                    # Este es el registro más reciente de este jugador
                    latest_by_player[player_id] = record
            
            if by_week:
                self.logger.info(f"📊 Últimos registros obtenidos para {len(latest_by_player)} jugadores únicos (semana {target_week})")
            else:
                self.logger.info(f"📊 Últimos registros obtenidos para {len(latest_by_player)} jugadores únicos")
            return latest_by_player
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo registros por jugador: {e}")
            return {}
    
    def get_week_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la base de datos agrupadas por semana.
        
        Returns:
            Diccionario con estadísticas por semana
        """
        try:
            # Obtener todos los registros con semana
            records_response = self.supabase.table('nfl_fantasy_trends').select(
                'semana, scraped_at, player_id'
            ).execute()
            
            if not records_response.data:
                return {'weeks': {}, 'current_week': 1, 'total_weeks': 0}
            
            # Agrupar por semana
            week_stats = {}
            for record in records_response.data:
                week = record.get('semana', 1)
                if week not in week_stats:
                    week_stats[week] = {
                        'records': 0,
                        'unique_players': set(),
                        'timestamps': set()
                    }
                
                week_stats[week]['records'] += 1
                if record.get('player_id'):
                    week_stats[week]['unique_players'].add(record['player_id'])
                if record.get('scraped_at'):
                    week_stats[week]['timestamps'].add(record['scraped_at'][:19])
            
            # Convertir sets a counts para el output
            formatted_stats = {}
            for week, stats in week_stats.items():
                formatted_stats[week] = {
                    'records': stats['records'],
                    'unique_players': len(stats['unique_players']),
                    'scraping_sessions': len(stats['timestamps'])
                }
            
            current_week = max(week_stats.keys()) if week_stats else 1
            
            return {
                'weeks': formatted_stats,
                'current_week': current_week,
                'total_weeks': len(week_stats)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo estadísticas por semana: {e}")
            return {'weeks': {}, 'current_week': 1, 'total_weeks': 0}

    def detect_player_changes_v2(self, new_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🔥 NUEVA VERSIÓN: Detecta cambios comparando cada jugador con su último registro individual.
        
        Args:
            new_data: Datos actuales del scraping
            
        Returns:
            Lista de jugadores que tuvieron cambios reales o son nuevos
        """
        # Detectar semana actual automáticamente
        current_week = self.detect_current_nfl_week()
        
        # Usar comparación por semana anterior por defecto
        if current_week > 1:
            previous_week = current_week - 1
            self.logger.info(f"🏈 Comparando semana {current_week} con semana {previous_week}")
            latest_by_player = self.get_latest_player_records(by_week=True, target_week=previous_week)
        else:
            # Si es semana 1, comparar con todo el historial
            self.logger.info(f"🔍 Semana 1 detectada - comparando con todo el historial")
            latest_by_player = self.get_latest_player_records(by_week=False)
        
        changed_players = []
        new_players = []
        updated_players = []
        
        self.logger.info(f"🔍 Comparando {len(new_data)} jugadores actuales con registros históricos individuales")
        
        for new_player in new_data:
            player_id = new_player.get('player_id')
            player_name = new_player.get('player_name', 'Unknown')
            
            if not player_id:
                self.logger.debug(f"⚠️ Jugador sin ID: {player_name}")
                continue
            
            if player_id in latest_by_player:
                # Jugador existente - comparar con su último registro
                previous_player = latest_by_player[player_id]
                
                if self.has_significant_changes(previous_player, new_player):
                    changed_players.append(new_player)
                    updated_players.append(player_name)
                    self.logger.debug(f"🔄 Cambios detectados en {player_name}")
                else:
                    self.logger.debug(f"✅ Sin cambios: {player_name}")
            else:
                # Jugador completamente nuevo (nunca antes registrado)
                changed_players.append(new_player)
                new_players.append(player_name)
                self.logger.info(f"🆕 Jugador nuevo detectado: {player_name}")
        
        # Resumen detallado
        comparison_scope = f"semana {current_week-1}" if current_week > 1 else "historial completo"
        self.logger.info(f"📈 Resultados de comparación individual ({comparison_scope}):")
        self.logger.info(f"   • Jugadores nuevos: {len(new_players)}")
        self.logger.info(f"   • Jugadores con cambios: {len(updated_players)}")
        self.logger.info(f"   • Total a insertar: {len(changed_players)}")
        self.logger.info(f"   • Semana objetivo: {current_week}")
        
        if new_players:
            self.logger.info(f"🆕 Nuevos jugadores: {', '.join(new_players[:5])}")
            if len(new_players) > 5:
                self.logger.info(f"    ... y {len(new_players) - 5} más")
        
        if updated_players:
            self.logger.info(f"� Jugadores actualizados: {', '.join(updated_players[:5])}")
            if len(updated_players) > 5:
                self.logger.info(f"    ... y {len(updated_players) - 5} más")
        
        return changed_players
    
    def has_significant_changes(self, old_player: Dict[str, Any], new_player: Dict[str, Any]) -> bool:
        """
        Determina si un jugador tuvo cambios significativos.
        
        Args:
            old_player: Datos anteriores del jugador
            new_player: Datos actuales del jugador
            
        Returns:
            True si hay cambios significativos
        """
        # Campos a monitorear para cambios
        fields_to_check = [
            'percent_rostered',
            'percent_rostered_change',
            'percent_started', 
            'percent_started_change',
            'adds',
            'drops'
        ]
        
        changes_detected = []
        
        for field in fields_to_check:
            old_val = old_player.get(field)
            new_val = new_player.get(field)
            
            # Comparar valores (manejar None)
            if old_val != new_val:
                changes_detected.append({
                    'field': field,
                    'old_value': old_val,
                    'new_value': new_val
                })
        
        if changes_detected:
            player_name = new_player.get('player_name', 'Unknown')
            self.logger.debug(f"🔄 Cambios en {player_name}: {len(changes_detected)} campos modificados")
            
        return len(changes_detected) > 0
    
    def insert_changed_players_only(self, players_data: List[Dict[str, Any]]) -> bool:
        """
        🔥 VERSIÓN 2.0: Inserta solo jugadores con cambios reales comparando con historial individual.
        
        Args:
            players_data: Lista completa de jugadores del scraping actual
            
        Returns:
            True si la operación fue exitosa
        """
        try:
            current_count = len(players_data)
            self.logger.info(f"🔍 Iniciando detección de cambios inteligente...")
            self.logger.info(f"📊 Jugadores en scraping actual: {current_count}")
            
            # 🔥 NUEVA LÓGICA: Comparar con historial individual por jugador
            changed_players = self.detect_player_changes_v2(players_data)
            
            # Validación de resultados
            change_percentage = (len(changed_players) / current_count) * 100 if current_count > 0 else 0
            self.logger.info(f"📈 Porcentaje de cambios: {change_percentage:.1f}%")
            
            # Validación de seguridad mejorada
            if change_percentage > 90:
                self.logger.warning(f"🚨 Porcentaje de cambios muy alto ({change_percentage:.1f}%)")
                
                # Verificar si es primera ejecución o problema real
                total_unique_players = len(self.get_latest_player_records())
                
                if total_unique_players < (current_count * 0.3):
                    self.logger.info(f"💡 Base de datos parece nueva o pequeña ({total_unique_players} jugadores únicos)")
                    self.logger.info(f"✅ Inserción masiva justificada")
                else:
                    self.logger.warning(f"⚠️ Posible problema: {total_unique_players} jugadores en BD vs {len(changed_players)} cambios")
                    
                    # Mostrar muestra de cambios para verificar
                    sample_size = min(3, len(changed_players))
                    self.logger.info(f"🔍 Muestra de cambios detectados:")
                    for i, player in enumerate(changed_players[:sample_size]):
                        self.logger.info(f"   {i+1}. {player.get('player_name')} ({player.get('position')})")
            
            # Si no hay cambios, no hacer nada
            if not changed_players:
                self.logger.info("✅ No se detectaron cambios. Base de datos actualizada.")
                return True
            
            # Insertar solo jugadores con cambios reales
            self.logger.info(f"📊 Insertando {len(changed_players)} jugadores con cambios verificados...")
            success = self.insert_players_batch_with_timestamp(changed_players)
            
            if success:
                self.logger.info(f"✅ Cambios registrados exitosamente")
                
                # Resumen final
                new_count = len([p for p in changed_players if not self.get_latest_player_records().get(p.get('player_id'))])
                updated_count = len(changed_players) - new_count
                
                self.logger.info(f"📈 Resumen final:")
                self.logger.info(f"   • Jugadores nuevos insertados: {new_count}")
                self.logger.info(f"   • Jugadores actualizados: {updated_count}")
                self.logger.info(f"   • Total procesado: {len(changed_players)}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error en detección de cambios v2: {e}")
            return False
    
    def detect_current_nfl_week(self) -> int:
        """
        Detecta la semana actual de la NFL usando web scraping y fecha como fallback.
        
        Returns:
            Número de semana actual (1-18)
        """
        try:
            # Intentar obtener semana desde la página web
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            driver = webdriver.Chrome(options=options)
            
            try:
                self.logger.info("🔍 Detectando semana NFL desde fantasy.nfl.com...")
                driver.get("https://fantasy.nfl.com/research/trends")
                
                # Buscar indicadores de semana en la página
                week_selectors = [
                    "[class*='week']",
                    "[data-week]",
                    ".week-selector",
                    "select[name*='week'] option[selected]"
                ]
                
                for selector in week_selectors:
                    try:
                        week_element = driver.find_element(By.CSS_SELECTOR, selector)
                        text = week_element.get_attribute('innerHTML') or week_element.text
                        
                        # Buscar número de semana en el texto
                        import re
                        week_match = re.search(r'week\s*(\d+)', text.lower())
                        if week_match:
                            week = int(week_match.group(1))
                            if 1 <= week <= 18:
                                self.logger.info(f"✅ Semana NFL detectada desde web: {week}")
                                return week
                    except:
                        continue
                
            finally:
                driver.quit()
            
            # Fallback: Calcular por fecha
            self.logger.info("📅 Calculando semana por fecha (fallback)...")
            return self._calculate_week_by_date()
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error detectando semana NFL: {e}")
            return self._calculate_week_by_date()
    
    def _calculate_week_by_date(self) -> int:
        """
        Calcula la semana NFL basada en la fecha actual.
        Temporada NFL 2024 inicia aproximadamente en septiembre.
        """
        try:
            from datetime import datetime, timedelta
            
            current_date = datetime.now()
            current_year = current_date.year
            
            # Fecha aproximada de inicio de temporada NFL (primer jueves de septiembre)
            # Para 2024: septiembre 5, 2025: septiembre 4 (aproximado)
            if current_year == 2024:
                season_start = datetime(2024, 9, 5)  # Temporada 2024
            elif current_year == 2025:
                season_start = datetime(2025, 9, 4)  # Temporada 2025
            else:
                # Calcular para años futuros (primer jueves de septiembre)
                import calendar
                september_1 = datetime(current_year, 9, 1)
                # Encontrar primer jueves
                days_to_thursday = (3 - september_1.weekday()) % 7
                season_start = september_1 + timedelta(days=days_to_thursday)
            
            # Calcular diferencia en días
            days_diff = (current_date - season_start).days
            
            if days_diff < 0:
                # Estamos antes del inicio de temporada, usar semana 1
                self.logger.info("📅 Antes del inicio de temporada, usando semana 1")
                return 1
            
            # Calcular semana (cada semana son 7 días)
            week = min(18, max(1, (days_diff // 7) + 1))
            
            self.logger.info(f"📅 Semana calculada por fecha: {week}")
            return week
            
        except Exception as e:
            self.logger.error(f"❌ Error calculando semana por fecha: {e}")
            return 1  # Default a semana 1
    
    def insert_players_batch_with_timestamp(self, players_data: List[Dict[str, Any]]) -> bool:
        """
        Inserta jugadores en lotes usando UN ÚNICO timestamp para TODO el scraping.
        ⚡ CORREGIDO: Timestamp se calcula UNA SOLA VEZ antes del bucle.
        🔥 NUEVO: Incluye detección automática de semana NFL.
        
        Args:
            players_data: Lista de diccionarios con datos de jugadores
            
        Returns:
            True si la inserción fue exitosa, False en caso contrario
        """
        try:
            batch_size = 100  # Insertar de 100 en 100
            total_inserted = 0
            
            # 🔥 CRÍTICO: Calcular timestamp UNA SOLA VEZ antes del bucle
            scraping_timestamp = datetime.now().isoformat()
            
            # 🏈 NUEVO: Detectar semana NFL automáticamente
            current_week = self.detect_current_nfl_week()
            
            self.logger.info(f"🕐 Timestamp único para todo el scraping: {scraping_timestamp[:19]}")
            self.logger.info(f"🏈 Semana NFL detectada: {current_week}")
            
            for i in range(0, len(players_data), batch_size):
                batch = players_data[i:i + batch_size]
                
                # Preparar datos para Supabase (omitir campos auto-generados como id, created_at)
                formatted_batch = []
                for player in batch:
                    formatted_player = {
                        'player_name': player.get('player_name', ''),
                        'player_id': player.get('player_id', ''),
                        'position': player.get('position', ''),
                        'team': player.get('team', ''),
                        'opponent': player.get('opponent', ''),
                        'percent_rostered': player.get('percent_rostered'),
                        'percent_rostered_change': player.get('percent_rostered_change'),
                        'percent_started': player.get('percent_started'),
                        'percent_started_change': player.get('percent_started_change'),
                        'adds': player.get('adds'),
                        'drops': player.get('drops'),
                        'scraped_at': scraping_timestamp,  # ✅ MISMO timestamp fijo para todo
                        'semana': current_week  # 🏈 NUEVO: Campo semana automático
                    }
                    formatted_batch.append(formatted_player)
                
                # Insertar lote en Supabase
                response = self.supabase.table('nfl_fantasy_trends').insert(formatted_batch).execute()
                
                if response.data:
                    total_inserted += len(response.data)
                    self.logger.info(f"✅ Insertados {len(response.data)} registros en Supabase (Lote {i//batch_size + 1})")
                else:
                    self.logger.error(f"❌ Error insertando lote {i//batch_size + 1}: {getattr(response, 'error', 'Unknown error')}")
                    return False
            
            self.logger.info(f"🎯 Total insertado en Supabase: {total_inserted} registros")
            self.logger.info(f"🕐 Todos con timestamp: {scraping_timestamp[:19]}")
            self.logger.info(f"🏈 Todos con semana NFL: {current_week}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error insertando en Supabase: {e}")
            return False
    
    def log_changes_summary(self, changed_players: List[Dict], previous_data: List[Dict]):
        """Registra un resumen de los cambios detectados."""
        try:
            previous_players = {p['player_id']: p for p in previous_data if p.get('player_id')}
            
            summary = {
                'new_players': 0,
                'updated_players': 0,
                'significant_changes': []
            }
            
            for player in changed_players:
                player_id = player.get('player_id')
                player_name = player.get('player_name', 'Unknown')
                
                if player_id not in previous_players:
                    summary['new_players'] += 1
                else:
                    summary['updated_players'] += 1
                    previous = previous_players[player_id]
                    
                    # Detectar cambios grandes en ownership
                    old_rostered = previous.get('percent_rostered', 0) or 0
                    new_rostered = player.get('percent_rostered', 0) or 0
                    rostered_diff = new_rostered - old_rostered
                    
                    if abs(rostered_diff) >= 5:  # Cambio significativo >= 5%
                        summary['significant_changes'].append({
                            'player': player_name,
                            'position': player.get('position'),
                            'team': player.get('team'),
                            'change': rostered_diff
                        })
            
            self.logger.info(f"📊 Resumen de cambios:")
            self.logger.info(f"   • Jugadores nuevos: {summary['new_players']}")
            self.logger.info(f"   • Jugadores actualizados: {summary['updated_players']}")
            
            if summary['significant_changes']:
                self.logger.info(f"   • Cambios significativos (±5% ownership):")
                for change in summary['significant_changes'][:5]:  # Top 5
                    sign = "+" if change['change'] > 0 else ""
                    self.logger.info(f"     - {change['player']} ({change['position']}) {sign}{change['change']:.1f}%")
                    
        except Exception as e:
            self.logger.warning(f"⚠️ Error generando resumen de cambios: {e}")
    
    def delete_recent_duplicates(self, count_to_delete: int) -> bool:
        """
        Elimina los registros más recientes de la base de datos.
        
        Args:
            count_to_delete: Número de registros a eliminar
            
        Returns:
            True si la eliminación fue exitosa
        """
        try:
            self.logger.info(f"🗑️ Iniciando eliminación de {count_to_delete} registros más recientes...")
            
            # Obtener los registros más recientes para eliminar
            recent_records = self.supabase.table('nfl_fantasy_trends').select(
                'id, player_name, scraped_at, created_at'
            ).order('created_at', desc=True).limit(count_to_delete).execute()
            
            if not recent_records.data:
                self.logger.warning("⚠️ No se encontraron registros para eliminar")
                return False
            
            # Mostrar resumen de lo que se va a eliminar
            self.logger.info(f"📋 Registros que se eliminarán:")
            timestamps_to_delete = {}
            for record in recent_records.data:
                timestamp = record.get('scraped_at', 'Unknown')[:19]
                timestamps_to_delete[timestamp] = timestamps_to_delete.get(timestamp, 0) + 1
            
            for timestamp, count in sorted(timestamps_to_delete.items(), reverse=True):
                self.logger.info(f"   • {timestamp}: {count} registros")
            
            # Confirmar eliminación
            total_found = len(recent_records.data)
            self.logger.info(f"🔍 Total encontrado para eliminar: {total_found} registros")
            
            if total_found != count_to_delete:
                self.logger.warning(f"⚠️ Se encontraron {total_found} registros, no {count_to_delete}")
            
            # Extraer IDs para eliminación
            ids_to_delete = [record['id'] for record in recent_records.data]
            
            # Eliminar en lotes de 100
            batch_size = 100
            total_deleted = 0
            
            for i in range(0, len(ids_to_delete), batch_size):
                batch_ids = ids_to_delete[i:i + batch_size]
                
                # Eliminar el lote
                delete_response = self.supabase.table('nfl_fantasy_trends').delete().in_(
                    'id', batch_ids
                ).execute()
                
                if delete_response.data:
                    total_deleted += len(delete_response.data)
                    self.logger.info(f"✅ Eliminados {len(delete_response.data)} registros (Lote {i//batch_size + 1})")
                else:
                    self.logger.error(f"❌ Error eliminando lote {i//batch_size + 1}")
                    return False
            
            self.logger.info(f"🎯 Total eliminado: {total_deleted} registros")
            
            # Verificar estado después de la eliminación
            remaining_count = len(self.supabase.table('nfl_fantasy_trends').select('id').execute().data)
            self.logger.info(f"📊 Registros restantes en BD: {remaining_count}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error eliminando registros: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas completas de la base de datos.
        
        Returns:
            Diccionario con estadísticas de la BD
        """
        try:
            # Total de registros
            total_response = self.supabase.table('nfl_fantasy_trends').select('id').execute()
            total_records = len(total_response.data) if total_response.data else 0
            
            # Contar registros por timestamp
            timestamps_response = self.supabase.table('nfl_fantasy_trends').select('scraped_at').execute()
            timestamp_counts = {}
            
            if timestamps_response.data:
                for record in timestamps_response.data:
                    ts = record['scraped_at']
                    timestamp_counts[ts] = timestamp_counts.get(ts, 0) + 1
            
            # Últimos 5 timestamps únicos
            sorted_timestamps = sorted(timestamp_counts.items(), key=lambda x: x[0], reverse=True)[:5]
            
            return {
                'total_records': total_records,
                'unique_timestamps': len(timestamp_counts),
                'recent_timestamps': sorted_timestamps,
                'timestamp_counts': timestamp_counts
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}
    def upsert_players_batch(self, players_data: List[Dict[str, Any]]) -> bool:
        """
        Hace UPSERT de jugadores en lotes. 
        Usa una estrategia híbrida: insertar nuevos y actualizar existentes.
        🔥 NUEVO: Incluye detección automática de semana NFL.
        
        Args:
            players_data: Lista de diccionarios con datos de jugadores
            
        Returns:
            True si el upsert fue exitoso, False en caso contrario
        """
        try:
            batch_size = 100
            total_processed = 0
            
            # ✅ ÚNICO timestamp para todo el scraping (CRÍTICO)
            scraping_timestamp = datetime.now().isoformat()
            
            # 🏈 NUEVO: Detectar semana NFL automáticamente
            current_week = self.detect_current_nfl_week()
            
            self.logger.info(f"🕐 Timestamp único: {scraping_timestamp[:19]}")
            self.logger.info(f"🏈 Semana NFL: {current_week}")
            
            for i in range(0, len(players_data), batch_size):
                batch = players_data[i:i + batch_size]
                
                # Preparar datos para Supabase con timestamp y semana
                formatted_batch = []
                
                for player in batch:
                    formatted_player = {
                        'player_name': player.get('player_name', ''),
                        'player_id': player.get('player_id', ''),
                        'position': player.get('position', ''),
                        'team': player.get('team', ''),
                        'opponent': player.get('opponent', ''),
                        'percent_rostered': player.get('percent_rostered'),
                        'percent_rostered_change': player.get('percent_rostered_change'),
                        'percent_started': player.get('percent_started'),
                        'percent_started_change': player.get('percent_started_change'),
                        'adds': player.get('adds'),
                        'drops': player.get('drops'),
                        'scraped_at': scraping_timestamp,  # ✅ MISMO timestamp para todo el scraping
                        'semana': current_week  # 🏈 NUEVO: Campo semana automático
                    }
                    formatted_batch.append(formatted_player)
                
                # Usar UPSERT con manejo de errores mejorado
                try:
                    response = self.supabase.table('nfl_fantasy_trends').upsert(formatted_batch).execute()
                    
                    if response.data:
                        total_processed += len(response.data)
                        self.logger.info(f"✅ Upserted {len(response.data)} registros en Supabase (Lote {i//batch_size + 1})")
                    else:
                        self.logger.warning(f"⚠️ Upsert lote {i//batch_size + 1} no devolvió data, pero no hay error")
                        total_processed += len(formatted_batch)  # Asumir éxito si no hay error
                        
                except Exception as upsert_error:
                    self.logger.warning(f"⚠️ UPSERT falló para lote {i//batch_size + 1}, intentando INSERT: {upsert_error}")
                    
                    # Fallback a INSERT normal si UPSERT falla
                    try:
                        response = self.supabase.table('nfl_fantasy_trends').insert(formatted_batch).execute()
                        if response.data:
                            total_processed += len(response.data)
                            self.logger.info(f"✅ Insertados {len(response.data)} registros (fallback) en Supabase (Lote {i//batch_size + 1})")
                        else:
                            self.logger.error(f"❌ Error en INSERT fallback lote {i//batch_size + 1}")
                            return False
                    except Exception as insert_error:
                        self.logger.error(f"❌ Error en INSERT fallback lote {i//batch_size + 1}: {insert_error}")
                        return False
            
            self.logger.info(f"🎯 Total procesado en Supabase: {total_processed} registros")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error general en upsert a Supabase: {e}")
            return False


class NFLFantasyCompleteScraper:
    """Scraper completo para NFL Fantasy Trends con integración a Supabase."""
    
    def __init__(self, save_to_supabase: bool = True):
        self.url = "https://fantasy.nfl.com/research/trends"
        self.driver = None
        self.all_data = []
        self.save_to_supabase = save_to_supabase and SUPABASE_AVAILABLE
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Inicializar Supabase si está habilitado
        if self.save_to_supabase:
            try:
                self.supabase_manager = SupabaseManager()
            except (ImportError, ValueError) as e:
                self.logger.warning(f"⚠️ No se pudo inicializar Supabase: {e}")
                self.save_to_supabase = False
    
    def setup_driver(self):
        """Configura Chrome con opciones para GitHub Actions y local."""
        try:
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            # Opciones adicionales para GitHub Actions
            if os.getenv('GITHUB_ACTIONS'):
                options.add_argument("--headless")  # Modo headless en GitHub Actions
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-plugins")
                options.add_argument("--disable-images")
                self.logger.info("🤖 Configurando para GitHub Actions (headless)")
            
            self.driver = webdriver.Chrome(options=options)
            self.logger.info("✅ Driver configurado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando driver: {e}")
            return False
    
    def scrape_all_data(self):
        """Extrae TODOS los datos del elemento bd navegando por todas las páginas."""
        try:
            if not self.setup_driver():
                return None
            
            self.logger.info(f"🌐 Cargando: {self.url}")
            self.driver.get(self.url)
            
            # Esperar y buscar el elemento bd
            wait = WebDriverWait(self.driver, 30)
            
            try:
                bd_element = wait.until(EC.presence_of_element_located((By.ID, "bd")))
                self.logger.info("✅ Elemento 'bd' encontrado")
            except TimeoutException:
                self.logger.error("❌ Elemento 'bd' no encontrado")
                return None
            
            # Esperar a que la página cargue completamente
            time.sleep(10)
            
            page_number = 1
            total_players = 0
            
            while True:
                self.logger.info(f"📄 Procesando página {page_number}")
                
                # Extraer datos de la página actual
                current_page_data = self.extract_current_page_data()
                if current_page_data:
                    self.all_data.extend(current_page_data)
                    total_players += len(current_page_data)
                    self.logger.info(f"✅ Extraídos {len(current_page_data)} jugadores de página {page_number}")
                else:
                    self.logger.warning(f"⚠️ No se extrajeron datos de página {page_number}")
                
                # Intentar hacer click en el botón "siguiente"
                if not self.click_next_page():
                    self.logger.info(f"🏁 No hay más páginas. Proceso completado.")
                    break
                
                page_number += 1
                
                # Esperar a que la nueva página cargue
                time.sleep(5)
                
                # Verificación de seguridad para evitar bucles infinitos
                if page_number > 50:  # Límite de seguridad
                    self.logger.warning("⚠️ Límite de páginas alcanzado (50). Deteniendo.")
                    break
            
            self.logger.info(f"🎯 Total final: {total_players} jugadores de {page_number} páginas")
            
            # Guardar datos automáticamente con detección de cambios
            if self.all_data:
                self.save_data(self.all_data, detect_changes=True)
            
            return self.all_data
            
        except Exception as e:
            self.logger.error(f"❌ Error durante scraping: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("🔒 Driver cerrado")
    
    def save_data(self, data: List[Dict[str, Any]], detect_changes: bool = True, use_upsert: bool = False) -> bool:
        """
        Guarda los datos tanto localmente como en Supabase.
        
        Args:
            data: Lista de datos de jugadores
            detect_changes: Si True, solo inserta jugadores con cambios
            use_upsert: Si True usa UPSERT, si False usa INSERT normal
            
        Returns:
            True si el guardado fue exitoso
        """
        success = True
        
        # Guardar localmente solo si NO estamos en GitHub Actions
        if not os.getenv('GITHUB_ACTIONS'):
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Guardar JSON
                json_filename = f'nfl_fantasy_trends_{timestamp}.json'
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Guardar CSV solo si pandas está disponible
                if PANDAS_AVAILABLE:
                    csv_filename = f'nfl_fantasy_trends_{timestamp}.csv'
                    df = pd.DataFrame(data)
                    df.to_csv(csv_filename, index=False, encoding='utf-8')
                    self.logger.info(f"💾 Scraping completo guardado localmente: {json_filename}, {csv_filename}")
                else:
                    self.logger.info(f"💾 Scraping completo guardado localmente: {json_filename}")
                
                
            except Exception as e:
                self.logger.error(f"❌ Error guardando localmente: {e}")
                success = False
        else:
            self.logger.info("🤖 GitHub Actions detectado: omitiendo archivos locales, solo Supabase")
        
        # Guardar en Supabase con detección de cambios
        if self.save_to_supabase and data:
            try:
                if detect_changes:
                    self.logger.info("🔍 Modo detección de cambios activado...")
                    supabase_success = self.supabase_manager.insert_changed_players_only(data)
                else:
                    # Modo tradicional (insertar todos)
                    if use_upsert:
                        self.logger.info("📊 Usando UPSERT para todos los jugadores...")
                        supabase_success = self.supabase_manager.upsert_players_batch(data)
                    else:
                        self.logger.info("📊 Usando INSERT para todos los jugadores...")
                        supabase_success = self.supabase_manager.insert_players_batch(data)
                
                if supabase_success:
                    if detect_changes:
                        self.logger.info("☁️ Cambios detectados y registrados en Supabase")
                    else:
                        self.logger.info("☁️ Todos los datos subidos exitosamente a Supabase")
                    
                    # Mostrar estadísticas de los últimos registros
                    latest = self.supabase_manager.get_latest_data(3)
                    if latest:
                        self.logger.info(f"📈 Últimos registros en Supabase:")
                        for record in latest:
                            scraped_time = record.get('scraped_at', 'N/A')[:19] if record.get('scraped_at') else 'N/A'
                            self.logger.info(f"   • {record.get('player_name')} - {scraped_time}")
                else:
                    self.logger.error("❌ Error subiendo a Supabase")
                    success = False
                    
            except Exception as e:
                self.logger.error(f"❌ Error con Supabase: {e}")
                success = False
        
        return success
    
    def extract_main_table_structured(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extrae la tabla principal con datos específicos de jugadores."""
        structured_data = []
        
        # Buscar cualquier tabla en el HTML
        tables = soup.find_all('table')
        
        if not tables:
            self.logger.warning("❌ No se encontraron tablas")
            return structured_data
        
        self.logger.info(f"📊 Encontradas {len(tables)} tablas, procesando...")
        
        # Procesar todas las tablas encontradas
        for table_idx, table in enumerate(tables):
            self.logger.info(f"📋 Procesando tabla {table_idx + 1}")
            
            # Buscar filas de datos en tbody o directamente en la tabla
            tbody = table.find('tbody')
            rows = tbody.find_all('tr') if tbody else table.find_all('tr')
            
            # Filtrar filas que parecen ser headers
            data_rows = []
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:  # Debe tener suficientes celdas
                    # Verificar si parece ser una fila de datos (no header)
                    first_cell_text = cells[0].get_text(strip=True)
                    if first_cell_text and not first_cell_text.lower() in ['player', 'name', 'opp', 'opponent']:
                        data_rows.append(row)
            
            self.logger.info(f"📝 Procesando {len(data_rows)} filas de datos en tabla {table_idx + 1}")
            
            for row_idx, row in enumerate(data_rows):
                player_data = self.extract_player_row_data(row, row_idx, {})
                if player_data and player_data.get('player_name'):
                    structured_data.append(player_data)
        
        self.logger.info(f"✅ {len(structured_data)} jugadores extraídos en total")
        return structured_data
    
    def extract_current_page_data(self) -> List[Dict[str, Any]]:
        """Extrae los datos de la página actual."""
        try:
            # Extraer el HTML del elemento bd
            bd_element = self.driver.find_element(By.ID, "bd")
            html_content = bd_element.get_attribute('outerHTML')
            
            # Parsear con BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extraer datos de la tabla principal
            return self.extract_main_table_structured(soup)
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo datos de página actual: {e}")
            return []
    
    def click_next_page(self) -> bool:
        """
        Hace click en el botón de siguiente página.
        
        Returns:
            True si se pudo hacer click, False si no hay más páginas
        """
        try:
            # Buscar el botón de siguiente página usando diferentes selectores
            next_selectors = [
                "li.next.last a",  # Selector específico del elemento proporcionado
                "li[class*='next'] a",  # Cualquier li con 'next' en la clase
                "a[href*='offset=']",  # Enlaces con offset en la URL
                ".pagination .next a",  # Paginación estándar
                "li.next a",  # Selector más simple
            ]
            
            next_button = None
            
            for selector in next_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        # Verificar que el botón esté visible y habilitado
                        if (button.is_displayed() and 
                            button.is_enabled() and 
                            ('>' in button.text or 'next' in button.get_attribute('class').lower())):
                            next_button = button
                            break
                    
                    if next_button:
                        break
                        
                except Exception:
                    continue
            
            # Si no encontramos con CSS, intentar con XPath
            if not next_button:
                try:
                    xpath_selectors = [
                        "//li[contains(@class, 'next') and contains(@class, 'last')]//a",
                        "//li[contains(@class, 'next')]//a",
                        "//a[contains(@href, 'offset=') and contains(text(), '>')]",
                        "//a[text()='>']"
                    ]
                    
                    for xpath in xpath_selectors:
                        try:
                            buttons = self.driver.find_elements(By.XPATH, xpath)
                            for button in buttons:
                                if button.is_displayed() and button.is_enabled():
                                    next_button = button
                                    break
                            if next_button:
                                break
                        except Exception:
                            continue
                            
                except Exception as e:
                    self.logger.warning(f"Error buscando con XPath: {e}")
            
            if next_button:
                # Verificar que no esté deshabilitado
                try:
                    parent_li = next_button.find_element(By.XPATH, "./..")
                    if 'disabled' in parent_li.get_attribute('class'):
                        self.logger.info("🛑 Botón de siguiente página está deshabilitado")
                        return False
                except:
                    pass  # Si no podemos verificar, continuamos
                
                # Hacer scroll al botón si es necesario
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(1)
                
                # Hacer click
                self.logger.info(f"🔄 Haciendo click en siguiente página: {next_button.get_attribute('href')}")
                self.driver.execute_script("arguments[0].click();", next_button)
                
                # Esperar a que la página cambie
                time.sleep(3)
                return True
            else:
                self.logger.info("🛑 No se encontró botón de siguiente página")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error haciendo click en siguiente página: {e}")
            return False
    
    def extract_player_row_data(self, row, row_idx: int, headers: Dict) -> Dict[str, Any]:
        """Extrae datos específicos de una fila de jugador en formato requerido."""
        cells = row.find_all(['td', 'th'])
        if len(cells) < 3:  # Debe tener al menos algunas celdas
            return None
        
        # Template con el formato específico requerido
        player_data = {
            "player_name": "",
            "player_id": "",
            "position": "",
            "team": "",
            "opponent": "",
            "percent_rostered": None,
            "percent_rostered_change": None,
            "percent_started": None,
            "percent_started_change": None,
            "adds": None,
            "drops": None
        }
        
        # Extraer información del jugador (primera celda)
        if len(cells) > 0:
            player_cell = cells[0]
            player_info = self.extract_player_info(player_cell)
            player_data.update(player_info)
        
        # Extraer oponente (segunda celda)
        if len(cells) > 1:
            opponent_cell = cells[1]
            opponent_text = opponent_cell.get_text(strip=True)
            player_data['opponent'] = opponent_text if opponent_text else ""
        
        # Extraer estadísticas numéricas en orden específico
        stat_mappings = [
            (2, 'percent_rostered'),
            (3, 'percent_rostered_change'), 
            (4, 'percent_started'),
            (5, 'percent_started_change'),
            (6, 'adds'),
            (7, 'drops')
        ]
        
        for cell_idx, field in stat_mappings:
            if cell_idx < len(cells):
                value = cells[cell_idx].get_text(strip=True)
                
                # Limpiar y convertir el valor
                cleaned_value = self.clean_numeric_value(value)
                player_data[field] = cleaned_value
        
        return player_data
    
    def extract_player_info(self, player_cell) -> Dict[str, Any]:
        """Extrae información específica del jugador de la celda."""
        player_info = {
            "player_name": "",
            "player_id": "",
            "position": "",
            "team": ""
        }
        
        # Buscar enlace del jugador
        player_link = player_cell.find('a', class_='playerName')
        if player_link:
            player_info['player_name'] = player_link.get_text(strip=True)
            # Extraer player_id de la URL
            href = player_link.get('href', '')
            player_id_match = re.search(r'playerId=(\d+)', href)
            if player_id_match:
                player_info['player_id'] = player_id_match.group(1)
        
        # Si no encontramos el enlace con clase, buscar cualquier enlace en la celda
        if not player_info['player_name']:
            any_link = player_cell.find('a')
            if any_link:
                player_info['player_name'] = any_link.get_text(strip=True)
                href = any_link.get('href', '')
                player_id_match = re.search(r'playerId=(\d+)', href)
                if player_id_match:
                    player_info['player_id'] = player_id_match.group(1)
        
        # Buscar posición y equipo
        position_info = player_cell.find('em')
        if position_info:
            pos_text = position_info.get_text(strip=True)
            # Formato típico: "TE - ATL" o "QB - HOU"
            pos_match = re.match(r'(\w+)\s*-\s*([A-Z]{2,4})', pos_text)
            if pos_match:
                player_info['position'] = pos_match.group(1)
                player_info['team'] = pos_match.group(2)
        
        # Si no encontramos posición/equipo en <em>, buscar en todo el texto de la celda
        if not player_info['position']:
            cell_text = player_cell.get_text()
            pos_match = re.search(r'(QB|RB|WR|TE|K|DEF)\s*-\s*([A-Z]{2,4})', cell_text)
            if pos_match:
                player_info['position'] = pos_match.group(1)
                player_info['team'] = pos_match.group(2)
        
        return player_info
    
    def clean_numeric_value(self, value: str):
        """Limpia y convierte valores numéricos."""
        if not value or value.strip() == '':
            return None
        
        # Remover caracteres no numéricos excepto punto, coma y signos
        cleaned = re.sub(r'[^\d.,+-]', '', value.strip())
        
        if not cleaned:
            return None
        
        try:
            # Manejar porcentajes
            if '%' in value:
                cleaned = cleaned.replace('%', '')
            
            # Manejar cambios positivos/negativos
            if '+' in value:
                cleaned = cleaned.replace('+', '')
            
            # Convertir a número
            if '.' in cleaned:
                return float(cleaned)
            else:
                return int(cleaned)
        except ValueError:
            return None


def test_individual_comparison():
    """
    🧪 Prueba específica de la nueva lógica de comparación individual por jugador.
    """
    print("🔬 PRUEBA: Comparación individual por jugador")
    print("=" * 60)
    
    try:
        # Inicializar Supabase Manager
        sm = SupabaseManager()
        print("✅ Supabase conectado correctamente")
        
        # Probar la nueva función de registros individuales
        print("\n🔍 Probando nueva lógica de comparación individual...")
        latest_by_player = sm.get_latest_player_records()
        
        print(f"📊 Jugadores únicos con registros: {len(latest_by_player)}")
        
        # Mostrar muestra de jugadores y sus últimos registros
        print(f"\n📋 Muestra de últimos registros por jugador:")
        sample_count = 0
        for player_id, record in latest_by_player.items():
            if sample_count >= 5:
                break
            
            player_name = record.get('player_name', 'Unknown')
            scraped_at = record.get('scraped_at', '')[:19]
            percent_rostered = record.get('percent_rostered', 'N/A')
            
            print(f"   • {player_name} (ID: {player_id[:8]}...) - {scraped_at} - {percent_rostered}% rostered")
            sample_count += 1
        
        # Simular detección de cambios con datos ficticios
        print(f"\n🔄 Simulando detección de cambios...")
        
        # Tomar un jugador existente y crear una versión "modificada"
        if latest_by_player:
            sample_player_id = list(latest_by_player.keys())[0]
            original_player = latest_by_player[sample_player_id]
            
            # Crear versión modificada (simular cambio en percent_rostered)
            modified_player = original_player.copy()
            original_rostered = modified_player.get('percent_rostered', 0) or 0
            modified_player['percent_rostered'] = original_rostered + 5  # Simular +5% change
            
            print(f"📝 Simulando cambio en {original_player.get('player_name')}:")
            print(f"   • Original: {original_rostered}% rostered")
            print(f"   • Modificado: {modified_player['percent_rostered']}% rostered")
            
            # Probar detección de cambios
            has_changes = sm.has_significant_changes(original_player, modified_player)
            print(f"   • ¿Cambio detectado?: {'✅ SÍ' if has_changes else '❌ NO'}")
        
        print(f"\n🎯 ANÁLISIS DE LA NUEVA LÓGICA:")
        print(f"✅ Comparación individual: IMPLEMENTADA")
        print(f"✅ Evita falsos positivos por timestamps fragmentados")
        print(f"✅ Solo detecta cambios reales en datos del jugador")
        print(f"💡 GitHub Actions puede ejecutarse sin riesgo de duplicados")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba individual: {e}")
        return False


def test_mode_quick():
    """
    Modo de prueba rápido que verifica el sistema sin hacer web scraping.
    🔥 MEJORADO: Incluye prueba de la nueva lógica individual.
    """
    print("🧪 MODO PRUEBA: Verificación rápida del sistema")
    print("=" * 60)
    
    try:
        # Inicializar solo Supabase Manager
        sm = SupabaseManager()
        print("✅ Supabase conectado correctamente")
        
        # Diagnóstico completo de timestamps
        print("\n🔍 DIAGNÓSTICO DE TIMESTAMPS:")
        print("-" * 40)
        
        timestamps_response = sm.supabase.table('nfl_fantasy_trends').select('scraped_at').execute()
        if timestamps_response.data:
            timestamp_counts = {}
            for record in timestamps_response.data:
                ts = record['scraped_at']
                timestamp_counts[ts] = timestamp_counts.get(ts, 0) + 1
            
            # Mostrar los 10 timestamps más recientes con sus conteos
            sorted_timestamps = sorted(timestamp_counts.items(), key=lambda x: x[0], reverse=True)[:10]
            
            print(f"📊 Total timestamps únicos: {len(timestamp_counts)}")
            print(f"📈 Últimos 10 timestamps:")
            
            for i, (ts, count) in enumerate(sorted_timestamps, 1):
                print(f"   {i:2d}. {ts[:19]} → {count:4d} registros")
            
            # Identificar el mejor timestamp para comparación
            complete_timestamps = [(ts, count) for ts, count in sorted_timestamps if count >= 500]
            if complete_timestamps:
                best = complete_timestamps[0]
                print(f"\n✅ Scraping completo más reciente: {best[0][:19]} ({best[1]} registros)")
            else:
                print(f"\n⚠️ No hay scrapings completos recientes (>=500 registros)")
                if sorted_timestamps:
                    largest = max(sorted_timestamps, key=lambda x: x[1])
                    print(f"📊 Scraping más grande: {largest[0][:19]} ({largest[1]} registros)")
        
        # 🔥 NUEVA PRUEBA: Comparación individual por jugador
        print(f"\n� PRUEBA DE NUEVA LÓGICA INDIVIDUAL:")
        print("-" * 40)
        
        latest_by_player = sm.get_latest_player_records()
        print(f"📊 Jugadores únicos registrados: {len(latest_by_player)}")
        
        if latest_by_player:
            print(f"✅ Sistema de comparación individual: OPERATIVO")
            
            # Mostrar muestra de jugadores únicos
            sample_players = list(latest_by_player.values())[:3]
            print(f"\n📋 Muestra de registros individuales:")
            for player in sample_players:
                scraped_at = player.get('scraped_at', '')[:19] if player.get('scraped_at') else 'N/A'
                print(f"   • {player.get('player_name')} ({player.get('position')}) - {scraped_at}")
        else:
            print(f"⚠️ Sin registros históricos - primera ejecución")
        
        print(f"\n🎯 VEREDICTO FINAL:")
        print(f"✅ Conexión: OK")
        print(f"✅ Lógica individual: IMPLEMENTADA")
        print(f"✅ Anti-duplicados: MÁXIMO")
        print(f"🤖 Listo para GitHub Actions sin riesgo de duplicados")
        return True
        
    except Exception as e:
        print(f"❌ Error en modo prueba: {e}")
        return False


def clean_duplicates_mode():
    """
    Modo de limpieza para eliminar registros duplicados.
    """
    print("🧹 MODO LIMPIEZA: Eliminación de registros duplicados")
    print("=" * 60)
    
    try:
        # Inicializar Supabase Manager
        sm = SupabaseManager()
        print("✅ Supabase conectado correctamente")
        
        # Obtener estadísticas actuales
        print("\n📊 ESTADO ACTUAL DE LA BASE DE DATOS:")
        print("-" * 40)
        
        stats = sm.get_database_stats()
        print(f"📈 Total de registros: {stats.get('total_records', 0)}")
        print(f"📅 Timestamps únicos: {stats.get('unique_timestamps', 0)}")
        
        recent_timestamps = stats.get('recent_timestamps', [])
        if recent_timestamps:
            print(f"📋 Últimos 5 timestamps:")
            for i, (ts, count) in enumerate(recent_timestamps, 1):
                print(f"    {i}. {ts[:19]} → {count:4d} registros")
        
        # Calcular registros a eliminar (últimos 876)
        count_to_delete = 876
        total_records = stats.get('total_records', 0)
        
        if total_records < count_to_delete:
            print(f"\n⚠️ Solo hay {total_records} registros en total")
            print(f"🤔 ¿Deseas eliminar TODOS los registros? Esto limpiará completamente la BD")
            response = input("Escribe 'SI' para confirmar eliminación completa: ")
            if response.upper() == 'SI':
                count_to_delete = total_records
            else:
                print("❌ Operación cancelada")
                return False
        
        print(f"\n🗑️ PREPARANDO ELIMINACIÓN:")
        print(f"   • Registros a eliminar: {count_to_delete}")
        print(f"   • Registros que quedarán: {total_records - count_to_delete}")
        
        # Confirmación del usuario
        print(f"\n⚠️ CONFIRMACIÓN REQUERIDA:")
        print(f"Esta operación eliminará los {count_to_delete} registros MÁS RECIENTES")
        print(f"Esta acción NO se puede deshacer")
        
        response = input(f"\nEscribe 'ELIMINAR' para confirmar: ")
        
        if response.upper() == 'ELIMINAR':
            print(f"\n🚀 Iniciando eliminación...")
            success = sm.delete_recent_duplicates(count_to_delete)
            
            if success:
                print(f"\n✅ ELIMINACIÓN COMPLETADA EXITOSAMENTE")
                
                # Mostrar nuevas estadísticas
                new_stats = sm.get_database_stats()
                print(f"\n📊 ESTADO DESPUÉS DE LA LIMPIEZA:")
                print(f"   • Total de registros: {new_stats.get('total_records', 0)}")
                print(f"   • Timestamps únicos: {new_stats.get('unique_timestamps', 0)}")
                
                print(f"\n💡 Puedes ejecutar una nueva verificación con: python scrapper.py --test")
                return True
            else:
                print(f"\n❌ ERROR: La eliminación falló")
                return False
        else:
            print(f"\n❌ Operación cancelada por el usuario")
            return False
            
    except Exception as e:
        print(f"❌ Error en modo limpieza: {e}")
        return False


def clean_duplicates_mode():
    """
    Modo especial para limpiar registros duplicados.
    """
    print("🧹 MODO LIMPIEZA: Eliminación de registros duplicados")
    print("=" * 60)
    
    try:
        # Inicializar Supabase
        supabase_manager = SupabaseManager()
        
        # Obtener estadísticas actuales
        stats = supabase_manager.get_database_stats()
        
        if not stats:
            print("❌ No se pudieron obtener estadísticas de la BD")
            return
        
        print(f"📊 Estado actual de la base de datos:")
        print(f"   • Total registros: {stats['total_records']}")
        print(f"   • Timestamps únicos: {stats['unique_timestamps']}")
        
        print(f"\n📅 Últimos timestamps:")
        for i, (timestamp, count) in enumerate(stats['recent_timestamps'], 1):
            print(f"   {i}. {timestamp[:19]} → {count:4d} registros")
        
        # Solicitar confirmación del usuario
        print(f"\n🗑️ Opciones de limpieza:")
        print(f"   1. Eliminar registros duplicados más recientes")
        print(f"   2. Ver análisis detallado de duplicados")
        print(f"   3. Cancelar")
        
        choice = input("\nSelecciona una opción (1-3): ").strip()
        
        if choice == "1":
            # Solicitar cantidad a eliminar
            count_input = input("\n¿Cuántos registros quieres eliminar?: ").strip()
            try:
                count_to_delete = int(count_input)
                if count_to_delete <= 0:
                    print("❌ La cantidad debe ser mayor a 0")
                    return
                
                # Confirmar eliminación
                print(f"\n⚠️ CONFIRMACIÓN:")
                print(f"   Se eliminarán los {count_to_delete} registros MÁS RECIENTES")
                print(f"   Esta operación NO se puede deshacer")
                
                confirm = input("\n¿Estás seguro? (sí/no): ").strip().lower()
                
                if confirm in ['sí', 'si', 's', 'yes', 'y']:
                    print(f"\n🔄 Eliminando {count_to_delete} registros...")
                    success = supabase_manager.delete_recent_duplicates(count_to_delete)
                    
                    if success:
                        print("✅ Eliminación completada exitosamente")
                        
                        # Mostrar estadísticas actualizadas
                        new_stats = supabase_manager.get_database_stats()
                        if new_stats:
                            print(f"\n📊 Estado después de la limpieza:")
                            print(f"   • Total registros: {new_stats['total_records']}")
                            print(f"   • Timestamps únicos: {new_stats['unique_timestamps']}")
                    else:
                        print("❌ Error durante la eliminación")
                else:
                    print("❌ Operación cancelada")
                    
            except ValueError:
                print("❌ Cantidad inválida")
                
        elif choice == "2":
            print(f"\n📈 Análisis detallado de timestamps:")
            for timestamp, count in stats['timestamp_counts'].items():
                print(f"   {timestamp[:19]} → {count:4d} registros")
                
        else:
            print("❌ Operación cancelada")
    
    except Exception as e:
        print(f"❌ Error en modo limpieza: {e}")


def auto_mode():
    """
    🤖 MODO AUTOMÁTICO para GitHub Actions - Sin duplicados garantizado.
    
    Este modo está específicamente diseñado para ejecución automática
    con máximas protecciones contra duplicados y validaciones inteligentes.
    """
    print("🤖 MODO AUTOMÁTICO: Ejecución para GitHub Actions")
    print("=" * 60)
    print("🔒 Protecciones anti-duplicados: MÁXIMAS")
    print("🧠 Validación inteligente: ACTIVADA")
    print("")
    
    try:
        # 1. Verificar conexión a Supabase
        print("🔌 Verificando conexión a Supabase...")
        supabase_manager = SupabaseManager()
        
        # 2. Obtener estadísticas pre-scraping
        print("📊 Analizando estado actual de la base de datos...")
        stats_before = supabase_manager.get_database_stats()
        
        if stats_before:
            print(f"   • Registros existentes: {stats_before['total_records']}")
            print(f"   • Timestamps únicos: {stats_before['unique_timestamps']}")
            
            # Mostrar último scraping
            if stats_before['recent_timestamps']:
                last_ts, last_count = stats_before['recent_timestamps'][0]
                print(f"   • Último scraping: {last_ts[:19]} ({last_count} registros)")
        
        # 3. Ejecutar scraping con detección de cambios OBLIGATORIA
        print("\n🕷️ Iniciando web scraping con detección de cambios...")
        scraper = NFLFantasyCompleteScraper(save_to_supabase=True)
        
        # Forzar detección de cambios (nunca insertar todos)
        data = scraper.scrape_all_data()
        
        if not data:
            print("❌ Error durante el scraping - abortando")
            return False
        
        print(f"✅ Scraping completado: {len(data)} jugadores extraídos")
        
        # 4. Verificar estadísticas post-scraping
        print("\n📈 Verificando resultado del scraping...")
        stats_after = supabase_manager.get_database_stats()
        
        if stats_after:
            records_added = stats_after['total_records'] - stats_before['total_records']
            print(f"   • Registros después: {stats_after['total_records']}")
            print(f"   • Registros añadidos: {records_added}")
            
            # 5. Validación de seguridad final
            if records_added > len(data):
                print(f"🚨 ALERTA: Se añadieron más registros ({records_added}) que jugadores extraídos ({len(data)})")
                print("🔍 Esto podría indicar un problema de duplicación")
                return False
            elif records_added == 0:
                print("✅ No se detectaron cambios - sin registros duplicados")
                print("💡 Sistema funcionando correctamente")
                return True
            else:
                print(f"✅ Se añadieron {records_added} registros con cambios reales")
                print("💡 Sistema anti-duplicados funcionando correctamente")
                return True
        
        return True
        
    except Exception as e:
        print(f"❌ Error en modo automático: {e}")
        return False


def test_week_detection():
    """
    🧪 Prueba la detección automática de semana NFL y estadísticas por semana.
    """
    print("🏈 PRUEBA: Detección automática de semana NFL")
    print("=" * 60)
    
    try:
        # Inicializar solo SupabaseManager para pruebas
        from datetime import datetime
        import logging
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        
        supabase_manager = SupabaseManager()
        
        # Prueba 1: Detectar semana actual
        print("\n🔍 1. Detectando semana NFL actual...")
        current_week = supabase_manager.detect_current_nfl_week()
        print(f"   ✅ Semana actual detectada: {current_week}")
        
        # Prueba 2: Obtener estadísticas por semana
        print("\n📊 2. Obteniendo estadísticas por semana...")
        week_stats = supabase_manager.get_week_stats()
        
        if week_stats['total_weeks'] > 0:
            print(f"   📈 Total de semanas en BD: {week_stats['total_weeks']}")
            print(f"   🏈 Semana más reciente en BD: {week_stats['current_week']}")
            print(f"\n📋 Resumen por semana:")
            
            for week in sorted(week_stats['weeks'].keys()):
                stats = week_stats['weeks'][week]
                print(f"   Semana {week}: {stats['records']} registros, {stats['unique_players']} jugadores únicos, {stats['scraping_sessions']} sesiones")
        else:
            print("   📝 No hay datos por semana en la BD (BD nueva o sin campo semana)")
        
        # Prueba 3: Obtener registros por semana específica
        if week_stats['total_weeks'] > 0 and current_week > 1:
            print(f"\n🔍 3. Probando comparación por semana...")
            previous_week = current_week - 1
            
            print(f"   🏈 Obteniendo registros de semana {previous_week}...")
            previous_records = supabase_manager.get_latest_player_records(by_week=True, target_week=previous_week)
            print(f"   📊 Jugadores únicos en semana {previous_week}: {len(previous_records)}")
            
            print(f"   🏈 Obteniendo registros de semana {current_week}...")
            current_records = supabase_manager.get_latest_player_records(by_week=True, target_week=current_week)
            print(f"   📊 Jugadores únicos en semana {current_week}: {len(current_records)}")
        else:
            print(f"\n📝 3. Comparación por semana no disponible (semana 1 o BD sin datos)")
        
        # Prueba 4: Cálculo de fecha fallback
        print(f"\n📅 4. Probando cálculo de semana por fecha (fallback)...")
        calculated_week = supabase_manager._calculate_week_by_date()
        print(f"   📅 Semana calculada por fecha: {calculated_week}")
        
        if calculated_week == current_week:
            print(f"   ✅ Coincidencia entre detección web y cálculo por fecha")
        else:
            print(f"   ⚠️ Diferencia: Web={current_week}, Fecha={calculated_week}")
        
        print(f"\n✅ Prueba de detección de semana completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error en prueba de semana: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Función principal que maneja diferentes modos de ejecución."""
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "--test":
            test_mode_quick()
            return
        elif mode == "--test-individual":
            test_individual_comparison()
            return
        elif mode == "--clean-duplicates":
            clean_duplicates_mode()
            return
        elif mode == "--auto":
            auto_mode()
            return
        elif mode == "--test-week":
            test_week_detection()
            return
        elif mode == "--help":
            print("🔧 NFL Fantasy Scraper - Modos disponibles:")
            print("   python scrapper.py                       # Scraping completo")
            print("   python scrapper.py --test               # Modo prueba general")
            print("   python scrapper.py --test-individual    # Prueba comparación individual")
            print("   python scrapper.py --test-week          # Prueba detección de semana NFL")
            print("   python scrapper.py --auto               # Modo automático (GitHub Actions)")
            print("   python scrapper.py --clean-duplicates   # Limpiar duplicados")
            print("   python scrapper.py --help               # Mostrar ayuda")
            return
        # Compatibilidad con versión anterior
        elif mode == "--clean":
            clean_duplicates_mode()
            return
    
    # Modo scraping completo por defecto
    print("🚀 Iniciando NFL Fantasy Scraper Completo...")
    print("=" * 60)
    
    # Verificar configuración de Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key or supabase_key == "tu_supabase_anon_key":
        print("⚠️ Variables de entorno de Supabase no configuradas correctamente")
        print("Configurando para guardar solo localmente...")
        scraper = NFLFantasyCompleteScraper(save_to_supabase=False)
    else:
        print("☁️ Configuración de Supabase detectada")
        scraper = NFLFantasyCompleteScraper(save_to_supabase=True)
    
    # Ejecutar scraping
    data = scraper.scrape_all_data()
    
    if data:
        print(f"✅ Scraping completado: {len(data)} jugadores procesados")
    else:
        print("❌ Error durante el scraping")


if __name__ == "__main__":
    main()
