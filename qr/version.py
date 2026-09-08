"""Etapas 2 y 3 del flujo (P1): seleccion de version y armado del bitstream.

Toma el `AnalisisTexto` de la etapa 1 (entrada.py) y produce el `MensajeCodificado`
del contrato, el texto convertido a bits, con sus etiquetas y su relleno, listo
para que P2 le calcule el respaldo.
"""

from __future__ import annotations

from .contrato import Modo, NivelCorreccion, ParametroInvalido, TextoNoEntra
from .entrada import AnalisisTexto
from .tablas import (
    CARACTERES_ALFANUMERICOS,
    bits_cuenta_caracteres,
    capacidad_bytes_datos,
    indicador_modo,
)

__all__ = [
    "codificar_segmento",
    "elegir_version",
]


def _int_a_bits(valor: int, ancho: int) -> list[int]:
    """`valor` como lista de `ancho` bits 0/1, MSB-first (el mas significativo
    primero). Se asume 0 <= valor < 2**ancho."""
    return [(valor >> (ancho - 1 - i)) & 1 for i in range(ancho)]


def _codificar_numerico(texto: str) -> list[int]:
    """Digitos de a 3: cada grupo completo son 10 bits. Un resto de 2 digitos
    toma 7 bits, un resto de 1 digito toma 4 bits. ISO/IEC 18004, 8.4.2."""
    bits: list[int] = []
    for inicio in range(0, len(texto), 3):
        grupo = texto[inicio : inicio + 3]
        ancho = {3: 10, 2: 7, 1: 4}[len(grupo)]
        bits += _int_a_bits(int(grupo), ancho)
    return bits


def _codificar_alfanumerico(texto: str) -> list[int]:
    """Caracteres de a 2: el par vale  45*primero + segundo  en 11 bits. Un
    caracter suelto al final son 6 bits. El valor de cada caracter es su
    posicion en CARACTERES_ALFANUMERICOS. ISO/IEC 18004, 8.4.3."""
    valores = [CARACTERES_ALFANUMERICOS.index(caracter) for caracter in texto]
    bits: list[int] = []
    for inicio in range(0, len(valores), 2):
        par = valores[inicio : inicio + 2]
        if len(par) == 2:
            bits += _int_a_bits(par[0] * 45 + par[1], 11)
        else:
            bits += _int_a_bits(par[0], 6)
    return bits


def _codificar_byte(texto: str) -> list[int]:
    """Cada byte UTF-8 del texto son 8 bits. ISO/IEC 18004, 8.4.4 (sin ECI)."""
    bits: list[int] = []
    for byte in texto.encode("utf-8"):
        bits += _int_a_bits(byte, 8)
    return bits


def codificar_segmento(analisis: AnalisisTexto) -> list[int]:
    """Convierte el texto a los bits de datos que van dentro del mensaje.

    Son SOLO los datos, no incluye el indicador de modo ni el de cantidad de
    caracteres. La cantidad de bits depende del modo, no de la version.

    `analisis` viene de `analizar_texto`, que ya garantizo que el texto es valido
    para `analisis.modo`, aca no se vuelve a validar.
    """
    if analisis.modo == Modo.NUMERICO:
        return _codificar_numerico(analisis.texto)
    if analisis.modo == Modo.ALFANUMERICO:
        return _codificar_alfanumerico(analisis.texto)
    return _codificar_byte(analisis.texto)


def _bits_necesarios(analisis: AnalisisTexto, version: int, bits_datos: int) -> int:
    """Cuantos bits ocupa el mensaje (sin terminador ni relleno) en esa version.

    Es  indicador de modo (4) + indicador de cantidad de caracteres + datos.
    El indicador de cantidad cambia de ancho segun el tramo de version, por eso
    depende de `version`.
    """
    return (
        len(indicador_modo(analisis.modo))
        + bits_cuenta_caracteres(version, analisis.modo)
        + bits_datos
    )


def elegir_version(
    analisis: AnalisisTexto,
    nivel_correccion: NivelCorreccion,
    version_minima: int | None = None,
) -> int:
    """Devuelve la version (tamano) mas chica donde entra el mensaje.

    Prueba desde la v1 hacia arriba y se queda con la primera donde  modo + cantidad + datos  
    cabe en la capacidad de datos de esa version y nivel de correccion. El terminador y el relleno se
    agregan despues y siempre caben, porque solo ocupan el hueco que sobra.

    - `version_minima` fuera de 1..40 -> ParametroInvalido.
    - El texto no entra en ninguna version soportada -> TextoNoEntra.
    """
    if version_minima is not None:
        if not isinstance(version_minima, int) or not (1 <= version_minima <= 40):
            raise ParametroInvalido(
                f"version_minima debe ser un entero de 1 a 40 o None, "
                f"se recibio {version_minima!r}"
            )

    bits_datos = len(codificar_segmento(analisis))
    for version in range(version_minima or 1, 41):
        capacidad_bits = capacidad_bytes_datos(version, nivel_correccion) * 8
        if _bits_necesarios(analisis, version, bits_datos) <= capacidad_bits:
            return version

    raise TextoNoEntra(
        f"el texto ({analisis.cantidad_caracteres} caracteres en modo "
        f"{analisis.modo.value}) no entra en ninguna version con nivel "
        f"{nivel_correccion.value}"
    )
