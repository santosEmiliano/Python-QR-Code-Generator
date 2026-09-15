"""Entrega 1 - Paso 4: diccionario que relaciona cada caracter con su ASCII."""


def texto_a_diccionario_ascii(texto: str) -> dict[str, int]:
    """Devuelve {caracter: codigo_ascii} por cada caracter distinto de `texto`."""
    return {caracter: ord(caracter) for caracter in texto}


if __name__ == "__main__":
    texto = input("Texto a codificar: ")
    diccionario = texto_a_diccionario_ascii(texto)
    for caracter, codigo in diccionario.items():
        print(f"'{caracter}' -> {codigo}")
