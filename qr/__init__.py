"""Generador de codigos QR desde cero (ISO/IEC 18004), 100% offline y sin librerias de QR.

Organizacion del paquete (una etapa del pipeline por archivo):

    contrato.py     Tipos del objeto de resultado y excepciones. Sin logica.
                    Todos los modulos importan de aca.
    tablas.py       Consulta pura de las tablas fijas del estandar. Ningun otro
                    modulo hardcodea un numero de la ISO: lo pide aca.

    entrada.py      Etapa 1  (P1) - analisis del texto y seleccion de modo.
    version.py      Etapas 2-3 (P1) - seleccion de version/nivel y armado de bits.
    reedsolomon.py  Etapa 4  (P2) - correccion de errores (Reed-Solomon / GF(256)).
    matriz.py       Etapa 5  (P3) - patrones fijos + colocado de datos en zigzag.
    mascaras.py     Etapas 6-7 (P4) - mascara e info de formato/version.
    render.py       Etapa 8  (P5) - SVG / PNG / terminal.
    cli.py          (P5) - interfaz de linea de comandos.
    ventana.py      (P5) - interfaz de ventana (tkinter).
    qr.py           Orquestador: generar_qr(). Llama a cada etapa en orden.

El pipeline es una cadena de funciones puras. Cada etapa recibe la salida de la
anterior y devuelve algo nuevo; no muta su entrada, no usa globales y no toca
disco (salvo los renderers de P5).
"""
