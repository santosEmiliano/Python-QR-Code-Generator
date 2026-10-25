"""Tests del orquestador (qr/qr.py): que generar_qr encadene las cuatro etapas y
arme el ResultadoQR del contrato.

La lectura real del QR con un decodificador externo no esta aca (el repo no
depende de ninguno); ver la verificacion manual descrita en el commit.

Correr con:

    python -m unittest tests.test_qr -v
"""

from __future__ import annotations

import unittest

from qr.contrato import (
    EntradaUsuario,
    ErrorQR,
    NivelCorreccion,
    ParametroInvalido,
    ResultadoQR,
    TextoNoValidoParaModo,
)
from qr.mascaras import bits_formato
from qr.matriz import _celdas_formato, lado
from qr.qr import generar_qr
from qr.reed_solomon import agregar_correccion
from qr.version import codificar_mensaje

L, M, Q, H = (
    NivelCorreccion.L,
    NivelCorreccion.M,
    NivelCorreccion.Q,
    NivelCorreccion.H,
)


class TestGenerarQR(unittest.TestCase):
    def test_devuelve_un_ResultadoQR_con_todas_las_etapas(self):
        entrada = EntradaUsuario(texto="HELLO WORLD")
        r = generar_qr(entrada)
        self.assertIsInstance(r, ResultadoQR)
        self.assertIs(r.entrada, entrada)
        self.assertEqual(r.mensaje, codificar_mensaje(entrada))
        self.assertEqual(r.correccion, agregar_correccion(r.mensaje))
        self.assertEqual(r.matriz_ordenada.matriz[0][:7], [True] * 7)  # localizador

    def test_hello_world_por_defecto_es_version_1_nivel_M(self):
        r = generar_qr(EntradaUsuario(texto="HELLO WORLD"))
        self.assertEqual(r.mensaje.version, 1)
        self.assertEqual(r.mensaje.nivel_correccion, M)
        self.assertEqual(len(r.final.matriz), 21)

    def test_el_lado_de_la_matriz_sigue_a_la_version(self):
        for texto, nivel in (("A" * 100, M), ("A" * 200, L), ("a" * 150, Q)):
            r = generar_qr(EntradaUsuario(texto=texto, nivel_correccion=nivel))
            n = lado(r.mensaje.version)
            self.assertEqual(len(r.final.matriz), n)
            self.assertTrue(all(len(f) == n for f in r.final.matriz))

    def test_mascara_forzada_se_respeta_y_queda_en_el_formato(self):
        for nivel in (L, M, Q, H):
            for mascara in (0, 4, 7):
                r = generar_qr(EntradaUsuario(texto="HOLA", nivel_correccion=nivel, mascara=mascara))
                self.assertEqual(r.final.mascara, mascara)
                self.assertEqual(r.final.bits_formato, bits_formato(nivel, mascara))
                celdas = _celdas_formato(lado(r.mensaje.version))
                leidos = [int(r.final.matriz[f][c]) for f, c in celdas[:15]]
                self.assertEqual(leidos, bits_formato(nivel, mascara))

    def test_version_minima_se_respeta(self):
        r = generar_qr(EntradaUsuario(texto="1", version_minima=5))
        self.assertEqual(r.mensaje.version, 5)
        self.assertEqual(len(r.final.matriz), lado(5))

    def test_es_deterministico(self):
        a = generar_qr(EntradaUsuario(texto="https://example.com"))
        b = generar_qr(EntradaUsuario(texto="https://example.com"))
        self.assertEqual(a.final, b.final)

    def test_texto_utf8_usa_modo_byte(self):
        r = generar_qr(EntradaUsuario(texto="ñandú"))
        self.assertEqual(r.mensaje.modo.value, "byte")

    def test_no_muta_la_matriz_ordenada_al_enmascarar(self):
        r = generar_qr(EntradaUsuario(texto="HELLO WORLD"))
        n = lado(r.mensaje.version)
        # los huecos de formato siguen vacios en la ordenada de P3
        for f, c in _celdas_formato(n):
            self.assertFalse(r.matriz_ordenada.matriz[f][c])

    def test_los_errores_de_las_etapas_llegan_sin_envolver(self):
        with self.assertRaises(TextoNoValidoParaModo):
            generar_qr(EntradaUsuario(texto="abc", modo="numerico"))
        with self.assertRaises(ParametroInvalido):
            generar_qr(EntradaUsuario(texto="abc", mascara=9))
        with self.assertRaises(ErrorQR):
            generar_qr(EntradaUsuario(texto="abc", version_minima=0))


if __name__ == "__main__":
    unittest.main()
