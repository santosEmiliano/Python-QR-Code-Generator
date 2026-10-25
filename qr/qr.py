"""Integrador del flujo completo, llama a cada etapa en orden y junta sus salidas
en un `ResultadoQR`. 

    EntradaUsuario
      -> codificar_mensaje      (P1, etapas 1-3)  MensajeCodificado
      -> agregar_correccion     (P2, etapa 4)     MensajeConCorreccion
      -> ordenar_matriz         (P3, etapa 5)     MatrizOrdenada
      -> finalizar_matriz       (P4, etapas 6-7)  MatrizFinal
"""

from __future__ import annotations

from .contrato import EntradaUsuario, ResultadoQR
from .mascaras import finalizar_matriz
from .matriz import ordenar_matriz
from .reed_solomon import agregar_correccion
from .version import codificar_mensaje

__all__ = ["generar_qr"]


def generar_qr(entrada: EntradaUsuario) -> ResultadoQR:
    """Genera el QR de `entrada`. Lanza una subclase de ErrorQR si el texto o los
    parametros no sirven (ver contrato.py)."""
    mensaje = codificar_mensaje(entrada)
    correccion = agregar_correccion(mensaje)
    ordenada = ordenar_matriz(correccion.secuencia, mensaje.version)
    final = finalizar_matriz(
        ordenada, mensaje.version, mensaje.nivel_correccion, entrada.mascara
    )
    return ResultadoQR(
        entrada=entrada,
        mensaje=mensaje,
        correccion=correccion,
        matriz_ordenada=ordenada,
        final=final,
    )
