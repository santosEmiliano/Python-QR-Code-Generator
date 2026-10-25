"""Dañoo simulado a un QR ya generado, para comprobar que la correccion de errores
funciona correctamente.

Invierte una parte de los modulos de datos y de correccion de la matriz final. Los
patrones fijos (localizadores, temporizacion, alineacion) y la informacion de
formato/version no se modifican.

Dos modos, los dos invierten exactamente la misma cantidad de modulos:
- "azar":   modulos sueltos repartidos por todo el QR.
- "bloque": una mancha continua. Como los bytes de los bloques van intercalados,
            una mancha dana entre varios bloques en vez de concentrarlo en uno.

El informe dice cuantos bytes quedaron danados en cada bloque y cuantos tolera ese
bloque (bytes de correccion // 2). Si todos los bloques estan dentro de su limite,
un lector deberia poder recuperar el mensaje.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .contrato import ParametroInvalido, ResultadoQR
from .reed_solomon import intercalar
from .tablas import bloques_correccion, total_bytes

__all__ = ["InformeDanio", "danar_matriz", "celdas_de_bytes"]

MODOS_DANIO = ("azar", "bloque")


@dataclass(frozen=True)
class InformeDanio:
    """Resultado de danar_matriz, la matriz danada y que tanto se rompio."""

    matriz: list[list[bool]]
    modo: str
    modulos_invertidos: int
    total_modulos: int                    # modulos de datos + correccion del QR
    bytes_danados: int
    total_bytes: int
    por_bloque: list[tuple[int, int]]     # (bytes danados, bytes que tolera), por bloque
    recuperable: bool                     # todos los bloques dentro de su limite


def celdas_de_bytes(reservado: list[list[bool]], version: int) -> list[tuple[int, int]]:
    """Las celdas (fila, columna) de los bits del mensaje, en el orden en que
    matriz.py los coloca (zigzag desde abajo a la derecha). Los bits de relleno final no se incluyen."""
    n = len(reservado)
    celdas: list[tuple[int, int]] = []
    fila = n - 1
    columna = n - 1
    hacia_arriba = True
    while columna > 0:
        if columna == 6:
            columna -= 1
        for _ in range(n):
            for c in (columna, columna - 1):
                if not reservado[fila][c]:
                    celdas.append((fila, c))
            fila += -1 if hacia_arriba else 1
            if fila < 0 or fila >= n:
                break
        columna -= 2
        hacia_arriba = not hacia_arriba
        fila += -1 if hacia_arriba else 1
    return celdas[: total_bytes(version) * 8]


def _bloque_de_cada_byte(resultado: ResultadoQR) -> tuple[list[int], list[int]]:
    """Para cada byte de la secuencia, el bloque al que pertenece, y los bytes de
    correccion de cada bloque. Se apoya en intercalar() para respetar su orden."""
    mensaje = resultado.mensaje
    estructura = bloques_correccion(mensaje.version, mensaje.nivel_correccion)
    marcas = []
    ec_por_bloque = []
    for cuantos, total, datos in estructura:
        for _ in range(cuantos):
            numero = len(marcas)
            marcas.append(([numero] * datos, [numero] * (total - datos)))
            ec_por_bloque.append(total - datos)
    return intercalar(marcas), ec_por_bloque


def _elegir_azar(celdas: list[tuple[int, int]], k: int, azar: random.Random):
    return azar.sample(celdas, k)


def _elegir_bloque(celdas: list[tuple[int, int]], k: int, azar: random.Random):
    """Las k celdas mas cercanas a un centro elegido al azar (distancia de
    Chebyshev, desempata por Manhattan), es una mancha contigua y cuadrada."""
    cf, cc = azar.choice(celdas)
    return sorted(
        celdas,
        key=lambda p: (max(abs(p[0] - cf), abs(p[1] - cc)), abs(p[0] - cf) + abs(p[1] - cc)),
    )[:k]


def danar_matriz(
    resultado: ResultadoQR,
    porcentaje: float,
    modo: str = "azar",
    semilla: int | None = None,
) -> InformeDanio:
    """Invierte "porcentaje" % de los modulos de datos y correccion de
    "resultado.final.matriz", devuelve una matriz nueva.

    - `porcentaje`: mayor que 0 y hasta 100. Siempre se invierte al menos un modulo.
    - `modo`: "azar" o "bloque".
    - `semilla`: para repetir el mismo daño, None usa uno distinto cada vez.
    """
    if modo not in MODOS_DANIO:
        raise ParametroInvalido(f"modo de daño desconocido: {modo!r} (usa {MODOS_DANIO})")
    if isinstance(porcentaje, bool) or not isinstance(porcentaje, (int, float)) \
            or not (0 < porcentaje <= 100):
        raise ParametroInvalido(
            f"el porcentaje debe ser mayor que 0 y hasta 100, se recibio {porcentaje!r}"
        )

    version = resultado.mensaje.version
    celdas = celdas_de_bytes(resultado.matriz_ordenada.reservado, version)
    total = len(celdas)
    k = min(total, max(1, round(total * porcentaje / 100)))

    azar = random.Random(semilla)
    elegir = _elegir_azar if modo == "azar" else _elegir_bloque
    elegidas = elegir(celdas, k, azar)

    matriz = [fila[:] for fila in resultado.final.matriz]
    for fila, columna in elegidas:
        matriz[fila][columna] = not matriz[fila][columna]

    indice_de_celda = {celda: i for i, celda in enumerate(celdas)}
    bytes_tocados = {indice_de_celda[c] // 8 for c in elegidas}
    bloque_de, ec_por_bloque = _bloque_de_cada_byte(resultado)
    danados = [0] * len(ec_por_bloque)
    for b in bytes_tocados:
        danados[bloque_de[b]] += 1
    por_bloque = [(d, ec // 2) for d, ec in zip(danados, ec_por_bloque)]

    return InformeDanio(
        matriz=matriz,
        modo=modo,
        modulos_invertidos=k,
        total_modulos=total,
        bytes_danados=len(bytes_tocados),
        total_bytes=total // 8,
        por_bloque=por_bloque,
        recuperable=all(d <= tolera for d, tolera in por_bloque),
    )
