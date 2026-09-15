"""Entrega 1 - Paso 6: insertar los datos ASCII dentro de la matriz.

Toma la matriz del paso 5 (finders + alineacion ya colocados) y coloca los
bits ASCII del texto (1 = negro, 0 = blanco) con el recorrido real del QR,
empezando en la esquina inferior derecha y sube en columnas de a pares, en
zigzag, saltando las celdas ya ocupadas por los patrones fijos.
"""

from _matriz_utils import LADO, celdas_ocupadas, crear_matriz_con_alineacion, imprimir_matriz


def texto_a_bits(texto: str) -> list[int]:
    """Cada caracter -> su ASCII en 8 bits, todos los bits concatenados."""
    return [
        int(bit)
        for caracter in texto
        for bit in format(ord(caracter), "08b")
    ]


def insertar_datos(matriz: list[list[bool]], bits: list[int]) -> list[list[bool]]:
    """Devuelve una copia de `matriz` con `bits` colocados con el recorrido zigzag.

    Empieza en la esquina inferior derecha y avanza en columnas de a dos:
    sube serpenteando hasta arriba, se corre a la izquierda, baja, y asi
    hasta llegar a la columna 0. Cada celda ya ocupada (finder o alineacion)
    se saltea sin gastar un bit.
    """
    n = len(matriz)
    ocupadas = celdas_ocupadas(n)
    resultado = [fila[:] for fila in matriz]

    indice = 0
    total = len(bits)
    fila = n - 1
    columna = n - 1
    hacia_arriba = True
    while columna > 0:
        for _ in range(n):
            for c in (columna, columna - 1):
                if (fila, c) not in ocupadas and indice < total:
                    resultado[fila][c] = bits[indice] == 1
                    indice += 1
            fila += -1 if hacia_arriba else 1
            if fila < 0 or fila >= n:
                break
        columna -= 2
        hacia_arriba = not hacia_arriba
        fila += -1 if hacia_arriba else 1

    if indice < total:
        print(f"Aviso: sobraron {total - indice} bits, no entraron en la matriz.")

    return resultado


if __name__ == "__main__":
    texto = input("Texto a insertar en la matriz: ")
    bits = texto_a_bits(texto)

    matriz_base = crear_matriz_con_alineacion()
    matriz_final = insertar_datos(matriz_base, bits)

    print(f"\nMatriz {LADO}x{LADO} con los datos ASCII de \"{texto}\" insertados:\n")
    imprimir_matriz(matriz_final)
