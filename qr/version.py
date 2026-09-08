"""Etapas 2 y 3 del flujo (P1): seleccion de version y armado del bitstream.

Toma el `AnalisisTexto` de la etapa 1 (entrada.py) y produce el `MensajeCodificado`
del contrato, el texto convertido a bits, con sus etiquetas y su relleno, listo
para que P2 le calcule el respaldo.
"""

from __future__ import annotations

from .contrato import Modo
from .entrada import AnalisisTexto
from .tablas import CARACTERES_ALFANUMERICOS

__all__ = [
    "codificar_segmento",
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
