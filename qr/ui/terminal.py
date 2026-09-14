from qr.contrato import EntradaUsuario, Modo, ErrorQR, NivelCorreccion
from qr.tablas import CAPACIDAD_ALFA, CAPACIDAD_BYTE, CAPACIDAD_NUM


def menu():
    while True:
        try:
            print("\nGenerador de códigos QR, Seleccione la acción que desea tomar:\n"
                "1) Generar QR simple\n"
                "2) Generar QR avanzado\n"
                "3) Salir\n")
            opt = int(input("> Respuesta: "))

            match opt:
                case 1:
                    qr_selector(opt)
                case 2:
                    qr_selector(opt)
                case 3:
                    break
        except ValueError:
            print("Valor no valido")

def qr_selector(tipo: int):
    match tipo:
        case 1:
            tipo_str = "Simple"
        case 2:
            tipo_str = "Avanzado"

    try:
        while True:
            try:
                print(f"\nHa seleccionado el modo {tipo_str} ¿Está seguro de esta elección?\n"
                "1) Continuar\n"
                "2) Regresar\n")

                opt = int(input("> Respuesta: "))

                if opt == 1:
                    match tipo:
                        case 1:
                            datos_qr = qr_auto()
                        case 2:
                            datos_qr = qr_advanced()

                    if datos_qr:
                        print(f"\nDatos de QR: {datos_qr}")
                    break
                elif opt == 2:
                    break
                else:
                    print("ERROR: Valor no es una opción válida\n")

            except ValueError:
                print("ERROR: Valor no es una opción válida\n")

        # Aquí debe mandar a llamar la función para generar el QR
        # resultado = generar_qr(entrada)
    except ErrorQR as mensaje:
        print(f"Error al crear el QR: {mensaje}\n")

# Solo manda el texto y lo empaqueta de forma que lo entienda el sistema
def qr_auto():
    texto = ingresar_texto("auto")

    if texto == 'n' or texto == 'N':
        return False

    entrada_user: EntradaUsuario = EntradaUsuario(texto)

    return entrada_user

def qr_advanced():
    modo = ingresar_modo()
    texto = ingresar_texto(modo)

    if texto == 'n' or texto == 'N':
        return False

    nivel = ingresar_nivel_correccion()
    version = ingresar_version_minima(texto,modo,nivel)
    mascara = ingresar_mascara()


    entrada_user: EntradaUsuario = EntradaUsuario(texto,nivel,modo,version,mascara)

    return entrada_user

# Ingresar contenido manualmente
def ingresar_texto(modo: str):
    while True:
        texto = input("\nIngrese el contenido que deseé convertir a un QR"
                      "\n> Para cancelar la opción tecleé 'n'"
                      "\n> Respuesta: ")

        if texto == 'n' or texto == 'N':
            print("Acción Cancelada: Retornando a menú\n")
            break
        else:
            match modo:
                case Modo.NUMERICO.value:
                    if texto.isnumeric():
                        break
                    else:
                        print(f"Texto no cuadra con modo [{modo}]")
                case Modo.ALFANUMERICO.value:
                    if texto.isnumeric():
                        break
                    else:
                        print(f"Texto no cuadra con modo [{modo}]")
                case Modo.BYTE.value:
                    break
                case "auto":
                    break

    return texto

# Ingresar nivel de correción manualmente
def ingresar_nivel_correccion():
    nivel: NivelCorreccion = NivelCorreccion.M
    array_nivel = ["L (Bajo - 7%)", "M (Medio - 15%)", "Q (Cuartil - 25%)", "H (Alto - 30%)"]

    while True:
        try:
            cont = 0
            print("\n¿Qué nivel corresponde mejor a su contenido?")
            for niv in array_nivel:
                cont += 1
                print(f"> {cont} - {niv}")
            print("> Para cancelar la opción tecleé 'n'\n")

            resp = input("> Respuesta: ")

            if resp == 'n':
                print("Acción cancelada: Nivel automático")
                break

            resp = int(resp)

            if resp < 1 or resp > (len(array_nivel)):
                print(f"Opción no válida: Valor debe ser entre 1 y {len(array_nivel)}")
            else:
                match resp:
                    case 1:
                        nivel = NivelCorreccion.L
                    case 2:
                        nivel = NivelCorreccion.M
                    case 3:
                        nivel = NivelCorreccion.Q
                    case 4:
                        nivel = NivelCorreccion.H
                break
        except ValueError:
            print("ERROR: Valor no es una opción válida\n")

    return nivel

def ingresar_modo():
    modo: str = "auto"
    array_modos = Modo

    while True:
        try:
            cont = 0
            print("\n¿Qué modo corresponde mejor a su contenido?")
            for mod in array_modos:
                cont += 1
                print(f"> {cont} - {mod.value}")
            print("> Para cancelar la opción tecleé 'n'\n")

            resp = input("> Respuesta: ")

            if resp == 'n':
                print("Acción cancelada: Modo automático")
                break

            resp = int(resp)

            if resp < 1 or resp > (len(array_modos)):
                print("Opción no válida: Valor debe ser entre 1 y 3")
            else:
                match resp:
                    case 1:
                        modo = Modo.NUMERICO.value
                        break
                    case 2:
                        modo = Modo.ALFANUMERICO.value
                        break
                    case 3:
                        modo = Modo.BYTE.value
                        break
                break
        except ValueError:
            print("ERROR: Valor no es una opción válida\n")

    return modo

def ingresar_version_minima(texto: str, modo: str, nivel_correccion: NivelCorreccion):
    min_ver: int = calcular_version_minima(texto, modo, nivel_correccion)

    while True:
        try:
            opt = input(f"\nIngrese la versión para su QR [Versión mínima permitida {min_ver}]"
                        "\n> Para cancelar la opción tecleé 'n'\n"
                        "\n> Respuesta: ")

            if opt == 'n' or opt == "N":
                print(f"Acción Cancelada: Versión Automática ({min_ver})")
                break
            else:
                opt = int(opt)
                if opt < min_ver or opt > 40:
                    print(f"No es posible crear un QR con las características específicadas [Versión mínima permitida {min_ver}]\n")
                else:
                    min_ver = opt
                    print(f"Versión seleccionada: {min_ver}")
                    break

        except ValueError:
            print("ERROR: Valor no es una opción válida\n")

    return min_ver

# Creo sería bueno mover esta función a otra parte pero no se a cual
def calcular_version_minima(texto: str, modo: str, nivel_correccion: NivelCorreccion):
    largo: int = len(texto)
    min_ver: int = 0

    match modo:
        case Modo.NUMERICO.value:
            for clave, valor in CAPACIDAD_NUM.items():
                max_len = valor.get(nivel_correccion)

                if max_len > largo:
                    min_ver = clave

        case Modo.ALFANUMERICO.value:
            for clave, valor in CAPACIDAD_ALFA.items():
                max_len = valor.get(nivel_correccion)

                if max_len > largo:
                    min_ver = clave

        case Modo.BYTE.value:
            for clave, valor in CAPACIDAD_BYTE.items():
                max_len = valor.get(nivel_correccion)

                if max_len > largo:
                    min_ver = clave
    return min_ver

def ingresar_mascara():
    mascara = None

    while True:
        try:
            resp = input("\n¿Qué máscara específica desea usar? (1-8)"
                          "\n> Para cancelar la opción tecleé 'n'"
                          "\n> Respuesta: ").strip().lower()
            if resp == 'n':
                print("Acción cancelada: Máscara automática")
                break

            resp = int(resp)

            if resp < 1 or resp > 8:
                print("ERROR: Valor no es una opción válida\n")
            else:
                mascara = resp
                break
        except ValueError:
            print("ERROR: Valor no es una opción válida\n")

    return mascara

def main():
    menu()

    print("\nFinalización del Programa: Tenga buen día")

if __name__ == "__main__":
    main()