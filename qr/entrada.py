"""Etapa 1 del flujo (P1): analisis del texto de entrada y seleccion de modo.

Recibe el texto que quiere codificar el usuario y decide en que modo
conviene guardarlo (numerico, alfanumerico o byte). NO arma bits ni elige
version: eso es la etapa 2 (version.py).
"""

from __future__ import annotations

from dataclasses import dataclass

from .contrato import Modo, ModoPedido, ParametroInvalido, TextoNoValidoParaModo
from .tablas import CARACTERES_ALFANUMERICOS

__all__ = [
    "detectar_modo",
    "validar_texto_para_modo",
    "AnalisisTexto",
    "analizar_texto",
]

# Conjuntos para chequear pertenencia caracter por caracter.
_DIGITOS = frozenset("0123456789")
_ALFANUMERICOS = frozenset(CARACTERES_ALFANUMERICOS)  # incluye a los digitos

def detectar_modo(texto: str) -> Modo:
    """Elige el modo mas compacto que sirva para `texto`.

    - solo digitos 0-9                         -> Modo.NUMERICO
    - solo caracteres del set alfanumerico     -> Modo.ALFANUMERICO
      (digitos, A-Z mayusculas y  " $%*+-./:")
    - cualquier otra cosa                      -> Modo.BYTE
      (minusculas, acentos, emojis, etc.)
    """
    if all(caracter in _DIGITOS for caracter in texto):
        return Modo.NUMERICO
    if all(caracter in _ALFANUMERICOS for caracter in texto):
        return Modo.ALFANUMERICO
    return Modo.BYTE


def validar_texto_para_modo(texto: str, modo: Modo) -> None:
    """Verifica que 'texto' se pueda codificar en 'modo'.

    No devuelve nada. Si el texto tiene algun caracter que ese modo no admite,
    lanza TextoNoValidoParaModo nombrando los caracteres que sobran.

    Modo.BYTE admite cualquier texto (se codifica como bytes UTF-8), asi que
    nunca falla. Se usa cuando el usuario forzo un modo concreto en vez de
    dejar "auto".
    """
    if modo == Modo.BYTE:
        return
    permitidos = _DIGITOS if modo == Modo.NUMERICO else _ALFANUMERICOS
    sobrantes = sorted({caracter for caracter in texto if caracter not in permitidos})
    if sobrantes:
        raise TextoNoValidoParaModo(
            f"el texto tiene caracteres que el modo {modo.value} no admite: {sobrantes!r}"
        )


@dataclass(frozen=True)
class AnalisisTexto:
    """Salida de la etapa 1. La consume la etapa 2 (version.py)."""

    modo: Modo                # el modo ya resuelto (nunca "auto")
    texto: str                # el texto original, sin tocar
    cantidad_caracteres: int  # lo que va en el indicador de cantidad del mensaje:
                              #   numerico / alfanumerico -> nro de caracteres
                              #   byte                    -> nro de bytes UTF-8


def analizar_texto(texto: str, modo: ModoPedido = "auto") -> AnalisisTexto:
    """Resuelve el modo definitivo y cuenta los caracteres del texto.

    - modo "auto": se detecta con detectar_modo().
    - modo concreto: se valida que el texto entre en ese modo, Si no,
      TextoNoValidoParaModo. Un nombre de modo desconocido -> ParametroInvalido.

    `cantidad_caracteres` es lo que despues arma el indicador de cantidad del
    mensaje: cantidad de caracteres para numerico y alfanumerico, cantidad de
    bytes UTF-8 para byte.
    """
    if modo == "auto":
        modo_real = detectar_modo(texto)
    else:
        try:
            modo_real = Modo(modo)
        except ValueError:
            raise ParametroInvalido(
                f"modo desconocido: {modo!r} "
                f"(esperado 'auto', 'numerico', 'alfanumerico' o 'byte')"
            ) from None
        validar_texto_para_modo(texto, modo_real)

    if modo_real == Modo.BYTE:
        cantidad = len(texto.encode("utf-8"))
    else:
        cantidad = len(texto)

    return AnalisisTexto(modo=modo_real, texto=texto, cantidad_caracteres=cantidad)
