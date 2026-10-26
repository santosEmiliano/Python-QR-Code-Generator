# Python-QR-Code-Generator

Generador de códigos QR **hecho desde cero** en Python: implementa la codificación
del estándar **ISO/IEC 18004** (análisis de datos, Reed-Solomon, construcción de la
matriz, enmascarado, info de formato/versión) y produce una imagen escaneable.

- **100% offline y sin librerías de QR ni dependencias externas.** El PNG se
  escribe a mano con `zlib` y `struct`.
- Materia: Programación en Python (UAA). Equipo de 5.
- Base temática: organización de datos y recuperación ante daño.

## Requisitos

- Python **3.10+**
- Nada más: no hay que instalar paquetes.

## Organización

El código vive en `qr/`, con una etapa del pipeline por archivo, y los tests en
`tests/`. El idioma del código es español (identificadores, tipos y comentarios).

## Uso

Desde la raíz del repositorio:

```
python3 -m qr.ui.terminal
```

La terminal ofrece un modo simple (solo pide el texto) y uno avanzado (modo, nivel
de corrección, versión y máscara). Después de mostrar el QR permite guardarlo como
`QR.png` y dañarlo a propósito para comprobar la corrección de errores.

Las tablas del estándar están cargadas de la versión 1 a la 10, una versión mayor
lanza `NotImplementedError`.

## Pruebas

```
python3 -m unittest discover -s tests
```
