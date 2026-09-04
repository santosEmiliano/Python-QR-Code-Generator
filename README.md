# Python-QR-Code-Generator

Generador de códigos QR **hecho desde cero** en Python: implementa la codificación
del estándar **ISO/IEC 18004** (análisis de datos, Reed-Solomon, construcción de la
matriz, enmascarado, info de formato/versión) y produce una imagen escaneable.

- **100% offline y sin librerías de QR.** Única dependencia opcional: Pillow, solo
  para exportar PNG.
- Materia: Programación en Python (UAA). Equipo de 5.
- Base temática: organización de datos y recuperación ante daño.

## Requisitos

- Python **3.10+**
- Nada más para el core. `pip install -r requirements.txt` solo si vas a tocar la
  exportación PNG.

## Organización

El código vive en `qr/`, con una etapa del pipeline por archivo, y los tests en
`tests/`. El idioma del código es español (identificadores, tipos y comentarios).
