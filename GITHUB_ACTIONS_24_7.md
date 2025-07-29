# 🤖 CONFIGURACIÓN GITHUB ACTIONS - NFL Fantasy Scraper 24/7

## 🎯 Configuración Automática Cada 30 Minutos

### 📋 Resumen de Workflows

1. **🏈 Scraper Principal**: `nfl-scraper-30min.yml`
   - **Frecuencia**: Cada 30 minutos, 24/7
   - **Comando**: `python scrapper.py --auto`
   - **Protecciones**: Máximas anti-duplicados
   - **Timeout**: 25 minutos (antes de la siguiente ejecución)

2. **🔍 Health Check**: `health-check.yml`
   - **Frecuencia**: Cada 2 horas
   - **Función**: Monitoreo de sistema y BD
   - **Verificaciones**: Conexión, registros recientes, actividad

3. **💾 Backup Scraper**: `nfl-scraper-hourly.yml`
   - **Frecuencia**: Cada 4 horas (backup)
   - **Función**: Respaldo del sistema principal
   - **Horario**: A los 45 minutos de cada 4 horas

## ⏰ Horarios de Ejecución (UTC)

### Scraper Principal (cada 30 minutos):
```
00:00, 00:30, 01:00, 01:30, 02:00, 02:30, ...
...continúa las 24 horas...
22:00, 22:30, 23:00, 23:30
```

### Health Check (cada 2 horas):
```
00:15, 02:15, 04:15, 06:15, 08:15, 10:15
12:15, 14:15, 16:15, 18:15, 20:15, 22:15
```

### Backup (cada 4 horas):
```
00:45, 04:45, 08:45, 12:45, 16:45, 20:45
```

## 🔧 Configuración Requerida

### 1. Secrets de GitHub
Configura estos secrets en tu repositorio:
- `SUPABASE_URL`: URL de tu proyecto Supabase
- `SUPABASE_KEY`: Clave anónima de Supabase

### 2. Campo Semana en Supabase
Ejecuta este SQL en tu base de datos:
```sql
ALTER TABLE nfl_fantasy_trends ADD COLUMN semana INTEGER DEFAULT 1;
CREATE INDEX idx_nfl_fantasy_trends_semana ON nfl_fantasy_trends(semana);
```

## 🎪 Funcionalidades del Sistema

### ✅ Detección Automática de Semana NFL
- Web scraping de fantasy.nfl.com
- Cálculo por fecha como fallback
- Comparaciones inteligentes por semana

### ✅ Sistema Anti-Duplicados
- Comparación individual por jugador
- Detección de cambios reales únicamente
- Validaciones pre y post-scraping

### ✅ Monitoreo Continuo
- Health checks automáticos
- Logs detallados en cada ejecución
- Sistema de backup redundante

## 📊 Volumen de Ejecuciones

### Por Día:
- **Scraper Principal**: 48 ejecuciones (cada 30 min)
- **Health Check**: 12 ejecuciones (cada 2 horas)
- **Backup**: 6 ejecuciones (cada 4 horas)
- **Total**: 66 ejecuciones por día

### Por Semana:
- **Scraper Principal**: 336 ejecuciones
- **Total General**: 462 ejecuciones

### Por Mes:
- **Scraper Principal**: ~1,440 ejecuciones
- **Total General**: ~1,980 ejecuciones

## 🔍 Monitoring y Debugging

### Logs en GitHub Actions:
- Cada workflow genera logs detallados
- Timestamps de inicio y fin
- Estadísticas de registros procesados
- Detección de errores automática

### Verificación Manual:
```bash
# Probar detección de semana
python scrapper.py --test-week

# Probar comparación individual
python scrapper.py --test-individual

# Ejecutar modo automático local
python scrapper.py --auto
```

## 🚨 Manejo de Errores

### Timeouts:
- Cada job tiene timeout de 25 minutos
- Permite completar antes de la siguiente ejecución

### Fallos de Red:
- Sistema de retry implícito en la siguiente ejecución
- Backup cada 4 horas como redundancia

### Fallos de BD:
- Health check detecta problemas de conexión
- Logs detallados para debugging

## 💡 Optimizaciones Implementadas

### 1. **Cache de Dependencias**
- Python dependencies cacheadas
- Instalación más rápida en ejecuciones subsecuentes

### 2. **Instalación Chrome Optimizada**
- Chrome estable instalado una vez por job
- Configuración headless para GitHub Actions

### 3. **Modo Auto Específico**
- Sin archivos locales en GitHub Actions
- Solo operaciones de BD críticas
- Validaciones de seguridad máximas

## 🎯 Resultados Esperados

### Primera Semana:
- Sistema detectará semana NFL actual
- Insertará baseline de jugadores
- Establecerá rutina de monitoreo

### Operación Normal:
- Solo cambios reales insertados
- 0-5% de jugadores con cambios típicos
- Transiciones de semana manejadas automáticamente

### Métricas de Éxito:
- **Uptime**: 99%+ (48 intentos por día)
- **Duplicados**: 0% (sistema anti-duplicados)
- **Cambios detectados**: 0-10% por ejecución
- **Tiempo de ejecución**: 5-15 minutos por scraping

---

## 🚀 Estado: LISTO PARA PRODUCCIÓN

El sistema está completamente configurado para operar 24/7 con:
- ✅ Detección automática de semanas NFL
- ✅ Protecciones anti-duplicados máximas  
- ✅ Monitoreo continuo y health checks
- ✅ Sistema de backup redundante
- ✅ Logging y debugging completo

**Próximo paso**: Commit y push para activar los workflows automáticos.
