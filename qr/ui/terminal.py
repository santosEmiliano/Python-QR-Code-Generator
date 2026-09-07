from qr.contrato import EntradaUsuario

# Lista de input que tiene que realizar el usuario
def ingresar_texto():
    texto = input("Texto")
    return texto

def ingresar_nivel_correccion():
    texto = input("nivel_correccion")
    return texto

def ingresar_modo():
    texto = input("modo")
    return texto

def ingresar_version_minima():
    texto = input("version_minima")
    return texto

def ingresar_mascara():
    mascara = None

    while True:
        try:
            texto = input("¿Qué máscara específica desea usar? (1-8)"
                          "\n> Para cancelar la opción tecleé 'n'"
                          "\n> Respuesta: ").strip().lower()
            if texto == 'n':
                print("Acción cancelada: Máscara automática")
                break

            texto = int(texto)

            if texto < 1 or texto > 8:
                print("Opción no válida: Valor debe ser entre 1 y 8")
            else:
                mascara = texto
                break
        except ValueError:
            print("ERROR: Valor no es un número o n\n")

    return mascara

def main():
    ingresar_mascara()

if __name__ == "__main__":
    main()