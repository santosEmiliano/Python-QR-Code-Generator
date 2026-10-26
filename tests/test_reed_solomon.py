"""Tests de la etapa 4 (qr/reed_solomon.py): aritmetica en GF(256), polinomio
generador, calculo de los bytes de correccion, particion en bloques e
intercalado.

Correr con:

    python -m unittest tests.test_reed_solomon -v
"""

from __future__ import annotations

import random
import unittest

from qr import reed_solomon as rs
from qr.contrato import ErrorQR, MensajeCodificado, Modo, NivelCorreccion
from qr.reed_solomon import (
    agregar_correccion,
    calcular_correccion,
    gf_mul,
    intercalar,
    polinomio_generador,
)
from qr.tablas import bloques_correccion, total_bytes

L, M, Q, H = (
    NivelCorreccion.L,
    NivelCorreccion.M,
    NivelCorreccion.Q,
    NivelCorreccion.H,
)

# "HELLO WORLD" en alfanumerico, 1-M y 1-Q (ejemplo de Thonky).
DATOS_HELLO_1M = [32, 91, 11, 120, 209, 114, 220, 77, 67, 64, 236, 17, 236, 17, 236, 17]
EC_HELLO_1M = [196, 35, 39, 119, 235, 215, 231, 226, 93, 23]
DATOS_HELLO_1Q = [32, 91, 11, 120, 209, 114, 220, 77, 67, 64, 236, 17, 236]
EC_HELLO_1Q = [168, 72, 22, 82, 217, 54, 156, 0, 46, 15, 180, 122, 16]


def evaluar(poli: list[int], x: int) -> int:
    """Evalua un polinomio (mayor grado primero) en x, con Horner en GF(256)."""
    acc = 0
    for c in poli:
        acc = gf_mul(acc, x) ^ c
    return acc


def mensaje(version: int, nivel: NivelCorreccion, datos: list[int]) -> MensajeCodificado:
    return MensajeCodificado(
        modo=Modo.ALFANUMERICO,
        version=version,
        nivel_correccion=nivel,
        cantidad_caracteres=0,
        bits=[],
        bytes_mensaje=datos,
    )


class TestAritmeticaGF(unittest.TestCase):
    def test_multiplicar_por_cero_y_por_uno(self):
        for a in (0, 1, 2, 57, 255):
            self.assertEqual(gf_mul(a, 0), 0)
            self.assertEqual(gf_mul(0, a), 0)
            self.assertEqual(gf_mul(a, 1), a)

    def test_alfa_al_cuadrado_y_reduccion_modulo_primitivo(self):
        self.assertEqual(gf_mul(2, 2), 4)
        # 0x80 * 2 se pasa de 8 bits y se reduce con 0x11D: 0x100 ^ 0x11D = 0x1D
        self.assertEqual(gf_mul(0x80, 2), 0x1D)

    def test_conmutativa_y_con_inverso(self):
        for a in range(1, 256):
            for b in (3, 29, 142, 255):
                self.assertEqual(gf_mul(a, b), gf_mul(b, a))
        # todo elemento distinto de cero tiene inverso: a * b = 1 para algun b
        for a in range(1, 256):
            self.assertTrue(any(gf_mul(a, b) == 1 for b in range(1, 256)))

    def test_tabla_exp_recorre_los_255_valores_no_nulos(self):
        self.assertEqual(sorted(rs._EXP[:255]), list(range(1, 256)))


class TestPolinomioGenerador(unittest.TestCase):
    def test_grado_y_coeficiente_lider(self):
        for n in (7, 10, 13, 17, 30):
            g = polinomio_generador(n)
            self.assertEqual(len(g), n + 1)
            self.assertEqual(g[0], 1)

    def test_grado_10_coincide_con_thonky(self):
        # Thonky lo da en exponentes de alfa: 0, 251, 67, 46, 61, 118, 70, 64, 94, 32, 45
        exponentes = [0, 251, 67, 46, 61, 118, 70, 64, 94, 32, 45]
        esperado = [rs._EXP[e] for e in exponentes]
        self.assertEqual(polinomio_generador(10), esperado)

    def test_las_raices_son_alfa_0_a_alfa_n_menos_1(self):
        g = polinomio_generador(13)
        for i in range(13):
            self.assertEqual(evaluar(g, rs._EXP[i]), 0)
        self.assertNotEqual(evaluar(g, rs._EXP[13]), 0)


class TestCalcularCorreccion(unittest.TestCase):
    def test_hello_world_1M(self):
        self.assertEqual(calcular_correccion(DATOS_HELLO_1M, 10), EC_HELLO_1M)

    def test_hello_world_1Q(self):
        self.assertEqual(calcular_correccion(DATOS_HELLO_1Q, 13), EC_HELLO_1Q)

    def test_largo_de_la_correccion(self):
        self.assertEqual(len(calcular_correccion([1, 2, 3], 7)), 7)

    def test_datos_en_cero_dan_correccion_en_cero(self):
        self.assertEqual(calcular_correccion([0] * 16, 10), [0] * 10)

    def test_no_modifica_la_lista_de_entrada(self):
        datos = list(DATOS_HELLO_1M)
        calcular_correccion(datos, 10)
        self.assertEqual(datos, DATOS_HELLO_1M)

    def test_palabra_codigo_es_multiplo_del_generador(self):
        # Propiedad independiente de cualquier vector: datos + correccion se
        # anula en alfa^0 .. alfa^(n_ec-1).
        azar = random.Random(18004)
        for n_ec in (7, 10, 17, 26, 30):
            datos = [azar.randrange(256) for _ in range(40)]
            palabra = datos + calcular_correccion(datos, n_ec)
            for i in range(n_ec):
                self.assertEqual(evaluar(palabra, rs._EXP[i]), 0, f"n_ec={n_ec}, i={i}")


class TestIntercalar(unittest.TestCase):
    def test_un_solo_bloque_queda_igual(self):
        self.assertEqual(intercalar([([1, 2, 3], [9, 8])]), [1, 2, 3, 9, 8])

    def test_dos_bloques_iguales_alternan(self):
        bloques = [([1, 2], [10, 11]), ([3, 4], [12, 13])]
        self.assertEqual(intercalar(bloques), [1, 3, 2, 4, 10, 12, 11, 13])

    def test_bloque_corto_se_saltea_cuando_se_agota(self):
        bloques = [([1, 2, 3], [10, 11]), ([4, 5], [12, 13])]
        self.assertEqual(intercalar(bloques), [1, 4, 2, 5, 3, 10, 12, 11, 13])


class TestAgregarCorreccion(unittest.TestCase):
    def test_hello_world_1M_secuencia_completa(self):
        r = agregar_correccion(mensaje(1, M, DATOS_HELLO_1M))
        self.assertEqual(r.secuencia, DATOS_HELLO_1M + EC_HELLO_1M)
        self.assertEqual(len(r.bloques), 1)
        self.assertEqual(r.bloques[0].bytes_mensaje, DATOS_HELLO_1M)
        self.assertEqual(r.bloques[0].bytes_correccion, EC_HELLO_1M)

    def test_hello_world_1Q_secuencia_completa(self):
        r = agregar_correccion(mensaje(1, Q, DATOS_HELLO_1Q))
        self.assertEqual(r.secuencia, DATOS_HELLO_1Q + EC_HELLO_1Q)

    def test_largo_total_coincide_con_la_tabla_en_todas_las_versiones_cargadas(self):
        azar = random.Random(4)
        for version in range(1, 11):
            for nivel in (L, M, Q, H):
                estructura = bloques_correccion(version, nivel)
                n_datos = sum(n * datos for n, _, datos in estructura)
                datos = [azar.randrange(256) for _ in range(n_datos)]
                r = agregar_correccion(mensaje(version, nivel, datos))
                self.assertEqual(len(r.secuencia), total_bytes(version), f"{version}-{nivel.value}")
                self.assertEqual(len(r.bloques), sum(n for n, _, _ in estructura))

    def test_version_con_bloques_de_distinto_tamano_intercala_bien(self):
        # 5-Q: dos grupos de bloques con distinto largo de datos.
        estructura = bloques_correccion(5, Q)
        self.assertGreater(len({datos for _, _, datos in estructura}), 1)
        n_datos = sum(n * datos for n, _, datos in estructura)
        datos = list(range(n_datos))
        r = agregar_correccion(mensaje(5, Q, datos))
        # el primer byte de cada bloque abre la secuencia, en orden de bloque
        inicios = [b.bytes_mensaje[0] for b in r.bloques]
        self.assertEqual(r.secuencia[: len(inicios)], inicios)
        # cada bloque sigue siendo una palabra de codigo valida
        for b in r.bloques:
            palabra = b.bytes_mensaje + b.bytes_correccion
            for i in range(len(b.bytes_correccion)):
                self.assertEqual(evaluar(palabra, rs._EXP[i]), 0)

    def test_mensaje_corto_lanza_ErrorQR(self):
        with self.assertRaises(ErrorQR):
            agregar_correccion(mensaje(1, M, DATOS_HELLO_1M[:-1]))

    def test_mensaje_largo_lanza_ErrorQR(self):
        with self.assertRaises(ErrorQR):
            agregar_correccion(mensaje(1, M, DATOS_HELLO_1M + [0]))

    def test_estructura_explicita_reemplaza_la_de_la_tabla(self):
        r = agregar_correccion(mensaje(1, M, [1, 2, 3, 4]), estructura_bloques=[(2, 4, 2)])
        self.assertEqual(len(r.bloques), 2)
        self.assertEqual(len(r.secuencia), 8)


if __name__ == "__main__":
    unittest.main()
