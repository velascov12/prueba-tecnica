import requests
from bs4 import BeautifulSoup
import time

def scrape_mercadolibre(palabra_clave, num_productos=5):
#Headers como un navegador real
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Construir URL de búsqueda
    base_url = "https://listado.mercadolibre.com.co/"
    search_url = f"{base_url}/{palabra_clave.replace(' ', '-')}"
    
    print(f"-Buscando '{palabra_clave}' en MercadoLibre...")
    print(f"URL: {search_url}")
    print("-" * 60)
    
    try:
        #petición HTTP
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()  
        
        # Parsear HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        productos = soup.find_all('div', class_='ui-search-result__wrapper', limit=num_productos)

        if not productos:
            print("- No se encontraron productos o la estructura de la página cambió")
            return
        
        print(f"-Se encontraron {len(productos)} productos:")
        print("=" * 60)
        #__________
        # Extraer información de cada producto
        for i, producto in enumerate(productos, 1):
            try:
                # TÍTULO 
                titulo_element = producto.find('a', class_='poly-component__title')
                titulo = titulo_element.get_text(strip=True) if titulo_element else "Título no disponible"
                
                # PRECIO ACTUAL
                precio_completo = "Precio no disponible"
                precio_section = producto.find('div', class_='poly-price__current')
                
                if precio_section:
                    
                    simbolo_element = precio_section.find('span', class_='andes-money-amount__currency-symbol')
                    fraccion_element = precio_section.find('span', class_='andes-money-amount__fraction')
                    
                    if simbolo_element and fraccion_element:
                        simbolo = simbolo_element.get_text(strip=True)
                        fraccion = fraccion_element.get_text(strip=True)
                        precio_completo = f"{simbolo} {fraccion}"
                        
                        # Agregar descuento si existe
                        descuento_element = precio_section.find('span', class_='andes-money-amount__discount')
                        if descuento_element:
                            descuento = descuento_element.get_text(strip=True)
                            precio_completo += f" ({descuento})"
                
                # INFORMACIÓN ADICIONAL
                marca_element = producto.find('span', class_='poly-component__brand')
                marca = marca_element.get_text(strip=True) if marca_element else ""
                
                # Imprimir información del producto
                print(f"- Producto {i}:")
                if marca:
                    print(f"   Marca: {marca}")
                print(f"   Título: {titulo}")
                print(f"   Precio: {precio_completo}")
                print("-" * 40)
                
            except Exception as e:
                print(f"-  Error al procesar producto {i}: {str(e)}")
                continue
                
    except requests.exceptions.RequestException as e:
        print(f"- Error de conexión: {str(e)}")
    except Exception as e:
        print(f"- Error inesperado: {str(e)}")
        
    print(f"URL: {search_url}")
    print("-" * 60)

#main para ejecutar
def main():
   
    palabra = "laptop" #cambiar palabra
    print("-INICIANDO SCRAPING DE MERCADOLIBRE")
    print("=" * 60)
    
    # Ejecutar scraping
    scrape_mercadolibre(palabra, num_productos=5)
    
    print("\n" + "=" * 60)
    print("-Scraping completado -sube para ver resultados")
    print(f"- Para cambiar la búsqueda, modifica la variable 'palabra' en main()")

if __name__ == "__main__":
    main()