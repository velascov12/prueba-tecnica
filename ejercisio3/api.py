import requests

def get_characters():
    """
    Obtiene todos los personajes de Rick and Morty
    """
    all_characters = []
    url = "https://rickandmortyapi.com/api/character"
    
    while url:
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            all_characters.extend(data['results'])
            url = data['info']['next']  # Siguiente página
        except Exception as e:
            print(f"Error: {e}")
            break
    
    return all_characters