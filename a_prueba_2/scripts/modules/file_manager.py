"""
Módulo para manejo de archivos y progreso de extracción.
"""

import json
import os
import glob
from datetime import datetime
from config import OUTPUTS_DIR

def guardar_progreso_incremental(seguidores_set, target_profile, es_final=False):
    """
    Guarda el progreso de forma incremental, siempre añadiendo usuarios nuevos.
    
    Args:
        seguidores_set (set): Conjunto de seguidores únicos
        target_profile (str): Perfil objetivo
        es_final (bool): Si es el guardado final
        
    Returns:
        str: Nombre del archivo guardado
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if es_final:
        filename = f"seguidores_{target_profile}_FINAL_{timestamp}.json"
    else:
        filename = f"seguidores_{target_profile}_progreso_{timestamp}.json"
    
    filepath = os.path.join(OUTPUTS_DIR, filename)
    
    data = {
        "perfil_objetivo": target_profile,
        "total_seguidores_obtenidos": len(seguidores_set),
        "fecha_extraccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "seguidores": sorted(list(seguidores_set)),  # Ordenados para mejor lectura
        "metadata": {
            "formato_version": "1.0",
            "extraccion_completa": es_final,
            "tipo_guardado": "incremental",
            "descripcion": "Lista acumulativa de usernames únicos de seguidores"
        }
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Guardado: {filename}")
    return filename

def cargar_todos_los_seguidores_anteriores(target_profile):
    """
    Carga TODOS los seguidores de todos los archivos anteriores (sin duplicados).
    
    Args:
        target_profile (str): Perfil objetivo
        
    Returns:
        set: Conjunto de seguidores únicos cargados
    """
    # Buscar todos los archivos de este perfil en el directorio de salida
    archivos_pattern = os.path.join(OUTPUTS_DIR, f"seguidores_{target_profile}_*.json")
    archivos_encontrados = glob.glob(archivos_pattern)
    
    if not archivos_encontrados:
        print("📂 No se encontraron archivos anteriores. Comenzando desde cero.")
        return set()
    
    seguidores_acumulados = set()
    archivos_leidos = 0
    
    print(f"📂 Encontrados {len(archivos_encontrados)} archivos anteriores...")
    
    for archivo in archivos_encontrados:
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                seguidores_del_archivo = set(data['seguidores'])
                
                # Contar solo los nuevos (no duplicados)
                nuevos_de_este_archivo = seguidores_del_archivo - seguidores_acumulados
                seguidores_acumulados.update(seguidores_del_archivo)
                
                if nuevos_de_este_archivo:
                    print(f"   ✅ {os.path.basename(archivo)}: +{len(nuevos_de_este_archivo)} nuevos seguidores")
                else:
                    print(f"   ⚪ {os.path.basename(archivo)}: sin seguidores nuevos")
                
                archivos_leidos += 1
                
        except Exception as e:
            print(f"   ❌ Error al leer {archivo}: {e}")
    
    print(f"📊 Resumen de carga:")
    print(f"   • Archivos procesados: {archivos_leidos}")
    print(f"   • Total seguidores únicos cargados: {len(seguidores_acumulados):,}")
    
    return seguidores_acumulados

def limpiar_archivos_antiguos(target_profile, mantener_ultimos=5):
    """
    Limpia archivos de progreso antiguos, manteniendo solo los más recientes.
    
    Args:
        target_profile (str): Perfil objetivo
        mantener_ultimos (int): Número de archivos de progreso a mantener
    """
    archivos_progreso = glob.glob(
        os.path.join(OUTPUTS_DIR, f"seguidores_{target_profile}_progreso_*.json")
    )
    
    if len(archivos_progreso) <= mantener_ultimos:
        return
    
    # Ordenar por fecha de modificación (más recientes primero)
    archivos_progreso.sort(key=os.path.getmtime, reverse=True)
    
    # Eliminar archivos antiguos
    archivos_a_eliminar = archivos_progreso[mantener_ultimos:]
    
    for archivo in archivos_a_eliminar:
        try:
            os.remove(archivo)
            print(f"🗑️ Eliminado archivo antiguo: {os.path.basename(archivo)}")
        except Exception as e:
            print(f"❌ Error al eliminar {archivo}: {e}")

def obtener_estadisticas_archivos(target_profile):
    """
    Obtiene estadísticas de los archivos existentes.
    
    Args:
        target_profile (str): Perfil objetivo
        
    Returns:
        dict: Estadísticas de archivos
    """
    archivos_pattern = os.path.join(OUTPUTS_DIR, f"seguidores_{target_profile}_*.json")
    archivos_encontrados = glob.glob(archivos_pattern)
    
    stats = {
        "total_archivos": len(archivos_encontrados),
        "archivos_progreso": 0,
        "archivos_finales": 0,
        "ultimo_guardado": None,
        "total_seguidores_unicos": 0
    }
    
    if not archivos_encontrados:
        return stats
    
    seguidores_unicos = set()
    archivo_mas_reciente = None
    fecha_mas_reciente = None
    
    for archivo in archivos_encontrados:
        if "_FINAL_" in archivo:
            stats["archivos_finales"] += 1
        else:
            stats["archivos_progreso"] += 1
        
        # Obtener fecha de modificación
        fecha_mod = os.path.getmtime(archivo)
        if fecha_mas_reciente is None or fecha_mod > fecha_mas_reciente:
            fecha_mas_reciente = fecha_mod
            archivo_mas_reciente = archivo
        
        # Cargar seguidores únicos
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                seguidores_unicos.update(data['seguidores'])
        except:
            continue
    
    stats["total_seguidores_unicos"] = len(seguidores_unicos)
    stats["ultimo_guardado"] = os.path.basename(archivo_mas_reciente) if archivo_mas_reciente else None
    
    return stats