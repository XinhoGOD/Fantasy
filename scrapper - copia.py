#!/usr/bin/env python3
"""
NFL Fantasy Football Trends Web Scraper - Versión Completa
Extrae TODOS los datos de la tabla de trends de fantasy NFL
"""

import time
import json
import logging
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


class NFLFantasyCompleteScraper:
    """Scraper completo para NFL Fantasy Trends con datos estructurados."""
    
    def __init__(self):
        self.url = "https://fantasy.nfl.com/research/trends"
        self.driver = None
        self.all_data = []
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self):
        """Configura Chrome con opciones básicas."""
        try:
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
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
            return self.all_data
            
        except Exception as e:
            self.logger.error(f"❌ Error durante scraping: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("🔒 Driver cerrado")
    
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
    print("🏈 NFL Fantasy Scraper - Todas las Páginas")
    print("=" * 60)
    
    scraper = NFLFantasyCompleteScraper()
    data = scraper.scrape_all_data()
    
    if data:
        print(f"\n✅ ¡Scraping completado exitosamente!")
        print(f"👥 Total de jugadores extraídos: {len(data)}")
        
        if data:
            print(f"\n📋 Datos de jugadores en formato JSON:")
            print("=" * 60)
            
            # Imprimir cada jugador en formato JSON
            for i, player in enumerate(data):
                print(f"\n// Jugador {i+1}")
                print("{")
                for key, value in player.items():
                    if isinstance(value, str):
                        print(f'  "{key}": "{value}",')
                    elif value is None:
                        print(f'  "{key}": null,')
                    else:
                        print(f'  "{key}": {value},')
                print("}")
            
            print(f"\n" + "=" * 60)
            print(f"� Resumen de calidad de datos:")
            
            with_names = len([p for p in data if p['player_name']])
            with_ids = len([p for p in data if p['player_id']])
            with_position = len([p for p in data if p['position']])
            with_team = len([p for p in data if p['team']])
            with_opponent = len([p for p in data if p['opponent']])
            with_rostered = len([p for p in data if p['percent_rostered'] is not None])
            with_started = len([p for p in data if p['percent_started'] is not None])
            with_adds = len([p for p in data if p['adds'] is not None])
            with_drops = len([p for p in data if p['drops'] is not None])
            
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
            
        else:
            print("\n⚠️ No se extrajeron jugadores.")
            print("Posibles causas:")
            print("   • La estructura de la página cambió")
            print("   • El contenido no se cargó completamente")
            print("   • Los selectores necesitan ajustes")
    
    else:
        print("\n❌ No se pudieron extraer datos")


if __name__ == "__main__":
    main()
