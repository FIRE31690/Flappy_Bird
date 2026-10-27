"""Rutas del proyecto con pathlib.

Las rutas se calculan a partir de la ubicación de ESTE archivo (``__file__``),
no de la carpeta desde donde se ejecuta el programa. Así funciona igual desde
cualquier lugar. La variable de entorno ``FLAPPY_DATOS`` permite cambiar la
carpeta base de datos (útil para pruebas o para tener varios perfiles).
"""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RAIZ_DATOS = Path(os.environ.get("FLAPPY_DATOS", RAIZ))

RUTA_JSON = RAIZ_DATOS / "data" / "flappy.json"
RUTA_BITACORA = RAIZ_DATOS / "data" / "bitacora.txt"
CARPETA_EXPORT = RAIZ_DATOS / "exports"
