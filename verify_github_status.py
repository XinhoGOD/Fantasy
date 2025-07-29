#!/usr/bin/env python3
"""
Verificador de Estado de GitHub Actions y Supabase
Verifica si el sistema automatizado está funcionando correctamente
"""
import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any

# Intentar importar Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    print("❌ Supabase no disponible localmente")
    SUPABASE_AVAILABLE = False

# Intentar cargar python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class GitHubStatusVerifier:
    def __init__(self):
        self.github_repo = "XinhoGOD/Fantasy"
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
    def verify_github_workflows(self) -> Dict[str, Any]:
        """Verifica el estado de los workflows de GitHub Actions"""
        print("🔍 Verificando workflows de GitHub Actions...")
        
        try:
            # GitHub API para workflows
            url = f"https://api.github.com/repos/{self.github_repo}/actions/runs"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                recent_runs = data.get('workflow_runs', [])[:5]  # Últimas 5 ejecuciones
                
                print(f"✅ Conectado a GitHub API exitosamente")
                print(f"📊 Últimas {len(recent_runs)} ejecuciones encontradas:")
                
                for i, run in enumerate(recent_runs, 1):
                    status = run.get('status', 'unknown')
                    conclusion = run.get('conclusion', 'unknown')
                    created_at = run.get('created_at', '')
                    workflow_name = run.get('name', 'Unknown')
                    
                    # Convertir fecha
                    try:
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        time_ago = datetime.now() - created_date.replace(tzinfo=None)
                        time_str = f"{time_ago.days}d {time_ago.seconds//3600}h {(time_ago.seconds//60)%60}m ago"
                    except:
                        time_str = "unknown time"
                    
                    status_emoji = "✅" if conclusion == "success" else "❌" if conclusion == "failure" else "🔄"
                    print(f"  {i}. {status_emoji} {workflow_name}: {status}/{conclusion} ({time_str})")
                
                return {
                    'success': True,
                    'total_runs': len(recent_runs),
                    'latest_status': recent_runs[0].get('conclusion') if recent_runs else 'none'
                }
            else:
                print(f"❌ Error conectando a GitHub API: {response.status_code}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            print(f"❌ Error verificando GitHub: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_supabase_connection(self) -> Dict[str, Any]:
        """Verifica la conexión con Supabase"""
        print("\n🔍 Verificando conexión con Supabase...")
        
        if not SUPABASE_AVAILABLE:
            print("❌ Supabase library no disponible localmente")
            return {'success': False, 'error': 'Supabase library not available'}
        
        if not self.supabase_url or not self.supabase_key:
            print("❌ Credenciales de Supabase no encontradas")
            return {'success': False, 'error': 'Missing credentials'}
        
        try:
            # Conectar a Supabase
            supabase: Client = create_client(self.supabase_url, self.supabase_key)
            
            # Verificar tabla nfl_fantasy_trends
            print("📊 Verificando tabla nfl_fantasy_trends...")
            response = supabase.table('nfl_fantasy_trends').select('*').limit(1).execute()
            
            if response.data:
                print("✅ Conexión con Supabase exitosa")
                
                # Contar registros totales
                count_response = supabase.table('nfl_fantasy_trends').select('*', count='exact').execute()
                total_records = count_response.count if hasattr(count_response, 'count') else 'unknown'
                
                # Obtener registro más reciente
                latest_response = supabase.table('nfl_fantasy_trends').select('*').order('timestamp', desc=True).limit(1).execute()
                
                if latest_response.data:
                    latest_record = latest_response.data[0]
                    latest_time = latest_record.get('timestamp', 'unknown')
                    latest_player = latest_record.get('player_name', 'unknown')
                    latest_week = latest_record.get('semana', 'unknown')
                    
                    print(f"📈 Total de registros: {total_records}")
                    print(f"🕐 Último registro: {latest_time}")
                    print(f"👤 Último jugador: {latest_player}")
                    print(f"🏈 Semana NFL: {latest_week}")
                    
                    # Verificar registros recientes (últimas 2 horas)
                    two_hours_ago = datetime.now() - timedelta(hours=2)
                    recent_response = supabase.table('nfl_fantasy_trends').select('*').gte('timestamp', two_hours_ago.isoformat()).execute()
                    recent_count = len(recent_response.data) if recent_response.data else 0
                    
                    print(f"🔄 Registros últimas 2 horas: {recent_count}")
                    
                    return {
                        'success': True,
                        'total_records': total_records,
                        'latest_timestamp': latest_time,
                        'latest_player': latest_player,
                        'latest_week': latest_week,
                        'recent_records': recent_count
                    }
                else:
                    print("⚠️ No hay registros en la tabla")
                    return {'success': True, 'total_records': 0}
            else:
                print("❌ No se pudo acceder a la tabla")
                return {'success': False, 'error': 'Could not access table'}
                
        except Exception as e:
            print(f"❌ Error conectando a Supabase: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_status_report(self):
        """Genera un reporte completo del estado del sistema"""
        print("🚀 VERIFICACIÓN DE ESTADO - NFL Fantasy Scraper")
        print("=" * 60)
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 Repositorio: {self.github_repo}")
        print()
        
        # Verificar GitHub Actions
        github_status = self.verify_github_workflows()
        
        # Verificar Supabase
        supabase_status = self.verify_supabase_connection()
        
        # Reporte final
        print("\n" + "=" * 60)
        print("📋 RESUMEN DEL ESTADO:")
        
        if github_status.get('success'):
            print(f"✅ GitHub Actions: Funcionando ({github_status.get('total_runs', 0)} ejecuciones recientes)")
        else:
            print(f"❌ GitHub Actions: Error - {github_status.get('error', 'Unknown')}")
        
        if supabase_status.get('success'):
            recent = supabase_status.get('recent_records', 0)
            total = supabase_status.get('total_records', 0)
            print(f"✅ Supabase: Conectado ({total} registros totales, {recent} recientes)")
        else:
            print(f"❌ Supabase: Error - {supabase_status.get('error', 'Unknown')}")
        
        # Evaluación general
        print("\n🎯 EVALUACIÓN GENERAL:")
        if github_status.get('success') and supabase_status.get('success'):
            if supabase_status.get('recent_records', 0) > 0:
                print("🟢 EXCELENTE: Sistema funcionando perfectamente con datos recientes")
            else:
                print("🟡 BUENO: Sistema funcionando, sin cambios recientes (normal en off-season)")
        else:
            print("🔴 ATENCIÓN: Requiere revisión")
        
        print("\n💡 PRÓXIMA EJECUCIÓN: En ~30 minutos automáticamente")
        print("🔄 FRECUENCIA: Cada 30 minutos, 24/7")

def main():
    verifier = GitHubStatusVerifier()
    verifier.generate_status_report()

if __name__ == "__main__":
    main()
