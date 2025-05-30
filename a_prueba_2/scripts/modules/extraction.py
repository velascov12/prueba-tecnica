"""
Módulo principal para la extracción de seguidores de Instagram.
"""

import threading
import time
from queue import Queue

from config import (
    NUM_THREADS, BLOCK_SIZE, MAX_ERRORS, 
    DELAY_BETWEEN_BLOCKS, PROGRESS_SAVE_INTERVAL
)
from .file_manager import guardar_progreso_incremental

def procesar_bloque_seguidores(followers_iterator, thread_id, progress_tracker, target_profile):
    """
    Procesa un bloque de seguidores en un hilo.
    
    Args:
        followers_iterator: Iterador de seguidores de Instagram
        thread_id (int): ID del hilo
        progress_tracker (ProgressTracker): Tracker de progreso
        target_profile (str): Perfil objetivo
        
    Returns:
        int: Número de seguidores procesados en este bloque
    """
    bloque_actual = []
    
    try:
        # Obtener bloque de seguidores
        for i, seguidor in enumerate(followers_iterator):
            if progress_tracker.should_stop(MAX_ERRORS):
                break
                
            if i >= BLOCK_SIZE:
                break
                
            username = seguidor.username
            bloque_actual.append(username)
        
        # Añadir seguidores al tracker
        if bloque_actual:
            added = progress_tracker.add_seguidores(bloque_actual)
            stats = progress_tracker.get_stats()
            
            print(f"🧵 Hilo-{thread_id}: +{added} seguidores | Total: {stats['total_seguidores']}")
            
            # Guardar progreso incremental cada PROGRESS_SAVE_INTERVAL seguidores
            if stats['total_seguidores'] % PROGRESS_SAVE_INTERVAL == 0:
                archivo_progreso = guardar_progreso_incremental(
                    progress_tracker.seguidores_obtenidos, 
                    target_profile
                )
                print(f"📈 Nuevos usuarios únicos en esta sesión: {stats['nuevos_en_sesion']:,}")
        
        # Reset errores si el bloque fue exitoso
        if bloque_actual:
            progress_tracker.reset_errors()
        
        return len(bloque_actual)
        
    except Exception as e:
        progress_tracker.add_error()
        stats = progress_tracker.get_stats()
        
        print(f"❌ Hilo-{thread_id} Error: {str(e)} | Errores consecutivos: {stats['errores_consecutivos']}")
        
        if stats['errores_consecutivos'] >= MAX_ERRORS:
            print(f"🛑 Demasiados errores ({MAX_ERRORS}). Deteniendo extracción...")
            progress_tracker.signal_stop()
        
        return 0

def worker_thread(followers_iterator, thread_id, progress_tracker, target_profile):
    """
    Función trabajadora para cada hilo.
    
    Args:
        followers_iterator: Iterador de seguidores
        thread_id (int): ID del hilo
        progress_tracker (ProgressTracker): Tracker de progreso
        target_profile (str): Perfil objetivo
    """
    while not progress_tracker.should_stop(MAX_ERRORS):
        try:
            # Procesar bloque
            seguidores_procesados = procesar_bloque_seguidores(
                followers_iterator, thread_id, progress_tracker, target_profile
            )
            
            if seguidores_procesados == 0:
                break
            
            # Pausa entre bloques para no saturar
            time.sleep(DELAY_BETWEEN_BLOCKS)
            
        except Exception as e:
            print(f"❌ Error en hilo-{thread_id}: {e}")
            break

def extraer_seguidores_con_hilos(profile, progress_tracker, target_profile):
    """
    Extrae seguidores usando múltiples hilos.
    
    Args:
        profile: Perfil de Instagram
        progress_tracker (ProgressTracker): Tracker de progreso
        target_profile (str): Perfil objetivo
        
    Returns:
        bool: True si la extracción fue exitosa
    """
    try:
        # Obtener iterador de seguidores
        followers_iterator = profile.get_followers()
        
        print("🔄 Modo incremental: revisando todos los seguidores para encontrar nuevos...")
        
        # Crear hilos de trabajo
        threads = []
        
        print(f"🧵 Iniciando {NUM_THREADS} hilos de trabajo...")
        
        for thread_id in range(NUM_THREADS):
            thread = threading.Thread(
                target=worker_thread,
                args=(followers_iterator, thread_id + 1, progress_tracker, target_profile)
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Esperar a que terminen los hilos
        for thread in threads:
            thread.join()
        
        return True
        
    except Exception as e:
        print(f"❌ Error en extracción con hilos: {e}")
        return False

def extraer_seguidores_simple(profile, progress_tracker, target_profile):
    """
    Extrae seguidores usando un solo hilo (modo simple).
    
    Args:
        profile: Perfil de Instagram
        progress_tracker (ProgressTracker): Tracker de progreso
        target_profile (str): Perfil objetivo
        
    Returns:
        bool: True si la extracción fue exitosa
    """
    try:
        followers_iterator = profile.get_followers()
        
        print("🔄 Modo simple: extrayendo seguidores...")
        
        while not progress_tracker.should_stop(MAX_ERRORS):
            seguidores_procesados = procesar_bloque_seguidores(
                followers_iterator, 1, progress_tracker, target_profile
            )
            
            if seguidores_procesados == 0:
                break
            
            time.sleep(DELAY_BETWEEN_BLOCKS)
        
        return True
        
    except Exception as e:
        print(f"❌ Error en extracción simple: {e}")
        return False

def validar_perfil_antes_extraccion(profile, progress_tracker):
    """
    Valida el perfil antes de comenzar la extracción.
    
    Args:
        profile: Perfil de Instagram
        progress_tracker (ProgressTracker): Tracker de progreso
        
    Returns:
        bool: True si se debe continuar con la extracción
    """
    stats = progress_tracker.get_stats()
    inicio_desde = progress_tracker.inicio_desde
    
    print(f"📊 Total de seguidores del perfil: {profile.followers:,}")
    print(f"📊 Ya tenemos únicos: {inicio_desde:,} seguidores")
    
    if profile.followers > 0:
        porcentaje_obtenido = (inicio_desde / profile.followers) * 100
        print(f"📊 Progreso actual: {porcentaje_obtenido:.2f}% del perfil")
        
        if inicio_desde >= profile.followers:
            print("🎉 ¡Ya tienes todos los seguidores posibles de este perfil!")
            return False
    
    return True