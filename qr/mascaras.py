"""Etapas 6-7 del flujo (P4): mascara e info de formato/version.

Recibe la `MatrizOrdenada` de P3 (datos ya colocados, sin mascara, con los
huecos de formato/version en False) y devuelve la `MatrizFinal` del contrato.

Pasos:
1. Para cada mascara candidata (0..7, o solo la que pidio el usuario):
   aplicarla a las celdas NO reservadas, escribir formato (+ version en v7+)
   y puntuar con las 4 reglas de penalizacion.
2. Quedarse con la de menor puntaje.

Referencia: ISO/IEC 18004, 8.8 (mascaras), 8.9 (evaluacion), 8.10 (formato/version).
"""

from __future__ import annotations

from .contrato import MatrizFinal, MatrizOrdenada, NivelCorreccion, ParametroInvalido
from .matriz import _celdas_formato, lado
from .tablas import indicador_nivel

__all__ = [
    "finalizar_matriz",
    "aplicar_mascara",
    "bits_formato",
    "bits_version",
    "puntaje",
    "todas_las_mascaras",
]

# Polinomios generadores de los codigos BCH.
_GEN_FORMATO = 0b10100110111          # BCH(15,5), 0x537
_MASCARA_FORMATO = 0b101010000010010  # XOR fijo para que el formato nunca sea todo ceros
_GEN_VERSION = 0b1111100100101        # Golay(18,6), 0x1F25


# Las 8 mascaras (i = fila, j = columna). True = invertir ese modulo.
_CONDICIONES = (
    lambda i, j: (i + j) % 2 == 0,
    lambda i, j: i % 2 == 0,
    lambda i, j: j % 3 == 0,
    lambda i, j: (i + j) % 3 == 0,
    lambda i, j: (i // 2 + j // 3) % 2 == 0,
    lambda i, j: (i * j) % 2 + (i * j) % 3 == 0,
    lambda i, j: ((i * j) % 2 + (i * j) % 3) % 2 == 0,
    lambda i, j: ((i + j) % 2 + (i * j) % 3) % 2 == 0,
)


def aplicar_mascara(
    matriz: list[list[bool]], reservado: list[list[bool]], mascara: int
) -> list[list[bool]]:
    """Copia de `matriz` con la mascara aplicada (XOR) solo a las celdas con
    reservado == False. No muta la entrada."""
    if not isinstance(mascara, int) or not (0 <= mascara <= 7):
        raise ParametroInvalido(f"mascara debe ser un entero de 0 a 7, se recibio {mascara!r}")
    cond = _CONDICIONES[mascara]
    n = len(matriz)
    return [
        [matriz[i][j] ^ (cond(i, j) and not reservado[i][j]) for j in range(n)]
        for i in range(n)
    ]


def _resto_bch(dato: int, generador: int, bits_resto: int) -> int:
    """Resto de dividir (dato << bits_resto) entre `generador` en GF(2)."""
    valor = dato << bits_resto
    largo_gen = generador.bit_length()
    while valor.bit_length() >= largo_gen:
        valor ^= generador << (valor.bit_length() - largo_gen)
    return valor


def bits_formato(nivel_correccion: NivelCorreccion, mascara: int) -> list[int]:
    """15 bits de formato, MSB-first: (2 bits nivel + 3 bits mascara) + 10 bits
    BCH, todo XOR 101010000010010."""
    nivel = indicador_nivel(nivel_correccion)
    dato = (nivel[0] << 4) | (nivel[1] << 3) | mascara
    valor = ((dato << 10) | _resto_bch(dato, _GEN_FORMATO, 10)) ^ _MASCARA_FORMATO
    return [(valor >> (14 - k)) & 1 for k in range(15)]


def bits_version(version: int) -> list[int] | None:
    """18 bits de version, MSB-first: 6 bits de version + 12 bits Golay.
    None de v1 a v6."""
    if version < 7:
        return None
    valor = (version << 12) | _resto_bch(version, _GEN_VERSION, 12)
    return [(valor >> (17 - k)) & 1 for k in range(18)]


def _escribir_formato(matriz: list[list[bool]], n: int, bits: list[int]) -> None:
    """Escribe los 15 bits (MSB-first) en las 2 copias de formato, en el orden
    en que las lista matriz._celdas_formato (15 + 15 celdas)."""
    for k, (fila, columna) in enumerate(_celdas_formato(n)):
        matriz[fila][columna] = bits[k % 15] == 1


def _escribir_version(matriz: list[list[bool]], n: int, bits: list[int]) -> None:
    """Escribe los 18 bits de version en los bloques de 6x3 (arriba-derecha) y
    3x6 (abajo-izquierda). El bit i (0 = LSB) va en (i//3, n-11+i%3) y su
    espejo (n-11+i%3, i//3)."""
    for i in range(18):
        oscuro = bits[17 - i] == 1
        fila = i // 3
        columna = n - 11 + i % 3
        matriz[fila][columna] = oscuro
        matriz[columna][fila] = oscuro


def _penalizacion_rachas(matriz: list[list[bool]]) -> int:
    """Regla 1: 5 o mas modulos seguidos del mismo color (filas y columnas).
    Cada racha suma 3 + (largo - 5)."""
    n = len(matriz)
    total = 0
    for lineas in (matriz, [list(c) for c in zip(*matriz)]):
        for linea in lineas:
            racha = 1
            for k in range(1, n):
                if linea[k] == linea[k - 1]:
                    racha += 1
                else:
                    if racha >= 5:
                        total += 3 + (racha - 5)
                    racha = 1
            if racha >= 5:
                total += 3 + (racha - 5)
    return total


def _penalizacion_bloques(matriz: list[list[bool]]) -> int:
    """Regla 2: cada bloque 2x2 del mismo color suma 3."""
    n = len(matriz)
    total = 0
    for i in range(n - 1):
        for j in range(n - 1):
            if matriz[i][j] == matriz[i][j + 1] == matriz[i + 1][j] == matriz[i + 1][j + 1]:
                total += 3
    return total


def _penalizacion_patron(matriz: list[list[bool]]) -> int:
    """Regla 3: patron 1011101 (oscuro-claro-oscuro-oscuro-oscuro-claro-oscuro)
    con 4 modulos claros de un lado. Cada aparicion suma 40."""
    n = len(matriz)
    patron_a = [True, False, True, True, True, False, True, False, False, False, False]
    patron_b = patron_a[::-1]
    total = 0
    for lineas in (matriz, [list(c) for c in zip(*matriz)]):
        for linea in lineas:
            for k in range(n - 10):
                tramo = linea[k : k + 11]
                if tramo == patron_a:
                    total += 40
                if tramo == patron_b:
                    total += 40
    return total


def _penalizacion_balance(matriz: list[list[bool]]) -> int:
    """Regla 4: que tan lejos esta la proporcion de oscuros del 50 %.
    10 puntos por cada 5 % de desviacion."""
    n = len(matriz)
    oscuros = sum(sum(fila) for fila in matriz)
    total = n * n
    k = (abs(oscuros * 20 - total * 10) + total - 1) // total - 1
    return 10 * max(k, 0)


def puntaje(matriz: list[list[bool]]) -> int:
    """Puntaje de penalizacion de una matriz completa. Menor = mejor."""
    return (
        _penalizacion_rachas(matriz)
        + _penalizacion_bloques(matriz)
        + _penalizacion_patron(matriz)
        + _penalizacion_balance(matriz)
    )


def _armar(
    ordenada: MatrizOrdenada, version: int, nivel_correccion: NivelCorreccion, mascara: int
) -> tuple[list[list[bool]], list[int], list[int] | None]:
    """Aplica una mascara concreta y escribe formato/version.
    Devuelve (matriz, bits_formato, bits_version)."""
    n = lado(version)
    matriz = aplicar_mascara(ordenada.matriz, ordenada.reservado, mascara)
    bf = bits_formato(nivel_correccion, mascara)
    _escribir_formato(matriz, n, bf)
    bv = bits_version(version)
    if bv is not None:
        _escribir_version(matriz, n, bv)
    return matriz, bf, bv


def finalizar_matriz(
    ordenada: MatrizOrdenada,
    version: int,
    nivel_correccion: NivelCorreccion,
    mascara: int | None = None,
) -> MatrizFinal:
    """Etapas 6-7 (P4) en una. Devuelve la `MatrizFinal` del contrato.

    - `ordenada`: salida de P3. No se muta.
    - `version`, `nivel_correccion`: los de `MensajeCodificado`.
    - `mascara`: 0..7 para forzar una; None para elegir la de menor puntaje.
    """
    n = lado(version)  # valida la version
    if len(ordenada.matriz) != n:
        raise ParametroInvalido(
            f"la matriz mide {len(ordenada.matriz)} y la v{version} mide {n}"
        )
    if not isinstance(nivel_correccion, NivelCorreccion):
        raise ParametroInvalido(f"nivel de correccion desconocido: {nivel_correccion!r}")
    if mascara is not None and (not isinstance(mascara, int) or not (0 <= mascara <= 7)):
        raise ParametroInvalido(
            f"mascara debe ser un entero de 0 a 7 o None, se recibio {mascara!r}"
        )

    candidatas = range(8) if mascara is None else [mascara]
    mejor = None
    for m in candidatas:
        matriz, bf, bv = _armar(ordenada, version, nivel_correccion, m)
        pts = puntaje(matriz)
        if mejor is None or pts < mejor[0]:  # empate: gana la de numero menor
            mejor = (pts, m, matriz, bf, bv)

    _, m, matriz, bf, bv = mejor
    return MatrizFinal(matriz=matriz, mascara=m, bits_formato=bf, bits_version=bv)


# ---------------------------------------------------------------------------
# EXTRA (no lo pide el contrato): las 8 versiones del QR, una por mascara.
# ---------------------------------------------------------------------------
def todas_las_mascaras(
    ordenada: MatrizOrdenada,
    version: int,
    nivel_correccion: NivelCorreccion,
) -> list[MatrizFinal]:
    """Devuelve las 8 `MatrizFinal`, una por cada mascara, en orden 0..7.
    No elige ninguna: cada una sale con su propio formato/version."""
    return [finalizar_matriz(ordenada, version, nivel_correccion, m) for m in range(8)]