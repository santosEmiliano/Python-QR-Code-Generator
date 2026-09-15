"""Entrega 1 - Paso 1: convertir texto a ASCII y guardarlo en un vector."""


def texto_a_vector_ascii(texto: str) -> list[int]:
    """Devuelve una lista con el codigo ASCII de cada caracter de `texto`."""
    return [ord(caracter) for caracter in texto]


if __name__ == "__main__":
    texto = input("Texto a codificar: ")
    vector = texto_a_vector_ascii(texto)
    print(f"Vector ASCII: {vector}")
