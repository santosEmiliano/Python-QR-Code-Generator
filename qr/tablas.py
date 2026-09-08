"""Consulta pura de las tablas fijas del estándar ISO/IEC 18004.

    - Tabla 1     : bits de relleno finales (remainder bits)
    - Tabla 2     : indicadores de modo
    - Tabla 3     : bits del indicador de cantidad de caracteres
    - Tabla 4     : caracteres alfanuméricos
    - Tablas 5-7  : capacidad de datos por version. nivel y modo
    - Tabla 8     : características de corrección de errores (bloques)
    - Tabla 9     : indicadores de nivel de corrección (para la info de formato)
    - Anexo E     : posiciones de los patrones de alineación

"""

from __future__ import annotations

from .contrato import Modo, NivelCorreccion, ParametroInvalido

__all__ = [
    "CARACTERES_ALFANUMERICOS",
    "bits_cuenta_caracteres",
    "capacidad_bytes_datos",
    "total_bytes",
    "bloques_correccion",
    "posiciones_alineacion",
    "bits_relleno_final",
    "indicador_modo",
    "indicador_nivel",
]

# Constantes

# ----- TABLA 1 -----
# Bits de relleno finales: se agregan sueltos, al final del todo, porque la zona de datos no siempre es múltiplo de 8.
_RELLENO_FINAL_POR_RANGO: tuple[tuple[range, int], ...] = (
    (range(1, 2), 0),    # v1
    (range(2, 7), 7),    # v2-6
    (range(7, 14), 0),   # v7-13
    (range(14, 21), 3),  # v14-20
    (range(21, 28), 4),  # v21-27
    (range(28, 35), 3),  # v28-34
    (range(35, 41), 0),  # v35-40
)

# ----- TABLA 2 -----
# Indicador de modo: 4 bits que van al principio del mensaje.
_INDICADOR_MODO: dict[Modo, tuple[int, int, int, int]] = {
    Modo.NUMERICO:     (0, 0, 0, 1),
    Modo.ALFANUMERICO: (0, 0, 1, 0),
    Modo.BYTE:         (0, 1, 0, 0),
}

# ----- TABLA 3 -----
# Bits del indicador de cantidad de caracteres, según modo y tramo de version.
# El tramo cambia en los cortes v1-9 / v10-26 / v27-40.
_CUENTA_BITS: dict[Modo, tuple[int, int, int]] = {
    #             v1-9  v10-26  v27-40
    Modo.NUMERICO:     (10, 12, 14),
    Modo.ALFANUMERICO: (9, 11, 13),
    Modo.BYTE:         (8, 16, 16),
}

# ----- TABLA 4 -----
# Los 45 caracteres del modo alfanumérico. La posición en esta cadena es el
# valor numérico del carácter (0..44). ISO/IEC 18004, Tabla 5.
CARACTERES_ALFANUMERICOS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"

# ----- TABLA 5 -----
# Tabla de capacidad para datos NUMÉRICOS (0-9)
CAPACIDAD_NUM: dict[int, dict[NivelCorreccion, int]] = {
    1: {
        NivelCorreccion.L: 41,
        NivelCorreccion.M: 34,
        NivelCorreccion.Q: 27,
        NivelCorreccion.H: 17,
    },
    2: {
        NivelCorreccion.L: 77,
        NivelCorreccion.M: 63,
        NivelCorreccion.Q: 48,
        NivelCorreccion.H: 34,
    },
    3: {
        NivelCorreccion.L: 0,
        NivelCorreccion.M: 0,
        NivelCorreccion.Q: 0,
        NivelCorreccion.H: 0,
    },
    4: {
        NivelCorreccion.L: 0,
        NivelCorreccion.M: 0,
        NivelCorreccion.Q: 0,
        NivelCorreccion.H: 0,
    },
    5: {
        NivelCorreccion.L: 0,
        NivelCorreccion.M: 0,
        NivelCorreccion.Q: 0,
        NivelCorreccion.H: 0,
    },
    6: {
        NivelCorreccion.L: 0,
        NivelCorreccion.M: 0,
        NivelCorreccion.Q: 0,
        NivelCorreccion.H: 0,
    },
    7: {
        NivelCorreccion.L: 0,
        NivelCorreccion.M: 0,
        NivelCorreccion.Q: 0,
        NivelCorreccion.H: 0,
    },
    8: {
        NivelCorreccion.L: 0,
        NivelCorreccion.M: 0,
        NivelCorreccion.Q: 0,
        NivelCorreccion.H: 0,
    },
    9: {
        NivelCorreccion.L: 0,
        NivelCorreccion.M: 0,
        NivelCorreccion.Q: 0,
        NivelCorreccion.H: 0,
    },
    10: {
        NivelCorreccion.L: 0,
        NivelCorreccion.M: 0,
        NivelCorreccion.Q: 0,
        NivelCorreccion.H: 0,
    }
}
# ----- TABLA 6 -----

# ----- TABLA 7 -----

# ----- TABLA 8 -----
# Estructura de bloques de corrección. Tabla 9.
# Formato: _EC_BLOQUES[version][nivel] = (bytes_correccion_por_bloque, grupos)
# donde grupos = [(cuantos_bloques, bytes_de_datos_por_bloque), ...]

_EC_BLOQUES: dict[int, dict[NivelCorreccion, tuple[int, list[tuple[int, int]]]]] = {
    1: {
        NivelCorreccion.L: (7,  [(1, 19)]),
        NivelCorreccion.M: (10, [(1, 16)]),
        NivelCorreccion.Q: (13, [(1, 13)]),
        NivelCorreccion.H: (17, [(1, 9)]),
    },
    2: {
        NivelCorreccion.L: (10, [(1, 34)]),
        NivelCorreccion.M: (16, [(1, 28)]),
        NivelCorreccion.Q: (22, [(1, 22)]),
        NivelCorreccion.H: (28, [(1, 16)]),
    },
    3: {
        NivelCorreccion.L: (15, [(1, 55)]),
        NivelCorreccion.M: (26, [(1, 44)]),
        NivelCorreccion.Q: (18, [(2, 17)]),
        NivelCorreccion.H: (22, [(2, 13)]),
    },
    4: {
        NivelCorreccion.L: (20, [(1, 80)]),
        NivelCorreccion.M: (18, [(2, 32)]),
        NivelCorreccion.Q: (26, [(2, 24)]),
        NivelCorreccion.H: (16, [(4, 9)]),
    },
    5: {
        NivelCorreccion.L: (26, [(1, 108)]),
        NivelCorreccion.M: (24, [(2, 43)]),
        NivelCorreccion.Q: (18, [(2, 15), (2, 16)]),
        NivelCorreccion.H: (22, [(2, 11), (2, 12)]),
    },
    6: {
        NivelCorreccion.L: (18, [(2, 68)]),
        NivelCorreccion.M: (16, [(4, 27)]),
        NivelCorreccion.Q: (24, [(4, 19)]),
        NivelCorreccion.H: (28, [(4, 15)]),
    },
    7: {
        NivelCorreccion.L: (20, [(2, 78)]),
        NivelCorreccion.M: (18, [(4, 31)]),
        NivelCorreccion.Q: (18, [(2, 14), (4, 15)]),
        NivelCorreccion.H: (26, [(4, 13), (1, 14)]),
    },
    8: {
        NivelCorreccion.L: (24, [(2, 97)]),
        NivelCorreccion.M: (22, [(2, 38), (2, 39)]),
        NivelCorreccion.Q: (22, [(4, 18), (2, 19)]),
        NivelCorreccion.H: (26, [(4, 14), (2, 15)]),
    },
    9: {
        NivelCorreccion.L: (30, [(2, 116)]),
        NivelCorreccion.M: (22, [(3, 36), (2, 37)]),
        NivelCorreccion.Q: (20, [(4, 16), (4, 17)]),
        NivelCorreccion.H: (24, [(4, 12), (4, 13)]),
    },
    10: {
        NivelCorreccion.L: (18, [(2, 68), (2, 69)]),
        NivelCorreccion.M: (26, [(4, 43), (1, 44)]),
        NivelCorreccion.Q: (24, [(6, 19), (2, 20)]),
        NivelCorreccion.H: (28, [(6, 15), (2, 16)]),
    },
}

# Cantidad total de bytes (datos + corrección) por version. Tabla 9, columna
# "total number of codewords".
_TOTAL_BYTES: dict[int, int] = {
    1: 26, 2: 44, 3: 70, 4: 100, 5: 134,
    6: 172, 7: 196, 8: 242, 9: 292, 10: 346,
}

# ----- TABLA 9 -----
# Indicador de nivel de corrección: 2 bits que van en la info de formato.
# OJO: el orden NO es alfabético. M es 00, no L. Tabla 12.
_INDICADOR_NIVEL: dict[NivelCorreccion, tuple[int, int]] = {
    NivelCorreccion.L: (0, 1),
    NivelCorreccion.M: (0, 0),
    NivelCorreccion.Q: (1, 1),
    NivelCorreccion.H: (1, 0),
}
# ----- Anexo E -----
# Coordenadas (fila = columna) de los centros de los patrones de alineación.
# Se combinan de a pares. Los que caen sobre un patron localizador se omiten.
_ALINEACION: dict[int, list[int]] = {
    1: [],
    2: [6, 18],
    3: [6, 22],
    4: [6, 26],
    5: [6, 30],
    6: [6, 34],
    7: [6, 22, 38],
    8: [6, 24, 42],
    9: [6, 26, 46],
    10: [6, 28, 50],
}

# Version más alta con tablas por-version cargadas.
_VERSION_MAX_CARGADA = 10

# Helpers privados

def _validar_version(version: int) -> None:
    """Una version válida del estándar es un entero de 1 a 40."""
    if not isinstance(version, int) or not (1 <= version <= 40):
        raise ParametroInvalido(
            f"version debe ser un entero de 1 a 40, se recibió {version!r}"
        )

def _exigir_cargada(version: int) -> None:
    """Corta con un mensaje claro si se pide una version todavía sin transcribir."""
    _validar_version(version)
    if version > _VERSION_MAX_CARGADA:
        raise NotImplementedError(
            f"las tablas por-version solo están cargadas hasta la v{_VERSION_MAX_CARGADA}; "
            f"falta transcribir la v{version} de ISO/IEC 18004 (Tablas 7 y 9, Anexo E)"
        )


# API pública

def bits_cuenta_caracteres(version: int, modo: Modo) -> int:
    """Cuantos bits ocupa el número "cantidad de caracteres" dentro del mensaje.

    Depende del modo y del tramo de version (v1-9 / v10-26 / v27-40).
    """
    _validar_version(version)
    if modo not in _CUENTA_BITS:
        raise ParametroInvalido(f"modo sin indicador de cantidad definido: {modo!r}")
    tramo = 0 if version <= 9 else (1 if version <= 26 else 2)
    return _CUENTA_BITS[modo][tramo]

def capacidad_bytes_datos(version: int, nivel_correccion: NivelCorreccion) -> int:
    """Cuantos bytes de mensaje (sin contar el respaldo) caben en ese QR con ese
    nivel de corrección. Es lo que P1 tiene que llenar exacto con datos + relleno.
    """
    _exigir_cargada(version)
    _ec, grupos = _EC_BLOQUES[version][nivel_correccion]
    return sum(cuantos * datos_por_bloque for cuantos, datos_por_bloque in grupos)

def total_bytes(version: int) -> int:
    """Cuantos bytes tiene el QR en total: mensaje + respaldo."""
    _exigir_cargada(version)
    return _TOTAL_BYTES[version]

def bloques_correccion(
    version: int, nivel_correccion: NivelCorreccion
) -> list[tuple[int, int, int]]:
    """Como se parte el mensaje en bloques para calcular el respaldo.

    Devuelve una lista de tuples (cuantos_bloques, bytes_totales_por_bloque,
    bytes_de_datos_por_bloque), en el orden en que los define el estándar.
    "Bytes_totales" = bytes_de_datos + bytes_de_correccion.
    """
    _exigir_cargada(version)
    ec_por_bloque, grupos = _EC_BLOQUES[version][nivel_correccion]
    return [
        (cuantos, datos_por_bloque + ec_por_bloque, datos_por_bloque)
        for cuantos, datos_por_bloque in grupos
    ]

def posiciones_alineacion(version: int) -> list[int]:
    """Coordenadas de los centros de los patrones de alineación (fila = columna).

    Se combinan de a pares. La v1 no tiene patrones de alineacion: devuelve [].
    """
    _exigir_cargada(version)
    return list(_ALINEACION[version])

def bits_relleno_final(version: int) -> int:
    """Bits de relleno que se agregan sueltos al final del todo (0, 3, 4 o 7).

    Existen porque la zona de datos del QR no siempre es múltiplo de 8.
    """
    _validar_version(version)
    for rango, cantidad in _RELLENO_FINAL_POR_RANGO:
        if version in rango:
            return cantidad
    raise AssertionError("rango de version no cubierto")  # inalcanzable

def indicador_modo(modo: Modo) -> list[int]:
    """Los 4 bits que definen el tipo numérico / alfanumérico / byte. MSB-first."""
    if modo not in _INDICADOR_MODO:
        raise ParametroInvalido(f"modo sin indicador definido: {modo!r}")
    return list(_INDICADOR_MODO[modo])

def indicador_nivel(nivel_correccion: NivelCorreccion) -> list[int]:
    """Los 2 bits del nivel de corrección, para la etiqueta de formato."""
    if nivel_correccion not in _INDICADOR_NIVEL:
        raise ParametroInvalido(f"nivel de corrección desconocido: {nivel_correccion!r}")
    return list(_INDICADOR_NIVEL[nivel_correccion])
