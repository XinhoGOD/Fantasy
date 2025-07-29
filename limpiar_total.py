#!/usr/bin/env python3
"""
Limpieza Total de Base de Datos - Procesa TODOS los registros
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

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


class LimpiadorTotal:
    """Limpiador que procesa TODA la base de datos sin límites."""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(self.url, self.key)
        print("✅ Conexión a Supabase establecida")
    
    def obtener_todos_los_registros(self) -> List[Dict[str, Any]]:
        """Obtiene TODOS los registros de la tabla."""
        print("📊 Obteniendo TODOS los registros de la base de datos...")
        
        todos_los_registros = []
        offset = 0
        batch_size = 1000  # Máximo por consulta
        
        while True:
            try:
                response = self.supabase.table('nfl_fantasy_trends').select('*').range(
                    offset, offset + batch_size - 1
                ).order('id').execute()
                
                if not response.data:
                    break
                
                batch_records = response.data
                todos_los_registros.extend(batch_records)
                
                print(f"   📈 Obtenidos {len(todos_los_registros)} registros...")
                
                if len(batch_records) < batch_size:
                    # No hay más registros
                    break
                
                offset += batch_size
                
            except Exception as e:
                print(f"   ❌ Error obteniendo registros: {e}")
                break
        
        print(f"✅ Total de registros obtenidos: {len(todos_los_registros)}")
        return todos_los_registros
    
    def analizar_todos_los_duplicados(self, registros: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Analiza TODOS los duplicados."""
        print("🔍 Analizando duplicados en TODOS los registros...")
        
        grupos_por_firma = defaultdict(list)
        
        for registro in registros:
            # Crear firma única para identificar duplicados
            firma = (
                f"{registro.get('player_id', '')}|"
                f"{registro.get('percent_rostered', '')}|"
                f"{registro.get('percent_started', '')}|"
                f"{registro.get('opponent', '')}|"
                f"{registro.get('semana', '')}"
            )
            grupos_por_firma[firma].append(registro)
        
        # Filtrar solo grupos con duplicados
        duplicados = {}
        total_duplicados = 0
        
        for firma, grupo in grupos_por_firma.items():
            if len(grupo) > 1:
                # Ordenar por created_at descendente (más reciente primero)
                grupo.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                duplicados[firma] = grupo
                total_duplicados += len(grupo) - 1  # Mantener uno, eliminar el resto
        
        print(f"✅ Grupos de duplicados encontrados: {len(duplicados)}")
        print(f"📊 Total de registros duplicados a eliminar: {total_duplicados}")
        
        return duplicados
    
    def generar_plan_eliminacion(self, duplicados: Dict[str, List[Dict[str, Any]]]) -> List[int]:
        """Genera la lista de IDs a eliminar."""
        print("📋 Generando plan de eliminación...")
        
        ids_a_eliminar = []
        
        for firma, grupo in duplicados.items():
            if len(grupo) > 1:
                # Mantener el primer registro (más reciente), eliminar el resto
                for registro in grupo[1:]:
                    ids_a_eliminar.append(registro.get('id'))
        
        print(f"✅ IDs a eliminar: {len(ids_a_eliminar)}")
        return ids_a_eliminar
    
    def eliminar_en_lotes(self, ids_a_eliminar: List[int], batch_size: int = 100):
        """Elimina registros en lotes para evitar timeouts."""
        print(f"🗑️ Eliminando {len(ids_a_eliminar)} registros en lotes de {batch_size}...")
        
        total_eliminados = 0
        lotes = [ids_a_eliminar[i:i + batch_size] for i in range(0, len(ids_a_eliminar), batch_size)]
        
        for i, lote in enumerate(lotes, 1):
            try:
                print(f"   Lote {i}/{len(lotes)}: Eliminando {len(lote)} registros...")
                
                response = self.supabase.table('nfl_fantasy_trends').delete().in_(
                    'id', lote
                ).execute()
                
                eliminados_en_lote = len(response.data) if response.data else 0
                total_eliminados += eliminados_en_lote
                
                print(f"   ✅ Eliminados {eliminados_en_lote} registros")
                
                # Pausa pequeña entre lotes
                import time
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Error en lote {i}: {e}")
                continue
        
        return total_eliminados
    
    def ejecutar_limpieza_completa(self):
        """Ejecuta la limpieza completa de toda la base de datos."""
        print("🚀 LIMPIEZA COMPLETA DE TODA LA BASE DE DATOS")
        print("=" * 60)
        
        # Paso 1: Obtener todos los registros
        todos_los_registros = self.obtener_todos_los_registros()
        
        if not todos_los_registros:
            print("❌ No se pudieron obtener registros")
            return
        
        registros_iniciales = len(todos_los_registros)
        print(f"📊 Registros iniciales: {registros_iniciales}")
        
        # Paso 2: Analizar duplicados
        duplicados = self.analizar_todos_los_duplicados(todos_los_registros)
        
        if not duplicados:
            print("✅ No se encontraron duplicados. Base de datos ya optimizada.")
            return
        
        # Paso 3: Generar plan de eliminación
        ids_a_eliminar = self.generar_plan_eliminacion(duplicados)
        
        if not ids_a_eliminar:
            print("✅ No hay registros para eliminar")
            return
        
        # Paso 4: Mostrar ejemplos antes de eliminar
        print(f"\n📋 EJEMPLOS DE DUPLICADOS A ELIMINAR:")
        print("-" * 50)
        
        ejemplos_mostrados = 0
        for firma, grupo in duplicados.items():
            if ejemplos_mostrados >= 3:
                break
            
            if len(grupo) > 1:
                print(f"Duplicado #{ejemplos_mostrados + 1}:")
                print(f"  Player: {grupo[0].get('player_name', 'N/A')}")
                print(f"  Registros duplicados: {len(grupo)}")
                print(f"  IDs: {[r.get('id') for r in grupo]}")
                print(f"  Se mantendrá: {grupo[0].get('id')} (más reciente)")
                print()
                ejemplos_mostrados += 1
        
        # Paso 5: Confirmación final
        print(f"⚠️ SE ELIMINARÁN {len(ids_a_eliminar)} REGISTROS DUPLICADOS")
        print(f"📊 Registros que permanecerán: {registros_iniciales - len(ids_a_eliminar)}")
        print()
        
        confirmacion = input("¿CONFIRMAR ELIMINACIÓN MASIVA? (ESCRIBIR 'ELIMINAR' para confirmar): ").strip()
        
        if confirmacion != 'ELIMINAR':
            print("❌ Eliminación cancelada")
            return
        
        # Paso 6: Ejecutar eliminación
        total_eliminados = self.eliminar_en_lotes(ids_a_eliminar)
        
        print(f"\n🎯 LIMPIEZA COMPLETADA:")
        print(f"   • Registros iniciales: {registros_iniciales}")
        print(f"   • Registros eliminados: {total_eliminados}")
        print(f"   • Registros finales: {registros_iniciales - total_eliminados}")
        print(f"   • Optimización: {(total_eliminados/registros_iniciales)*100:.1f}% reducción")
        
        # Verificar resultado final
        self.verificar_resultado_final()
    
    def verificar_resultado_final(self):
        """Verifica el estado final de la base de datos."""
        print(f"\n📊 VERIFICACIÓN FINAL:")
        print("-" * 40)
        
        try:
            # Contar registros totales actuales
            count_response = self.supabase.table('nfl_fantasy_trends').select('id').execute()
            total_final = len(count_response.data) if count_response.data else 0
            
            print(f"📈 Registros totales finales: {total_final}")
            
            # Contar jugadores únicos
            players_response = self.supabase.table('nfl_fantasy_trends').select('player_id').execute()
            unique_players = set()
            
            if players_response.data:
                for record in players_response.data:
                    player_id = record.get('player_id')
                    if player_id:
                        unique_players.add(player_id)
            
            print(f"👥 Jugadores únicos: {len(unique_players)}")
            
            if total_final > 0 and unique_players:
                promedio = total_final / len(unique_players)
                print(f"📊 Promedio registros por jugador: {promedio:.1f}")
                
                if promedio <= 2.0:
                    print(f"✅ Base de datos PERFECTAMENTE optimizada")
                elif promedio <= 3.0:
                    print(f"✅ Base de datos bien optimizada")
                else:
                    print(f"⚠️ Aún podrían quedar algunos duplicados")
            
        except Exception as e:
            print(f"❌ Error en verificación final: {e}")


def main():
    """Función principal."""
    print("🚨 ADVERTENCIA: LIMPIEZA TOTAL DE DUPLICADOS")
    print("Este script procesará TODA la base de datos y eliminará TODOS los duplicados")
    print("Asegúrate de tener un backup completo antes de continuar")
    print()
    
    limpiador = LimpiadorTotal()
    limpiador.ejecutar_limpieza_completa()


if __name__ == "__main__":
    main()
