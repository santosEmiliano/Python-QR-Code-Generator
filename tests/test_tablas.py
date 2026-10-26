"""Las tablas de capacidad deben coincidir con lo que sale de los bytes de datos.

CAPACIDAD_NUM / ALFA / BYTE estan transcritas a mano, asi que se comparan con el
calculo a partir de capacidad_bytes_datos y el ancho del contador de cada modo.
"""

import unittest

from qr.contrato import Modo, NivelCorreccion
from qr.tablas import (
    CAPACIDAD_ALFA,
    CAPACIDAD_BYTE,
    CAPACIDAD_NUM,
    VERSION_MAX_CARGADA,
    bits_cuenta_caracteres,
    capacidad_bytes_datos,
)


def _caracteres_que_caben(version: int, nivel: NivelCorreccion, modo: Modo) -> int:
    bits = capacidad_bytes_datos(version, nivel) * 8 - 4 - bits_cuenta_caracteres(version, modo)
    if modo == Modo.NUMERICO:
        resto = bits % 10
        return bits // 10 * 3 + (2 if resto >= 7 else 1 if resto >= 4 else 0)
    if modo == Modo.ALFANUMERICO:
        return bits // 11 * 2 + (1 if bits % 11 >= 6 else 0)
    return bits // 8


class TestCapacidades(unittest.TestCase):
    def _comparar(self, tabla, modo):
        for version in range(1, VERSION_MAX_CARGADA + 1):
            for nivel in NivelCorreccion:
                with self.subTest(version=version, nivel=nivel.value):
                    self.assertEqual(tabla[version][nivel], _caracteres_que_caben(version, nivel, modo))

    def test_numerico(self):
        self._comparar(CAPACIDAD_NUM, Modo.NUMERICO)

    def test_alfanumerico(self):
        self._comparar(CAPACIDAD_ALFA, Modo.ALFANUMERICO)

    def test_byte(self):
        self._comparar(CAPACIDAD_BYTE, Modo.BYTE)


if __name__ == "__main__":
    unittest.main()
