# NFL Fantasy Football Trends Scraper

Un scraper en Python para extraer datos de tendencias de jugadores de fantasy football desde la página oficial de NFL Fantasy.

## 📋 Descripción

Este proyecto extrae automáticamente los datos de la tabla de tendencias de jugadores de fantasy football desde `https://fantasy.nfl.com/research/trends`. Los datos incluyen información sobre:

- Nombres de jugadores y posiciones
- Equipos
- Estadísticas de tendencias
- Porcentajes de rostros y inicios
- Datos de agregar/eliminar jugadores

## 🚀 Características

- **Scraping dinámico**: Utiliza Selenium para manejar contenido JavaScript
- **Parsing robusto**: BeautifulSoup para extraer datos de HTML
- **Múltiples formatos**: Exporta datos en CSV y JSON
- **Logging detallado**: Seguimiento completo del proceso
- **Manejo de errores**: Gestión robusta de excepciones
- **Configurable**: Opciones para modo headless y timeouts

## 🛠️ Instalación

### Prerrequisitos

1. **Python 3.8+** instalado en tu sistema
2. **Google Chrome** instalado
3. **ChromeDriver** (se puede instalar automáticamente)

### Pasos de instalación

1. **Clonar o descargar el proyecto**:
   ```bash
   cd "c:\Users\saavedra\Desktop\PROYECTO FANTASY"
   ```

2. **Crear un entorno virtual** (recomendado):
   ```bash
   python -m venv venv
   venv\Scripts\activate  # En Windows
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Instalar ChromeDriver** (opcional - se puede hacer automáticamente):
   ```bash
   pip install webdriver-manager
   ```

## 📖 Uso

### Uso básico

```python
from nfl_fantasy_scraper import NFLFantasyTrendsScraper

# Crear instancia del scraper
scraper = NFLFantasyTrendsScraper(headless=True)

# Ejecutar scraping
data = scraper.scrape()

# Los datos se guardan automáticamente en CSV y JSON
print(f"Extraídos {len(data)} registros")
```

### Ejecutar desde línea de comandos

```bash
python nfl_fantasy_scraper.py
```

### Opciones de configuración

```python
# Scraper con navegador visible (para debugging)
scraper = NFLFantasyTrendsScraper(headless=False, timeout=60)

# Solo guardar en CSV
data = scraper.scrape(save_csv=True, save_json=False)

# Solo extraer datos sin guardar
scraper = NFLFantasyTrendsScraper()
scraper.setup_driver()
scraper.load_page()
data = scraper.extract_table_data()
scraper.close()
```

## 📁 Estructura del proyecto

```
PROYECTO FANTASY/
├── .github/
│   └── copilot-instructions.md
├── .vscode/
│   └── tasks.json
├── nfl_fantasy_scraper.py      # Script principal
├── requirements.txt            # Dependencias
└── README.md                  # Este archivo
```

## 📊 Formato de datos

### Estructura de datos extraídos

Cada registro contiene:

```json
{
  "Column_1": "Nombre del jugador",
  "Column_2": "Posición y equipo",
  "Column_3": "Estadística 1",
  "Column_4": "Estadística 2",
  "table_index": 0,
  "row_index": 1,
  "scraped_at": "2025-01-28T10:30:45.123456"
}
```

### Archivos de salida

- **CSV**: `nfl_fantasy_trends_YYYYMMDD_HHMMSS.csv`
- **JSON**: `nfl_fantasy_trends_YYYYMMDD_HHMMSS.json`

## 🔧 Configuración avanzada

### Variables de entorno

Puedes configurar las siguientes variables de entorno:

```bash
# Tiempo de espera en segundos
SCRAPER_TIMEOUT=30

# Modo headless (true/false)
SCRAPER_HEADLESS=true
```

### Personalización del XPath

El scraper utiliza el XPath `//*[@id="bd"]` como se especificó. Si necesitas cambiarlo:

```python
# En la función extract_table_data(), línea 114
table_element = self.driver.find_element(By.XPATH, "tu_nuevo_xpath_aqui")
```

## 🚨 Solución de problemas

### Chrome/ChromeDriver no encontrado

```bash
# Instalar webdriver-manager para gestión automática
pip install webdriver-manager

# Agregar al código:
from webdriver_manager.chrome import ChromeDriverManager
service = Service(ChromeDriverManager().install())
self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
```

### Timeout al cargar la página

```python
# Aumentar el timeout
scraper = NFLFantasyTrendsScraper(timeout=60)
```

### Elementos no encontrados

- Verificar que la página esté cargada completamente
- Aumentar el tiempo de espera
- Ejecutar en modo no-headless para debug

## 📝 Registro de cambios

### v1.0.0 (2025-01-28)
- Implementación inicial del scraper
- Soporte para extracción de datos de tabla
- Exportación a CSV y JSON
- Logging y manejo de errores

## 📄 Licencia

Este proyecto es para uso educativo y de investigación. Asegúrate de cumplir con los términos de servicio de NFL.com.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Hacer fork del proyecto
2. Crear una rama para tu feature
3. Commit de tus cambios
4. Push a la rama
5. Abrir un Pull Request

## 📞 Soporte

Si encuentras problemas o tienes preguntas:

1. Revisa la sección de solución de problemas
2. Verifica que todas las dependencias estén instaladas
3. Asegúrate de que Chrome esté actualizado

---

**Nota**: Este scraper está diseñado específicamente para extraer datos de la tabla en `//*[@id="bd"]` de https://fantasy.nfl.com/research/trends. Si la estructura de la página cambia, puede ser necesario actualizar el código.
