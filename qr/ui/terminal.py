from qr.contrato import EntradaUsuario, ModoPedido, ErrorQR, NivelCorreccion

# Ingresar contenido manualmente
def ingresar_texto():
    texto = input("Ingrese el contenido que deseé convertir a un QR"
                  "\n> Para cancelar la opción tecleé 'n'"
                  "\n> Respuesta: ")
    if texto == 'n':
        print("Acción Cancelada: Retornando a menú")

    return texto

# Ingresar nivel de correción manualmente
def ingresar_nivel_correccion():
    texto = input("nivel_correccion")
    return texto

def ingresar_modo():
    modo: ModoPedido = "auto"
    array_modos: ModoPedido[3] = ["numerico","alfanumerico","byte"]

    while True:
        try:
            cont = 0
            print("¿Qué modo corresponde mejor a su contenido?")
            for mod in array_modos:
                cont += 1
                if mod == "auto":
                    continue
                else:
                    print(f"> {cont} - {mod}")
            print("> Para cancelar la opción tecleé 'n'")

            resp = input("> Respuesta: ")

            if resp == 'n':
                print("Acción cancelada: Modo automático")
                break

            resp = int(resp)

            if resp < 1 or resp > (len(array_modos)):
                print("Opción no válida: Valor debe ser entre 1 y 3")
            else:
                index = resp-1
                modo = array_modos[index]
                break
        except ValueError:
            print("ERROR: Valor no es una opción válida\n")
        except ErrorQR:
            print("Opción no válida para QR")

    return modo

def ingresar_version_minima():
    texto = input("version_minima")
    return texto

def calcular_version_minima(texto: str, modo: ModoPedido, nivel_correccion: NivelCorreccion):
    largo = len(texto)

    return min

def ingresar_mascara():
    mascara = None

    while True:
        try:
            resp = input("¿Qué máscara específica desea usar? (1-8)"
                          "\n> Para cancelar la opción tecleé 'n'"
                          "\n> Respuesta: ").strip().lower()
            if resp == 'n':
                print("Acción cancelada: Máscara automática")
                break

            resp = int(resp)

            if resp < 1 or resp > 8:
                print("Opción no válida: Valor debe ser entre 1 y 8")
            else:
                mascara = resp
                break
        except ValueError:
            print("ERROR: Valor no es un número o n\n")

    return mascara

def main():
    ingresar_modo()

if __name__ == "__main__":
    main()