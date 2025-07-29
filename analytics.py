#!/usr/bin/env python3
"""
NFL Fantasy Analytics - Análisis de datos con Supabase
Utiliza las funciones optimizadas del SupabaseManager para análisis de datos
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd

# Importar nuestras clases
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from scrapper import SupabaseManager


class NFLFantasyAnalytics:
    """Clase para análisis avanzado de datos de NFL Fantasy."""
    
    def __init__(self):
        """Inicializa el analizador con conexión a Supabase."""
        try:
            self.supabase_manager = SupabaseManager()
            print("✅ Conexión a Supabase establecida")
        except Exception as e:
            print(f"❌ Error conectando a Supabase: {e}")
            raise
    
    def get_trending_report(self, min_change: float = 5.0) -> Dict[str, Any]:
        """
        Genera un reporte de jugadores con tendencias significativas.
        
        Args:
            min_change: Cambio mínimo en porcentaje para considerar tendencia
            
        Returns:
            Diccionario con análisis de tendencias
        """
        print(f"📈 Generando reporte de tendencias (cambio mínimo: {min_change}%)")
        
        trending_players = self.supabase_manager.get_trending_players(min_change)
        
        if not trending_players:
            return {"error": "No se encontraron jugadores con tendencias significativas"}
        
        # Análisis por posición
        by_position = {}
        rising_stars = []
        falling_players = []
        
        for player in trending_players:
            pos = player.get('position', 'Unknown')
            if pos not in by_position:
                by_position[pos] = []
            by_position[pos].append(player)
            
            # Clasificar por tipo de tendencia
            rostered_change = player.get('percent_rostered_change', 0) or 0
            if rostered_change >= min_change:
                rising_stars.append(player)
            elif rostered_change <= -min_change:
                falling_players.append(player)
        
        return {
            "total_trending": len(trending_players),
            "rising_stars": len(rising_stars),
            "falling_players": len(falling_players),
            "by_position": {pos: len(players) for pos, players in by_position.items()},
            "top_rising": sorted(rising_stars, key=lambda x: x.get('percent_rostered_change', 0), reverse=True)[:5],
            "top_falling": sorted(falling_players, key=lambda x: x.get('percent_rostered_change', 0))[:5],
            "generated_at": datetime.now().isoformat()
        }
    
    def analyze_team(self, team: str) -> Dict[str, Any]:
        """
        Analiza todos los jugadores de un equipo específico.
        
        Args:
            team: Código del equipo (ej: 'KC', 'BUF', 'LAR')
            
        Returns:
            Análisis completo del equipo
        """
        print(f"🏈 Analizando equipo: {team.upper()}")
        
        team_players = self.supabase_manager.get_team_players(team)
        
        if not team_players:
            return {"error": f"No se encontraron jugadores para el equipo {team}"}
        
        # Análisis por posición
        by_position = {}
        total_rostered = 0
        total_started = 0
        
        for player in team_players:
            pos = player.get('position', 'Unknown')
            if pos not in by_position:
                by_position[pos] = []
            by_position[pos].append(player)
            
            # Sumar estadísticas
            total_rostered += player.get('percent_rostered', 0) or 0
            total_started += player.get('percent_started', 0) or 0
        
        # Jugadores más populares
        most_rostered = sorted(team_players, key=lambda x: x.get('percent_rostered', 0) or 0, reverse=True)[:5]
        most_started = sorted(team_players, key=lambda x: x.get('percent_started', 0) or 0, reverse=True)[:5]
        
        return {
            "team": team.upper(),
            "total_players": len(team_players),
            "by_position": {pos: len(players) for pos, players in by_position.items()},
            "avg_rostered": round(total_rostered / len(team_players), 2),
            "avg_started": round(total_started / len(team_players), 2),
            "most_rostered": most_rostered,
            "most_started": most_started,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def player_history(self, player_name: str) -> Dict[str, Any]:
        """
        Obtiene el historial completo de un jugador.
        
        Args:
            player_name: Nombre del jugador (búsqueda parcial)
            
        Returns:
            Historial y tendencias del jugador
        """
        print(f"👤 Buscando historial de: {player_name}")
        
        player_data = self.supabase_manager.get_player_stats(player_name)
        
        if not player_data:
            return {"error": f"No se encontró historial para {player_name}"}
        
        # Análisis de tendencias
        df = pd.DataFrame(player_data)
        
        if len(df) > 1:
            # Calcular cambios a lo largo del tiempo
            df['scraped_at'] = pd.to_datetime(df['scraped_at'])
            df = df.sort_values('scraped_at')
            
            latest = df.iloc[-1]
            previous = df.iloc[-2] if len(df) > 1 else df.iloc[-1]
            
            rostered_trend = (latest['percent_rostered'] or 0) - (previous['percent_rostered'] or 0)
            started_trend = (latest['percent_started'] or 0) - (previous['percent_started'] or 0)
        else:
            latest = df.iloc[0]
            rostered_trend = latest.get('percent_rostered_change', 0) or 0
            started_trend = latest.get('percent_started_change', 0) or 0
        
        return {
            "player_name": latest['player_name'],
            "player_id": latest['player_id'],
            "position": latest['position'],
            "team": latest['team'],
            "total_records": len(player_data),
            "latest_stats": {
                "percent_rostered": latest['percent_rostered'],
                "percent_started": latest['percent_started'],
                "adds": latest['adds'],
                "drops": latest['drops']
            },
            "trends": {
                "rostered_change": rostered_trend,
                "started_change": started_trend
            },
            "history": player_data,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def generate_daily_summary(self) -> Dict[str, Any]:
        """
        Genera un resumen diario completo de la actividad fantasy.
        
        Returns:
            Resumen completo del día
        """
        print("📊 Generando resumen diario...")
        
        # Obtener datos más recientes
        latest_data = self.supabase_manager.get_latest_data(50)
        
        if not latest_data:
            return {"error": "No hay datos recientes disponibles"}
        
        # Análisis general
        positions = {}
        total_adds = 0
        total_drops = 0
        high_owned = []
        trending_up = []
        trending_down = []
        
        for player in latest_data:
            pos = player.get('position', 'Unknown')
            positions[pos] = positions.get(pos, 0) + 1
            
            total_adds += player.get('adds', 0) or 0
            total_drops += player.get('drops', 0) or 0
            
            rostered = player.get('percent_rostered', 0) or 0
            rostered_change = player.get('percent_rostered_change', 0) or 0
            
            if rostered >= 80:
                high_owned.append(player)
            
            if rostered_change >= 5:
                trending_up.append(player)
            elif rostered_change <= -5:
                trending_down.append(player)
        
        return {
            "summary_date": datetime.now().date().isoformat(),
            "total_players_analyzed": len(latest_data),
            "by_position": positions,
            "activity": {
                "total_adds": total_adds,
                "total_drops": total_drops,
                "net_adds": total_adds - total_drops
            },
            "ownership": {
                "high_owned_count": len(high_owned),
                "trending_up_count": len(trending_up),
                "trending_down_count": len(trending_down)
            },
            "top_trending_up": sorted(trending_up, key=lambda x: x.get('percent_rostered_change', 0), reverse=True)[:5],
            "top_trending_down": sorted(trending_down, key=lambda x: x.get('percent_rostered_change', 0))[:5],
            "most_added": sorted(latest_data, key=lambda x: x.get('adds', 0) or 0, reverse=True)[:5],
            "most_dropped": sorted(latest_data, key=lambda x: x.get('drops', 0) or 0, reverse=True)[:5],
            "generated_at": datetime.now().isoformat()
        }


def main():
    """Función principal para demostrar las capacidades de análisis."""
    print("🏈 NFL Fantasy Analytics")
    print("=" * 50)
    
    try:
        analytics = NFLFantasyAnalytics()
        
        # Resumen diario
        print("\n📊 RESUMEN DIARIO")
        print("-" * 30)
        daily_summary = analytics.generate_daily_summary()
        if "error" not in daily_summary:
            print(f"📈 Jugadores analizados: {daily_summary['total_players_analyzed']}")
            print(f"📊 Por posición: {daily_summary['by_position']}")
            print(f"⬆️ Trending up: {daily_summary['ownership']['trending_up_count']}")
            print(f"⬇️ Trending down: {daily_summary['ownership']['trending_down_count']}")
            print(f"🔥 Más agregados: {daily_summary['activity']['total_adds']}")
            print(f"❄️ Más dropeados: {daily_summary['activity']['total_drops']}")
        else:
            print(f"❌ {daily_summary['error']}")
        
        # Análisis de tendencias
        print("\n📈 JUGADORES TRENDING")
        print("-" * 30)
        trending_report = analytics.get_trending_report(3.0)
        if "error" not in trending_report:
            print(f"🚀 Rising stars: {trending_report['rising_stars']}")
            print(f"📉 Falling players: {trending_report['falling_players']}")
            
            if trending_report['top_rising']:
                print("\n🔥 Top Rising:")
                for player in trending_report['top_rising']:
                    change = player.get('percent_rostered_change', 0)
                    print(f"   • {player['player_name']} ({player['position']}) +{change}%")
        else:
            print(f"❌ {trending_report['error']}")
        
        # Ejemplo de análisis por equipo
        print("\n🏈 ANÁLISIS POR EQUIPO (Ejemplo: KC)")
        print("-" * 30)
        team_analysis = analytics.analyze_team('KC')
        if "error" not in team_analysis:
            print(f"👥 Total jugadores: {team_analysis['total_players']}")
            print(f"📊 Por posición: {team_analysis['by_position']}")
            print(f"📈 % Rostered promedio: {team_analysis['avg_rostered']}%")
            
            if team_analysis['most_rostered']:
                print("\n🌟 Más populares:")
                for player in team_analysis['most_rostered'][:3]:
                    rostered = player.get('percent_rostered', 0)
                    print(f"   • {player['player_name']} ({player['position']}) - {rostered}%")
        else:
            print(f"❌ {team_analysis['error']}")
            
    except Exception as e:
        print(f"❌ Error en analytics: {e}")


if __name__ == "__main__":
    main()
