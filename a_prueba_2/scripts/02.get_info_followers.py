from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import os
import time
import random
import pandas as pd
from datetime import datetime
import signal
import re
import undetected_chromedriver as uc

import requests
from fake_useragent import UserAgent

# --- CONFIGURACIÓN AVANZADA ---
USERNAME = "rpadev.py@gmail.com"
PASSWORD = "3115674080"
INPUT_JSON = "seguidores.json"
RESUME_FILE = "seguidores_datos_RESUMIBLE.xlsx"
OUTPUT_EXCEL = f"seguidores_datos_EXTRAIDOS_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
MAX_USUARIOS = 200  # Reducido para ser más cauteloso
MAX_ERRORS = 5
WAIT_TIME = 5  # Aumentado para mayor seguridad

# Variables globales para control
stop_signal = False
errores_consecutivos = 0
session_requests = 0
MAX_SESSION_REQUESTS = 100  # Límite de requests por sesión


def extraer_nombre_completo(driver, username=""):
    """
    Extrae el nombre completo del perfil de Instagram, priorizando la primera línea de la biografía,
    y con validaciones para evitar capturar números u otros datos irrelevantes.
    """
    import re
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.by import By

    # Paso 1: Intentar extraer desde la biografía (primer bloque visible de texto sin "@" y sin números)
    try:
        print("🔍 Intentando extraer nombre desde la biografía...")
        bio_selector = "//div[contains(@class,'-vDIg') or contains(@class, 'x7a106z')]/div"
        bloques_bio = driver.find_elements(By.XPATH, bio_selector)

        for bloque in bloques_bio:
            lineas = bloque.text.strip().split('\n')
            for linea in lineas:
                linea_limpia = linea.strip()
                if (
                    linea_limpia
                    and len(linea_limpia) > 1
                    and not linea_limpia.startswith("@")
                    and not re.match(r"^\d+\s*(posts|followers|following|publicaciones|seguidores|seguidos)?$", linea_limpia.lower())
                    and not linea_limpia.replace(" ", "").isdigit()
                    and not any(palabra in linea_limpia.lower() for palabra in [
                        'posts', 'followers', 'following',
                        'publicaciones', 'seguidores', 'seguidos'
                    ])
                ):
                    print(f"✅ Nombre completo encontrado en bio: '{linea_limpia}'")
                    return linea_limpia
    except Exception as e:
        print(f"⚠️ Error extrayendo desde bio: {e}")

    # Paso 2: Buscar por selectores visuales
    print("🔍 Buscando nombre por otros selectores...")
    selectores_nombre = [
        "//span[contains(@class, 'x1lliihq') and string-length(text()) > 1 and not(contains(text(), '@'))]",
        "//header//h2[string-length(text()) > 0 and not(contains(@class, 'username'))]",
        "//div[contains(@class, 'x7a106z')]//h2",
        "//section//h2[not(contains(text(), '@'))]",
        "//div[@data-testid='user-name']//h2",
        "//header//div//h2[string-length(text()) > 0]",
        "//h2[@class and string-length(text()) > 0 and not(contains(text(), '@'))]",
        "//div[contains(@class, 'x78zum5')]//h2[string-length(text()) > 0]",
        "//h2[string-length(text()) > 0 and string-length(text()) < 100]"
    ]

    username = username.lower()

    for i, selector in enumerate(selectores_nombre):
        try:
            print(f"🔍 Probando selector de nombre {i + 1}...")
            elementos = driver.find_elements(By.XPATH, selector)

            for elemento in elementos:
                nombre = elemento.text.strip()

                if (
                    nombre
                    and len(nombre) > 1
                    and len(nombre) < 100
                    and not nombre.startswith('@')
                    and nombre.lower() != username
                    and not nombre.replace(" ", "").isdigit()
                    and not any(palabra in nombre.lower() for palabra in [
                        'posts', 'followers', 'following',
                        'publicaciones', 'seguidores', 'seguidos'
                    ])
                    and not re.match(r"^\d+\s+(posts|followers|following|publicaciones|seguidores|seguidos)$", nombre.lower())
                    and not re.match(r"^\d+\s*$", nombre)
                ):
                    print(f"✅ Nombre completo encontrado con selector {i + 1}: '{nombre}'")
                    return nombre

        except NoSuchElementException:
            continue
        except Exception as e:
            print(f"⚠️ Error en selector {i + 1}: {e}")
            continue

    # Paso 3: Fallback con regex
    print("🔍 Intentando método alternativo con regex...")
    try:
        page_source = driver.page_source
        patrones_nombre = [
            r'"full_name":"([^"]+)"',
            r'"fullName":"([^"]+)"',
            r'full_name":\s*"([^"]+)"',
            r'"name":"([^"@]+)"'
        ]

        for patron in patrones_nombre:
            matches = re.findall(patron, page_source)
            for match in matches:
                if match and len(match) > 1 and not match.startswith('@'):
                    try:
                        nombre_limpio = match.encode().decode('unicode_escape')
                        print(f"✅ Nombre encontrado por regex: '{nombre_limpio}'")
                        return nombre_limpio
                    except:
                        return match

    except Exception as e:
        print(f"⚠️ Error en método regex: {e}")

    print("⚠️ No se pudo extraer el nombre completo")
    return "N/A"

def extraer_username_y_nombre(driver):
    """Extrae tanto el username como el nombre completo del perfil"""
    try:
        # Extraer username desde la URL
        current_url = driver.current_url
        username_from_url = current_url.split('/')[-2] if current_url.endswith('/') else current_url.split('/')[-1]
        username = username_from_url.split('?')[0].lower()

        print(f"👤 Username extraído de URL: @{username}")

        # Pasar el username para evitar confusión en validación del nombre
        nombre_completo = extraer_nombre_completo(driver, username=username)

        return {
            "username": username,
            "nombre_completo": nombre_completo
        }

    except Exception as e:
        print(f"❌ Error extrayendo username y nombre: {e}")
        return {
            "username": "N/A",
            "nombre_completo": "N/A"
        }



def signal_handler(sig, frame):
    global stop_signal
    print("\n⚠️ Interrupción detectada. Guardando progreso...")
    stop_signal = True


signal.signal(signal.SIGINT, signal_handler)


def obtener_user_agent_aleatorio():
    """Genera un User-Agent aleatorio realista"""
    ua = UserAgent()
    return ua.random


def configurar_driver_stealth():
    """Configura driver con máxima capacidad anti-detección"""
    try:
        # Usar undetected-chromedriver (más efectivo que Selenium normal)
        options = uc.ChromeOptions()

        # Configuración de perfil real
        perfil_path = "C:\\Users\\57314\\AppData\\Local\\Google\\Chrome\\User Data"
        options.add_argument(f"--user-data-dir={perfil_path}")
        options.add_argument("--profile-directory=Default")

        # Anti-detección avanzada
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions-file-access-check")
        options.add_argument("--disable-extensions-http-throttling")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-features=VizDisplayCompositor")

        # Simular comportamiento humano en viewport
        options.add_argument("--window-size=1366,768")  # Resolución común

        # User agent aleatorio
        user_agent = obtener_user_agent_aleatorio()
        options.add_argument(f"--user-agent={user_agent}")

        # Configuraciones experimentales anti-detección
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)

        # Configurar preferencias para parecer más humano
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2,  # Deshabilitar imágenes para ir más rápido
            "profile.default_content_setting_values.geolocation": 2
        }
        options.add_experimental_option("prefs", prefs)

        # FIX: Crear driver con undetected-chromedriver sin version_main deprecated
        try:
            driver = uc.Chrome(options=options)
        except Exception as e:
            print(f"⚠️ Error con undetected_chromedriver: {e}")
            print("🔄 Intentando con ChromeDriver estándar...")
            # Fallback a ChromeDriver estándar
            driver = webdriver.Chrome(options=options)

        # Scripts adicionales anti-detección
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en', 'es']})")
        driver.execute_script("window.chrome = { runtime: {} }")

        return driver

    except Exception as e:
        print(f"❌ Error configurando driver: {e}")
        print("🔄 Intentando configuración básica...")
        # Configuración básica de fallback
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        return webdriver.Chrome(options=options)


def comportamiento_humano_avanzado(driver):
    """Simula comportamiento humano más realista"""
    try:
        actions = ActionChains(driver)

        # Movimientos de mouse aleatorios
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            actions.move_by_offset(x, y)
            time.sleep(random.uniform(0.5, 1.5))

        # Scroll aleatorio
        if random.choice([True, False]):
            driver.execute_script(f"window.scrollTo(0, {random.randint(100, 500)});")
            time.sleep(random.uniform(1, 2))

        actions.perform()
    except Exception as e:
        print(f"⚠️ Error en comportamiento humano: {e}")


def typing_humano(element, text):
    """Escribe texto de manera más humana con pausas variables"""
    try:
        element.clear()
        time.sleep(random.uniform(0.5, 1))

        for char in text:
            element.send_keys(char)
            # Pausas variables más realistas
            if char == '@' or char == '.':
                time.sleep(random.uniform(0.2, 0.4))  # Pausa más larga en caracteres especiales
            else:
                time.sleep(random.uniform(0.05, 0.2))

            # Errores ocasionales de tipeo (backspace)
            if random.random() < 0.02:  # 2% probabilidad de error
                time.sleep(random.uniform(0.1, 0.3))
                element.send_keys(Keys.BACK_SPACE)
                time.sleep(random.uniform(0.1, 0.2))
                element.send_keys(char)
    except Exception as e:
        print(f"⚠️ Error en typing humano: {e}")


def iniciar_sesion_stealth(driver, username, password):
    """Inicio de sesión con comportamiento humano avanzado"""
    global session_requests

    try:
        print("🔐 Iniciando sesión stealth en Instagram...")

        # Visitar la página principal primero (comportamiento humano)
        driver.get("https://www.instagram.com/")
        time.sleep(random.uniform(3, 6))
        comportamiento_humano_avanzado(driver)

        # Ir a login
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(random.uniform(4, 7))

        # Esperar campos de login
        username_field = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_field = driver.find_element(By.NAME, "password")

        # Simular comportamiento antes de escribir
        comportamiento_humano_avanzado(driver)

        # Focus en campo usuario con click
        username_field.click()
        time.sleep(random.uniform(0.5, 1.2))

        # Escribir usuario de forma humana
        typing_humano(username_field, username)
        time.sleep(random.uniform(1, 2.5))

        # Click en campo contraseña
        password_field.click()
        time.sleep(random.uniform(0.3, 0.8))

        # Escribir contraseña
        typing_humano(password_field, password)
        time.sleep(random.uniform(1.5, 3))

        # Comportamiento humano antes de enviar
        comportamiento_humano_avanzado(driver)

        # Enviar formulario
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        session_requests += 1

        # Espera larga después del login
        time.sleep(random.uniform(8, 12))

        # Manejar posibles captchas o verificaciones
        if any(keyword in driver.page_source.lower() for keyword in
               ['captcha', 'recaptcha', 'verificar', 'confirm', 'challenge']):
            print("🤖 Verificación detectada - manejando manualmente...")
            manejar_verificacion(driver)

        # Manejar diálogos post-login
        manejar_dialogos_post_login(driver)

        # Verificar éxito del login
        time.sleep(5)
        if "instagram.com" in driver.current_url and "login" not in driver.current_url:
            print("✅ Sesión iniciada correctamente")
            return True
        else:
            print("❌ Error al iniciar sesión")
            return False

    except Exception as e:
        print(f"❌ Error en el proceso de login: {e}")
        return False


def manejar_verificacion(driver):
    """Maneja verificaciones y captchas"""
    print("🔐 Verificación detectada:")
    print("1. Resuelve cualquier captcha o verificación en el navegador")
    print("2. Completa el proceso manualmente")
    print("3. Presiona ENTER cuando hayas terminado...")

    input("Presiona ENTER después de completar la verificación: ")
    time.sleep(random.uniform(3, 6))


def manejar_dialogos_post_login(driver):
    """Maneja diálogos que aparecen después del login"""
    dialogos_posibles = [
        "//button[contains(text(), 'Ahora no') or contains(text(), 'Not Now')]",
        "//button[contains(text(), 'Cancelar') or contains(text(), 'Cancel')]",
        "//button[@aria-label='Close' or @aria-label='Cerrar']"
    ]

    for xpath in dialogos_posibles:
        try:
            boton = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            time.sleep(random.uniform(1, 2))
            boton.click()
            time.sleep(random.uniform(2, 4))
            print("📝 Diálogo cerrado")
        except TimeoutException:
            continue


def obtener_info_usuario_stealth(driver, username):
    """Extrae información de usuario con técnicas anti-detección"""
    global session_requests

    try:
        print(f"🔍 Analizando perfil de @{username}...")

        # Control de límite de requests por sesión
        if session_requests >= MAX_SESSION_REQUESTS:
            print("⚠️ Límite de requests alcanzado. Reiniciando sesión...")
            return "RESTART_SESSION"

        # Comportamiento humano antes de navegar
        if random.random() < 0.3:  # 30% probabilidad
            comportamiento_humano_avanzado(driver)

        # Navegar al perfil
        profile_url = f"https://www.instagram.com/{username}/"
        driver.get(profile_url)
        session_requests += 1

        # Espera variable más larga
        tiempo_espera = random.uniform(4, 8)
        print(f"⏳ Esperando {tiempo_espera:.1f}s para que cargue el perfil...")
        time.sleep(tiempo_espera)

        # Verificar si el perfil existe
        if any(keyword in driver.page_source.lower() for keyword in
               ['sorry', 'not available', 'no disponible', 'lo sentimos', 'user not found']):
            print(f"⚠️ Perfil @{username} no encontrado")
            return None

        # Comportamiento humano en el perfil
        if random.random() < 0.4:  # 40% probabilidad
            scroll_amount = random.randint(200, 600)
            driver.execute_script(f"window.scrollTo(0, {scroll_amount});")
            time.sleep(random.uniform(1, 3))
            driver.execute_script("window.scrollTo(0, 0);")  # Volver arriba
            time.sleep(random.uniform(0.5, 1.5))

        # Extraer información paso a paso
        print(f"📊 Extrayendo información de @{username}...")

        # Inicializar info - CORREGIDO: username vs nombre completo
        info = {
            "Usuario": username,  # Este es el @username
            "Nombre completo": "N/A",  # Este será el display name
            "Email": "N/A",
            "Teléfono": "N/A",
            "Fecha primer post": "N/A",
            "Antigüedad estimada": "N/A",
            "Privado": False
        }

        # Extraer nombre completo CORRECTAMENTE
        print("🏷️ Extrayendo nombre completo (display name)...")
        usuario_info = extraer_username_y_nombre(driver)
        info["Nombre completo"] = usuario_info["nombre_completo"]

        # Verificar que estamos en el perfil correcto
        if usuario_info["username"].lower() != username.lower():
            print(f"⚠️ Advertencia: Username esperado (@{username}) vs encontrado (@{usuario_info['username']})")

        # Verificar si es privada
        print("🔒 Verificando si la cuenta es privada...")
        info["Privado"] = verificar_cuenta_privada(driver)

        # Extraer biografía y contactos
        print("📝 Extrayendo biografía...")
        biografia = extraer_biografia(driver)
        if biografia:
            print(f"✅ Biografía encontrada: '{biografia[:100]}...'")
            email, telefono = extraer_contacto_desde_bio(biografia)
            if email:
                info["Email"] = email
                print(f"📧 Email encontrado: {email}")
            if telefono:
                info["Teléfono"] = telefono
                print(f"📞 Teléfono encontrado: {telefono}")

        # Solo intentar obtener fecha si no es privada
        if not info["Privado"]:
            print("📅 Intentando obtener fecha del primer post...")
            fecha_info = obtener_fecha_primer_post_stealth(driver)
            if fecha_info:
                info["Fecha primer post"] = fecha_info.get("fecha", "N/A")
                info["Antigüedad estimada"] = fecha_info.get("antiguedad", "N/A")
                print(f"📅 Primer post: {info['Fecha primer post']}")
                print(f"⏰ Antigüedad: {info['Antigüedad estimada']}")
        else:
            print("🔒 Cuenta privada - no se puede obtener fecha del primer post")

        # Mostrar resumen de información extraída - MEJORADO
        print(f"\n📋 RESUMEN DE @{username}:")
        print(f"   👤 Username: @{username}")
        print(f"   🏷️ Nombre completo: {info['Nombre completo']}")
        print(f"   📧 Email: {info['Email']}")
        print(f"   📞 Teléfono: {info['Teléfono']}")
        print(f"   🔒 Privado: {'Sí' if info['Privado'] else 'No'}")
        print(f"   📅 Primer post: {info['Fecha primer post']}")
        print(f"   ⏰ Antigüedad: {info['Antigüedad estimada']}")

        return info

    except Exception as e:
        print(f"❌ Error al obtener info de @{username}: {e}")
        import traceback
        traceback.print_exc()
        return None


def extraer_biografia(driver):
    """Extrae biografía con múltiples selectores mejorados"""
    selectores = [
        # Selectores actualizados para Instagram 2025
        "//div[contains(@class, 'x7a106z')]//span[string-length(text()) > 5]",
        "//div[@data-testid='user-bio']//span",
        "//div[contains(@class, 'x78zum5')]//span[@dir='auto' and string-length(text()) > 10]",
        "//section//div//span[contains(text(), '@') or contains(text(), '.com') or string-length(text()) > 20]",
        # Selector más amplio para biografías
        "//span[@dir='auto' and string-length(text()) > 15 and string-length(text()) < 500]"
    ]

    for i, selector in enumerate(selectores):
        try:
            elementos = driver.find_elements(By.XPATH, selector)
            for elemento in elementos:
                bio = elemento.text.strip()
                # Validar que sea una biografía real
                if (bio and
                        len(bio) > 5 and
                        len(bio) < 500 and
                        bio not in ['Posts', 'Followers', 'Following', 'Publicaciones', 'Seguidores', 'Seguidos']):
                    print(f"✅ Biografía encontrada con selector {i + 1}: '{bio[:50]}...'")
                    return bio
        except NoSuchElementException:
            continue
        except Exception as e:
            print(f"⚠️ Error en selector biografía {i + 1}: {e}")
            continue

    print("⚠️ No se pudo extraer la biografía")
    return ""


def verificar_cuenta_privada(driver):
    """Verifica si la cuenta es privada"""
    indicadores_privada = [
        "This Account is Private",
        "Esta cuenta es privada",
        "private account",
        "cuenta privada"
    ]

    page_source = driver.page_source.lower()
    return any(indicador.lower() in page_source for indicador in indicadores_privada)


def obtener_fecha_primer_post_stealth(driver):
    """Obtiene fecha del primer post con comportamiento stealth"""
    try:
        print("📸 Buscando primer post...")

        # Scroll hacia abajo para cargar posts
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(random.uniform(2, 4))

        # Selectores para encontrar el primer post
        selectores_posts = [
            "//div[contains(@class, '_ac7v')]//a",
            "//article//div//a[contains(@href, '/p/')]",
            "//div[@role='button']//a[contains(@href, '/p/')]",
        ]

        first_post = None
        for selector in selectores_posts:
            try:
                posts = driver.find_elements(By.XPATH, selector)
                if posts:
                    # Tomar el último post (que debería ser el primero cronológicamente)
                    first_post = posts[-1] if len(posts) > 1 else posts[0]
                    print(f"📸 Post encontrado con selector: {selector}")
                    break
            except NoSuchElementException:
                continue

        if not first_post:
            print("⚠️ No se encontraron posts")
            return None

        # Scroll hacia el elemento
        driver.execute_script("arguments[0].scrollIntoView(true);", first_post)
        time.sleep(random.uniform(1, 2))

        # Click con comportamiento humano
        ActionChains(driver).move_to_element(first_post).pause(random.uniform(0.5, 1)).click().perform()
        time.sleep(random.uniform(3, 5))

        # Buscar fecha en el modal
        selectores_fecha = [
            "//time[@datetime]",
            "//time[@title]",
            "//span[contains(@class, 'time')]"
        ]

        fecha_post = None
        for selector in selectores_fecha:
            try:
                time_element = driver.find_element(By.XPATH, selector)
                fecha_post = time_element.get_attribute("datetime") or time_element.get_attribute("title")
                if fecha_post:
                    print(f"📅 Fecha encontrada: {fecha_post}")
                    break
            except NoSuchElementException:
                continue

        if not fecha_post:
            print("⚠️ No se pudo extraer la fecha del post")
            cerrar_modal_post(driver)
            return None

        # Procesar fecha
        try:
            if 'T' in fecha_post:
                fecha_obj = datetime.fromisoformat(fecha_post.replace('Z', '+00:00'))
            else:
                # Intentar parsear otros formatos
                fecha_obj = datetime.strptime(fecha_post, '%B %d, %Y')

            fecha_formateada = fecha_obj.strftime('%Y-%m-%d')

            # Calcular antigüedad
            if fecha_obj.tzinfo:
                delta = datetime.now(fecha_obj.tzinfo) - fecha_obj
            else:
                delta = datetime.now() - fecha_obj

            meses = delta.days // 30
            anios = meses // 12
            meses_restantes = meses % 12

            if anios > 0:
                antiguedad = f"{anios} años, {meses_restantes} meses" if meses_restantes > 0 else f"{anios} años"
            else:
                antiguedad = f"{meses} meses" if meses > 0 else f"{delta.days} días"

            # Cerrar modal
            cerrar_modal_post(driver)

            return {
                "fecha": fecha_formateada,
                "antiguedad": antiguedad
            }
        except Exception as e:
            print(f"⚠️ Error procesando fecha: {e}")
            cerrar_modal_post(driver)
            return None

    except Exception as e:
        print(f"❌ Error obteniendo fecha del primer post: {e}")
        return None


def cerrar_modal_post(driver):
    """Cierra modal de post de forma humana"""
    try:
        # Intentar cerrar con botón
        close_button = driver.find_element(By.XPATH,
                                           "//button[contains(@aria-label, 'Close') or contains(@aria-label, 'Cerrar')]")
        ActionChains(driver).move_to_element(close_button).pause(random.uniform(0.3, 0.7)).click().perform()
        time.sleep(random.uniform(1, 2))
    except NoSuchElementException:
        # Si no encuentra botón, usar ESC
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(random.uniform(1, 2))


def extraer_contacto_desde_bio(biografia):
    """Extrae email y teléfono de la biografía con regex mejorado"""
    if not biografia:
        return None, None

    # Regex más específico para email
    email = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', biografia)

    # Regex más específico para teléfono
    telefono = re.search(r'(\+?[\d\s\-\(\)\.]{8,})', biografia)

    return (email.group(0) if email else None,
            telefono.group(0).strip() if telefono else None)


def pausa_inteligente():
    """Genera pausas inteligentes basadas en el comportamiento humano"""
    # Pausas más largas durante "horas de descanso"
    hora_actual = datetime.now().hour

    if 2 <= hora_actual <= 6:  # Madrugada
        base_wait = random.uniform(15, 25)
    elif 12 <= hora_actual <= 14:  # Hora de almuerzo
        base_wait = random.uniform(10, 18)
    else:
        base_wait = random.uniform(6, 12)

    # Añadir variabilidad
    variacion = random.uniform(0.8, 1.4)
    tiempo_final = base_wait * variacion

    print(f"⏳ Pausa inteligente: {tiempo_final:.1f}s")
    time.sleep(tiempo_final)


def cargar_progreso_previo():
    """Carga el progreso previo desde archivo Excel"""
    if os.path.exists(RESUME_FILE):
        try:
            df = pd.read_excel(RESUME_FILE)
            ya_procesados = set(df['Usuario'].tolist())
            print(f"📂 Cargados {len(ya_procesados)} usuarios ya procesados")
            return ya_procesados
        except Exception as e:
            print(f"⚠️ Error cargando archivo de progreso: {e}")
            return set()
    return set()


def guardar_parcial(datos):
    """Guarda datos parciales combinando con progreso previo"""
    try:
        # Cargar datos existentes si hay
        if os.path.exists(RESUME_FILE):
            df_existente = pd.read_excel(RESUME_FILE)
            df_nuevo = pd.DataFrame(datos)
            df_combinado = pd.concat([df_existente, df_nuevo], ignore_index=True)
        else:
            df_combinado = pd.DataFrame(datos)

        # Eliminar duplicados
        df_combinado = df_combinado.drop_duplicates(subset=['Usuario'], keep='last')

        # Guardar
        df_combinado.to_excel(RESUME_FILE, index=False)
        print(f"💾 Progreso guardado: {len(df_combinado)} registros en {RESUME_FILE}")

    except Exception as e:
        print(f"❌ Error guardando progreso: {e}")


def guardar_resultados_finales():
    """Guarda resultados finales con marca de tiempo"""
    try:
        if os.path.exists(RESUME_FILE):
            # Leer y renombrar el archivo de resumen
            df = pd.read_excel(RESUME_FILE)
            df.to_excel(OUTPUT_EXCEL, index=False)
            print(f"✅ Resultados finales guardados en {OUTPUT_EXCEL}")

            # Opcional: eliminar el archivo de resumen
            os.remove(RESUME_FILE)
            print("🗑️ Archivo de resumen temporal eliminado")
        else:
            print("⚠️ No hay datos para guardar como resultados finales")
    except Exception as e:
        print(f"❌ Error guardando resultados finales: {e}")


def procesar_usernames_stealth(driver, usernames, ya_procesados):
    """Procesa usernames con técnicas anti-detección avanzadas"""
    global stop_signal, errores_consecutivos, session_requests

    datos = []
    procesados = 0
    total_usernames = len(usernames)
    reiniciar_sesion_contador = 0

    print(f"🚀 Iniciando procesamiento stealth de {total_usernames} usuarios...")

    for i, username in enumerate(usernames, 1):
        # Verificar condiciones de parada
        if stop_signal:
            print("🛑 Detenido por señal de interrupción")
            break
        if procesados >= MAX_USUARIOS:
            print(f"🎯 Límite alcanzado: {MAX_USUARIOS} usuarios")
            break
        if errores_consecutivos >= MAX_ERRORS:
            print(f"❌ Demasiados errores consecutivos: {errores_consecutivos}")
            break

        # Saltar si ya fue procesado
        if username in ya_procesados:
            print(f"⏭️ Saltando @{username} (ya procesado)")
            continue

        print(f"📥 Procesando @{username} ({i}/{total_usernames})...")

        # Obtener información del usuario
        info_usuario = obtener_info_usuario_stealth(driver, username)

        # Manejar reinicio de sesión
        if info_usuario == "RESTART_SESSION":
            print("🔄 Reiniciando sesión...")
            if datos:
                guardar_parcial(datos)
                datos.clear()

            # Pequeña pausa antes de reiniciar
            time.sleep(random.uniform(30, 60))
            session_requests = 0
            reiniciar_sesion_contador += 1

            if reiniciar_sesion_contador >= 3:
                print("⚠️ Demasiados reinicios de sesión. Terminando.")
                break

            continue

        elif info_usuario:
            datos.append(info_usuario)
            procesados += 1
            errores_consecutivos = 0
            print(f"✅ @{username} procesado exitosamente ({procesados} completados)")
        else:
            errores_consecutivos += 1
            print(f"❌ Error con @{username} ({errores_consecutivos}/{MAX_ERRORS})")

        # Pausa inteligente entre requests
        pausa_inteligente()

        # Guardar progreso cada 8 registros (reducido para mayor seguridad)
        if len(datos) >= 8:
            guardar_parcial(datos)
            datos.clear()

    # Guardar los últimos registros
    if datos:
        guardar_parcial(datos)
        print(f"💾 Guardados {len(datos)} registros finales")

    print(f"\n📊 Resumen final: {procesados} usuarios procesados correctamente")
    return procesados


def cargar_usernames_desde_json(path):
    """Carga la lista de usernames desde archivo JSON"""
    if not os.path.exists(path):
        print(f"❌ Archivo no encontrado: {path}")
        return []

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            usernames = data.get("seguidores", [])
            print(f"📋 {len(usernames)} usernames cargados desde {path}")
            return usernames
    except Exception as e:
        print(f"❌ Error cargando JSON: {e}")
        return []


def main():
    """Función principal del script"""
    global stop_signal

    print("🚀 INICIANDO SCRIPT DE EXTRACCIÓN DE SEGUIDORES INSTAGRAM 🚀")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔧 Configurando entorno...")

    # Cargar datos iniciales
    usernames = cargar_usernames_desde_json(INPUT_JSON)
    if not usernames:
        print("❌ No se pudieron cargar usernames. Saliendo...")
        return

    ya_procesados = cargar_progreso_previo()

    # Configurar driver
    driver = configurar_driver_stealth()
    if not driver:
        print("❌ No se pudo configurar el driver. Saliendo...")
        return

    try:
        # Iniciar sesión
        if not iniciar_sesion_stealth(driver, USERNAME, PASSWORD):
            print("❌ No se pudo iniciar sesión. Saliendo...")
            return

        # Procesar usernames
        procesar_usernames_stealth(driver, usernames, ya_procesados)

        # Guardar resultados finales
        if not stop_signal:
            guardar_resultados_finales()

    except Exception as e:
        print(f"❌ Error fatal en el script: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cerrar driver
        try:
            driver.quit()
            print("🚪 Driver cerrado correctamente")
        except:
            pass

    print("🏁 Proceso completado")


if __name__ == "__main__":
    main()