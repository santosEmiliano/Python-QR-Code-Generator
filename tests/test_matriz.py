"""Tests de la etapa 5 (qr/matriz.py): patrones fijos, zonas reservadas y
colocado de datos en zigzag.

P3 se prueba contra secuencias stubbeadas (listas de bytes armadas a mano del
largo correcto): el recorrido y los patrones no dependen del contenido real de
P2. Correr con:

    python -m unittest tests.test_matriz -v
"""

from __future__ import annotations

import unittest

from qr.contrato import ErrorQR, MatrizOrdenada, ParametroInvalido
from qr.matriz import lado, ordenar_matriz
from qr.tablas import bits_relleno_final, total_bytes


def stub(version: int, relleno: int = 0) -> list[int]:
    """Secuencia stubbeada del largo exacto de esa version (bytes 0..255)."""
    n = total_bytes(version)
    return [(relleno + i) % 256 for i in range(n)]


def subgrilla(matriz: list[list[bool]], fila: int, col: int, alto: int, ancho: int):
    return [r[col : col + ancho] for r in matriz[fila : fila + alto]]


def patron_localizador():
    """El 7x7 esperado: borde oscuro, anillo claro, nucleo 3x3 oscuro."""
    return [
        [i in (0, 6) or j in (0, 6) or (2 <= i <= 4 and 2 <= j <= 4) for j in range(7)]
        for i in range(7)
    ]


def patron_alineacion():
    """El 5x5 esperado: borde oscuro, interior claro, centro oscuro."""
    return [
        [abs(i - 2) == 2 or abs(j - 2) == 2 or (i == 2 and j == 2) for j in range(5)]
        for i in range(5)
    ]


def leer_datos(resultado: MatrizOrdenada) -> list[int]:
    """Relee los bits de datos caminando el zigzag igual que P3 (columna 6
    salteada, celdas reservadas salteadas), de abajo-derecha hacia la izquierda.
    Es el inverso del colocado: sirve para comprobar que cada bit quedo donde
    debe, sin depender del codigo interno de matriz.py."""
    n = len(resultado.matriz)
    bits: list[int] = []
    fila = n - 1
    columna = n - 1
    hacia_arriba = True
    while columna > 0:
        if columna == 6:
            columna -= 1
        for _ in range(n):
            for c in (columna, columna - 1):
                if not resultado.reservado[fila][c]:
                    bits.append(1 if resultado.matriz[fila][c] else 0)
            fila += -1 if hacia_arriba else 1
            if fila < 0 or fila >= n:
                break
        columna -= 2
        hacia_arriba = not hacia_arriba
        fila += -1 if hacia_arriba else 1
    return bits


def a_bytes(bits: list[int]) -> list[int]:
    return [
        sum(b << (7 - j) for j, b in enumerate(bits[i : i + 8]))
        for i in range(0, len(bits), 8)
    ]


class TestLado(unittest.TestCase):
    def test_v1_mide_21(self):
        self.assertEqual(lado(1), 21)

    def test_formula(self):
        self.assertEqual(lado(2), 25)
        self.assertEqual(lado(10), 57)
        self.assertEqual(lado(40), 177)

    def test_version_fuera_de_rango_lanza(self):
        for mala in (0, 41, -1, "1", 2.5, None):
            with self.subTest(version=mala):
                with self.assertRaises(ParametroInvalido):
                    lado(mala)  # type: ignore[arg-type]


class TestValidacion(unittest.TestCase):
    def test_devuelve_MatrizOrdenada_cuadrada(self):
        r = ordenar_matriz(stub(1), 1)
        self.assertIsInstance(r, MatrizOrdenada)
        self.assertEqual(len(r.matriz), 21)
        self.assertTrue(all(len(f) == 21 for f in r.matriz))
        self.assertEqual(len(r.reservado), 21)

    def test_secuencia_corta_o_larga_lanza(self):
        with self.assertRaises(ParametroInvalido):
            ordenar_matriz([0] * 25, 1)  # v1 lleva 26 bytes.
        with self.assertRaises(ParametroInvalido):
            ordenar_matriz([0] * 27, 1)

    def test_byte_fuera_de_rango_lanza(self):
        mala = stub(1)
        mala[0] = 256
        with self.assertRaises(ParametroInvalido):
            ordenar_matriz(mala, 1)

    def test_version_fuera_de_rango_lanza(self):
        with self.assertRaises(ParametroInvalido):
            ordenar_matriz(stub(1), 0)

    def test_version_sin_tablas_propaga_NotImplementedError(self):
        with self.assertRaises(NotImplementedError):
            ordenar_matriz([0] * 100, 11)

    def test_error_es_subclase_de_ErrorQR(self):
        with self.assertRaises(ErrorQR):
            ordenar_matriz([0] * 5, 1)


class TestLocalizadores(unittest.TestCase):
    """Los tres 7x7 tipo diana + su linea separadora clara."""

    def test_los_tres_localizadores_tienen_el_patron(self):
        r = ordenar_matriz(stub(1), 1)
        esperado = patron_localizador()
        n = 21
        self.assertEqual(subgrilla(r.matriz, 0, 0, 7, 7), esperado)
        self.assertEqual(subgrilla(r.matriz, 0, n - 7, 7, 7), esperado)
        self.assertEqual(subgrilla(r.matriz, n - 7, 0, 7, 7), esperado)

    def test_localizadores_quedan_reservados(self):
        r = ordenar_matriz(stub(1), 1)
        n = 21
        for f0, c0 in ((0, 0), (0, n - 7), (n - 7, 0)):
            for i in range(7):
                for j in range(7):
                    self.assertTrue(r.reservado[f0 + i][c0 + j])

    def test_separadores_claros_y_reservados(self):
        r = ordenar_matriz(stub(1), 1)
        n = 21
        # Arriba-izquierda: fila 7 y columna 7.
        for k in range(8):
            self.assertFalse(r.matriz[7][k])
            self.assertTrue(r.reservado[7][k])
            self.assertFalse(r.matriz[k][7])
            self.assertTrue(r.reservado[k][7])
        # Arriba-derecha y abajo-izquierda.
        for k in range(8):
            self.assertFalse(r.matriz[7][n - 8 + k])
            self.assertFalse(r.matriz[n - 8][k])
            self.assertFalse(r.matriz[k][n - 8])
            self.assertFalse(r.matriz[n - 8 + k][7])


class TestSincronizacionYModuloOscuro(unittest.TestCase):
    def test_timing_alterna_empezando_oscuro(self):
        r = ordenar_matriz(stub(1), 1)
        for k in range(8, 13):  # v1: indices 8..12.
            self.assertEqual(r.matriz[6][k], k % 2 == 0)
            self.assertEqual(r.matriz[k][6], k % 2 == 0)
            self.assertTrue(r.reservado[6][k])
            self.assertTrue(r.reservado[k][6])

    def test_modulo_oscuro_en_su_posicion(self):
        # Fila 4*V+9, columna 8, siempre negro y reservado.
        for version, fila in ((1, 13), (2, 17), (7, 37)):
            with self.subTest(version=version):
                r = ordenar_matriz(stub(version), version)
                self.assertTrue(r.matriz[fila][8])
                self.assertTrue(r.reservado[fila][8])


class TestAlineacion(unittest.TestCase):
    def test_v1_no_tiene_alineacion(self):
        r = ordenar_matriz([0] * 26, 1)
        # La (18, 18) es zona de datos en v1: libre y clara con stub de ceros.
        self.assertFalse(r.reservado[18][18])
        self.assertFalse(r.matriz[18][18])

    def test_v2_un_patron_en_18_18(self):
        r = ordenar_matriz([0] * 44, 2)
        self.assertEqual(subgrilla(r.matriz, 16, 16, 5, 5), patron_alineacion())
        self.assertTrue(r.matriz[18][18])  # centro oscuro.

    def test_v7_patron_interior_y_sobre_timing(self):
        # Centros v7: [6, 22, 38]. La (22, 22) es interior; la (6, 22) se dibuja
        # aunque pise la linea de sincronizacion (alineacion manda).
        r = ordenar_matriz([0] * 196, 7)
        self.assertEqual(subgrilla(r.matriz, 20, 20, 5, 5), patron_alineacion())
        self.assertTrue(r.matriz[6][22])
        self.assertTrue(r.reservado[6][22])


class TestReservasFormato(unittest.TestCase):
    def test_las_30_celdas_reservadas_y_vacias(self):
        r = ordenar_matriz(stub(1), 1)
        n = 21
        copia1 = (
            [(8, c) for c in range(6)]
            + [(8, 7), (8, 8), (7, 8)]
            + [(f, 8) for f in (5, 4, 3, 2, 1, 0)]
        )
        copia2 = [(f, 8) for f in range(n - 1, n - 8, -1)] + [
            (8, c) for c in range(n - 8, n)
        ]
        self.assertEqual(len(copia1) + len(copia2), 30)
        for f, c in copia1 + copia2:
            with self.subTest(celda=(f, c)):
                self.assertTrue(r.reservado[f][c])
                self.assertFalse(r.matriz[f][c])  # hueco para P4.

    def test_timing_no_se_confunde_con_formato(self):
        # La (8, 6) y la (6, 8) son de sincronizacion: reservadas pero oscuras.
        r = ordenar_matriz(stub(1), 1)
        self.assertTrue(r.reservado[8][6])
        self.assertTrue(r.matriz[8][6])
        self.assertTrue(r.reservado[6][8])
        self.assertTrue(r.matriz[6][8])


class TestReservaVersion(unittest.TestCase):
    def test_v1_no_reserva_zona_de_version(self):
        r = ordenar_matriz([0] * 26, 1)
        # Donde iria el bloque superior en v7+: en v1 es zona de datos.
        self.assertFalse(r.reservado[0][10])

    def test_v7_reserva_los_dos_bloques_vacios(self):
        r = ordenar_matriz([0] * 196, 7)
        n = 45
        for f in range(6):
            for c in range(n - 11, n - 8):
                self.assertTrue(r.reservado[f][c])
                self.assertFalse(r.matriz[f][c])
        for f in range(n - 11, n - 8):
            for c in range(6):
                self.assertTrue(r.reservado[f][c])
                self.assertFalse(r.matriz[f][c])


class TestInvarianteCapacidad(unittest.TestCase):
    """Las celdas libres son exactamente mensaje+respaldo+relleno final."""

    def test_celdas_libres_igual_bytes_mas_relleno(self):
        for version in range(1, 11):
            with self.subTest(version=version):
                r = ordenar_matriz(stub(version), version)
                libres = sum(
                    not celda for fila in r.reservado for celda in fila
                )
                self.assertEqual(
                    libres,
                    total_bytes(version) * 8 + bits_relleno_final(version),
                )


class TestZigzag(unittest.TestCase):
    def test_primeros_bits_caen_abajo_derecha(self):
        # 0xAA = 10101010: las primeras 4 celdas del recorrido son
        # (20,20), (20,19), (19,20), (19,19).
        r = ordenar_matriz([0xAA] + [0] * 25, 1)
        self.assertTrue(r.matriz[20][20])
        self.assertFalse(r.matriz[20][19])
        self.assertTrue(r.matriz[19][20])
        self.assertFalse(r.matriz[19][19])

    def test_columna_6_intocable(self):
        r = ordenar_matriz(stub(1), 1)
        self.assertTrue(all(r.reservado[f][6] for f in range(21)))

    def test_ida_y_vuelta_recupera_la_secuencia(self):
        for version in (1, 2, 5):
            with self.subTest(version=version):
                secuencia = stub(version)
                r = ordenar_matriz(secuencia, version)
                bits = leer_datos(r)
                self.assertEqual(
                    a_bytes(bits[: len(secuencia) * 8]), secuencia
                )

    def test_bits_de_relleno_final_quedan_claros(self):
        # v2 tiene 7 bits de relleno: lo que sobra tras la secuencia es claro.
        r = ordenar_matriz(stub(2), 2)
        sobra = leer_datos(r)[44 * 8 :]
        self.assertEqual(len(sobra), bits_relleno_final(2))
        self.assertEqual(sobra, [0] * len(sobra))

    def test_los_datos_no_tocan_lo_reservado(self):
        r = ordenar_matriz([0xFF] * 26, 1)
        # Con todo en 1, cada celda reservada clara sigue clara (separadores,
        # formato): el colocado las salteo.
        self.assertFalse(r.matriz[7][0])
        self.assertFalse(r.matriz[8][0])


class TestPureza(unittest.TestCase):
    def test_no_muta_la_secuencia(self):
        secuencia = stub(1)
        copia = list(secuencia)
        ordenar_matriz(secuencia, 1)
        self.assertEqual(secuencia, copia)

    def test_llamadas_independientes(self):
        a = ordenar_matriz(stub(1), 1)
        b = ordenar_matriz(stub(1), 1)
        b.matriz[20][20] = not b.matriz[20][20]
        self.assertNotEqual(a.matriz[20][20], b.matriz[20][20])

    def test_solo_booleanos(self):
        r = ordenar_matriz(stub(3), 3)
        self.assertTrue(
            all(type(c) is bool for f in r.matriz for c in f)
            and all(type(c) is bool for f in r.reservado for c in f)
        )

    def test_resultado_es_inmutable(self):
        r = ordenar_matriz(stub(1), 1)
        with self.assertRaises(Exception):
            r.matriz = []  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
