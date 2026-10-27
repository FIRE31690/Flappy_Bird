"""Reglas de negocio puras (sin entrada/salida): fáciles de probar."""
from .dificultad import DIFICULTADES  # se reexporta: validadores e interfaz la importan de aquí

PUNTAJE_MAX = 9999
NOMBRE_MIN, NOMBRE_MAX = 3, 15  # asignación múltiple con tuplas

SKINS = {"clasico": 0, "rojo": 50, "dorado": 150, "fantasma": 300}  # costo en monedas

_MEDALLAS = [(100, "platino"), (40, "oro"), (20, "plata"), (10, "bronce")]
_NIVELES = [(500, 5), (250, 4), (100, 3), (30, 2)]  # monedas acumuladas -> nivel


def medalla_para(puntaje: int) -> str:
    for minimo, nombre in _MEDALLAS:
        if puntaje >= minimo:
            return nombre
    return "ninguna"


def monedas_para(puntaje: int, dificultad: str) -> int:
    # Polimorfismo: cada objeto Dificultad sabe calcular sus monedas.
    return DIFICULTADES[dificultad].monedas_para(puntaje)


def nivel_para(monedas_acumuladas: int) -> int:
    for minimo, nivel in _NIVELES:
        if monedas_acumuladas >= minimo:
            return nivel
    return 1


def categoria_para(nivel: int, mejor_puntaje: int, partidas: int) -> str:
    """Clasifica a un jugador. Ejemplo de if / elif / else y de and / or."""
    if partidas == 0:
        return "sin jugar"
    elif nivel >= 4 and mejor_puntaje >= 40:
        return "experto"
    elif nivel >= 2 or mejor_puntaje >= 10:
        return "regular"
    else:
        return "novato"
