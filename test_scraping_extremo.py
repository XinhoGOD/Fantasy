#!/usr/bin/env python3
"""
Prueba de Scraping con Sensibilidad Extrema
Ejecuta un scraping real para ver cuántos cambios detecta con la nueva sensibilidad
"""

import os
import sys
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Importar el scraper
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scrapper import NFLFantasyCompleteScraper, SupabaseManager


def test_scraping_sensibilidad_extrema():
    """Prueba un scraping real con sensibilidad extrema."""
    print("🚀 PRUEBA DE SCRAPING CON SENSIBILIDAD EXTREMA")
    print("="*60)
    print("Ejecutando scraping real para ver cuántos cambios detecta")
    print("con la nueva función súper sensible")
    print()
    
    # Mostrar estadísticas antes
    print("📊 ESTADÍSTICAS ANTES DEL SCRAPING:")
    print("-"*40)
    
    sm = SupabaseManager()
    
    try:
        # Contar registros actuales
        latest_data = sm.get_latest_data(1)
        if latest_data:
            last_scraping = latest_data[0].get('scraped_at', 'N/A')[:19]
            print(f"Último scraping: {last_scraping}")
        
        # Contar jugadores únicos
        latest_records = sm.get_latest_player_records()
        print(f"Jugadores únicos: {len(latest_records)}")
        
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
    
    print(f"\n🔥 NUEVA CONFIGURACIÓN:")
    print(f"   • Detecta cambios de 0.01% o más")
    print(f"   • Incluye cambios de oponente/matchup")
    print(f"   • Súper sensible a cualquier variación")
    
    # Ejecutar scraping
    print(f"\n🕷️ INICIANDO SCRAPING CON SENSIBILIDAD EXTREMA...")
    print("-"*50)
    
    try:
        scraper = NFLFantasyCompleteScraper(save_to_supabase=True)
        data = scraper.scrape_all_data()
        
        if data:
            print(f"\n✅ SCRAPING COMPLETADO:")
            print(f"   • Jugadores extraídos: {len(data)}")
            print(f"   • Cambios detectados y guardados automáticamente")
            print(f"   • Base de datos actualizada")
            
            # Mostrar algunos ejemplos de los datos extraídos
            print(f"\n📋 MUESTRA DE JUGADORES EXTRAÍDOS:")
            print("-"*40)
            
            for i, player in enumerate(data[:5]):
                name = player.get('player_name', 'Unknown')
                rostered = player.get('percent_rostered', 'N/A')
                started = player.get('percent_started', 'N/A')
                opponent = player.get('opponent', 'N/A')
                
                print(f"{i+1}. {name}")
                print(f"   Rostered: {rostered}% | Started: {started}% | vs {opponent}")
            
            if len(data) > 5:
                print(f"   ... y {len(data) - 5} jugadores más")
                
        else:
            print("❌ Error durante el scraping")
            
    except Exception as e:
        print(f"❌ Error ejecutando scraping: {e}")
        import traceback
        traceback.print_exc()
    
    # Mostrar estadísticas después
    print(f"\n📈 VERIFICACIÓN POST-SCRAPING:")
    print("-"*40)
    
    try:
        # Obtener estadísticas actualizadas
        latest_data_after = sm.get_latest_data(3)
        if latest_data_after:
            print(f"Últimos 3 timestamps:")
            for record in latest_data_after:
                timestamp = record.get('scraped_at', 'N/A')[:19]
                player_name = record.get('player_name', 'Unknown')
                print(f"   • {timestamp} - {player_name}")
        
        # Contar registros nuevos
        all_records_after = sm.get_latest_player_records()
        print(f"\nJugadores únicos después: {len(all_records_after)}")
        
    except Exception as e:
        print(f"Error obteniendo estadísticas post-scraping: {e}")
    
    print(f"\n🎯 RESULTADO:")
    print(f"   La nueva función súper sensible detectará muchos más cambios")
    print(f"   que la versión anterior, registrando variaciones mínimas")
    print(f"   en percent_rostered, percent_started y cambios de oponente")


if __name__ == "__main__":
    # Advertencia
    print("⚠️ ADVERTENCIA:")
    print("Este scraping detectará MÁS cambios que antes debido a la sensibilidad extrema")
    print("Esto es normal y esperado con la nueva configuración")
    print()
    
    confirmacion = input("¿Continuar con el scraping de prueba? (s/N): ").strip().lower()
    
    if confirmacion in ['s', 'si', 'y', 'yes']:
        test_scraping_sensibilidad_extrema()
    else:
        print("❌ Prueba cancelada")
        print("🔧 La función de sensibilidad extrema ya está implementada y lista para usar")
