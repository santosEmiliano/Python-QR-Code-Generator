"""Etapa 4 — Reed-Solomon / corrección de errores (responsable: P2).

Recibe el MensajeCodificado de P1 (etapas 1-3) y devuelve el
MensajeConCorreccion que consume P3 (etapa 5):

  1. parte el mensaje en bloques (estructura según versión y nivel)
  2. calcula los bytes de corrección de cada bloque con Reed-Solomon
     sobre GF(256): polinomio generador + resto de la división
  3. intercala datos y corrección como manda el estándar
"""

from __future__ import annotations
#Creado basado a un pipeline de pruebas, modificar si es necesario. 
from contrato import BloqueCorreccion, ErrorQR, MensajeCodificado, MensajeConCorreccion

# Aritmética en GF(256): sumar y restar es XOR; multiplicar y dividir usa dos
# tablas de consulta (log/exp) construidas una vez. Polinomio primitivo del
# estándar: 0x11D, con generador alfa = 2.
_PRIMITIVO = 0x11D
_EXP = [0] * 512
_LOG = [0] * 256


def _cargar_tablas() -> None:
    x = 1
    for i in range(255):
        _EXP[i] = x
        _LOG[x] = i
        x <<= 1
        if x & 0x100:              # se pasó de 8 bits -> reducir módulo el primitivo
            x ^= _PRIMITIVO
    for i in range(255, 512):      # duplicado para no calcular % 255 al multiplicar
        _EXP[i] = _EXP[i - 255]


_cargar_tablas()


def gf_mul(a: int, b: int) -> int:
    """Producto en GF(256)."""
    return 0 if a == 0 or b == 0 else _EXP[_LOG[a] + _LOG[b]]


def polinomio_generador(n_ec: int) -> list[int]:
    """g(x) = (x - a^0)(x - a^1)...(x - a^(n_ec-1)). Coefs. de mayor a menor grado."""
    g = [1]
    for i in range(n_ec):
        r = _EXP[i]                       # alfa^i
        nueva = g + [0]                   # multiplicar g por (x + alfa^i)
        for j, c in enumerate(g):
            nueva[j + 1] ^= gf_mul(c, r)
        g = nueva
    return g


def calcular_correccion(datos: list[int], n_ec: int) -> list[int]:
    """Respaldo de un bloque: resto de dividir datos(x) * x^n_ec entre g(x)."""
    g = polinomio_generador(n_ec)
    resto = list(datos) + [0] * n_ec
    for i in range(len(datos)):
        f = resto[i]
        if f:
            for j in range(1, len(g)):
                resto[i + j] ^= gf_mul(g[j], f)
    return resto[len(datos):]


# ---------------------------------------------------------------------------
# Bloques e intercalado
# ---------------------------------------------------------------------------

def _partir_en_bloques(bytes_msg: list[int], estructura) -> list[tuple[list[int], int]]:
    """Corta el mensaje según la estructura del estándar:
    [(n_bloques, codewords_totales_por_bloque, codewords_de_datos), ...]
    Devuelve [(datos_del_bloque, n_ec_del_bloque), ...]."""
    bloques, idx = [], 0
    for n_bloques, total, n_datos in estructura:
        for _ in range(n_bloques):
            trozo = bytes_msg[idx: idx + n_datos]
            if len(trozo) != n_datos:
                raise ErrorQR("el mensaje no alcanza a llenar la estructura de bloques")
            bloques.append((trozo, total - n_datos))
            idx += n_datos
    if idx != len(bytes_msg):
        raise ErrorQR("el largo del mensaje no coincide con la estructura de bloques")
    return bloques


def intercalar(bloques: list[tuple[list[int], list[int]]]) -> list[int]:
    """Datos: una ronda por bloque (1er byte de cada uno, 2do de cada uno...).
    Después lo mismo con la corrección. Los bloques cortos se agotan y se saltean."""
    datos = [d for d, _ in bloques]
    ecs = [e for _, e in bloques]
    seq: list[int] = []
    for ronda in range(max(len(d) for d in datos)):
        for d in datos:
            if ronda < len(d):
                seq.append(d[ronda])
    for ronda in range(max(len(e) for e in ecs)):
        for e in ecs:
            if ronda < len(e):
                seq.append(e[ronda])
    return seq


# La etapa del contrato

def agregar_correccion(mensaje: MensajeCodificado,
                       estructura_bloques=None) -> MensajeConCorreccion:
    """Etapa 4: consume MensajeCodificado (P1) -> produce MensajeConCorreccion (P3).

    estructura_bloques: [(n_bloques, total, datos), ...]. Normalmente la provee
    tables.ec_blocks(version, nivel) de P1; si se omite, se importa de tables.
    El parámetro existe para probar cualquier versión sin esperar esa tabla.
    """
    if estructura_bloques is None:
        from tables import ec_blocks    # tabla del estándar, la mantiene P1
        estructura_bloques = ec_blocks(mensaje.version, mensaje.nivel_correccion)

    cortes = _partir_en_bloques(mensaje.bytes_mensaje, estructura_bloques)
    bloques = [
        BloqueCorreccion(bytes_mensaje=d, bytes_correccion=calcular_correccion(d, n_ec))
        for d, n_ec in cortes
    ]
    return MensajeConCorreccion(
        secuencia=intercalar([(b.bytes_mensaje, b.bytes_correccion) for b in bloques]),
        bloques=bloques,
    )
