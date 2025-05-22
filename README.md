# Prueba Técnica - Desarrollador Junior North Marketh

Solución completa a los 3 ejercicios de la prueba técnica, implementando análisis numérico, web scraping, y aplicación completa con autenticación y consumo de API.

## 🎯 Resumen de Ejercicios

| Ejercicio | Nivel | Descripción | Tecnologías |
|-----------|-------|-------------|-------------|
| **[Ejercicio 1](./ejercisio1/)** | Principiante | Función número más frecuente | Python, Collections |
| **[Ejercicio 2](./ejercisio2/)** | Intermedio | Web scraping MercadoLibre | Requests, BeautifulSoup |
| **[Ejercicio 3](./ejercisio3/)** | Intermedio/Avanzado | App Rick & Morty con auth | Tkinter, SQLite, API, bcrypt |

## 🗂️ Estructura del Proyecto

```
prueba_tecnica/
├── README.md                              
├── requirements.txt                        # Dependencias del proyecto
├── .gitignore                             # Archivos ignorados por Git
├── diagramas/                             # Diagramas de flujo (DrawIO)
│   ├── 1-diagrama_de_flujo.drawio
│   ├── 2.Scraping.drawio
│   └── 3-Diagrama_de_flujo.drawio
├── ejercicio1/                            #Número más frecuente
│   ├                         # Documentación específica
│   └── ejercicio_numf.py
├── ejercicio2/                            # Web Scraping
│   ├                         # Documentación específica
│   └── scraping.py
└── ejercicio3/                            # Aplicación completa
    ├── README.md                          
    ├── img_funcionamiento/                # Capturas de pantalla
    ├── api.py                            # API Rick and Morty
    ├── db.py                             # Base de datos SQLite
    └── main.py                           # Interfaz gráfica
```

## Instalación Rápida

```bash
# Clonar repositorio
git clone <url-del-repositorio>
cd prueba_tecnica

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## 🎮 Ejecución Rápida

```bash
# Ejercicio 1: Función número más frecuente
cd ejercicio1 && python ejercicio_numf.py

# Ejercicio 2: Web scraping MercadoLibre  
cd ejercicio2 && python scraping.py

# Ejercicio 3: Aplicación Rick & Morty
cd ejercicio3 && python main.py
# Credenciales: octavio / north
```

## 📦 Dependencias Principales

```
requests>=2.32.3      # HTTP requests para API y scraping
beautifulsoup4>=4.13.4 # Parsing HTML
bcrypt>=4.3.0         # Encriptación de contraseñas  
pillow>=11.2.1        # Procesamiento de imágenes
```

*Librerías incluidas en Python: sqlite3, tkinter, threading, collections, io, time*

## 📊 Diagramas de Flujo

Los diagramas explicativos están disponibles en formato DrawIO:
- **[Ejercicio 1](./diagramas/1-diagrama_de_flujo_ej1)**:
- **[Ejercicio 2](./diagramas/2.Scraping.drawio)**: 
- **[Ejercicio 3](./diagramas/3-Diagrama _de_flujo_api)**: 



### Error de módulos:
```bash
pip install -r requirements.txt
```



## Características Destacadas
- **Seguridad implementada** (bcrypt, validaciones)


## Información

**Desarrollado para North Marketh**  
Prueba técnica - Desarrollador Junior  
Implementación completa siguiendo mejores prácticas de desarrollo

-
