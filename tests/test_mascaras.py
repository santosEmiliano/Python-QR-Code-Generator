"""Tests de las etapas 6-7 (qr/mascaras.py): las 8 mascaras, bits de formato y
de version (BCH / Golay), las 4 reglas de penalizacion y finalizar_matriz.

Correr con:

    python -m unittest tests.test_mascaras -v
"""

from __future__ import annotations

import unittest

from qr.contrato import MatrizOrdenada, NivelCorreccion, ParametroInvalido
from qr.mascaras import (
    aplicar_mascara,
    bits_formato,
    bits_version,
    finalizar_matriz,
    puntaje,
    todas_las_mascaras,
)
from qr.mascaras import (
    _penalizacion_balance,
    _penalizacion_bloques,
    _penalizacion_patron,
    _penalizacion_rachas,
)
from qr.matriz import _celdas_formato, lado, ordenar_matriz

L, M, Q, H = (
    NivelCorreccion.L,
    NivelCorreccion.M,
    NivelCorreccion.Q,
    NivelCorreccion.H,
)

# "HELLO WORLD" 1-M despues de Reed-Solomon (datos + correccion), 26 bytes.
SECUENCIA_1M = [32, 91, 11, 120, 209, 114, 220, 77, 67, 64, 236, 17, 236, 17, 236, 17,
                196, 35, 39, 119, 235, 215, 231, 226, 93, 23]


def a_cadena(bits: list[int]) -> str:
    return "".join(str(b) for b in bits)


def grilla(n: int, valor: bool = False) -> list[list[bool]]:
    return [[valor] * n for _ in range(n)]


def ordenada_de_prueba(version: int = 1) -> MatrizOrdenada:
    n = lado(version)
    if version == 1:
        secuencia = SECUENCIA_1M
    else:
        from qr.tablas import total_bytes
        secuencia = [(i * 37 + 11) % 256 for i in range(total_bytes(version))]
    return ordenar_matriz(secuencia, version)


# Referencia independiente de donde va cada bit (esquema publicado por Nayuki,
# con (x, y) = (columna, fila)). `valor` es el entero de 15 bits ya con el XOR.
def posiciones_formato_referencia(n: int, valor: int) -> dict[tuple[int, int], int]:
    bit = lambda i: (valor >> i) & 1
    # claves (fila, columna); copia 1
    ref: dict[tuple[int, int], int] = {}
    for i in range(0, 6):
        ref[(i, 8)] = bit(i)
    ref[(7, 8)] = bit(6)
    ref[(8, 8)] = bit(7)
    ref[(8, 7)] = bit(8)
    for i in range(9, 15):
        ref[(8, 14 - i)] = bit(i)
    # copia 2
    for i in range(0, 8):
        ref[(8, n - 1 - i)] = bit(i)
    for i in range(8, 15):
        ref[(n - 15 + i, 8)] = bit(i)
    return ref


class TestAplicarMascara(unittest.TestCase):
    def test_las_ocho_condiciones_en_celdas_conocidas(self):
        # (mascara, fila, columna) -> debe invertir, segun ISO/IEC 18004 tabla 10
        casos = {
            0: [((0, 0), True), ((0, 1), False), ((1, 1), True), ((2, 3), False)],
            1: [((0, 5), True), ((1, 0), False), ((2, 7), True), ((3, 3), False)],
            2: [((4, 0), True), ((4, 1), False), ((0, 3), True), ((5, 5), False)],
            3: [((0, 0), True), ((1, 1), False), ((1, 2), True), ((2, 2), False)],
            4: [((0, 0), True), ((0, 3), False), ((2, 3), True), ((1, 3), False)],
            5: [((0, 0), True), ((1, 1), False), ((2, 3), True), ((1, 2), False)],
            6: [((0, 0), True), ((1, 1), True), ((1, 2), True), ((1, 3), False)],
            7: [((0, 0), True), ((1, 3), True), ((1, 1), False), ((1, 2), False)],
        }
        for mascara, lista in casos.items():
            m = aplicar_mascara(grilla(8), grilla(8), mascara)
            for (i, j), invierte in lista:
                self.assertEqual(m[i][j], invierte, f"mascara {mascara} en ({i},{j})")

    def test_mascara_0_es_un_tablero_de_ajedrez(self):
        m = aplicar_mascara(grilla(6), grilla(6), 0)
        for i in range(6):
            for j in range(6):
                self.assertEqual(m[i][j], (i + j) % 2 == 0)

    def test_aplicar_dos_veces_devuelve_el_original(self):
        base = [[(i * 3 + j * 5) % 7 < 3 for j in range(21)] for i in range(21)]
        reservado = grilla(21)
        for mascara in range(8):
            una = aplicar_mascara(base, reservado, mascara)
            dos = aplicar_mascara(una, reservado, mascara)
            self.assertEqual(dos, base)

    def test_no_toca_las_celdas_reservadas(self):
        base = [[(i + j) % 3 == 0 for j in range(10)] for i in range(10)]
        reservado = grilla(10, True)
        for mascara in range(8):
            self.assertEqual(aplicar_mascara(base, reservado, mascara), base)

    def test_no_muta_la_entrada(self):
        base = grilla(8)
        copia = [fila[:] for fila in base]
        aplicar_mascara(base, grilla(8), 3)
        self.assertEqual(base, copia)

    def test_mascara_invalida_lanza_ParametroInvalido(self):
        for malo in (-1, 8, 99, "3", 2.0, None):
            with self.assertRaises(ParametroInvalido, msg=repr(malo)):
                aplicar_mascara(grilla(5), grilla(5), malo)  # type: ignore[arg-type]


class TestBitsFormato(unittest.TestCase):
    def test_vectores_de_la_tabla_del_estandar(self):
        # (nivel, mascara) -> 15 bits, ya con el XOR 101010000010010
        casos = {
            (L, 0): "111011111000100",
            (L, 1): "111001011110011",
            (M, 0): "101010000010010",
            (M, 1): "101000100100101",
            (Q, 0): "011010101011111",
            (H, 0): "001011010001001",
        }
        for (nivel, mascara), esperado in casos.items():
            self.assertEqual(a_cadena(bits_formato(nivel, mascara)), esperado, f"{nivel.value}{mascara}")

    def test_largo_y_valores_binarios(self):
        for nivel in (L, M, Q, H):
            for mascara in range(8):
                bits = bits_formato(nivel, mascara)
                self.assertEqual(len(bits), 15)
                self.assertTrue(all(b in (0, 1) for b in bits))

    def test_las_32_combinaciones_son_distintas(self):
        todas = {a_cadena(bits_formato(n, m)) for n in (L, M, Q, H) for m in range(8)}
        self.assertEqual(len(todas), 32)

    def test_nunca_es_todo_ceros(self):
        for nivel in (L, M, Q, H):
            for mascara in range(8):
                self.assertIn(1, bits_formato(nivel, mascara))

    def test_distancia_minima_entre_codigos_es_8(self):
        # BCH(15,5) corrige 3 errores: dos codigos distintos difieren en >= 7 bits.
        valores = [int(a_cadena(bits_formato(n, m)), 2) for n in (L, M, Q, H) for m in range(8)]
        for a in range(len(valores)):
            for b in range(a + 1, len(valores)):
                self.assertGreaterEqual(bin(valores[a] ^ valores[b]).count("1"), 7)


class TestBitsVersion(unittest.TestCase):
    def test_de_v1_a_v6_no_hay(self):
        for v in range(1, 7):
            self.assertIsNone(bits_version(v))

    def test_vectores_del_estandar(self):
        casos = {
            7: "000111110010010100",
            8: "001000010110111100",
            40: "101000110001101001",
        }
        for version, esperado in casos.items():
            self.assertEqual(a_cadena(bits_version(version)), esperado, f"v{version}")

    def test_largo_18_y_los_primeros_6_bits_son_la_version(self):
        for v in range(7, 41):
            bits = bits_version(v)
            self.assertEqual(len(bits), 18)
            self.assertEqual(int(a_cadena(bits[:6]), 2), v)


class TestPenalizaciones(unittest.TestCase):
    def test_rachas_una_fila_de_siete_iguales(self):
        # 7 iguales seguidos suman 3 + (7 - 5) = 5; el resto alterna sin rachas.
        m = [[(i + j) % 2 == 0 for j in range(7)] for i in range(7)]
        m[0] = [True] * 7
        self.assertEqual(_penalizacion_rachas(m), 5)

    def test_rachas_exactamente_cinco_suman_tres(self):
        m = [[(i + j) % 2 == 0 for j in range(8)] for i in range(8)]
        m[3] = [True] * 5 + [False, True, False]
        self.assertEqual(_penalizacion_rachas(m), 3)

    def test_rachas_cuatro_iguales_no_penalizan(self):
        m = [[(i + j) % 2 == 0 for j in range(8)] for i in range(8)]
        m[3] = [True] * 4 + [False, True, False, True]
        self.assertEqual(_penalizacion_rachas(m), 0)

    def test_tablero_no_tiene_rachas_ni_bloques(self):
        m = [[(i + j) % 2 == 0 for j in range(12)] for i in range(12)]
        self.assertEqual(_penalizacion_rachas(m), 0)
        self.assertEqual(_penalizacion_bloques(m), 0)

    def test_bloques_2x2(self):
        self.assertEqual(_penalizacion_bloques(grilla(3)), 3 * 4)      # 4 bloques
        self.assertEqual(_penalizacion_bloques(grilla(2)), 3)          # 1 bloque
        self.assertEqual(_penalizacion_bloques(grilla(4, True)), 3 * 9)

    def test_patron_1011101_con_cuatro_claros(self):
        n = 15
        m = [[(i + j) % 2 == 0 for j in range(n)] for i in range(n)]
        base = _penalizacion_patron(m)
        fila = [False] * n
        # 1011101 0000 en las columnas 2..12
        for k, v in enumerate([1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]):
            fila[2 + k] = bool(v)
        m[5] = fila
        self.assertGreaterEqual(_penalizacion_patron(m) - base, 40)

    def test_patron_inverso_0000101_1101_tambien_penaliza(self):
        n = 11
        m = grilla(n)
        m[0] = [False, False, False, False, True, False, True, True, True, False, True]
        self.assertEqual(_penalizacion_patron(m), 40)

    def test_patron_en_los_dos_sentidos(self):
        n = 11
        m = grilla(n)
        # el mismo patron en la fila 0 y, trasladado, en la columna 0
        patron = [True, False, True, True, True, False, True, False, False, False, False]
        for k, v in enumerate(patron):
            m[0][k] = v
            m[k][0] = v
        # fila 0 y columna 0 comparten la celda (0,0) = True, que es patron[0]
        self.assertEqual(_penalizacion_patron(m), 80)

    def test_balance_cincuenta_por_ciento_no_penaliza(self):
        m = [[(i + j) % 2 == 0 for j in range(10)] for i in range(10)]
        self.assertEqual(_penalizacion_balance(m), 0)

    def test_balance_todo_de_un_color_es_el_escalon_maximo(self):
        # Desvio de 50 puntos: en el estandar el rango 95-100 % es el escalon 9.
        # (No se fijan los multiplos exactos de 5 %, donde las fuentes difieren.)
        self.assertEqual(_penalizacion_balance(grilla(10, True)), 90)
        self.assertEqual(_penalizacion_balance(grilla(10, False)), 90)

    def test_balance_siete_por_ciento_de_desvio_suma_diez(self):
        # 57 oscuros de 100 = 57 %: desvio de 7 puntos, un escalon de 5 -> 10.
        m = grilla(10)
        for k in range(57):
            m[k // 10][k % 10] = True
        self.assertEqual(_penalizacion_balance(m), 10)

    def test_puntaje_es_la_suma_de_las_cuatro_reglas(self):
        m = [[(i * i + 3 * j) % 5 < 2 for j in range(21)] for i in range(21)]
        self.assertEqual(
            puntaje(m),
            _penalizacion_rachas(m) + _penalizacion_bloques(m)
            + _penalizacion_patron(m) + _penalizacion_balance(m),
        )


class TestFinalizarMatriz(unittest.TestCase):
    def setUp(self):
        self.ordenada = ordenada_de_prueba(1)

    def test_formato_en_las_dos_copias_segun_referencia_independiente(self):
        n = lado(1)
        for nivel in (L, M, Q, H):
            for mascara in (0, 3, 7):
                r = finalizar_matriz(self.ordenada, 1, nivel, mascara)
                valor = int(a_cadena(bits_formato(nivel, mascara)), 2)
                for (fila, col), bit in posiciones_formato_referencia(n, valor).items():
                    self.assertEqual(r.matriz[fila][col], bool(bit), f"{nivel.value}{mascara} ({fila},{col})")

    def test_forzar_mascara_la_respeta(self):
        for mascara in range(8):
            r = finalizar_matriz(self.ordenada, 1, M, mascara)
            self.assertEqual(r.mascara, mascara)
            self.assertEqual(r.bits_formato, bits_formato(M, mascara))
            self.assertIsNone(r.bits_version)

    def test_automatica_elige_la_de_menor_puntaje(self):
        r = finalizar_matriz(self.ordenada, 1, M, None)
        puntajes = [puntaje(f.matriz) for f in todas_las_mascaras(self.ordenada, 1, M)]
        self.assertEqual(puntaje(r.matriz), min(puntajes))
        self.assertEqual(r.mascara, puntajes.index(min(puntajes)))  # empate: la menor

    def test_los_patrones_fijos_no_cambian(self):
        r = finalizar_matriz(self.ordenada, 1, M, 5)
        res = self.ordenada.reservado
        formato = set(_celdas_formato(lado(1)))
        for i in range(lado(1)):
            for j in range(lado(1)):
                if res[i][j] and (i, j) not in formato:
                    self.assertEqual(r.matriz[i][j], self.ordenada.matriz[i][j], f"({i},{j})")

    def test_no_muta_la_ordenada(self):
        antes = [f[:] for f in self.ordenada.matriz]
        finalizar_matriz(self.ordenada, 1, M, None)
        self.assertEqual(self.ordenada.matriz, antes)

    def test_version_7_escribe_los_dos_bloques_de_version(self):
        ordenada = ordenada_de_prueba(7)
        n = lado(7)
        r = finalizar_matriz(ordenada, 7, M, 2)
        self.assertEqual(a_cadena(r.bits_version), "000111110010010100")
        valor = int(a_cadena(r.bits_version), 2)
        for i in range(18):
            esperado = bool((valor >> i) & 1)
            self.assertEqual(r.matriz[i // 3][n - 11 + i % 3], esperado, f"superior bit {i}")
            self.assertEqual(r.matriz[n - 11 + i % 3][i // 3], esperado, f"inferior bit {i}")

    def test_todas_las_mascaras_devuelve_ocho_en_orden(self):
        todas = todas_las_mascaras(self.ordenada, 1, Q)
        self.assertEqual([t.mascara for t in todas], list(range(8)))
        self.assertEqual(len({a_cadena(sum(([int(c) for c in f] for f in t.matriz), [])) for t in todas}), 8)

    def test_errores_de_parametros(self):
        with self.assertRaises(ParametroInvalido):
            finalizar_matriz(self.ordenada, 1, M, 8)
        with self.assertRaises(ParametroInvalido):
            finalizar_matriz(self.ordenada, 1, "M", None)  # type: ignore[arg-type]
        with self.assertRaises(ParametroInvalido):
            finalizar_matriz(self.ordenada, 2, M, None)    # la matriz es de v1


if __name__ == "__main__":
    unittest.main()
