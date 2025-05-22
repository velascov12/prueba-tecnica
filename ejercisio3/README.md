# Ejercicio 3 - Aplicación Rick & Morty con Autenticación

**Nivel:** Intermedio/Avanzado  
**Objetivo:** Aplicación completa con GUI, autenticación y consumo de API

## Enunciado

Crear una aplicación que:
- Use módulo gráfico para ventana de login
- Utilice SQLite para validar usuarios registrados
- Muestre error si usuario no existe
- Al login exitoso, mostrar datos de API pública (Rick and Morty)
- Interfaz simple con usuario, contraseña, botón login


## Ejecución

```bash
cd ejercicio3
python main.py
```
### Credenciales de prueba:
- **Usuario:** `octavio`
- **Contraseña:** `north`


## Arquitectura

```
ejercicio3/
├── main.py          # Interfaz gráfica y lógica principal
├── db.py            # Manejo de base de datos SQLite  
├── api.py           # Consumo API Rick and Morty
└── img_funcionamiento/  # Capturas de pantalla
```




### . Interfaz Gráfica - `main.py`

Componentes principales:
- **Login Window:** Autenticación de usuarios
- **Characters Grid:** Visualización de personajes

`

### Credenciales de prueba:
- **Usuario:** `octavio`
- **Contraseña:** `north`

## 🖼️ Capturas de Funcionamiento

Las imágenes del funcionamiento están en: `img_funcionamiento/`

Incluyen:
- Pantalla de login
- Validación de credenciales
- Grid de personajes
- Funcionalidad de búsqueda
- Carga de imágenes

## 🎨 Características de la Interfaz

### Login Screen
- **Campos:** Usuario y contraseña
- **Validación:** Campos obligatorios
- **Seguridad:** Contraseña oculta con asteriscos
- **UX:** Enter para submit, centrado en pantalla

