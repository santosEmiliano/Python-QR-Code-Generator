import random

from qr.contrato import EntradaUsuario, Modo, ErrorQR, NivelCorreccion, ResultadoQR
from qr.danio import InformeDanio, MODOS_DANIO, danar_matriz, modulos_tolerados
from qr.qr import generar_qr
from qr.tablas import VERSION_MAX_CARGADA
from qr.entrada import analizar_texto, validar_texto_para_modo
from qr.version import elegir_version
from qr.ui.qr_imagen import crear_imagen_qr

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
                        resultado = generar_qr(datos_qr)
                        mostrar_resultado(resultado)
                        break
                elif opt == 2:
                    break
                else:
                    print("ERROR: Valor no es una opción válida\n")

            except ValueError:
                print("ERROR: Valor no es una opción válida\n")

    except ErrorQR as mensaje:
        print(f"Error al crear el QR: {mensaje}\n")
    except NotImplementedError:
        # Las tablas del estándar solo están cargadas hasta la versión 10
        print(f"Error al crear el QR: por ahora solo se pueden generar QR hasta la versión "
              f"{VERSION_MAX_CARGADA}. El texto o la versión pedida son demasiado grandes.\n")

# Solo manda el texto y lo empaqueta de forma que lo entienda el sistema
def qr_auto():
    texto = ingresar_texto("auto")

    if texto == 'n' or texto == 'N':
        return False

    entrada_user: EntradaUsuario = EntradaUsuario(texto=texto)

    return entrada_user

def qr_advanced():
    modo = ingresar_modo()
    texto = ingresar_texto(modo)

    if texto == 'n' or texto == 'N':
        return False

    nivel = ingresar_nivel_correccion()
    version = ingresar_version_minima(texto,modo,nivel)
    mascara = ingresar_mascara()


    entrada_user: EntradaUsuario = EntradaUsuario(texto=texto, nivel_correccion=nivel, modo=modo,
                                                 version_minima=version, mascara=mascara)

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
            if modo == "auto":
                break
            try:
                validar_texto_para_modo(texto, Modo(modo))
                break
            except ErrorQR as error:
                print(f"Texto no cuadra con modo [{modo}]: {error}")

    return texto

# Ingresar nivel de corrección manualmente
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
            opt = input(f"\nIngrese la versión para su QR [Versión mínima permitida {min_ver}, máxima {VERSION_MAX_CARGADA}]"
                        "\n> Para cancelar la opción tecleé 'n'\n"
                        "\n> Respuesta: ")

            if opt == 'n' or opt == "N":
                print(f"Acción Cancelada: Versión Automática ({min_ver})")
                break
            else:
                opt = int(opt)
                if opt < min_ver or opt > VERSION_MAX_CARGADA:
                    print(f"No es posible crear un QR con las características específicadas "
                          f"[Versión mínima permitida {min_ver}, máxima {VERSION_MAX_CARGADA}]\n")
                else:
                    min_ver = opt
                    print(f"Versión seleccionada: {min_ver}")
                    break

        except ValueError:
            print("ERROR: Valor no es una opción válida\n")

    return min_ver

# Versión más chica donde entra el texto: la misma cuenta que hace el generador
def calcular_version_minima(texto: str, modo: str, nivel_correccion: NivelCorreccion):
    return elegir_version(analizar_texto(texto, modo), nivel_correccion)

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
                mascara = resp - 1  # el usuario ve 1-8, el contrato usa 0-7
                break
        except ValueError:
            print("ERROR: Valor no es una opción válida\n")

    return mascara

# Margen blanco que exige el estándar alrededor del QR, en módulos
MARGEN_QR = 4

# Devuelve el QR como texto para terminal de fondo oscuro: el claro se dibuja con
# bloques y el oscuro queda vacío. Cada módulo ocupa dos caracteres para que no se
# vea estirado.
def imprimir_qr(matriz: list[list[bool]]):
    colum = len(matriz[0])
    linea_margen = "██" * (colum + 2 * MARGEN_QR) + "\n"

    resultado: str = linea_margen * MARGEN_QR

    for fila in matriz:
        resultado += "██" * MARGEN_QR
        for modulo in fila:
            resultado += "  " if modulo else "██"
        resultado += "██" * MARGEN_QR + "\n"

    resultado += linea_margen * MARGEN_QR

    return resultado

def mostrar_resultado(resultado: ResultadoQR):
    datos_matriz = resultado.final.matriz
    datos_mascara = resultado.final.mascara

    # Imprimir Matriz
    print(imprimir_qr(datos_matriz))

    print("############# DATOS DE LA MATRIZ #############")
    print(f"Modo: {resultado.mensaje.modo.value}")
    print(f"Nivel de corrección: {resultado.mensaje.nivel_correccion.value}")
    print(f"Versión: {resultado.mensaje.version}")
    print(f"Máscara usada: {datos_mascara}")

    # Preguntar si quiere generar imagen
    while True:
        opc = input("¿Desea generar una imagen de su QR? (S/N): ").strip().upper()

        match opc:
            case "S":
                crear_imagen_qr("QR", datos_matriz)
                print("Imagen guardada como QR.png")
                break
            case "N":
                break
            case _:
                print("ERROR: Valor no válido")

    ofrecer_danio(resultado)
    return

# Daño simulado: invierte módulos del QR para comprobar la corrección de errores
def ofrecer_danio(resultado: ResultadoQR):
    while True:
        opc = input("\n¿Desea dañar el QR para probar la corrección de errores? (S/N): ").strip().upper()

        match opc:
            case "S":
                danar_qr(resultado)
            case "N":
                break
            case _:
                print("ERROR: Valor no válido")

def danar_qr(resultado: ResultadoQR):
    modo = ingresar_modo_danio()
    if modo is None:
        return

    # La misma semilla para calcular el límite y para dañar: así el límite es exacto
    semilla = random.randrange(2 ** 32)
    total = len(resultado.correccion.secuencia) * 8
    limite = modulos_tolerados(resultado, modo, semilla)
    cantidad = ingresar_intensidad_danio(modo, limite, total)
    if cantidad is None:
        return

    try:
        informe = danar_matriz(resultado, modo=modo, semilla=semilla, **cantidad)
    except ErrorQR as mensaje:
        print(f"Error al dañar el QR: {mensaje}\n")
        return

    print(imprimir_qr(informe.matriz))
    mostrar_informe_danio(informe, resultado.mensaje.nivel_correccion)

    while True:
        opc = input("¿Desea guardar el QR dañado como imagen? (S/N): ").strip().upper()

        match opc:
            case "S":
                crear_imagen_qr("QR_danado", informe.matriz)
                print("Imagen guardada como QR_danado.png")
                break
            case "N":
                break
            case _:
                print("ERROR: Valor no válido")

def ingresar_modo_danio():
    while True:
        print("\n¿Cómo desea dañar el QR?"
              "\n> 1 - Al azar (módulos sueltos repartidos por todo el QR)"
              "\n> 2 - Mancha (módulos juntos, como un borrón)"
              "\n> Para cancelar la opción tecleé 'n'\n")

        resp = input("> Respuesta: ").strip().lower()

        if resp == 'n':
            print("Acción cancelada: Sin daño")
            return None
        if resp in ("1", "2"):
            return MODOS_DANIO[int(resp) - 1]
        print("ERROR: Valor no es una opción válida\n")

# Muestra cuánto aguanta este QR y deja elegir entre tres intensidades o una propia.
# Devuelve los argumentos de danar_matriz para la cantidad (modulos o porcentaje).
def ingresar_intensidad_danio(modo: str, limite: int, total: int):
    leve = max(1, limite // 2)
    excesivo = min(total, limite * 2)
    tipo = "al azar" if modo == "azar" else "en mancha"

    print(f"\nReferencia: con daño {tipo}, este QR aguanta hasta {limite} de {total} módulos "
          f"({limite / total:.1%}). Con uno más ya no se puede recuperar.")

    while True:
        print("\n¿Cuánto daño desea aplicar?"
              f"\n> 1 - Leve: {leve} módulos ({leve / total:.1%}), debería leerse con margen"
              f"\n> 2 - Justo en el límite: {limite} módulos ({limite / total:.1%}), un lector real puede fallar aquí"
              f"\n> 3 - Excesivo: {excesivo} módulos ({excesivo / total:.1%}), no debería poder leerse"
              "\n> 4 - Personalizado (un porcentaje)"
              "\n> Para cancelar la opción tecleé 'n'\n")

        resp = input("> Respuesta: ").strip().lower()

        if resp == 'n':
            print("Acción cancelada: Sin daño")
            return None
        match resp:
            case "1":
                return {"modulos": leve}
            case "2":
                return {"modulos": limite}
            case "3":
                return {"modulos": excesivo}
            case "4":
                porcentaje = ingresar_porcentaje_danio()
                if porcentaje is not None:
                    return {"porcentaje": porcentaje}
                return None
            case _:
                print("ERROR: Valor no es una opción válida\n")

def ingresar_porcentaje_danio():
    while True:
        resp = input("\n¿Qué porcentaje de los módulos de datos desea invertir? (mayor que 0 y hasta 100)"
                     "\n> Para cancelar la opción tecleé 'n'"
                     "\n> Respuesta: ").strip().lower().replace(",", ".")

        if resp == 'n':
            print("Acción cancelada: Sin daño")
            return None
        try:
            porcentaje = float(resp)
        except ValueError:
            print("ERROR: Valor no es un número\n")
            continue
        if 0 < porcentaje <= 100:
            return porcentaje
        print("ERROR: El porcentaje debe ser mayor que 0 y hasta 100\n")

def mostrar_informe_danio(informe: InformeDanio, nivel_correccion: NivelCorreccion):
    fuera = [(d, t) for d, t in informe.por_bloque if d > t]
    mas_danado, tolera = max(informe.por_bloque, key=lambda b: b[0] - b[1])

    print("############# DAÑO SIMULADO #############")
    print(f"Tipo de daño: {'al azar' if informe.modo == 'azar' else 'mancha'}")
    print(f"Módulos invertidos: {informe.modulos_invertidos} de {informe.total_modulos} "
          f"({informe.modulos_invertidos / informe.total_modulos:.1%})")
    print(f"Bytes dañados: {informe.bytes_danados} de {informe.total_bytes}")
    print(f"Bloques de corrección: {len(informe.por_bloque)} | fuera de su límite: {len(fuera)}")
    print(f"Bloque más afectado: {mas_danado} bytes dañados, tolera {tolera} (nivel {nivel_correccion.value})")

    if informe.recuperable:
        print("Resultado esperado: todos los bloques están dentro de su límite, el QR debería poder leerse.")
        print("(Un lector real puede fallar un poco antes del límite teórico.)")
    else:
        print("Resultado esperado: algún bloque supera su límite, el QR NO debería poder leerse.")

def main():
    menu()

    print("\nFinalización del Programa: Tenga buen día")

if __name__ == "__main__":
    main()