"""Etapa 5 del flujo (P3): armado del tablero y colocado de datos en zigzag.

Recibe la `secuencia` de P2 (mensaje + respaldo, ya intercalada) y la version,
y devuelve la `MatrizOrdenada` del contrato: la cuadricula con los patrones
fijos dibujados y los datos colocados, pero SIN mascara y con los huecos de la
info de formato/version todavia vacios (en False). P4 los llena despues.

Dibuja, en este orden:

1. Localizadores (finders) + separadores.
2. Patrones de sincronizacion (timing).
3. Patrones de alineacion (segun tablas.posiciones_alineacion).
4. Modulo oscuro.
5. Reserva de zonas de formato (siempre) y de version (v7 en adelante).
6. Colocado de la secuencia en zigzag desde la esquina inferior derecha,
   salteando todo lo reservado y la columna 6 (timing vertical).

Referencia: ISO/IEC 18004, 7.7 (funcion) y 8.5 (colocado). Sin ECI ni kanji.
"""

from __future__ import annotations

from .contrato import MatrizOrdenada, ParametroInvalido
from .tablas import bits_relleno_final, posiciones_alineacion, total_bytes

__all__ = [
    "lado",
    "ordenar_matriz",
]


def lado(version: int) -> int:
    """Lado en modulos del QR de esa version:  n = 21 + 4 * (version - 1).

    La v1 mide 21x21, la v40 mide 177x177.
    """
    if not isinstance(version, int) or not (1 <= version <= 40):
        raise ParametroInvalido(
            f"version debe ser un entero de 1 a 40, se recibio {version!r}"
        )
    return 21 + 4 * (version - 1)


def _nueva_grilla(n: int, valor: bool) -> list[list[bool]]:
    """Grilla nueva de n x n llena con `valor`."""
    return [[valor for _ in range(n)] for _ in range(n)]


def _dibujar_localizador(
    matriz: list[list[bool]], reservado: list[list[bool]], fila: int, columna: int
) -> None:
    """Dibuja un localizador de 7x7 con su esquina superior izquierda en
    (fila, columna): borde externo oscuro, anillo interno claro, nucleo 3x3
    oscuro. Todo queda marcado como reservado."""
    for i in range(7):
        for j in range(7):
            oscuro = i in (0, 6) or j in (0, 6) or (2 <= i <= 4 and 2 <= j <= 4)
            matriz[fila + i][columna + j] = oscuro
            reservado[fila + i][columna + j] = True


def _dibujar_separadores(
    matriz: list[list[bool]], reservado: list[list[bool]], n: int
) -> None:
    """Linea de modulos claros que rodea cada localizador para separarlo de lo
    demas. Incluye la esquina (7, 7) y sus equivalentes."""
    for k in range(8):
        # Arriba-izquierda.
        matriz[7][k] = False
        reservado[7][k] = True
        matriz[k][7] = False
        reservado[k][7] = True
        # Arriba-derecha.
        matriz[7][n - 8 + k] = False
        reservado[7][n - 8 + k] = True
        matriz[k][n - 8] = False
        reservado[k][n - 8] = True
        # Abajo-izquierda.
        matriz[n - 8][k] = False
        reservado[n - 8][k] = True
        matriz[n - 8 + k][7] = False
        reservado[n - 8 + k][7] = True


def _dibujar_sincronizacion(
    matriz: list[list[bool]], reservado: list[list[bool]], n: int
) -> None:
    """Dos lineas que alternan oscuro/claro (empiezan oscuro): fila 6 y columna
    6, entre los separadores (indices 8 a n-9 inclusive)."""
    for k in range(8, n - 8):
        oscuro = k % 2 == 0
        matriz[6][k] = oscuro
        reservado[6][k] = True
        matriz[k][6] = oscuro
        reservado[k][6] = True


def _dibujar_alineacion(
    matriz: list[list[bool]],
    reservado: list[list[bool]],
    centros: list[int],
) -> None:
    """Un patron de 5x5 por cada par de centros (fila, columna): borde oscuro
    con centro oscuro. Los tres pares que caen sobre un localizador (las dos
    primeras combinaciones de esquina) se omiten."""
    if not centros:
        return  # v1: no lleva patrones de alineacion.
    ultimo = len(centros) - 1
    for i, fila in enumerate(centros):
        for j, columna in enumerate(centros):
            if (i == 0 and j == 0) or (i == 0 and j == ultimo) or (i == ultimo and j == 0):
                continue  # pisa un localizador + separador.
            for di in range(-2, 3):
                for dj in range(-2, 3):
                    borde = abs(di) == 2 or abs(dj) == 2
                    centro = di == 0 and dj == 0
                    matriz[fila + di][columna + dj] = borde or centro
                    reservado[fila + di][columna + dj] = True


def _celdas_formato(n: int) -> list[tuple[int, int]]:
    """Las 30 celdas reservadas para la info de formato (15 x 2 copias).

    Copia 1: alrededor del localizador superior-izquierdo. Copia 2: franja
    vertical abajo-izquierda (7 celdas) + franja horizontal arriba-derecha
    (8 celdas). La (8, 6) y la (6, 8) son de sincronizacion, no de formato.
    """
    copia1 = (
        [(8, c) for c in range(6)]
        + [(8, 7), (8, 8), (7, 8)]
        + [(f, 8) for f in (5, 4, 3, 2, 1, 0)]
    )
    copia2 = [(f, 8) for f in range(n - 1, n - 8, -1)] + [
        (8, c) for c in range(n - 8, n)
    ]
    return copia1 + copia2


def _celdas_version(n: int) -> list[tuple[int, int]]:
    """Las 36 celdas reservadas para la info de version (18 x 2 bloques).

    Solo existe de la v7 en adelante: bloque superior-derecho de 6x3 y bloque
    inferior-izquierdo de 3x6.
    """
    return [(f, c) for f in range(6) for c in range(n - 11, n - 8)] + [
        (f, c) for f in range(n - 11, n - 8) for c in range(6)
    ]


def _reservar_zonas(
    matriz: list[list[bool]], reservado: list[list[bool]], n: int, version: int
) -> None:
    """Marca las zonas de formato (siempre) y de version (v7+) como reservadas
    y las deja en False. P4 escribe ahi los bits de formato/version."""
    for fila, columna in _celdas_formato(n):
        matriz[fila][columna] = False
        reservado[fila][columna] = True
    if version >= 7:
        for fila, columna in _celdas_version(n):
            matriz[fila][columna] = False
            reservado[fila][columna] = True


def _a_bits(secuencia: list[int]) -> list[int]:
    """La secuencia de bytes como lista de 0/1, MSB-first dentro de cada byte."""
    return [(byte >> (7 - k)) & 1 for byte in secuencia for k in range(8)]


def _colocar_datos(
    matriz: list[list[bool]], reservado: list[list[bool]], n: int, bits: list[int]
) -> None:
    """Recorre la matriz en columnas de a dos, en zigzag, desde la esquina
    inferior derecha: sube hasta arriba, se corre a la izquierda, baja, y asi.
    Cada celda libre (no reservada) recibe el siguiente bit (1 = oscuro).

    La columna 6 (sincronizacion vertical) se saltea entera. Cuando el camino
    se topa con un patron fijo o una zona reservada, lo saltea y sigue del otro
    lado. Si los bits se acaban antes que las celdas (bits de relleno final),
    lo que sobra queda en False (claro).
    """
    indice = 0
    total = len(bits)
    fila = n - 1
    columna = n - 1
    hacia_arriba = True
    while columna > 0:
        if columna == 6:
            columna -= 1  # saltear la columna de sincronizacion.
        for _ in range(n):
            for c in (columna, columna - 1):
                if not reservado[fila][c]:
                    if indice < total:
                        matriz[fila][c] = bits[indice] == 1
                        indice += 1
            if hacia_arriba:
                fila -= 1
            else:
                fila += 1
            if fila < 0 or fila >= n:
                break
        columna -= 2
        hacia_arriba = not hacia_arriba
        fila += -1 if hacia_arriba else 1


def _validar_secuencia(secuencia: list[int], version: int) -> None:
    """La secuencia tiene que ser exactamente los bytes del QR (mensaje +
    respaldo): enteros 0..255 y del largo de total_bytes(version)."""
    if not isinstance(secuencia, list) or any(
        not isinstance(b, int) or not (0 <= b <= 255) for b in secuencia
    ):
        raise ParametroInvalido(
            "la secuencia debe ser una lista de enteros 0..255 "
            f"(los bytes de P2), se recibio {secuencia!r}"
        )
    esperado = total_bytes(version)
    if len(secuencia) != esperado:
        raise ParametroInvalido(
            f"la secuencia mide {len(secuencia)} bytes y la v{version} "
            f"lleva {esperado} (mensaje + respaldo)"
        )


def ordenar_matriz(secuencia: list[int], version: int) -> MatrizOrdenada:
    """Etapa 5 (P3) en una: arma la cuadricula con patrones fijos y coloca la
    secuencia en zigzag. Devuelve la `MatrizOrdenada` del contrato, lista para
    que P4 la enmascare.

    - `secuencia`: salida de P2 (mensaje + respaldo intercalados). No se muta.
    - `version`: 1..40 (las tablas por-version llegan a v10; arriba de eso,
      `tablas` lanza NotImplementedError hasta transcribir).

    La matriz sale con los huecos de formato/version en False y marcados como
    reservados; la mascara de P4 solo toca celdas con `reservado == False`.
    """
    n = lado(version)  # valida la version (1..40).
    _validar_secuencia(secuencia, version)  # valida largo y rango.

    matriz = _nueva_grilla(n, False)
    reservado = _nueva_grilla(n, False)

    _dibujar_localizador(matriz, reservado, 0, 0)
    _dibujar_localizador(matriz, reservado, 0, n - 7)
    _dibujar_localizador(matriz, reservado, n - 7, 0)
    _dibujar_separadores(matriz, reservado, n)
    _dibujar_sincronizacion(matriz, reservado, n)
    _dibujar_alineacion(matriz, reservado, posiciones_alineacion(version))
    matriz[4 * version + 9][8] = True  # modulo oscuro: siempre negro.
    reservado[4 * version + 9][8] = True
    _reservar_zonas(matriz, reservado, n, version)
    _colocar_datos(matriz, reservado, n, _a_bits(secuencia))

    return MatrizOrdenada(matriz=matriz, reservado=reservado)
