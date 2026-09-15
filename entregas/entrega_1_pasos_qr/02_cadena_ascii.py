"""Entrega 1 - Paso 2: convertir texto a ASCII y unir los numeros en una sola cadena."""


def texto_a_cadena_ascii(texto: str) -> str:
    """Concatena el codigo ASCII decimal de cada caracter en una sola cadena.

    Ejemplo: "AB" -> "6566" (65 de 'A' seguido de 66 de 'B').
    """
    return "".join(str(ord(caracter)) for caracter in texto)


if __name__ == "__main__":
    texto = input("Texto a codificar: ")
    cadena = texto_a_cadena_ascii(texto)
    print(f"Cadena ASCII: {cadena}")
