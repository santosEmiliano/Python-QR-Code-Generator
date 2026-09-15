"""Entrega 1 - Paso 5: acomodo de datos (simulacion de matriz QR).

Arma una matriz de 25x25 (version 2), dibuja los 3 patrones de posicion
(finders) y coloca el patron de alineacion que le corresponde a esa version.
"""

from _matriz_utils import LADO, crear_matriz_con_alineacion, imprimir_matriz

if __name__ == "__main__":
    matriz = crear_matriz_con_alineacion()
    print(f"Matriz {LADO}x{LADO} con los 3 finders y el patron de alineacion:\n")
    imprimir_matriz(matriz)
