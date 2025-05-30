# Extractor Masivo Incremental de Seguidores de Instagram

Un script robusto y modular para extraer seguidores de Instagram de forma masiva, incremental y sin duplicados.

## 🚀 Características

- ✅ **Incremental**: Nunca sobrescribe datos, solo añade usuarios nuevos
- ✅ **Sin duplicados**: Combina todos los archivos anteriores eliminando duplicados
- ✅ **Resistente a interrupciones**: Continúa desde cualquier punto
- ✅ **Multi-hilo**: Extracción paralela para mayor eficiencia
- ✅ **Progreso automático**: Guardado incremental cada 1000 seguidores
- ✅ **Manejo de errores**: Control robusto de errores y reconexiones
- ✅ **Estructura modular**: Código organizado y mantenible

## 📁 Estructura del Proyecto

```
extractor_seguidores/
│
├── extraer_lista_followers.py                  # Script principal (punto de entrada)
├── config.py                # Configuraciones globales
├── README.md                # Este archivo
├── requirements.txt         # Dependencias
│
├── modules/
│   ├── __init__.py
│   ├── login.py             # Manejo de autenticación y cookies
│   ├── file_manager.py      # Manejo de archivos y progreso
│   ├── extraction.py        # Lógica de extracción de seguidores
│   └── utils.py             # Utilidades comunes
│
└── outputs/                 # Directorio para archivos de salida
```

## 🛠️ Instalación

1. **Clona o descarga el proyecto**
2. **Instala las dependencias**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configura tus cookies de Instagram** (ver sección de configuración)

## ⚙️ Configuración

### 1. Archivo de Cookies

Necesitas un archivo `cookies_instagram.json` con tus cookies de Instagram. Puedes obtenerlas:

1. Ve a Instagram en tu navegador
2. Abre las herramientas de desarrollador (F12)
3. Ve a la pestaña "Application" > "Cookies" > "https://www.instagram.com"
4. Exporta las cookies en formato JSON

### 2. Configuración Principal

Edita `config.py` con tus parámetros:

```python
# Configuración de autenticación
USERNAME = "tu_usuario@email.com"
TARGET_PROFILE = "perfil_objetivo"

# Configuración de extracción
NUM_THREADS = 2          # Número de hilos (recomendado: 2-3)
BLOCK_SIZE = 100         # Seguidores por bloque
MAX_ERRORS = 10          # Máximo errores antes de parar
DELAY_BETWEEN_BLOCKS = 5 # Segundos entre bloques
```

## 🚀 Uso

### Ejecución Básica

```bash
python extraer_lista_followers.py
```

### Lo que hace el script:

1. **Carga datos anteriores**: Busca y combina todos los archivos previos
2. **Muestra estadísticas**: Información sobre archivos existentes y progreso
3. **Inicia sesión**: Usa las cookies para autenticarse
4. **Valida el perfil**: Verifica que el perfil sea accesible
5. **Extrae seguidores**: Usa múltiples hilos para extraer de forma eficiente
6. **Guarda progreso**: Guardado automático cada 1000 seguidores
7. **Limpia archivos**: Elimina archivos de progreso antiguos

## 📊 Archivos de Salida

### Tipos de Archivos

- **Progreso**: `seguidores_PERFIL_progreso_TIMESTAMP.json`
- **Final**: `seguidores_PERFIL_FINAL_TIMESTAMP.json`

### Estructura del JSON

```json
{
  "perfil_objetivo": "perfil_ejemplo",
  "total_seguidores_obtenidos": 15420,
  "fecha_extraccion": "2024-01-15 14:30:25",
  "seguidores": ["usuario1", "usuario2", "..."],
  "metadata": {
    "formato_version": "1.0",
    "extraccion_completa": true,
    "tipo_guardado": "incremental"
  }
}
```

## 🔧 Características Técnicas

### Control de Errores

- Reintentos automáticos
- Control de errores consecutivos
- Parada limpia con Ctrl+C

### Optimizaciones

- Extracción multi-hilo
- Delays configurables para evitar rate limits
- Guardado incremental para evitar pérdida de datos

### Gestión de Memoria

- Uso eficiente de sets para duplicados
- Limpieza automática de archivos antiguos
- Threading seguro con locks

## 📋 Comandos Útiles

### Ver estadísticas sin ejecutar

Puedes modificar `main.py` para solo mostrar estadísticas:

```python
# Comentar la línea de input() y la extracción
stats = obtener_estadisticas_archivos(TARGET_PROFILE)
print(f"Total seguidores únicos: {stats['total_seguidores_unicos']:,}")
```

### Limpiar archivos antiguos

```python
from modules.file_manager import limpiar_archivos_antiguos
limpiar_archivos_antiguos("perfil_objetivo", mantener_ultimos=3)
```

## ⚠️ Precauciones

1. **Rate Limits**: Instagram tiene límites de requests. El script incluye delays automáticos.
2. **Cookies válidas**: Asegúrate de que tus cookies no estén expiradas.
3. **Perfiles privados**: Solo funciona con perfiles públicos o que sigas.
4. **Uso responsable**: Respeta los términos de servicio de Instagram.

## 🐛 Resolución de Problemas

### Error: Archivo de cookies no encontrado
- Verifica que `cookies_instagram.json` esté en el directorio raíz
- Asegúrate de que el formato JSON sea válido

### Error: No se pudo iniciar sesión
- Cookies expiradas: obtén cookies nuevas
- Verifica que el username en config.py sea correcto

### Pocos seguidores obtenidos
- Aumenta `DELAY_BETWEEN_BLOCKS` para evitar rate limits
- Reduce `NUM_THREADS` a 1 para ser más conservador

### Error: Perfil privado
- Solo puedes extraer seguidores de perfiles públicos
- Si sigues al perfil privado, debería funcionar

## 📈 Monitoreo del Progreso

El script muestra información en tiempo real:

```
🧵 Hilo-1: +87 seguidores | Total: 12,847
🧵 Hilo-2: +92 seguidores | Total: 12,939
💾 Progreso incremental guardado: seguidores_perfil_progreso_20240115_143025.json
📈 Nuevos usuarios únicos en esta sesión: 2,456
```

## 🔄 Continuación Automática

El script es 100% incremental:
- Si se interrumpe, continúa desde donde se quedó
- Nunca pierde datos anteriores
- Combina automáticamente todos los archivos previos

