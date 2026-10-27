"""Validación y normalización de datos. Lanza ValidacionError."""
import re

from .excepciones import ValidacionError
from .reglas import DIFICULTADES, NOMBRE_MAX, NOMBRE_MIN, PUNTAJE_MAX, SKINS

_PATRON_NOMBRE = re.compile(r"^[A-Za-z0-9_áéíóúÁÉÍÓÚñÑ ]+$")


def validar_nombre(texto) -> str:
    nombre = str(texto).strip()
    if not (NOMBRE_MIN <= len(nombre) <= NOMBRE_MAX):
        raise ValidacionError(f"El nombre debe tener entre {NOMBRE_MIN} y {NOMBRE_MAX} caracteres.")
    if not _PATRON_NOMBRE.match(nombre):
        raise ValidacionError("El nombre solo admite letras, números, espacios y guion bajo.")
    return nombre


def validar_entero(texto, campo="valor") -> int:
    try:
        return int(str(texto).strip())
    except ValueError:
        raise ValidacionError(f"{campo} debe ser un número entero.") from None


def validar_puntaje(valor) -> int:
    puntaje = validar_entero(valor, "El puntaje")
    if not 0 <= puntaje <= PUNTAJE_MAX:
        raise ValidacionError(f"El puntaje debe estar entre 0 y {PUNTAJE_MAX}.")
    return puntaje


def validar_dificultad(texto) -> str:
    dificultad = str(texto).strip().lower()
    if dificultad not in DIFICULTADES:
        raise ValidacionError(f"Dificultad inválida. Use: {', '.join(DIFICULTADES)}.")
    return dificultad


def validar_skin(texto) -> str:
    skin = str(texto).strip().lower()
    if skin not in SKINS:
        raise ValidacionError(f"Skin inexistente. Disponibles: {', '.join(SKINS)}.")
    return skin
