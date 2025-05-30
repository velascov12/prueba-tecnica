# --- Configuración Global ---
"""
Archivo de configuración central para el extractor de seguidores de Instagram.
"""

import os

# Configuración de autenticación
COOKIES_FILE = "cookies_instagram.json"
USERNAME = "rpadev.py@gmail.com"

# Configuración del objetivo
TARGET_PROFILE = "elcorteingles"

# Configuración de extracción
NUM_THREADS = 2  # Solo 2-3 hilos para no sobrecargar
BLOCK_SIZE = 100  # Seguidores por bloque
MAX_ERRORS = 10   # Máximo errores antes de parar
DELAY_BETWEEN_BLOCKS = 5  # Segundos entre bloques

# Configuración de archivos
OUTPUTS_DIR = "outputs"
PROGRESS_SAVE_INTERVAL = 1000  # Guardar progreso cada X seguidores

# Configuración de logs
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Crear directorio de salida si no existe
if not os.path.exists(OUTPUTS_DIR):
    os.makedirs(OUTPUTS_DIR)