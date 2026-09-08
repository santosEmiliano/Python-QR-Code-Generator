"""Tests de las etapas 2-3 (qr/version.py): codificacion de datos por modo,
seleccion de version, ensamblado del bitstream y composicion de la etapa.

Correr con:

    python -m unittest tests.test_version -v
"""

from __future__ import annotations

import unittest

from qr.contrato import (
    EntradaUsuario,
    MensajeCodificado,
    Modo,
    NivelCorreccion,
    ParametroInvalido,
    TextoNoEntra,
    TextoNoValidoParaModo,
)
from qr.entrada import AnalisisTexto, analizar_texto
from qr.tablas import capacidad_bytes_datos
from qr.version import (
    agrupar_en_bytes,
    armar_bits,
    codificar_mensaje,
    codificar_segmento,
    elegir_version,
)

L, M, Q, H = (
    NivelCorreccion.L,
    NivelCorreccion.M,
    NivelCorreccion.Q,
    NivelCorreccion.H,
)


def bits_str(bits: list[int]) -> str:
    return "".join(str(b) for b in bits)


def hexs(bytes_: list[int]) -> list[str]:
    return [format(b, "02X") for b in bytes_]


class TestCodificarSegmento(unittest.TestCase):
    """codificar_segmento(): texto -> bits de datos, sin etiquetas."""

    def test_numerico_thonky(self):
        # "8675309" -> 867(10) 530(10) 9(4)
        self.assertEqual(
            bits_str(codificar_segmento(analizar_texto("8675309"))),
            "110110001110000100101001",
        )

    def test_numerico_resto_de_dos_digitos_toma_7_bits(self):
        self.assertEqual(bits_str(codificar_segmento(analizar_texto("12"))), "0001100")

    def test_numerico_resto_de_un_digito_toma_4_bits(self):
        self.assertEqual(bits_str(codificar_segmento(analizar_texto("1"))), "0001")

    def test_alfanumerico_hello_world(self):
        self.assertEqual(
            bits_str(codificar_segmento(analizar_texto("HELLO WORLD"))),
            "0110000101101111000110100010111001011011100010011010100001101",
        )

    def test_alfanumerico_caracter_suelto_toma_6_bits(self):
        # 'A' vale 10 en el set alfanumerico -> 001010
        self.assertEqual(bits_str(codificar_segmento(analizar_texto("A"))), "001010")

    def test_byte_ascii(self):
        self.assertEqual(
            bits_str(codificar_segmento(analizar_texto("Hello", "byte"))),
            "0100100001100101011011000110110001101111",
        )

    def test_byte_cuenta_por_byte_utf8_no_por_caracter(self):
        # '€' son 3 bytes UTF-8: E2 82 AC
        self.assertEqual(
            bits_str(codificar_segmento(analizar_texto("€"))),
            "111000101000001010101100",
        )

    def test_texto_vacio_da_lista_vacia(self):
        self.assertEqual(codificar_segmento(analizar_texto("")), [])


class TestElegirVersion(unittest.TestCase):
    """elegir_version(): la version mas chica donde entra el mensaje."""

    def test_hello_world_nivel_Q_es_v1(self):
        self.assertEqual(elegir_version(analizar_texto("HELLO WORLD"), Q), 1)

    def test_numerico_corto_es_v1(self):
        self.assertEqual(elegir_version(analizar_texto("01234567"), M), 1)

    def test_sube_de_version_cuando_no_entra_en_v1(self):
        # 23 bytes en modo byte no entran en v1-M (196 bits > 128), si en v2-M.
        texto = "https://www.qrcode.com/"
        self.assertEqual(elegir_version(analizar_texto(texto), M), 2)

    def test_version_minima_como_piso(self):
        self.assertEqual(elegir_version(analizar_texto("1"), M, version_minima=5), 5)

    def test_version_minima_no_impide_subir_mas(self):
        texto = "https://www.qrcode.com/"
        self.assertEqual(elegir_version(analizar_texto(texto), M, version_minima=1), 2)

    def test_version_minima_fuera_de_rango_lanza(self):
        for mala in (0, 41, -1):
            with self.subTest(version_minima=mala):
                with self.assertRaises(ParametroInvalido):
                    elegir_version(analizar_texto("1"), M, version_minima=mala)

    def test_version_minima_no_entera_lanza(self):
        with self.assertRaises(ParametroInvalido):
            elegir_version(analizar_texto("1"), M, version_minima=2.5)  # type: ignore[arg-type]

    def test_texto_mas_grande_que_v10_corta_con_NotImplementedError(self):
        # Las tablas por-version llegan a v10, un texto que no entra antes
        # dispara el NotImplementedError de tablas.
        with self.assertRaises(NotImplementedError):
            elegir_version(analizar_texto("A" * 5000), H)


class TestArmarBits(unittest.TestCase):
    """armar_bits(): bitstream completo, del largo exacto de la capacidad."""

    def test_hello_world_v1_Q_vector_completo_thonky(self):
        bits = armar_bits(analizar_texto("HELLO WORLD"), 1, Q)
        self.assertEqual(
            hexs(agrupar_en_bytes(bits)),
            ["20", "5B", "0B", "78", "D1", "72", "DC", "4D", "43", "40", "EC", "11", "EC"],
        )

    def test_01234567_v1_M_vector_completo_iso(self):
        bits = armar_bits(analizar_texto("01234567"), 1, M)
        self.assertEqual(
            hexs(agrupar_en_bytes(bits)),
            ["10", "20", "0C", "56", "61", "80"] + ["EC", "11"] * 5,
        )

    def test_largo_es_exactamente_la_capacidad(self):
        casos = [("HOLA", 1, M), ("12345", 1, H), ("test data 123", 3, Q), ("x" * 40, 5, L)]
        for texto, version, nivel in casos:
            with self.subTest(texto=texto, version=version, nivel=nivel):
                bits = armar_bits(analizar_texto(texto), version, nivel)
                self.assertEqual(len(bits), capacidad_bytes_datos(version, nivel) * 8)

    def test_solo_bits_0_y_1(self):
        bits = armar_bits(analizar_texto("HELLO WORLD"), 1, Q)
        self.assertEqual(set(bits) - {0, 1}, set())

    def test_version_demasiado_chica_lanza_TextoNoEntra(self):
        with self.assertRaises(TextoNoEntra):
            armar_bits(analizar_texto("una URL larga de ejemplo " * 5), 1, H)

    def test_cantidad_que_no_entra_en_el_indicador_lanza_TextoNoEntra(self):
        # AnalisisTexto armado a mano con una cuenta imposible para v1 byte
        # (indicador de 8 bits -> tope 255).
        falso = AnalisisTexto(modo=Modo.BYTE, texto="x", cantidad_caracteres=999)
        with self.assertRaises(TextoNoEntra):
            armar_bits(falso, 1, L)


class TestAgruparEnBytes(unittest.TestCase):
    """agrupar_en_bytes(): bits de a 8, MSB-first."""

    def test_un_byte_msb_first(self):
        self.assertEqual(agrupar_en_bytes([1, 0, 1, 0, 0, 0, 0, 0]), [0xA0])

    def test_todos_unos(self):
        self.assertEqual(agrupar_en_bytes([1] * 8), [255])

    def test_dos_bytes(self):
        bits = [0, 0, 0, 1, 0, 0, 0, 0] + [1, 1, 1, 0, 1, 1, 0, 0]
        self.assertEqual(agrupar_en_bytes(bits), [0x10, 0xEC])

    def test_lista_vacia_da_lista_vacia(self):
        self.assertEqual(agrupar_en_bytes([]), [])

    def test_no_multiplo_de_8_lanza(self):
        with self.assertRaises(ParametroInvalido):
            agrupar_en_bytes([1, 0, 1])


class TestCodificarMensaje(unittest.TestCase):
    """codificar_mensaje(): compone la etapa y devuelve MensajeCodificado."""

    def test_hello_world_Q_resultado_completo(self):
        r = codificar_mensaje(
            EntradaUsuario(texto="HELLO WORLD", nivel_correccion=Q)
        )
        self.assertIsInstance(r, MensajeCodificado)
        self.assertEqual(r.modo, Modo.ALFANUMERICO)
        self.assertEqual(r.version, 1)
        self.assertEqual(r.nivel_correccion, Q)
        self.assertEqual(r.cantidad_caracteres, 11)
        self.assertEqual(
            hexs(r.bytes_mensaje),
            ["20", "5B", "0B", "78", "D1", "72", "DC", "4D", "43", "40", "EC", "11", "EC"],
        )

    def test_bits_y_bytes_mensaje_son_consistentes(self):
        r = codificar_mensaje(EntradaUsuario(texto="datos de prueba 123"))
        self.assertEqual(agrupar_en_bytes(r.bits), r.bytes_mensaje)
        self.assertEqual(len(r.bits), len(r.bytes_mensaje) * 8)

    def test_invariante_bytes_mensaje_llena_la_capacidad(self):
        for texto, nivel in [("HOLA", M), ("12345678", L), ("Prueba Larga XYZ", Q)]:
            with self.subTest(texto=texto, nivel=nivel):
                r = codificar_mensaje(
                    EntradaUsuario(texto=texto, nivel_correccion=nivel)
                )
                self.assertEqual(
                    len(r.bytes_mensaje),
                    capacidad_bytes_datos(r.version, nivel),
                )

    def test_defaults_modo_auto_y_nivel_M(self):
        r = codificar_mensaje(EntradaUsuario(texto="12345"))
        self.assertEqual(r.modo, Modo.NUMERICO)
        self.assertEqual(r.nivel_correccion, M)

    def test_modo_forzado_incompatible_propaga_TextoNoValidoParaModo(self):
        with self.assertRaises(TextoNoValidoParaModo):
            codificar_mensaje(EntradaUsuario(texto="abc", modo="numerico"))

    def test_modo_desconocido_propaga_ParametroInvalido(self):
        with self.assertRaises(ParametroInvalido):
            codificar_mensaje(EntradaUsuario(texto="abc", modo="raro"))  # type: ignore[arg-type]

    def test_version_minima_se_respeta(self):
        r = codificar_mensaje(EntradaUsuario(texto="12345", version_minima=3))
        self.assertEqual(r.version, 3)

    def test_mascara_fuera_de_rango_lanza_ParametroInvalido(self):
        for mala in (-1, 8, 9):
            with self.subTest(mascara=mala):
                with self.assertRaises(ParametroInvalido):
                    codificar_mensaje(EntradaUsuario(texto="x", mascara=mala))

    def test_mascara_valida_y_none_no_molestan(self):
        for buena in (None, 0, 7):
            with self.subTest(mascara=buena):
                r = codificar_mensaje(EntradaUsuario(texto="x", mascara=buena))
                self.assertIsInstance(r, MensajeCodificado)


if __name__ == "__main__":
    unittest.main()
