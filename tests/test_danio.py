"""Tests de qr/danio.py: dano simulado para comprobar la correccion de errores.

Correr con:

    python -m unittest tests.test_danio -v
"""

from __future__ import annotations

import unittest

from qr.contrato import EntradaUsuario, NivelCorreccion, ParametroInvalido
from qr.danio import InformeDanio, celdas_de_bytes, danar_matriz
from qr.qr import generar_qr

L, M, Q, H = (
    NivelCorreccion.L,
    NivelCorreccion.M,
    NivelCorreccion.Q,
    NivelCorreccion.H,
)


def qr(texto: str = "HELLO WORLD", nivel: NivelCorreccion = M, **kw):
    return generar_qr(EntradaUsuario(texto=texto, nivel_correccion=nivel, **kw))


def celdas_distintas(a: list[list[bool]], b: list[list[bool]]) -> set[tuple[int, int]]:
    return {
        (i, j)
        for i in range(len(a))
        for j in range(len(a))
        if a[i][j] != b[i][j]
    }


class TestCeldasDeBytes(unittest.TestCase):
    def test_leer_las_celdas_devuelve_la_secuencia_colocada(self):
        # Garantiza que el recorrido de danio.py coincide con el de matriz.py.
        casos = [("HELLO WORLD", M), ("A" * 40, Q), ("a" * 120, M), ("b" * 100, H), ("1" * 300, L)]
        for texto, nivel in casos:
            r = qr(texto, nivel)
            celdas = celdas_de_bytes(r.matriz_ordenada.reservado, r.mensaje.version)
            bits = [int(r.matriz_ordenada.matriz[f][c]) for f, c in celdas]
            leidos = [
                int("".join(str(b) for b in bits[i : i + 8]), 2)
                for i in range(0, len(bits), 8)
            ]
            self.assertEqual(leidos, r.correccion.secuencia, f"v{r.mensaje.version}-{nivel.value}")

    def test_son_8_celdas_por_byte_y_ninguna_reservada_ni_repetida(self):
        r = qr("a" * 120)
        celdas = celdas_de_bytes(r.matriz_ordenada.reservado, r.mensaje.version)
        self.assertEqual(len(celdas), 8 * len(r.correccion.secuencia))
        self.assertEqual(len(set(celdas)), len(celdas))
        for f, c in celdas:
            self.assertFalse(r.matriz_ordenada.reservado[f][c])


class TestDanarMatriz(unittest.TestCase):
    def setUp(self):
        self.r = qr("HELLO WORLD", M)
        self.celdas = set(celdas_de_bytes(self.r.matriz_ordenada.reservado, 1))

    def test_devuelve_un_informe_con_una_matriz_nueva(self):
        i = danar_matriz(self.r, 2, "azar", semilla=1)
        self.assertIsInstance(i, InformeDanio)
        self.assertIsNot(i.matriz, self.r.final.matriz)
        self.assertEqual(len(i.matriz), len(self.r.final.matriz))

    def test_no_muta_el_resultado_original(self):
        antes = [f[:] for f in self.r.final.matriz]
        danar_matriz(self.r, 10, "azar", semilla=3)
        danar_matriz(self.r, 10, "bloque", semilla=3)
        self.assertEqual(self.r.final.matriz, antes)

    def test_invierte_exactamente_la_cantidad_pedida_en_los_dos_modos(self):
        total = len(self.celdas)
        for modo in ("azar", "bloque"):
            for porcentaje in (1, 5, 10, 50):
                i = danar_matriz(self.r, porcentaje, modo, semilla=7)
                esperado = round(total * porcentaje / 100)
                self.assertEqual(i.modulos_invertidos, esperado, f"{modo} {porcentaje}")
                self.assertEqual(len(celdas_distintas(i.matriz, self.r.final.matriz)), esperado)

    def test_solo_cambian_celdas_de_datos_y_correccion(self):
        for modo in ("azar", "bloque"):
            i = danar_matriz(self.r, 20, modo, semilla=2)
            self.assertLessEqual(celdas_distintas(i.matriz, self.r.final.matriz), self.celdas)

    def test_el_formato_y_los_patrones_fijos_quedan_intactos(self):
        i = danar_matriz(self.r, 100, "azar", semilla=0)
        reservado = self.r.matriz_ordenada.reservado
        for f in range(len(reservado)):
            for c in range(len(reservado)):
                if reservado[f][c]:
                    self.assertEqual(i.matriz[f][c], self.r.final.matriz[f][c])

    def test_cien_por_ciento_invierte_todas_las_celdas_de_datos(self):
        i = danar_matriz(self.r, 100, "bloque", semilla=0)
        self.assertEqual(celdas_distintas(i.matriz, self.r.final.matriz), self.celdas)
        self.assertEqual(i.bytes_danados, i.total_bytes)
        self.assertFalse(i.recuperable)

    def test_porcentaje_minimo_invierte_al_menos_un_modulo(self):
        i = danar_matriz(self.r, 0.0001, "azar", semilla=0)
        self.assertEqual(i.modulos_invertidos, 1)
        self.assertEqual(i.bytes_danados, 1)

    def test_misma_semilla_mismo_dano_y_semillas_distintas_cambian_el_dano(self):
        for modo in ("azar", "bloque"):
            a = danar_matriz(self.r, 5, modo, semilla=11)
            b = danar_matriz(self.r, 5, modo, semilla=11)
            c = danar_matriz(self.r, 5, modo, semilla=12)
            self.assertEqual(a.matriz, b.matriz)
            self.assertNotEqual(a.matriz, c.matriz)

    def test_sin_semilla_funciona(self):
        self.assertIsInstance(danar_matriz(self.r, 3), InformeDanio)


class TestInforme(unittest.TestCase):
    def test_bytes_danados_coincide_con_los_bytes_que_cambiaron(self):
        r = qr("a" * 120, M)
        celdas = celdas_de_bytes(r.matriz_ordenada.reservado, r.mensaje.version)
        for modo in ("azar", "bloque"):
            for porcentaje in (1, 4, 9):
                i = danar_matriz(r, porcentaje, modo, semilla=5)
                tocados = {
                    k // 8
                    for k, (f, c) in enumerate(celdas)
                    if i.matriz[f][c] != r.final.matriz[f][c]
                }
                self.assertEqual(i.bytes_danados, len(tocados))
                self.assertEqual(sum(d for d, _ in i.por_bloque), len(tocados))
                self.assertLessEqual(i.bytes_danados, i.modulos_invertidos)

    def test_la_tolerancia_es_la_mitad_de_los_bytes_de_correccion(self):
        # v1-M: 10 bytes de correccion -> tolera 5. v1-L: 7 -> 3. v1-H: 17 -> 8.
        for nivel, tolera in ((M, 5), (L, 3), (H, 8)):
            r = qr("HOLA", nivel)
            self.assertEqual(r.mensaje.version, 1)
            i = danar_matriz(r, 1, "azar", semilla=0)
            self.assertEqual([t for _, t in i.por_bloque], [tolera], nivel.value)

    def test_un_bloque_por_cada_bloque_del_estandar(self):
        r = qr("a" * 120, M)  # varios bloques
        i = danar_matriz(r, 1, "azar", semilla=0)
        self.assertEqual(len(i.por_bloque), len(r.correccion.bloques))

    def test_recuperable_depende_de_que_ningun_bloque_pase_su_tolerancia(self):
        r = qr("HELLO WORLD", M)
        poco = danar_matriz(r, 1, "azar", semilla=1)    # 2 bytes <= 5
        mucho = danar_matriz(r, 30, "azar", semilla=1)
        self.assertTrue(poco.recuperable)
        self.assertFalse(mucho.recuperable)
        for i in (poco, mucho):
            self.assertEqual(i.recuperable, all(d <= t for d, t in i.por_bloque))

    def test_una_mancha_contigua_rompe_menos_bytes_que_el_azar(self):
        # Con la misma cantidad de modulos invertidos, juntarlos en una mancha
        # toca menos bytes que repartirlos.
        r = qr("HELLO WORLD", M)
        azar = danar_matriz(r, 10, "azar", semilla=1)
        mancha = danar_matriz(r, 10, "bloque", semilla=1)
        self.assertEqual(azar.modulos_invertidos, mancha.modulos_invertidos)
        self.assertLess(mancha.bytes_danados, azar.bytes_danados)

    def test_la_mancha_es_compacta_y_el_azar_se_reparte(self):
        r = qr("a" * 120, M)  # v7, 45 x 45
        def extension(i):
            celdas = celdas_distintas(i.matriz, r.final.matriz)
            filas = [f for f, _ in celdas]
            cols = [c for _, c in celdas]
            return max(max(filas) - min(filas), max(cols) - min(cols))
        mancha = danar_matriz(r, 5, "bloque", semilla=4)
        azar = danar_matriz(r, 5, "azar", semilla=4)
        self.assertLess(extension(mancha), 20)
        self.assertGreater(extension(azar), 30)


class TestParametros(unittest.TestCase):
    def setUp(self):
        self.r = qr("HOLA")

    def test_modo_desconocido(self):
        with self.assertRaises(ParametroInvalido):
            danar_matriz(self.r, 5, "diagonal")

    def test_porcentaje_fuera_de_rango_o_de_tipo_incorrecto(self):
        for malo in (0, -1, 100.01, 101, "5", None, True):
            with self.assertRaises(ParametroInvalido, msg=repr(malo)):
                danar_matriz(self.r, malo)  # type: ignore[arg-type]

    def test_cien_es_valido(self):
        self.assertIsInstance(danar_matriz(self.r, 100), InformeDanio)


if __name__ == "__main__":
    unittest.main()
