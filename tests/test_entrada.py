"""Tests de qr/entrada.py: deteccion de modo, validacion contra un
modo forzado y analisis completo del texto.

Sin librerias: se usa unittest, que viene con Python. Correr con:

    python -m unittest
    python -m unittest tests.test_entrada -v
"""

from __future__ import annotations

import unittest

from qr.contrato import ErrorQR, Modo, ParametroInvalido, TextoNoValidoParaModo
from qr.entrada import (
    AnalisisTexto,
    analizar_texto,
    detectar_modo,
    validar_texto_para_modo,
)

class TestDetectarModo(unittest.TestCase):
    """detectar_modo() elige el modo mas compacto que sirva para el texto."""

    def test_solo_digitos_es_numerico(self):
        self.assertEqual(detectar_modo("0123456789"), Modo.NUMERICO)

    def test_alfanumerico_con_letras_y_simbolos_permitidos(self):
        # El set alfanumerico del QR: digitos, A-Z y  espacio $ % * + - . / :
        self.assertEqual(detectar_modo("HELLO WORLD $%*+-./:"), Modo.ALFANUMERICO)

    def test_digitos_sueltos_no_bloquean_alfanumerico(self):
        self.assertEqual(detectar_modo("ABC123"), Modo.ALFANUMERICO)

    def test_minusculas_caen_a_byte(self):
        self.assertEqual(detectar_modo("Hello"), Modo.BYTE)

    def test_acentos_caen_a_byte(self):
        self.assertEqual(detectar_modo("CÓDIGO"), Modo.BYTE)

    def test_emoji_cae_a_byte(self):
        self.assertEqual(detectar_modo("QR 🔥👻🐒"), Modo.BYTE)

    def test_texto_vacio_es_numerico(self):
        self.assertEqual(detectar_modo(""), Modo.NUMERICO)

class TestValidarTextoParaModo(unittest.TestCase):
    """validar_texto_para_modo() no devuelve nada, solo determina si el texto no entra."""

    def test_numerico_valido_no_lanza(self):
        self.assertIsNone(validar_texto_para_modo("12345", Modo.NUMERICO))

    def test_alfanumerico_valido_no_lanza(self):
        self.assertIsNone(validar_texto_para_modo("HELLO 123", Modo.ALFANUMERICO))

    def test_byte_admite_cualquier_cosa(self):
        self.assertIsNone(validar_texto_para_modo("cualquier cosa codigo 🔥🐒👻", Modo.BYTE))

    def test_numerico_con_letra_lanza(self):
        with self.assertRaises(TextoNoValidoParaModo):
            validar_texto_para_modo("12A45", Modo.NUMERICO)

    def test_alfanumerico_con_minuscula_lanza(self):
        with self.assertRaises(TextoNoValidoParaModo):
            validar_texto_para_modo("Hello", Modo.ALFANUMERICO)

    def test_mensaje_nombra_los_caracteres_sobrantes_ordenados_y_sin_repetir(self):
        with self.assertRaises(TextoNoValidoParaModo) as ctx:
            validar_texto_para_modo("1b1a1a1b", Modo.NUMERICO)
        mensaje = str(ctx.exception)
        # sorted({'b', 'a'}) -> ['a', 'b']
        self.assertIn("['a', 'b']", mensaje)

    def test_error_es_subclase_de_ErrorQR(self):
        # La UI atrapa solo ErrorQR; esto garantiza que este error entra ahi.
        with self.assertRaises(ErrorQR):
            validar_texto_para_modo("X", Modo.NUMERICO)

class TestAnalizarTextoAuto(unittest.TestCase):
    """analizar_texto(texto, 'auto'): detecta el modo y cuenta caracteres."""

    def test_devuelve_AnalisisTexto(self):
        self.assertIsInstance(analizar_texto("123"), AnalisisTexto)

    def test_numerico(self):
        r = analizar_texto("12345")
        self.assertEqual(r.modo, Modo.NUMERICO)
        self.assertEqual(r.cantidad_caracteres, 5)
        self.assertEqual(r.texto, "12345")

    def test_alfanumerico(self):
        r = analizar_texto("HELLO WORLD")
        self.assertEqual(r.modo, Modo.ALFANUMERICO)
        self.assertEqual(r.cantidad_caracteres, 11)

    def test_byte_cuenta_bytes_utf8_no_caracteres(self):
        # "café" son 4 caracteres pero 5 bytes UTF-8 (é ocupa 2).
        r = analizar_texto("café")
        self.assertEqual(r.modo, Modo.BYTE)
        self.assertEqual(r.cantidad_caracteres, 5)

    def test_auto_es_el_valor_por_defecto(self):
        self.assertEqual(analizar_texto("abc"), analizar_texto("abc", "auto"))

    def test_no_altera_el_texto_original(self):
        r = analizar_texto("Hola Mundo")
        self.assertEqual(r.texto, "Hola Mundo")

class TestAnalizarTextoModoForzado(unittest.TestCase):
    """analizar_texto(texto, modo): valida contra ese modo o lanza."""

    def test_forzar_byte_sobre_texto_alfanumerico(self):
        # El texto entraria en alfanumerico, pero se pidio byte: se deja tal cual.
        r = analizar_texto("ABC", "byte")
        self.assertEqual(r.modo, Modo.BYTE)
        self.assertEqual(r.cantidad_caracteres, 3)

    def test_forzar_numerico_valido(self):
        r = analizar_texto("42", "numerico")
        self.assertEqual(r.modo, Modo.NUMERICO)
        self.assertEqual(r.cantidad_caracteres, 2)

    def test_forzar_alfanumerico_valido(self):
        r = analizar_texto("AB 12", "alfanumerico")
        self.assertEqual(r.modo, Modo.ALFANUMERICO)

    def test_forzar_numerico_sobre_texto_no_numerico_lanza(self):
        with self.assertRaises(TextoNoValidoParaModo):
            analizar_texto("12A", "numerico")

    def test_modo_desconocido_lanza_ParametroInvalido(self):
        with self.assertRaises(ParametroInvalido):
            analizar_texto("hola", "hexadecimal")

    def test_modo_desconocido_es_subclase_de_ErrorQR(self):
        with self.assertRaises(ErrorQR):
            analizar_texto("hola", "hexadecimal")

class TestAnalisisTextoEsInmutable(unittest.TestCase):
    """AnalisisTexto es un dataclass frozen, o sea, no se le reasignan campos."""

    def test_no_se_puede_reasignar_un_campo(self):
        r = analizar_texto("123")
        with self.assertRaises(Exception):
            r.modo = Modo.BYTE  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
