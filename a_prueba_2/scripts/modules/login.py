"""
Módulo para manejo de autenticación y cookies de Instagram.
"""

import instaloader
import json
import os
from http.cookiejar import Cookie, CookieJar

def iniciar_sesion_con_cookies(cookies_file, username):
    """
    Inicia sesión en Instagram usando cookies.
    
    Args:
        cookies_file (str): Ruta al archivo de cookies
        username (str): Nombre de usuario para la sesión
        
    Returns:
        instaloader.Instaloader: Instancia de Instaloader autenticada o None si falla
    """
    L = instaloader.Instaloader()
    
    try:
        if not os.path.exists(cookies_file):
            print(f"❌ Error: Archivo de cookies no encontrado: {cookies_file}")
            return None

        with open(cookies_file, 'r') as f:
            cookies = json.load(f)

        cookie_jar = CookieJar()
        
        for cookie_data in cookies:
            if cookie_data['name'] == 'sessionid':
                c = Cookie(
                    version=0,
                    name=cookie_data['name'],
                    value=cookie_data['value'],
                    port=None,
                    port_specified=False,
                    domain=cookie_data['domain'],
                    domain_specified=True,
                    domain_initial_dot=cookie_data['domain'].startswith('.'),
                    path=cookie_data['path'],
                    path_specified=True,
                    secure=cookie_data['secure'],
                    expires=int(cookie_data['expiry']) if 'expiry' in cookie_data else None,
                    discard=False,
                    comment=None,
                    comment_url=None,
                    rest={'HttpOnly': True},
                    rfc2109=False
                )
                cookie_jar.set_cookie(c)

        L.context._session.cookies = cookie_jar
        L.context.username = username
        L.test_login()
        
        print(f"✅ Sesión iniciada correctamente para: {username}")
        return L
        
    except Exception as e:
        print(f"❌ Error al iniciar sesión: {e}")
        return None

def validar_perfil(loader, target_profile):
    """
    Valida que el perfil objetivo sea accesible.
    
    Args:
        loader (instaloader.Instaloader): Instancia autenticada
        target_profile (str): Nombre del perfil objetivo
        
    Returns:
        instaloader.Profile: Perfil validado o None si no es accesible
    """
    try:
        profile = instaloader.Profile.from_username(loader.context, target_profile)
        
        if profile.is_private:
            print(f"⚠️ Perfil @{target_profile} es privado: Necesitas seguir al perfil.")
            return None
            
        print(f"✅ Perfil @{target_profile} accesible")
        print(f"📊 Total de seguidores: {profile.followers:,}")
        
        return profile
        
    except Exception as e:
        print(f"❌ Error al acceder al perfil @{target_profile}: {e}")
        return None