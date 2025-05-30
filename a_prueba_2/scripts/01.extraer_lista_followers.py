#!/usr/bin/env python3
"""
Extractor Masivo Incremental de Seguidores de Instagram

Script principal para extraer seguidores de Instagram de forma masiva e incremental,
preservando datos anteriores y evitando duplicados.

Autor: Refactorizado para estructura modular
Fecha: 2024
"""

import sys
import os

# Añadir el directorio actual al path para importar módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import (
    COOKIES_FILE, USERNAME, TARGET_PROFILE, 
    NUM_THREADS, BLOCK_SIZE, MAX_ERRORS, DELAY_BETWEEN_BLOCKS
)
from modules.login import iniciar_sesion_con_cookies, validar_perfil
from modules.file_manager import (
    cargar_todos_los_seguidores_anteriores, 
    guardar_progreso_incremental,
    limpiar_archivos_antiguos,
    obtener_estadisticas_archivos
)
from modules.extraction import (
    extraer_seguidores_con_hilos,
    validar_perfil_antes_extraccion
)
from modules.utils import (
    ProgressTracker, SignalHandler, mostrar_configuracion, 
    mostrar_resumen_final, validar_configuracion
)

def main():
    """Función principal del extractor."""
    
    # Validar configuración
    if not validar_configuracion():
        print("❌ Configuración inválida. Revisa el archivo config.py")
        return 1
    
    # Mostrar configuración
    config_display = {
        "Perfil objetivo": f"@{TARGET_PROFILE}",
        "Hilos de trabajo": NUM_THREADS,
        "Tamaño de bloque": BLOCK_SIZE,
        "Máximo errores": MAX_ERRORS,
        "Pausa entre bloques": f"{DELAY_BETWEEN_BLOCKS}s"
    }
    mostrar_configuracion(config_display)
    
    # Mostrar estadísticas de archivos existentes
    stats_archivos = obtener_estadisticas_archivos(TARGET_PROFILE)
    if stats_archivos["total_archivos"] > 0:
        print("📊 Archivos existentes:")
        print(f"   • Total archivos: {stats_archivos['total_archivos']}")
        print(f"   • Archivos de progreso: {stats_archivos['archivos_progreso']}")
        print(f"   • Archivos finales: {stats_archivos['archivos_finales']}")
        if stats_archivos["ultimo_guardado"]:
            print(f"   • Último guardado: {stats_archivos['ultimo_guardado']}")
        print(f"   • Seguidores únicos acumulados: {stats_archivos['total_seguidores_unicos']:,}")
        print("=" * 60)
    
    input("⏳ Presiona ENTER para comenzar (Ctrl+C para detener en cualquier momento)...")
    
    # Inicializar tracker de progreso
    progress_tracker = ProgressTracker()
    progress_tracker.start_timer()
    
    # Configurar manejo de señales
    signal_handler = SignalHandler(progress_tracker)
    
    print(f"🚀 Iniciando extracción INCREMENTAL de seguidores de @{TARGET_PROFILE}")
    print("📋 Modo: AÑADIR usuarios nuevos (sin sobrescribir)")
    
    # Cargar seguidores anteriores
    seguidores_anteriores = cargar_todos_los_seguidores_anteriores(TARGET_PROFILE)
    progress_tracker.seguidores_obtenidos = seguidores_anteriores.copy()
    progress_tracker.set_inicio_desde(len(seguidores_anteriores))
    
    # Iniciar sesión
    print("🔐 Iniciando sesión...")
    loader = iniciar_sesion_con_cookies(COOKIES_FILE, USERNAME)
    if not loader:
        print("❌ No se pudo iniciar sesión. Verifica tus cookies.")
        return 1
    
    # Validar perfil
    print(f"🔍 Validando perfil @{TARGET_PROFILE}...")
    profile = validar_perfil(loader, TARGET_PROFILE)
    if not profile:
        print("❌ No se pudo acceder al perfil objetivo.")
        return 1
    
    # Verificar si vale la pena continuar
    if not validar_perfil_antes_extraccion(profile, progress_tracker):
        return 0
    
    # Comenzar extracción
    print("🎯 Comenzando extracción...")
    exito = extraer_seguidores_con_hilos(profile, progress_tracker, TARGET_PROFILE)
    
    # Guardar resultado final
    if progress_tracker.seguidores_obtenidos:
        archivo_final = guardar_progreso_incremental(
            progress_tracker.seguidores_obtenidos, 
            TARGET_PROFILE, 
            es_final=True
        )
        
        # Limpiar archivos de progreso antiguos
        limpiar_archivos_antiguos(TARGET_PROFILE)
        
        # Mostrar resumen final
        stats_finales = progress_tracker.get_stats()
        mostrar_resumen_final(stats_finales, archivo_final)
        
        return 0 if exito else 1
    else:
        print("❌ No se obtuvieron seguidores.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Proceso interrumpido por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)