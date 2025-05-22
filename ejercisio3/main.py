import tkinter as tk
from tkinter import messagebox
import threading
from PIL import Image, ImageTk
import requests
from io import BytesIO
from db import create_table, get_user, insert_user
from api import get_characters

# Crear base de datos e insertar usuario
create_table()
try:
    insert_user("octavio", "north")
except:
    pass

# Cache para imágenes
imagen_cache = {}
imagen_placeholder = None

def get_placeholder():
    global imagen_placeholder
    if imagen_placeholder is None:
        img = Image.new('RGB', (80, 80), color='#ecf0f1')
        imagen_placeholder = ImageTk.PhotoImage(img)
    return imagen_placeholder

def cargar_imagen_async(url, label_imagen):
    
    def cargar():
        if url in imagen_cache:
            try:
                if label_imagen.winfo_exists():
                    label_imagen.config(image=imagen_cache[url])
            except:
                pass
            return
        
        try:
            response = requests.get(url, timeout=3)
            img = Image.open(BytesIO(response.content))
            img = img.resize((80, 80), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            imagen_cache[url] = photo
            
            # Actualizar en hilo principal solo si el widget existe
            def actualizar_imagen():
                try:
                    if label_imagen.winfo_exists():
                        label_imagen.config(image=photo)
                except:
                    pass
            
            label_imagen.after(0, actualizar_imagen)
        except:
            pass  # Si falla, mantiene el placeholder
    
    threading.Thread(target=cargar, daemon=True).start()

def crear_carta_personaje(parent, personaje, fila, columna):
   #Crear una carta simple para un personaje
    # Frame de la carta
    carta = tk.Frame(parent, relief="solid", bd=1, bg="white", width=200, height=180)
    carta.grid(row=fila, column=columna, padx=5, pady=5, sticky="nsew")
    carta.grid_propagate(False)
    
    # Imagen placeholder primero
    img_frame = tk.Frame(carta, bg="white")
    img_frame.pack(pady=(5, 5))
    
    img_label = tk.Label(img_frame, image=get_placeholder(), bg="white")
    img_label.pack()
    
    # Cargar imagen real en segundo plano
    cargar_imagen_async(personaje['image'], img_label)
    
    # Nombre
    name_text = personaje['name']
    if len(name_text) > 18:
        name_text = name_text[:15] + "..."
    tk.Label(carta, text=name_text, font=("Arial", 10, "bold"), 
             bg="white", fg="#2c3e50").pack(pady=(0, 3))
    
    # Estado con color
    status_colors = {"Alive": "#27ae60", "Dead": "#e74c3c", "unknown": "#f39c12"}
    color = status_colors.get(personaje['status'], "#34495e")
    
    tk.Label(carta, text=personaje['status'], 
             font=("Arial", 9), bg="white", fg=color).pack(pady=1)
    
    # Especie
    tk.Label(carta, text=personaje['species'], 
             font=("Arial", 8), bg="white", fg="#34495e").pack(pady=1)

def mostrar_personajes():
    ventana = tk.Toplevel()
    ventana.title("Rick and Morty - Personajes")
    ventana.geometry("900x600")
    
    # Frame para búsqueda
    search_frame = tk.Frame(ventana, bg="#f8f9fa", pady=8)
    search_frame.pack(fill="x", padx=10, pady=5)
    
    tk.Label(search_frame, text="Buscar:", font=("Arial", 11), bg="#f8f9fa").pack(side="left", padx=5)
    
    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var, font=("Arial", 11), width=25)
    search_entry.pack(side="left", padx=5)
    
    # Botón buscar
    def buscar_ahora():
        buscar_personajes()
    
    tk.Button(search_frame, text="Buscar", command=buscar_ahora, 
              font=("Arial", 10), bg="#3498db", fg="white").pack(side="left", padx=5)
    
    # Label de estado
    status_label = tk.Label(search_frame, text="Cargando...", font=("Arial", 10), bg="#f8f9fa", fg="#6c757d")
    status_label.pack(side="right", padx=10)
    
    # Frame principal con scroll
    main_frame = tk.Frame(ventana)
    main_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    canvas = tk.Canvas(main_frame, bg="#f8f9fa")
    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    cards_frame = tk.Frame(canvas, bg="#f8f9fa")
    
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.create_window((0, 0), window=cards_frame, anchor="nw")
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Variables
    todos_personajes = []
    
    def actualizar_cartas(personajes_mostrar):
        
        # Limpiar widgets existentes de forma segura
        for widget in cards_frame.winfo_children():
            try:
                widget.destroy()
            except:
                pass
        
        # Limpiar cache de imágenes viejas para liberar memoria
        if len(imagen_cache) > 50:  # Mantener solo las últimas 50 imágenes
            keys_to_remove = list(imagen_cache.keys())[:-50]
            for key in keys_to_remove:
                if key != 'default':  # No borrar la imagen por defecto
                    del imagen_cache[key]
        
        # Mostrar solo primeros 20 para que sea rápido
        personajes_mostrar = personajes_mostrar[:20]
        
        # Crear cartas
        columnas = 4
        for i, personaje in enumerate(personajes_mostrar):
            fila = i // columnas
            columna = i % columnas
            crear_carta_personaje(cards_frame, personaje, fila, columna)
        
        for col in range(columnas):
            cards_frame.grid_columnconfigure(col, weight=1)
        
        # Actualizar scroll
        cards_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        status_label.config(text=f"Mostrando: {len(personajes_mostrar)} personajes")
    
    def buscar_personajes(*args):
        """Filtrar personajes"""
        busqueda = search_var.get().lower().strip()
        
        if not busqueda:
            personajes_filtrados = todos_personajes[:20]  # Solo primeros 20
        else:
            personajes_filtrados = []
            count = 0
            for p in todos_personajes:
                if count >= 20:  # Máximo 20 resultados
                    break
                if (busqueda in p['name'].lower() or 
                    busqueda in p['species'].lower() or 
                    busqueda in p['status'].lower()):
                    personajes_filtrados.append(p)
                    count += 1
        
        actualizar_cartas(personajes_filtrados)
    
    def cargar_personajes():
        """Cargar personajes rápidamente"""
        def cargar_en_hilo():
            try:
                personajes = get_characters()
                
                def actualizar_ui():
                    nonlocal todos_personajes
                    todos_personajes = personajes
                    actualizar_cartas(personajes[:20])  # Solo primeros 20
                    search_var.trace("w", buscar_personajes)
                    status_label.config(text=f"Total: {len(personajes)} personajes. Mostrando primeros 20")
                
                ventana.after(0, actualizar_ui)
                
            except Exception as e:
                def mostrar_error():
                    status_label.config(text="Error al cargar")
                    messagebox.showerror("Error", str(e))
                
                ventana.after(0, mostrar_error)
        
        threading.Thread(target=cargar_en_hilo, daemon=True).start()
    
    # Scroll con mouse
    def scroll_mouse(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    canvas.bind("<MouseWheel>", scroll_mouse)
    
    # Cargar datos
    ventana.after(100, cargar_personajes)
    
    ventana.protocol("WM_DELETE_WINDOW", lambda: [ventana.destroy(), root.destroy()])

def login():
    """Función de login"""
    user = entry_usuario.get().strip()
    password = entry_password.get().strip()
    
    if not user or not password:
        messagebox.showerror("Error", "Complete ambos campos")
        return
    
    if get_user(user, password):
        messagebox.showinfo("Éxito", f"Bienvenido {user}")
        root.withdraw()
        mostrar_personajes()
    else:
        messagebox.showerror("Error", "Usuario o contraseña incorrectos")

# Ventana principal de login
root = tk.Tk()
root.title("Login - Rick & Morty")
root.geometry("450x400")
root.resizable(False, False)

# Centrar ventana
root.eval('tk::PlaceWindow . center')

# Frame del login
login_frame = tk.Frame(root, padx=30, pady=30)
login_frame.pack(fill="both", expand=True)

# Título
tk.Label(login_frame, text="Rick & Morty", 
         font=("Arial", 20, "bold"), fg="#2c3e50").pack(pady=(0, 20))

# Campo usuario
tk.Label(login_frame, text="Usuario:", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
entry_usuario = tk.Entry(login_frame, font=("Arial", 12), width=30)
entry_usuario.pack(pady=(0, 15), ipady=5)
entry_usuario.insert(0, "")

# Campo contraseña
tk.Label(login_frame, text="Contraseña:", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
entry_password = tk.Entry(login_frame, show="*", font=("Arial", 12), width=30)
entry_password.pack(pady=(0, 20), ipady=5)
entry_password.insert(0, "")

# Botón login
tk.Button(login_frame, text="Iniciar Sesión", command=login,
          font=("Arial", 12), padx=20, pady=8, bg="#3498db", fg="white").pack(pady=(0, 10))

# Info de credenciales
tk.Label(login_frame, text="Credenciales: octavio / north", 
         font=("Arial", 9), fg="#7f8c8d").pack()

# Enter para hacer login
entry_password.bind('<Return>', lambda e: login())

root.mainloop()