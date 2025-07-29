#!/usr/bin/env python3
"""
NFL Fantasy Football Trends Web Scraper - Versión Completa con Supabase
Extrae TODOS los datos de la tabla de trends de fantasy NFL y los sube a Supabase
"""

import time
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import pandas as pd

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
        
        Args:
            players_data: Lista de diccionarios con datos de jugadores
            
        Returns:
            True si la inserción fue exitosa, False en caso contrario
        """
        try:
            batch_size = 100  # Insertar de 100 en 100
            total_inserted = 0
            
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
                        'scraped_at': datetime.now().isoformat()  # Timestamp del scraping
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
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error insertando en Supabase: {e}")
            return False
    
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
    
    def get_trending_players(self, min_change: float = 5.0) -> List[Dict]:
        """
        Obtiene jugadores con cambios significativos en ownership.
        Usa filtros numéricos gte/lte.
        """
        try:
            response = self.supabase.table('nfl_fantasy_trends').select('*').or_(
                f'percent_rostered_change.gte.{min_change},percent_started_change.gte.{min_change}'
            ).order('percent_rostered_change', desc=True).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo jugadores trending: {e}")
            return []
    
    def upsert_players_batch(self, players_data: List[Dict[str, Any]]) -> bool:
        """
        Hace UPSERT de jugadores en lotes. 
        Usa una estrategia híbrida: insertar nuevos y actualizar existentes.
        
        Args:
            players_data: Lista de diccionarios con datos de jugadores
            
        Returns:
            True si el upsert fue exitoso, False en caso contrario
        """
        try:
            batch_size = 100
            total_processed = 0
            
            for i in range(0, len(players_data), batch_size):
                batch = players_data[i:i + batch_size]
                
                # Preparar datos para Supabase con timestamp
                formatted_batch = []
                current_timestamp = datetime.now().isoformat()
                
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
                        'scraped_at': current_timestamp
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
            
            # Guardar datos automáticamente
            if self.all_data:
                self.save_data(self.all_data)
            
            return self.all_data
            
        except Exception as e:
            self.logger.error(f"❌ Error durante scraping: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("🔒 Driver cerrado")
    
    def save_data(self, data: List[Dict[str, Any]], use_upsert: bool = True) -> bool:
        """
        Guarda los datos tanto localmente como en Supabase.
        
        Args:
            data: Lista de datos de jugadores
            use_upsert: Si True usa UPSERT, si False usa INSERT normal
            
        Returns:
            True si el guardado fue exitoso
        """
        success = True
        
        # Guardar localmente (JSON y CSV)
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Guardar JSON
            json_filename = f'nfl_fantasy_trends_{timestamp}.json'
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Guardar CSV
            csv_filename = f'nfl_fantasy_trends_{timestamp}.csv'
            df = pd.DataFrame(data)
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            
            self.logger.info(f"💾 Datos guardados localmente: {json_filename}, {csv_filename}")
            
        except Exception as e:
            self.logger.error(f"❌ Error guardando localmente: {e}")
            success = False
        
        # Guardar en Supabase si está habilitado
        if self.save_to_supabase and data:
            try:
                # Usar UPSERT o INSERT según la preferencia
                if use_upsert:
                    self.logger.info("📊 Usando UPSERT para evitar duplicados...")
                    supabase_success = self.supabase_manager.upsert_players_batch(data)
                else:
                    self.logger.info("📊 Usando INSERT normal...")
                    # Opcional: limpiar datos del día actual antes de insertar
                    # self.supabase_manager.clear_today_data()
                    supabase_success = self.supabase_manager.insert_players_batch(data)
                
                if supabase_success:
                    self.logger.info("☁️ Datos subidos exitosamente a Supabase")
                    
                    # Mostrar estadísticas adicionales
                    latest = self.supabase_manager.get_latest_data(3)
                    if latest:
                        self.logger.info(f"📈 Últimos registros guardados:")
                        for record in latest:
                            self.logger.info(f"   • {record.get('player_name')} - {record.get('scraped_at', 'N/A')[:19]}")
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


def main():
    """Función principal."""
    print("🏈 NFL Fantasy Scraper - Supabase Integration")
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
        print(f"\n✅ ¡Scraping completado exitosamente!")
        print(f"👥 Total de jugadores extraídos: {len(data)}")
        
        # Mostrar muestra de datos insertados en Supabase
        if scraper.save_to_supabase:
            try:
                print(f"\n☁️ Verificando datos en Supabase...")
                latest = scraper.supabase_manager.get_latest_data(5)
                if latest:
                    print(f"📊 Últimos 5 registros en Supabase:")
                    for record in latest:
                        scraped_time = record.get('scraped_at', 'N/A')[:19] if record.get('scraped_at') else 'N/A'
                        print(f"   • {record.get('player_name')} ({record.get('position')}) - {record.get('team')} - {scraped_time}")
                
                # Mostrar estadísticas de análisis rápido
                print(f"\n🔍 Análisis rápido disponible:")
                print(f"   • Trending players: Use analytics.py para obtener jugadores en tendencia")
                print(f"   • Team analysis: Analizar jugadores por equipo")
                print(f"   • Player history: Historial de cualquier jugador")
                print(f"   • Daily summaries: Resúmenes diarios automáticos")
                
            except Exception as e:
                print(f"⚠️ No se pudieron obtener datos de Supabase: {e}")
        
        # Mostrar estadísticas resumidas (sin imprimir todos los jugadores)
        print(f"\n" + "=" * 60)
        print(f"📈 Resumen de calidad de datos:")
        
        with_names = len([p for p in data if p['player_name']])
        with_ids = len([p for p in data if p['player_id']])
        with_position = len([p for p in data if p['position']])
        with_team = len([p for p in data if p['team']])
        with_opponent = len([p for p in data if p['opponent']])
        with_rostered = len([p for p in data if p['percent_rostered'] is not None])
        with_started = len([p for p in data if p['percent_started'] is not None])
        with_adds = len([p for p in data if p['adds'] is not None])
        
        print(f"   • Con nombre: {with_names}/{len(data)}")
        print(f"   • Con ID: {with_ids}/{len(data)}")
        print(f"   • Con posición: {with_position}/{len(data)}")
        print(f"   • Con equipo: {with_team}/{len(data)}")
        print(f"   • Con oponente: {with_opponent}/{len(data)}")
        print(f"   • Con % rostered: {with_rostered}/{len(data)}")
        print(f"   • Con % started: {with_started}/{len(data)}")
        print(f"   • Con adds: {with_adds}/{len(data)}")
        
        # Mostrar resumen por posiciones
        positions = {}
        for player in data:
            pos = player.get('position', 'Unknown')
            positions[pos] = positions.get(pos, 0) + 1
        
        print(f"\n🏃 Resumen por posiciones:")
        for pos, count in sorted(positions.items()):
            print(f"   • {pos}: {count} jugadores")
        
        # Información sobre donde se guardaron los datos
        if scraper.save_to_supabase:
            print(f"\n💾 Datos guardados en:")
            print(f"   • Supabase: tabla 'nfl_fantasy_trends' con {len(data)} registros")
            print(f"   • Archivos locales: JSON y CSV con timestamp")
            print(f"\n🚀 Nuevas capacidades habilitadas:")
            print(f"   • UPSERT automático (evita duplicados)")
            print(f"   • Análisis de tendencias en tiempo real")
            print(f"   • Filtros avanzados por equipo, posición, cambios")
            print(f"   • Ejecuta 'python analytics.py' para análisis completo")
        else:
            print(f"\n💾 Datos guardados localmente en archivos JSON y CSV")
            print(f"⚠️ Para habilitar análisis avanzado, configura las variables de Supabase")
    
    else:
        print("\n❌ No se pudieron extraer datos")


if __name__ == "__main__":
    main()
