"""Entrega 1 - Paso 3: validar que el texto solo tenga caracteres permitidos por el QR.

Valida contra el set del MODO ALFANUMERICO del estandar (ISO/IEC 18004): son
solo 45 caracteres, digitos, MAYUSCULAS y unos pocos simbolos, las
minusculas quedan fuera a proposito, ya que, un QR real no
rechaza minusculas, si el texto no entra en este set, se codifica en modo
BYTE (admite cualquier caracter, pero gasta mas espacio). Se usa el mismo
set que ya existe en `qr/tablas.py` para no duplicarlo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qr.tablas import CARACTERES_ALFANUMERICOS

CARACTERES_PERMITIDOS = frozenset(CARACTERES_ALFANUMERICOS)


def validar_texto(texto: str) -> tuple[bool, list[str]]:
    """Revisa `texto` contra el set alfanumerico del QR.

    Devuelve (es_valido, caracteres_no_permitidos). Si la lista viene vacia,
    el texto es valido.
    """
    no_permitidos = sorted({c for c in texto if c not in CARACTERES_PERMITIDOS})
    return (not no_permitidos, no_permitidos)


if __name__ == "__main__":
    texto = input("Texto a validar: ")
    es_valido, no_permitidos = validar_texto(texto)
    if es_valido:
        print("Texto valido: todos los caracteres estan permitidos.")
    else:
        print(f"Texto invalido. Caracteres no permitidos: {no_permitidos}")
