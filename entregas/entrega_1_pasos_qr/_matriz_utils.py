"""Helpers compartidos por los pasos 5 y 6: matriz base con patrones fijos.

No es uno de los 6 pasos pedidos; es la parte de dibujo que ambos pasos
reutilizan para no repetir el mismo codigo dos veces.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qr.tablas import posiciones_alineacion  # noqa: E402

VERSION = 2  # version 2 = 25x25, la que pide el paso a paso del proyecto.
LADO = 21 + 4 * (VERSION - 1)  # 25


def nueva_matriz(n: int = LADO) -> list[list[bool]]:
    """Cuadrícula de n x n, todo en False (blanco)."""
    return [[False for _ in range(n)] for _ in range(n)]


def dibujar_localizador(matriz: list[list[bool]], fila: int, columna: int) -> None:
    """Patron de posicion (finder) de 7x7: borde oscuro, anillo claro, nucleo oscuro."""
    for i in range(7):
        for j in range(7):
            oscuro = i in (0, 6) or j in (0, 6) or (2 <= i <= 4 and 2 <= j <= 4)
            matriz[fila + i][columna + j] = oscuro


def dibujar_alineacion(matriz: list[list[bool]], fila: int, columna: int) -> None:
    """Patron de alineacion de 5x5: borde oscuro con centro oscuro."""
    for di in range(-2, 3):
        for dj in range(-2, 3):
            borde = abs(di) == 2 or abs(dj) == 2
            centro = di == 0 and dj == 0
            matriz[fila + di][columna + dj] = borde or centro


def celdas_ocupadas(n: int = LADO) -> set[tuple[int, int]]:
    """Coordenadas ya usadas por localizadores + alineacion (para el paso 6)."""
    ocupadas = set()
    for f, c in ((0, 0), (0, n - 7), (n - 7, 0)):
        ocupadas.update((f + i, c + j) for i in range(7) for j in range(7))
    for f, c in posicion_alineacion_util(n):
        ocupadas.update((f + di, c + dj) for di in range(-2, 3) for dj in range(-2, 3))
    return ocupadas


def posicion_alineacion_util(n: int = LADO) -> list[tuple[int, int]]:
    """Centros reales de alineacion para esta version (sin los que pisan un finder)."""
    centros = posiciones_alineacion(VERSION)
    if not centros:
        return []
    ultimo = len(centros) - 1
    resultado = []
    for i, fila in enumerate(centros):
        for j, columna in enumerate(centros):
            if (i == 0 and j == 0) or (i == 0 and j == ultimo) or (i == ultimo and j == 0):
                continue
            resultado.append((fila, columna))
    return resultado


def imprimir_matriz(matriz: list[list[bool]]) -> None:
    for fila in matriz:
        print("".join("█" if celda else "·" for celda in fila))


def crear_matriz_con_alineacion() -> list[list[bool]]:
    """Matriz base: los 3 finders + el patron de alineacion de esta version."""
    matriz = nueva_matriz(LADO)

    dibujar_localizador(matriz, 0, 0)
    dibujar_localizador(matriz, 0, LADO - 7)
    dibujar_localizador(matriz, LADO - 7, 0)

    for fila, columna in posicion_alineacion_util(LADO):
        dibujar_alineacion(matriz, fila, columna)

    return matriz
