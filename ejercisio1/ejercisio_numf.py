from collections import Counter

def numero_mas_frecuente(lista):
    #control de errores
    if not isinstance(lista,list) or not  all(isinstance(item,int)for item in lista):
        raise ValueError("No se esta pasando el prametro solicitado de tipo lista de num enteros")
    
    if not lista:
       return None

    #freq por elemento
    frecuncia_x_elemento=Counter(lista)
    mayor_frecuencia=max(frecuncia_x_elemento.values())
    
    num_mas_frecuentes=[
        num for num ,freq in frecuncia_x_elemento.items()
        if freq==mayor_frecuencia]
    
    return min(num_mas_frecuentes)



print("_______________________")
print(f"el num mas frecuente es : {numero_mas_frecuente([1,1,2,3,8,2,2])}")
print("_______________________")

