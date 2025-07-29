#!/usr/bin/env python3
"""
Depurador de Base de Datos - Identificar Registros Idénticos
Encuentra y analiza registros con valores exactamente iguales para limpieza
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import defaultdict

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


class DepuradorBD:
    """Clase para identificar y limpiar registros idénticos en la base de datos."""
    
    def __init__(self):
        """Inicializar conexión a Supabase."""
        try:
            self.url = os.getenv("SUPABASE_URL")
            self.key = os.getenv("SUPABASE_KEY")
            
            if not self.url or not self.key:
                print("❌ Variables de entorno SUPABASE_URL y SUPABASE_KEY son requeridas")
                sys.exit(1)
            
            self.supabase: Client = create_client(self.url, self.key)
            print("✅ Conexión a Supabase establecida")
            
        except Exception as e:
            print(f"❌ Error conectando a Supabase: {e}")
            sys.exit(1)
    
    def crear_firma_registro(self, registro: Dict[str, Any]) -> str:
        """
        Crea una firma única basada en los campos que importan para detectar duplicados.
        
        Args:
            registro: Diccionario con datos del jugador
            
        Returns:
            String que representa la "firma" del registro
        """
        # Campos importantes para determinar si un registro es único
        campos_firma = [
            'player_id',
            'percent_rostered',
            'percent_rostered_change',
            'percent_started', 
            'percent_started_change',
            'opponent',
            'semana'
        ]
        
        valores = []
        for campo in campos_firma:
            valor = registro.get(campo, 'NULL')
            # Normalizar valores None a 'NULL' para comparación consistente
            if valor is None:
                valor = 'NULL'
            valores.append(str(valor))
        
        return '|'.join(valores)
    
    def obtener_todos_los_registros(self) -> List[Dict[str, Any]]:
        """
        Obtiene TODOS los registros de la base de datos con paginación.
        
        Returns:
            Lista con todos los registros
        """
        print("📊 Obteniendo todos los registros de la base de datos...")
        
        todos_los_registros = []
        offset = 0
        batch_size = 1000
        
        while True:
            try:
                response = self.supabase.table('nfl_fantasy_trends').select('*').range(
                    offset, offset + batch_size - 1
                ).order('created_at', desc=True).execute()
                
                if not response.data:
                    break
                
                todos_los_registros.extend(response.data)
                print(f"   📥 Cargados {len(response.data)} registros (total: {len(todos_los_registros)})")
                
                if len(response.data) < batch_size:
                    break
                
                offset += batch_size
                
            except Exception as e:
                print(f"❌ Error obteniendo registros: {e}")
                break
        
        print(f"✅ Total de registros obtenidos: {len(todos_los_registros)}")
        return todos_los_registros
    
    def identificar_duplicados_exactos(self, registros: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identifica grupos de registros con valores exactamente idénticos.
        
        Args:
            registros: Lista de todos los registros
            
        Returns:
            Diccionario con firmas como claves y listas de registros duplicados como valores
        """
        print("\n🔍 Identificando registros con valores exactamente idénticos...")
        
        # Agrupar registros por su firma
        grupos_por_firma = defaultdict(list)
        
        for registro in registros:
            firma = self.crear_firma_registro(registro)
            grupos_por_firma[firma].append(registro)
        
        # Filtrar solo grupos con más de 1 registro (duplicados)
        duplicados = {}
        total_duplicados = 0
        
        for firma, grupo in grupos_por_firma.items():
            if len(grupo) > 1:
                duplicados[firma] = grupo
                total_duplicados += len(grupo) - 1  # -1 porque uno debe quedarse
        
        print(f"📈 Grupos de duplicados encontrados: {len(duplicados)}")
        print(f"📊 Total de registros duplicados innecesarios: {total_duplicados}")
        
        return duplicados
    
    def analizar_duplicados_por_jugador(self, duplicados: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Analiza los duplicados agrupados por jugador.
        
        Args:
            duplicados: Diccionario con grupos de registros duplicados
        """
        print(f"\n👥 ANÁLISIS POR JUGADOR:")
        print("="*80)
        
        jugadores_con_duplicados = defaultdict(int)
        
        for firma, grupo in duplicados.items():
            if len(grupo) > 1:
                # Obtener nombre del jugador del primer registro del grupo
                player_name = grupo[0].get('player_name', 'Unknown')
                jugadores_con_duplicados[player_name] += len(grupo) - 1
        
        # Mostrar jugadores con más duplicados
        jugadores_ordenados = sorted(jugadores_con_duplicados.items(), key=lambda x: x[1], reverse=True)
        
        print(f"🔝 Top 20 jugadores con más registros duplicados:")
        for i, (jugador, count) in enumerate(jugadores_ordenados[:20], 1):
            print(f"   {i:2d}. {jugador:<30} | {count:3d} duplicados")
        
        if len(jugadores_ordenados) > 20:
            print(f"   ... y {len(jugadores_ordenados) - 20} jugadores más con duplicados")
    
    def analizar_duplicados_por_fecha(self, duplicados: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Analiza los duplicados agrupados por fecha de scraping.
        
        Args:
            duplicados: Diccionario con grupos de registros duplicados
        """
        print(f"\n📅 ANÁLISIS POR FECHA DE SCRAPING:")
        print("="*80)
        
        fechas_con_duplicados = defaultdict(int)
        
        for firma, grupo in duplicados.items():
            if len(grupo) > 1:
                # Agrupar por fecha
                for registro in grupo:
                    fecha = registro.get('scraped_at', '')[:19]  # Solo fecha y hora
                    fechas_con_duplicados[fecha] += 1
        
        # Mostrar fechas con más duplicados
        fechas_ordenadas = sorted(fechas_con_duplicados.items(), key=lambda x: x[1], reverse=True)
        
        print(f"🔝 Top 15 fechas con más registros duplicados:")
        for i, (fecha, count) in enumerate(fechas_ordenadas[:15], 1):
            print(f"   {i:2d}. {fecha} | {count:3d} duplicados")
    
    def mostrar_ejemplos_duplicados(self, duplicados: Dict[str, List[Dict[str, Any]]], max_ejemplos: int = 5) -> None:
        """
        Muestra ejemplos detallados de registros duplicados.
        
        Args:
            duplicados: Diccionario con grupos de registros duplicados
            max_ejemplos: Número máximo de ejemplos a mostrar
        """
        print(f"\n📋 EJEMPLOS DE REGISTROS DUPLICADOS:")
        print("="*80)
        
        count = 0
        for firma, grupo in duplicados.items():
            if count >= max_ejemplos:
                break
            
            if len(grupo) > 1:
                primer_registro = grupo[0]
                player_name = primer_registro.get('player_name', 'Unknown')
                
                print(f"\n🔄 Ejemplo {count + 1}: {player_name}")
                print(f"   📊 {len(grupo)} registros idénticos encontrados")
                print(f"   🎯 Valores idénticos:")
                print(f"      • % Rostered: {primer_registro.get('percent_rostered')}%")
                print(f"      • % Started: {primer_registro.get('percent_started')}%") 
                print(f"      • Rostered Change: {primer_registro.get('percent_rostered_change')}")
                print(f"      • Started Change: {primer_registro.get('percent_started_change')}")
                print(f"      • Oponente: {primer_registro.get('opponent')}")
                print(f"      • Semana: {primer_registro.get('semana')}")
                
                print(f"   📅 Fechas de estos registros idénticos:")
                for i, registro in enumerate(grupo, 1):
                    fecha = registro.get('scraped_at', '')[:19]
                    created_at = registro.get('created_at', '')[:19]
                    record_id = registro.get('id', 'N/A')
                    print(f"      {i}. ID {record_id} | Scraped: {fecha} | Created: {created_at}")
                
                count += 1
    
    def generar_query_limpieza(self, duplicados: Dict[str, List[Dict[str, Any]]], limit_queries: int = 10) -> None:
        """
        Genera queries SQL para limpiar los duplicados.
        
        Args:
            duplicados: Diccionario con grupos de registros duplicados
            limit_queries: Número máximo de queries a generar
        """
        print(f"\n🧹 QUERIES PARA LIMPIAR DUPLICADOS:")
        print("="*80)
        
        total_ids_to_delete = []
        count = 0
        
        for firma, grupo in duplicados.items():
            if len(grupo) > 1:
                # Mantener el registro más reciente (primer elemento ya que están ordenados por created_at desc)
                registros_a_eliminar = grupo[1:]  # Todos excepto el primero
                
                for registro in registros_a_eliminar:
                    record_id = registro.get('id')
                    if record_id:
                        total_ids_to_delete.append(record_id)
        
        if total_ids_to_delete:
            print(f"📊 Total de IDs para eliminar: {len(total_ids_to_delete)}")
            
            # Generar queries en lotes de 100
            batch_size = 100
            query_count = 0
            
            print(f"\n💾 Queries SQL (lotes de {batch_size}):")
            
            for i in range(0, len(total_ids_to_delete), batch_size):
                if query_count >= limit_queries:
                    remaining_batches = (len(total_ids_to_delete) - i + batch_size - 1) // batch_size
                    print(f"   ... y {remaining_batches} lotes más")
                    break
                
                batch = total_ids_to_delete[i:i + batch_size]
                ids_str = ','.join(map(str, batch))
                
                query_count += 1
                print(f"\n-- Lote {query_count}: Eliminar {len(batch)} registros duplicados")
                print(f"DELETE FROM nfl_fantasy_trends WHERE id IN ({ids_str});")
            
            print(f"\n💡 RECOMENDACIÓN:")
            print(f"   • Hacer backup antes de ejecutar")
            print(f"   • Ejecutar de uno en uno para monitorear")
            print(f"   • Total a eliminar: {len(total_ids_to_delete)} registros")
            print(f"   • Esto liberará espacio significativo en la BD")
        else:
            print("✅ No hay IDs válidos para eliminar")
    
    def ejecutar_limpieza_automatica(self, duplicados: Dict[str, List[Dict[str, Any]]], max_delete: int = 100) -> bool:
        """
        Ejecuta limpieza automática de duplicados (modo seguro).
        
        Args:
            duplicados: Diccionario con grupos de registros duplicados
            max_delete: Número máximo de registros a eliminar por seguridad
            
        Returns:
            True si la limpieza fue exitosa
        """
        print(f"\n🤖 LIMPIEZA AUTOMÁTICA (MODO SEGURO - max {max_delete} registros):")
        print("="*80)
        
        ids_to_delete = []
        
        for firma, grupo in duplicados.items():
            if len(grupo) > 1:
                # Mantener el registro más reciente, eliminar los demás
                registros_a_eliminar = grupo[1:]
                
                for registro in registros_a_eliminar:
                    record_id = registro.get('id')
                    if record_id and len(ids_to_delete) < max_delete:
                        ids_to_delete.append(record_id)
        
        if not ids_to_delete:
            print("✅ No hay registros para eliminar")
            return True
        
        print(f"🗑️ Preparando eliminar {len(ids_to_delete)} registros duplicados...")
        
        # Mostrar muestra de lo que se va a eliminar
        print(f"\n📋 Muestra de registros que se eliminarán:")
        sample_count = 0
        for firma, grupo in duplicados.items():
            if len(grupo) > 1 and sample_count < 5:
                player_name = grupo[0].get('player_name', 'Unknown')
                duplicates_count = len(grupo) - 1
                print(f"   • {player_name}: {duplicates_count} duplicados")
                sample_count += 1
        
        # Confirmar antes de proceder
        confirmacion = input(f"\n❓ ¿Proceder con la eliminación de {len(ids_to_delete)} registros? (s/N): ").strip().lower()
        
        if confirmacion not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Limpieza cancelada por el usuario")
            return False
        
        try:
            # Eliminar en lotes pequeños
            batch_size = 20
            total_deleted = 0
            
            for i in range(0, len(ids_to_delete), batch_size):
                batch = ids_to_delete[i:i + batch_size]
                
                response = self.supabase.table('nfl_fantasy_trends').delete().in_(
                    'id', batch
                ).execute()
                
                if response.data:
                    deleted_count = len(response.data)
                    total_deleted += deleted_count
                    print(f"✅ Eliminados {deleted_count} registros (lote {i//batch_size + 1})")
                else:
                    print(f"⚠️ Lote {i//batch_size + 1} no devolvió confirmación, pero puede haber sido exitoso")
            
            print(f"\n🎯 Limpieza completada:")
            print(f"   • Total eliminado: {total_deleted} registros")
            print(f"   • Espacio liberado en la BD")
            print(f"   • Base de datos optimizada")
            
            return True
            
        except Exception as e:
            print(f"❌ Error durante la limpieza: {e}")
            return False
    
    def run_depuracion_completa(self, modo_automatico: bool = False):
        """
        Ejecuta el proceso completo de depuración.
        
        Args:
            modo_automatico: Si True, ejecuta limpieza automática limitada
        """
        print("🔍 DEPURACIÓN COMPLETA DE BASE DE DATOS")
        print("="*80)
        print("Identificando registros con valores exactamente idénticos...")
        print()
        
        # 1. Obtener todos los registros
        registros = self.obtener_todos_los_registros()
        
        if not registros:
            print("❌ No se pudieron obtener registros")
            return
        
        # 2. Identificar duplicados exactos
        duplicados = self.identificar_duplicados_exactos(registros)
        
        if not duplicados:
            print("✅ ¡Excelente! No se encontraron registros duplicados")
            return
        
        # 3. Análisis detallado
        self.analizar_duplicados_por_jugador(duplicados)
        self.analizar_duplicados_por_fecha(duplicados)
        self.mostrar_ejemplos_duplicados(duplicados)
        self.generar_query_limpieza(duplicados)
        
        # 4. Opción de limpieza automática
        if modo_automatico:
            self.ejecutar_limpieza_automatica(duplicados)
        else:
            print(f"\n💡 PRÓXIMOS PASOS:")
            print("="*40)
            print("1. Revisar los ejemplos de duplicados mostrados")
            print("2. Ejecutar las queries SQL proporcionadas (con backup)")
            print("3. O usar: python depurar_bd.py --auto para limpieza automática limitada")


def main():
    """Función principal."""
    try:
        # Verificar argumentos
        modo_automatico = '--auto' in sys.argv or '-a' in sys.argv
        
        if modo_automatico:
            print("🤖 Modo automático activado (limpieza limitada y segura)")
        
        depurador = DepuradorBD()
        depurador.run_depuracion_completa(modo_automatico=modo_automatico)
        
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
