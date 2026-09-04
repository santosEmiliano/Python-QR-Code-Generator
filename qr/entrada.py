"""Etapa 1 del flujo (P1): analisis del texto de entrada y seleccion de modo.

Recibe el texto que quiere codificar el usuario y decide en que modo
conviene guardarlo (numerico, alfanumerico o byte). NO arma bits ni elige
version: eso es la etapa 2 (version.py).
"""

from __future__ import annotations

from .contrato import Modo
from .tablas import CARACTERES_ALFANUMERICOS

__all__ = ["detectar_modo"]

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
