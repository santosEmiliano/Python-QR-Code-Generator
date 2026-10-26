"""Generador de codigos QR desde cero (ISO/IEC 18004), 100% offline y sin librerias de QR.

Organizacion del paquete (una etapa del pipeline por archivo):

    contrato.py       Tipos del objeto de resultado y excepciones. Sin logica.
                      Todos los modulos importan de aca.
    tablas.py         Consulta pura de las tablas fijas del estandar. Ningun otro
                      modulo hardcodea un numero de la ISO: lo pide aca.

    entrada.py        Etapa 1 - analisis del texto y seleccion de modo.
    version.py        Etapas 2-3 - seleccion de version/nivel y armado de bits.
    reed_solomon.py   Etapa 4 - correccion de errores (Reed-Solomon / GF(256)).
    matriz.py         Etapa 5 - patrones fijos + colocado de datos en zigzag.
    mascaras.py       Etapas 6-7 - mascara e info de formato/version.
    qr.py             Orquestador: generar_qr(). Llama a cada etapa en orden.

    danio.py          Simulador de dano: invierte modulos de un QR ya generado y
                      dice si la correccion de errores podria recuperarlo.
    ui/terminal.py    Interfaz de terminal (modo simple y avanzado).
    ui/qr_imagen.py   Exportacion a PNG.
    ui/gui.py         Ventana de prueba, sin conectar al generador.

El pipeline es una cadena de funciones puras. Cada etapa recibe la salida de la
anterior y devuelve algo nuevo; no muta su entrada, no usa globales y no toca
disco (salvo la exportacion de imagen de ui/qr_imagen.py).
"""
