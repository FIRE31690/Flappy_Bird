"""CONTROLADOR del juego: lee las teclas, actualiza el modelo y le pide a la vista que dibuje."""
import time
from dataclasses import dataclass

try:
    import curses
except ImportError:  # Windows sin 'windows-curses'
    curses = None

from gestor.dificultad import Dificultad
from gestor.excepciones import EntornoNoSoportadoError

from . import vista
from .modelo import Juego

TECLAS_SALTO = (ord(" "), ord("w"), ord("W"), 259)   # 259 = flecha arriba en curses
TECLAS_PAUSA = (ord("p"), ord("P"))
TECLAS_SALIR = (ord("q"), ord("Q"), 27)              # 27 = Esc


@dataclass
class ResultadoJuego:
    puntaje: int
    abandonado: bool


def accion_para(tecla: int) -> str:
    """Traduce una tecla a una acción del juego."""
    if tecla in TECLAS_SALTO:
        return "saltar"
    elif tecla in TECLAS_PAUSA:
        return "pausa"
    elif tecla in TECLAS_SALIR:
        return "salir"
    else:
        return "nada"


def jugar(nombre: str, skin: str, dificultad: Dificultad, record: int = 0) -> ResultadoJuego:
    """Abre la pantalla de curses, corre una partida y devuelve el resultado.

    ``record`` es el mejor puntaje previo del jugador (se muestra en el encabezado).
    """
    if curses is None:
        raise EntornoNoSoportadoError(
            "Falta el módulo curses. En Windows instálalo con:  pip install windows-curses")
    return curses.wrapper(_partida, nombre, skin, dificultad, record)


def _partida(pantalla, nombre: str, skin: str, dificultad: Dificultad,
             record: int = 0) -> ResultadoJuego:
    alto, ancho = pantalla.getmaxyx()
    if alto < vista.ALTO_MINIMO or ancho < vista.ANCHO_MINIMO:
        raise EntornoNoSoportadoError(
            f"La terminal es muy pequeña ({ancho}x{alto}). "
            f"Necesita al menos {vista.ANCHO_MINIMO}x{vista.ALTO_MINIMO}.")
    try:
        curses.curs_set(0)          # oculta el cursor
    except curses.error:
        pass
    pantalla.nodelay(True)          # getch() no se queda esperando
    pantalla.keypad(True)           # permite leer las flechas

    estilos = vista.Estilos.para_terminal()   # colores si la terminal los soporta
    tema = vista.elegir_tema()                # Unicode o ASCII
    juego = Juego(dificultad)
    estado = "listo"                # listo -> jugando <-> pausa
    fase = 0                        # contador de fotogramas para las animaciones

    while True:
        fase += 1
        saltar = False
        tecla = pantalla.getch()
        while tecla != -1:          # se leen todas las teclas acumuladas en este tic
            accion = accion_para(tecla)
            if accion == "salir":
                return ResultadoJuego(juego.puntaje, abandonado=True)
            elif accion == "pausa":
                if estado == "jugando":
                    estado = "pausa"
                elif estado == "pausa":
                    estado = "jugando"
            elif accion == "saltar":
                if estado == "listo":
                    estado = "jugando"
                if estado == "jugando":
                    saltar = True
            tecla = pantalla.getch()

        if estado == "jugando":
            juego.tick(saltar)
        if juego.terminado:
            # choque: un destello y luego el pájaro caído (X) para ver dónde chocó
            vista.dibujar(pantalla, estilos, tema, juego, nombre, skin, estado, fase, record,
                          destello=True)
            time.sleep(0.12)
            vista.dibujar(pantalla, estilos, tema, juego, nombre, skin, estado, fase, record)
            break
        vista.dibujar(pantalla, estilos, tema, juego, nombre, skin, estado, fase, record)
        time.sleep(dificultad.intervalo())

    time.sleep(0.8)                 # pausa breve para ver dónde chocó
    curses.flushinp()               # descarta teclas que quedaron acumuladas
    vista.pantalla_final(pantalla, estilos, tema, juego, nombre, record)
    pantalla.nodelay(False)
    pantalla.getch()
    return ResultadoJuego(juego.puntaje, abandonado=False)
