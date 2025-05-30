"""
Utilidades comunes para el extractor de seguidores.
"""

import signal
import sys
import threading
import time
from datetime import datetime

class ProgressTracker:
    """Clase para seguimiento del progreso de extracción."""
    
    def __init__(self):
        self.seguidores_obtenidos = set()
        self.total_procesados = 0
        self.errores_consecutivos = 0
        self.stop_signal = False
        self.lock = threading.Lock()
        self.inicio_desde = 0
        self.start_time = None
    
    def set_inicio_desde(self, cantidad):
        """Establece la cantidad inicial de seguidores."""
        self.inicio_desde = cantidad
    
    def start_timer(self):
        """Inicia el cronómetro."""
        self.start_time = time.time()
    
    def get_elapsed_time(self):
        """Obtiene el tiempo transcurrido en minutos."""
        if self.start_time is None:
            return 0
        return (time.time() - self.start_time) / 60
    
    def add_seguidores(self, nuevos_seguidores):
        """Añade nuevos seguidores de forma thread-safe."""
        with self.lock:
            added = 0
            for seguidor in nuevos_seguidores:
                if seguidor not in self.seguidores_obtenidos:
                    self.seguidores_obtenidos.add(seguidor)
                    added += 1
            self.total_procesados += added
            return added
    
    def add_error(self):
        """Incrementa el contador de errores consecutivos."""
        with self.lock:
            self.errores_consecutivos += 1
    
    def reset_errors(self):
        """Resetea el contador de errores consecutivos."""
        with self.lock:
            self.errores_consecutivos = 0
    
    def should_stop(self, max_errors):
        """Verifica si se debe detener la extracción."""
        with self.lock:
            return self.stop_signal or self.errores_consecutivos >= max_errors
    
    def signal_stop(self):
        """Señala que se debe detener la extracción."""
        with self.lock:
            self.stop_signal = True
    
    def get_stats(self):
        """Obtiene estadísticas actuales."""
        with self.lock:
            return {
                "total_seguidores": len(self.seguidores_obtenidos),
                "nuevos_en_sesion": len(self.seguidores_obtenidos) - self.inicio_desde,
                "errores_consecutivos": self.errores_consecutivos,
                "tiempo_transcurrido": self.get_elapsed_time()
            }

class SignalHandler:
    """Manejo de señales para parada limpia."""
    
    def __init__(self, progress_tracker):
        self.progress_tracker = progress_tracker
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """Maneja Ctrl+C para parada limpia."""
        print("\n⚠️ Deteniendo proceso... Guardando datos actuales...")
        self.progress_tracker.signal_stop()

def mostrar_configuracion(config_dict):
    """
    Muestra la configuración actual de forma organizada.
    
    Args:
        config_dict (dict): Diccionario con la configuración
    """
    print("=" * 60)
    print("🎯 EXTRACTOR MASIVO INCREMENTAL DE SEGUIDORES")
    print("=" * 60)
    print("📋 Características:")
    print("   ✅ Nunca sobrescribe - solo añade usuarios nuevos")
    print("   ✅ Combina todos los archivos anteriores")
    print("   ✅ Elimina duplicados automáticamente")
    print("   ✅ Continúa desde cualquier punto")
    print("=" * 60)
    print(f"📋 Configuración:")
    for key, value in config_dict.items():
        print(f"   • {key}: {value}")
    print("=" * 60)

def mostrar_resumen_final(stats, archivo_final=None):
    """
    Muestra el resumen final de la extracción.
    
    Args:
        stats (dict): Estadísticas finales
        archivo_final (str): Nombre del archivo final
    """
    print(f"\n🎉 Extracción incremental finalizada!")
    print(f"📊 Total seguidores únicos acumulados: {stats['total_seguidores']:,}")
    print(f"📈 Nuevos usuarios añadidos en esta sesión: {stats['nuevos_en_sesion']:,}")
    print(f"⏱️ Tiempo total: {stats['tiempo_transcurrido']:.2f} minutos")
    
    if archivo_final:
        print(f"💾 Archivo final: {archivo_final}")
    
    if stats['nuevos_en_sesion'] == 0:
        print("ℹ️ No se encontraron usuarios nuevos. El perfil puede no haber cambiado.")

def calcular_progreso_perfil(seguidores_actuales, total_seguidores_perfil):
    """
    Calcula el porcentaje de progreso respecto al perfil completo.
    
    Args:
        seguidores_actuales (int): Seguidores obtenidos actualmente
        total_seguidores_perfil (int): Total de seguidores del perfil
        
    Returns:
        float: Porcentaje de progreso
    """
    if total_seguidores_perfil == 0:
        return 0.0
    return (seguidores_actuales / total_seguidores_perfil) * 100

def formatear_numero(numero):
    """
    Formatea un número con separadores de miles.
    
    Args:
        numero (int): Número a formatear
        
    Returns:
        str: Número formateado
    """
    return f"{numero:,}"

def validar_configuracion():
    """
    Valida que la configuración sea correcta.
    
    Returns:
        bool: True si la configuración es válida
    """
    from config import (
        COOKIES_FILE, USERNAME, TARGET_PROFILE, 
        NUM_THREADS, BLOCK_SIZE, MAX_ERRORS, DELAY_BETWEEN_BLOCKS
    )
    
    validaciones = [
        (COOKIES_FILE, "Archivo de cookies no especificado"),
        (USERNAME, "Nombre de usuario no especificado"),
        (TARGET_PROFILE, "Perfil objetivo no especificado"),
        (NUM_THREADS > 0, "Número de hilos debe ser mayor a 0"),
        (BLOCK_SIZE > 0, "Tamaño de bloque debe ser mayor a 0"),
        (MAX_ERRORS > 0, "Máximo de errores debe ser mayor a 0"),
        (DELAY_BETWEEN_BLOCKS >= 0, "Delay entre bloques debe ser mayor o igual a 0")
    ]
    
    for condicion, mensaje in validaciones:
        if not condicion:
            print(f"❌ Error de configuración: {mensaje}")
            return False
    
    return True