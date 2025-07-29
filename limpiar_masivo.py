#!/usr/bin/env python3
"""
Limpieza Masiva de Duplicados - Modo Avanzado
Limpia TODOS los duplicados de forma segura y eficiente
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


class LimpiadorMasivo:
    """Limpiador masivo de registros duplicados."""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(self.url, self.key)
        print("✅ Conexión a Supabase establecida")
    
    def limpiar_todos_los_duplicados(self, batch_size: int = 50):
        """
        Limpia TODOS los duplicados de la base de datos.
        
        Args:
            batch_size: Tamaño del lote para eliminación
        """
        print("🧹 LIMPIEZA MASIVA DE TODOS LOS DUPLICADOS")
        print("="*60)
        
        total_eliminados = 0
        iteracion = 1
        
        while True:
            print(f"\n🔄 Iteración {iteracion}:")
            
            # Obtener registros actuales
            print("   📊 Obteniendo registros actuales...")
            registros = self.obtener_registros_paginados()
            
            if not registros:
                print("   ❌ No se pudieron obtener registros")
                break
            
            print(f"   📈 Total registros actuales: {len(registros)}")
            
            # Identificar duplicados
            duplicados = self.identificar_duplicados_rapido(registros)
            
            if not duplicados:
                print("   ✅ No se encontraron más duplicados")
                break
            
            # Contar IDs a eliminar en esta iteración
            ids_a_eliminar = []
            for grupo in duplicados.values():
                if len(grupo) > 1:
                    # Mantener el más reciente, eliminar el resto
                    for registro in grupo[1:]:
                        ids_a_eliminar.append(registro.get('id'))
            
            # Limitar batch
            ids_a_eliminar = ids_a_eliminar[:batch_size]
            
            if not ids_a_eliminar:
                print("   ✅ No hay IDs válidos para eliminar")
                break
            
            print(f"   🗑️ Eliminando {len(ids_a_eliminar)} duplicados...")
            
            # Eliminar
            eliminados = self.eliminar_por_ids(ids_a_eliminar)
            total_eliminados += eliminados
            
            print(f"   ✅ Eliminados {eliminados} registros")
            print(f"   📊 Total eliminado hasta ahora: {total_eliminados}")
            
            if eliminados < len(ids_a_eliminar):
                print("   ⚠️ No se eliminaron todos los registros esperados")
                break
            
            iteracion += 1
            
            # Pausa para no sobrecargar
            import time
            time.sleep(1)
        
        print(f"\n🎯 LIMPIEZA COMPLETADA:")
        print(f"   • Total de registros eliminados: {total_eliminados}")
        print(f"   • Iteraciones realizadas: {iteracion - 1}")
        print(f"   • Base de datos optimizada")
        
        # Verificar estado final
        self.verificar_estado_final()
    
    def obtener_registros_paginados(self, max_records: int = 2000) -> List[Dict[str, Any]]:
        """Obtiene registros con paginación limitada."""
        try:
            response = self.supabase.table('nfl_fantasy_trends').select('*').order(
                'created_at', desc=True
            ).limit(max_records).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            print(f"   ❌ Error obteniendo registros: {e}")
            return []
    
    def identificar_duplicados_rapido(self, registros: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Identificación rápida de duplicados."""
        grupos_por_firma = defaultdict(list)
        
        for registro in registros:
            # Crear firma simple
            firma = f"{registro.get('player_id')}|{registro.get('percent_rostered')}|{registro.get('percent_started')}|{registro.get('semana')}"
            grupos_por_firma[firma].append(registro)
        
        # Solo devolver grupos con duplicados
        duplicados = {}
        for firma, grupo in grupos_por_firma.items():
            if len(grupo) > 1:
                # Ordenar por created_at desc para mantener el más reciente
                grupo.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                duplicados[firma] = grupo
        
        return duplicados
    
    def eliminar_por_ids(self, ids: List[int]) -> int:
        """Elimina registros por sus IDs."""
        try:
            response = self.supabase.table('nfl_fantasy_trends').delete().in_(
                'id', ids
            ).execute()
            
            return len(response.data) if response.data else 0
            
        except Exception as e:
            print(f"   ❌ Error eliminando: {e}")
            return 0
    
    def verificar_estado_final(self):
        """Verifica el estado final de la base de datos."""
        print(f"\n📊 VERIFICACIÓN FINAL:")
        print("-" * 40)
        
        try:
            # Contar registros totales
            total_response = self.supabase.table('nfl_fantasy_trends').select('id').execute()
            total_registros = len(total_response.data) if total_response.data else 0
            
            print(f"📈 Registros restantes: {total_registros}")
            
            # Verificar si quedan duplicados
            muestra_registros = self.obtener_registros_paginados(1000)
            duplicados_restantes = self.identificar_duplicados_rapido(muestra_registros)
            
            if duplicados_restantes:
                total_duplicados = sum(len(grupo) - 1 for grupo in duplicados_restantes.values())
                print(f"⚠️ Duplicados restantes en muestra: {total_duplicados}")
                print(f"💡 Ejecutar de nuevo para continuar limpieza")
            else:
                print(f"✅ No se detectaron duplicados en la muestra")
            
            # Contar jugadores únicos
            unique_players_response = self.supabase.table('nfl_fantasy_trends').select('player_id').execute()
            unique_player_ids = set()
            
            if unique_players_response.data:
                for record in unique_players_response.data:
                    player_id = record.get('player_id')
                    if player_id:
                        unique_player_ids.add(player_id)
            
            print(f"👥 Jugadores únicos: {len(unique_player_ids)}")
            
            if total_registros > 0 and unique_player_ids:
                avg_records = total_registros / len(unique_player_ids)
                print(f"📊 Promedio registros por jugador: {avg_records:.1f}")
                
                if avg_records <= 2.0:
                    print(f"✅ Base de datos bien optimizada")
                elif avg_records <= 3.0:
                    print(f"⚠️ Aún hay algunos duplicados menores")
                else:
                    print(f"🚨 Quedan muchos duplicados por limpiar")
            
        except Exception as e:
            print(f"❌ Error en verificación: {e}")


def main():
    """Función principal."""
    print("🚨 ADVERTENCIA: Este script eliminará TODOS los duplicados")
    print("Asegúrate de tener un backup de tu base de datos")
    print()
    
    confirmacion = input("¿Continuar con la limpieza masiva? (ESCRIBIR 'SI' para confirmar): ").strip()
    
    if confirmacion != 'SI':
        print("❌ Limpieza cancelada")
        sys.exit(0)
    
    try:
        limpiador = LimpiadorMasivo()
        limpiador.limpiar_todos_los_duplicados()
        
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
