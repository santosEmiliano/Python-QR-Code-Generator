"""Contrato de datos entre las etapas del flujo de trabajo:

Quien produce cada cosa
-----------------------
    EntradaUsuario         la arma la UI (P5) con lo que pide el usuario
    MensajeCodificado      la produce P1  (etapas 1-3)  -> la consume P2
    MensajeConCorreccion   la produce P2  (etapa 4)     -> la consume P3
    MatrizOrdenada         la produce P3  (etapa 5)     -> la consume P4
    MatrizFinal            la produce P4  (etapas 6-7)  -> la consume P5
    ResultadoQR            la arma el orquestador (P1)  -> la consume la UI / P5

Convenciones que valen para todo el contrato
--------------------------------------------
- **Matriz**: list[list[bool]], se indexa matriz[fila][columna]. True = modulo
  oscuro (negro), False = claro. El origen (0,0) es la esquina superior izquierda
  del QR, SIN contar el margen blanco (ese lo agrega el renderer de P5).
- **Tamano**: un QR de version V mide  n = 21 + 4 * (V - 1)  modulos de lado.
- **Bits**: siempre una lista de enteros 0/1. Dentro de cada byte, el bit mas
  significativo va primero (MSB-first).
- **Byte** (en la jerga QR, "codeword"): un entero de 0 a 255. Una secuencia de
  bytes es una list[int].
- Los dataclasses son `frozen` (no se les puede reasignar un campo). Las listas
  que llevan adentro son mutables por Python, pero la convencion es que **nadie
  las modifica**: cada etapa devuelve estructuras nuevas.
- Ante entrada imposible o parametro invalido, la etapa lanza una excepcion de
  `ErrorQR` (ver el final del archivo). Nunca devuelve None ni algo a medio armar.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

__all__ = [
    "Modo",
    "NivelCorreccion",
    "EntradaUsuario",
    "MensajeCodificado",
    "BloqueCorreccion",
    "MensajeConCorreccion",
    "MatrizOrdenada",
    "MatrizFinal",
    "ResultadoQR",
    "ErrorQR",
    "TextoNoEntra",
    "ParametroInvalido",
    "TextoNoValidoParaModo",
]

# Enumeraciones

class Modo(str, Enum):
    """Como se codifica el texto dentro del QR.

    Cada modo tiene una regla distinta para pasar el texto a bits. Cuanto mas
    arriba en esta lista, mas compacto (menos bits por caracter), pero admite
    menos caracteres.
    """

    NUMERICO = "numerico"          # el texto son puros digitos 0-9
    ALFANUMERICO = "alfanumerico"  # digitos + LETRAS MAYUSCULAS + " $%*+-./:"
    BYTE = "byte"                  # cualquier otra cosa (minusculas, acentos,
                                   # emojis...): el texto se toma como bytes UTF-8

class NivelCorreccion(str, Enum):
    """Cuanto dano puede sufrir el QR y aun asi leerse.

    Mas correccion es mas espacio ocupado por el respaldo, que, a su vez, es menos lugar para el
    texto. El valor por defecto en todo el proyecto es M.
    """

    L = "L"  # recupera hasta ~7 % del codigo danado
    M = "M"  # ~15 %
    Q = "Q"  # ~25 %
    H = "H"  # ~30 %

# Modo que puede pedir el usuario. "auto" no es un Modo real: le dice a P1 que
# elija solo el modo mas compacto que sirva para ese texto.
ModoPedido = Literal["auto", "numerico", "alfanumerico", "byte"]

# Entrada del flujo de trabajo

@dataclass(frozen=True)
class EntradaUsuario:
    """Lo que pide el usuario. Es la entrada de todo el flujo de trabajo."""

    texto: str
    # Cuanto dano debe tolerar el QR. Por defecto, el nivel medio.
    nivel_correccion: NivelCorreccion = NivelCorreccion.M
    # "auto": P1 elige el modo mas compacto que sirva para `texto`.
    # Si se fija un modo concreto y el texto tiene caracteres que ese modo no
    # admite, P1 lanza TextoNoValidoParaModo.
    modo: ModoPedido = "auto"
    # Forzar un tamano de QR minimo (1..40). None: usar el mas chico donde entre.
    # Si el texto no entra ni siquiera en la version 40, P1 lanza TextoNoEntra.
    version_minima: int | None = None
    # Forzar uno de los 8 patrones de mascara (0..7). None: P4 elige el mejor.
    mascara: int | None = None

# Etapas 1-3 - P1 - codificar_mensaje()

@dataclass(frozen=True)
class MensajeCodificado:
    """Salida de P1. El texto del usuario ya convertido a bits y agrupado en
    bytes, listo para que P2 le calcule el respaldo.

    P1 aca ya decidio tres cosas: en que modo se codifica, en que version (tamano)
    entra y con que nivel de correccion. El relleno para llegar al tamano exacto
    tambien lo mete P1 (son bytes de prueba, no dicen nada. No hay que confundirlo con el
    respaldo de P2, que si sirve para reparar).
    """

    modo: Modo
    # Version (tamano) de QR elegida, 1..40. El QR mide n = 21 + 4*(version-1).
    version: int
    nivel_correccion: NivelCorreccion
    # Cuantos caracteres del texto original se codificaron (para la "etiqueta"
    # de cantidad que va dentro del mensaje).
    cantidad_caracteres: int
    # El mensaje entero como lista de 0/1:
    #   indicador de modo + indicador de cantidad + datos + terminador + relleno.
    # MSB-first dentro de cada byte.
    bits: list[int]
    # Exactamente los mismos bits de arriba, agrupados de a 8 -> lista de enteros
    # 0..255. TODAVIA sin los bytes de correccion (eso lo agrega P2).
    bytes_mensaje: list[int]

# Etapa 4 - P2 - agregar_correccion()

@dataclass(frozen=True)
class BloqueCorreccion:
    """Un bloque del mensaje con su respaldo, ANTES de intercalar.

    En los QR grandes el mensaje se parte en varios bloques y se calcula respaldo
    para cada uno por separado (asi una mancha localizada no se lleva todo). En
    los QR chicos hay un solo bloque.

    Es un intermedio: sirve para depurar y para los tests por etapa. La secuencia
    que de verdad se pinta en la matriz es `MensajeConCorreccion.secuencia`.
    """

    bytes_mensaje: list[int]     # el pedazo del mensaje que le toca a este bloque
    bytes_correccion: list[int]  # los bytes de respaldo calculados para ese pedazo


@dataclass(frozen=True)
class MensajeConCorreccion:
    """Salida de P2. Mensaje + respaldo, ya partido en bloques e intercalado,
       listo para que P3 lo pinte en la matriz.
    """

    # mensaje + respaldo de todos los bloques, intercalados en el orden que manda
    # el estandar. Esta es la unica lista que P3 necesita para colocar los datos.
    secuencia: list[int]
    # El detalle por bloque, sin intercalar (para depurar / tests). El orden de
    # la lista es el orden de los bloques del estandar.
    bloques: list[BloqueCorreccion]

# Etapa 5 - P3 - ordenar_matriz()

@dataclass(frozen=True)
class MatrizOrdenada:
    """Salida de P3. La cuadricula con los patrones fijos dibujados y los datos
    ya colocados en zigzag, pero SIN mascara y con los huecos de la info de
    formato/version todavia vacios (en False).

    Es "la matriz ordenada": tiene todo en su lugar, le falta el ultimo paso
    (P4) para ser escaneable.
    """

    # n x n. True = cuadro oscuro, False = cuadro claro. matriz[fila][columna], origen
    # arriba-izquierda, sin margen blanco.
    matriz: list[list[bool]]
    # Misma forma que `matriz`. True = ese cuadro NO se puede tocar con la
    # mascara: o es un patron fijo (localizador, separador, temporizacion,
    # alineacion, modulo oscuro) o es un hueco reservado para la info de
    # formato/version que llena P4. Este es el dato clave que P4 necesita.
    reservado: list[list[bool]]

# Etapas 6-7 - P4 - finalizar_matriz()

@dataclass(frozen=True)
class MatrizFinal:
    """Salida de P4. La matriz ya escaneable.

    P4 hará dos cosas: (1) probar los 8 patrones de mascara, les pondra un puntaje
    de "que tan feo/dificil de leer quedo" con las 4 reglas del estandar y se
    quedara con el mejor; (2) armara la info de formato (nivel + mascara) y, de la
    version 7 en adelante, la info de version (tamano), cada una con su propio
    respaldo, y las colocara en los huecos reservados.
    """

    # n x n. Datos + mascara aplicada + info de formato/version ya colocada.
    # Esta es la matriz que P5 renderizara.
    matriz: list[list[bool]]
    # Cual de los 8 patrones (0..7) se termino usando.
    mascara: int
    # Los bits de la "etiqueta" de formato (nivel de correccion + mascara), ya
    # con su propio respaldo BCH. Se guardan aca para inspeccion / tests.
    bits_formato: list[int]
    # Los bits de la "etiqueta" de version (tamano), ya con su respaldo BCH.
    # Solo existe de la version 7 en adelante; en versiones 1-6 es None.
    bits_version: list[int] | None


# Objeto de resultado completo - lo arma P1

@dataclass(frozen=True)
class ResultadoQR:
    """Todo el flujo en una sola estructura.

    Lo arma `generar_qr()` llamando a cada etapa en orden y guardando su salida.
    La UI llama a `generar_qr(entrada)` y despues pasa `resultado.final.matriz` a
    los renderers de P5. Guardar tambien los intermedios permite que la UI
    muestre datos de depuracion sin volver a correr nada.
    """

    entrada: EntradaUsuario
    mensaje: MensajeCodificado
    correccion: MensajeConCorreccion
    matriz_ordenada: MatrizOrdenada
    final: MatrizFinal

# Excepciones

class ErrorQR(Exception):
    """Base de todos los errores del generador. La UI puede atrapar solo esta."""


class TextoNoEntra(ErrorQR):
    """El texto no cabe ni en el QR mas grande (version 40) con el nivel de
    correccion pedido. La lanza P1 al seleccionar version."""


class ParametroInvalido(ErrorQR):
    """Un parametro de EntradaUsuario esta fuera de rango: mascara fuera de 0..7,
    version_minima fuera de 1..40, nivel_correccion desconocido, etc."""


class TextoNoValidoParaModo(ErrorQR):
    """Se forzo un modo (p. ej. 'numerico') pero el texto tiene caracteres que
    ese modo no admite. La lanza P1 al analizar la entrada."""
