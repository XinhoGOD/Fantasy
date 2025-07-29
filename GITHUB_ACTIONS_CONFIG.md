# 🏈 NFL Fantasy Scraper - Configuración GitHub Actions 24/7

## 📋 RESUMEN DE CONFIGURACIÓN COMPLETADA

### ✅ WORKFLOWS CONFIGURADOS

#### 1. **Workflow Principal: `nfl-scraper-30min.yml`**
- **Frecuencia**: ⏰ Cada 30 minutos, 24 horas al día
- **Programación**: `0,30 * * * *` (minutos 0 y 30 de cada hora)
- **Ejecuciones por día**: 48 ejecuciones automáticas
- **Modo**: `python scrapper.py --auto` (máximas protecciones anti-duplicados)
- **Características**:
  - ✅ Detección automática de semana NFL
  - ✅ Comparación individual por jugador (evita duplicados)
  - ✅ Instalación optimizada de Chrome y dependencias
  - ✅ Timeout de 25 minutos (seguridad antes de próxima ejecución)
  - ✅ Logging detallado y notificaciones de error
  - ✅ Recuperación automática en caso de fallos

#### 2. **Workflow de Monitoreo: `health-check-advanced.yml`**
- **Frecuencia**: ⏰ Cada 2 horas 
- **Función**: Verificar salud del sistema y estadísticas de BD
- **Características**:
  - ✅ Verificación de conexión Supabase
  - ✅ Conteo de registros y sesiones
  - ✅ Análisis de actividad reciente
  - ✅ Verificación del campo `semana`
  - ✅ Análisis detallado bajo demanda

#### 3. **Workflow Existente: `health-check.yml`**
- Mantener como backup o remover según preferencia

### ⚙️ CONFIGURACIÓN TÉCNICA

#### Variables de Entorno Requeridas (GitHub Secrets)
```
SUPABASE_URL=tu_url_de_supabase
SUPABASE_KEY=tu_clave_anonima_de_supabase
```

#### Dependencias Optimizadas (`requirements.txt`)
```
selenium==4.15.2        # Web scraping
beautifulsoup4==4.12.2  # HTML parsing  
supabase==1.2.0         # Base de datos
python-dotenv==1.0.0    # Variables de entorno
httpx[http2]==0.24.1    # HTTP client para Supabase
```

### 🚀 FUNCIONAMIENTO AUTOMÁTICO

#### Flujo de Ejecución (Cada 30 Minutos)
```
1. GitHub Actions dispara workflow
2. Instala Chrome y dependencias Python
3. Ejecuta: python scrapper.py --auto
4. Sistema detecta semana NFL automáticamente
5. Compara jugadores con registros individuales previos
6. Inserta solo cambios reales (anti-duplicados)
7. Logs detallados del resultado
8. Espera 30 minutos y repite
```

#### Protecciones Implementadas
- ✅ **Anti-duplicados máximos**: Comparación individual por jugador
- ✅ **Detección inteligente**: Solo inserta cambios reales
- ✅ **Timeout de seguridad**: 25 minutos máximo por ejecución
- ✅ **Recuperación automática**: Continúa tras errores
- ✅ **Logging completo**: Trazabilidad total del proceso
- ✅ **Verificación de integridad**: Valida resultados antes/después

### 📊 CRONOGRAMA DE EJECUCIÓN

#### Ejecuciones Diarias (Ejemplo)
```
00:00 UTC - Scraping automático
00:30 UTC - Scraping automático  
01:00 UTC - Scraping automático
01:30 UTC - Scraping automático
02:00 UTC - Scraping automático + Health Check
02:30 UTC - Scraping automático
03:00 UTC - Scraping automático
03:30 UTC - Scraping automático
04:00 UTC - Scraping automático + Health Check
...y así 24 horas al día, 7 días a la semana
```

#### Estadísticas Esperadas
- **Ejecuciones diarias**: 48 scrapings + 12 health checks
- **Registros por semana**: Variable según cambios NFL
- **Uptime esperado**: 99%+ (GitHub Actions es muy confiable)

### 🎯 COMANDOS MANUALES DISPONIBLES

#### Desde GitHub Actions UI:
```
1. Ir a Actions → "NFL Fantasy Scraper 24/7"
2. Click "Run workflow" 
3. Opciones disponibles:
   - "Normal execution" (modo automático)
   - "Test mode" (prueba sin insertar datos)
   - "Week detection test" (solo probar detección de semana)
```

#### Desde línea de comandos (local):
```bash
python scrapper.py --auto              # Modo automático (GitHub Actions)
python scrapper.py --test             # Prueba general
python scrapper.py --test-week        # Prueba detección de semana
python scrapper.py --test-individual  # Prueba comparación individual
python scrapper.py --help            # Ver todas las opciones
```

### ✅ CHECKLIST DE VALIDACIÓN

#### Antes de Activar Producción:
- [ ] Secrets configurados en GitHub (SUPABASE_URL, SUPABASE_KEY)
- [ ] Campo `semana` agregado a tabla Supabase ✅
- [ ] Workflow `nfl-scraper-30min.yml` commitado ✅
- [ ] `requirements.txt` optimizado ✅
- [ ] Prueba manual exitosa: `python scrapper.py --auto`

#### Después de Activar:
- [ ] Verificar primera ejecución automática en Actions
- [ ] Comprobar que se insertan datos en Supabase
- [ ] Validar que no hay duplicados masivos
- [ ] Monitorear logs durante primeras horas

### 🔄 MANTENIMIENTO

#### Automatizado (No Requiere Intervención):
- ✅ Ejecución cada 30 minutos
- ✅ Recuperación de errores temporales
- ✅ Detección automática de semanas NFL
- ✅ Monitoreo de salud del sistema

#### Manual (Ocasional):
- 🔍 Revisar logs si hay errores persistentes
- 📊 Verificar estadísticas de base de datos
- 🔧 Actualizar dependencias si es necesario
- 🏈 Ajustar lógica si la NFL cambia formato de datos

### 🎉 RESULTADO FINAL

**El sistema está completamente configurado para ejecutarse automáticamente cada 30 minutos, las 24 horas del día, con máximas protecciones contra duplicados y detección inteligente de cambios.**

**Próximo paso**: Activar el workflow haciendo commit/push de los cambios a GitHub.
