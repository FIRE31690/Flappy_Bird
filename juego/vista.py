"""VISTA del juego: gráficos de terminal.

Está dividida en dos capas para poder probarla sin abrir una pantalla:

* ``construir_escena()`` es una función PURA: recibe el estado del juego y devuelve
  una cuadrícula de celdas ``(carácter, estilo)``. No usa curses.
* ``dibujar()`` es la que pinta esa cuadrícula en la terminal, con colores.

Hay dos *temas* de caracteres: **Unicode** (bloques, marco doble, formas) y **ASCII**
(solo caracteres simples) para terminales que no soportan Unicode. Se elige solo
(``elegir_tema``) y se puede forzar con las variables de entorno ``FLAPPY_ASCII=1``
o ``FLAPPY_UNICODE=1``.
"""
import os
import sys
import unicodedata
from dataclasses import dataclass

try:
    import curses
except ImportError:  # Windows sin 'windows-curses'
    curses = None

from gestor import reglas

from .modelo import ALTO, ANCHO, Juego

FILAS_SUELO = 2                       # filas decorativas bajo el campo (hierba y tierra)
ALTO_MINIMO = ALTO + FILAS_SUELO + 6  # campo + suelo + marco + encabezado + mensajes
ANCHO_MINIMO = ANCHO + 4


# ======================================================================= temas
@dataclass(frozen=True)
class Tema:
    nombre: str
    borde: tuple      # esquina sup. izq., horizontal, esq. sup. der., vertical, esq. inf. izq., esq. inf. der.
    bloque: str       # cuerpo de la tubería (columna izquierda)
    sombra: str       # cuerpo de la tubería (columna derecha)
    tapa: str         # "labio" de la tubería junto al hueco
    nube: str
    colinas: str      # un carácter por altura 0..4
    hierba: str       # patrón que se repite y se desplaza
    tierra: str
    ala: tuple        # dos cuadros de la animación del ala
    choque: str
    pajaros: dict     # skin -> carácter
    separador: str
    flecha: str


TEMA_UNICODE = Tema(
    nombre="unicode", borde=("╔", "═", "╗", "║", "╚", "╝"),
    bloque="█", sombra="▓", tapa="▒", nube="░", colinas=" ▁▂▃▄", hierba="▀▀▀▄", tierra="▒▓",
    ala=("/", "\\"), choque="✖",
    pajaros={"clasico": "●", "rojo": "●", "dorado": "◆", "fantasma": "○"},
    separador="·", flecha="↑")

TEMA_ASCII = Tema(
    nombre="ascii", borde=("+", "-", "+", "|", "+", "+"),
    bloque="#", sombra="#", tapa="=", nube="~", colinas=" ..^^", hierba="\"\"'\"", tierra="=-",
    ala=("/", "\\"), choque="X",
    pajaros={"clasico": "O", "rojo": "R", "dorado": "$", "fantasma": "~"},
    separador="|", flecha="flecha arriba")


def elegir_tema() -> Tema:
    """Unicode si la terminal lo soporta; ASCII en caso contrario (o si se fuerza)."""
    if os.environ.get("FLAPPY_ASCII"):
        return TEMA_ASCII
    if os.environ.get("FLAPPY_UNICODE"):
        return TEMA_UNICODE
    codificacion = (getattr(sys.stdout, "encoding", None) or "").lower()
    return TEMA_UNICODE if "utf" in codificacion else TEMA_ASCII


def _adaptar(texto: str, tema: Tema) -> str:
    """En el tema ASCII se quitan tildes y signos especiales (á -> a, ¡ se elimina)."""
    if tema.nombre != "ascii":
        return texto
    normal = unicodedata.normalize("NFKD", texto)
    return normal.encode("ascii", "ignore").decode("ascii")


# ====================================================================== estilos
# nombre -> (color de letra, color de fondo, negrita)
ESTILOS = {
    "cielo": ("blanco", "cian", False),
    "destello": ("negro", "blanco", False),
    "nube": ("blanco", "cian", True),
    "colinas": ("verde", "cian", False),
    "tuberia": ("verde", "cian", False),
    "tuberia_borde": ("negro", "verde", False),
    "hierba": ("verde", "amarillo", False),
    "tierra": ("amarillo", "negro", False),
    "pajaro_clasico": ("amarillo", "cian", True),
    "pajaro_rojo": ("rojo", "cian", True),
    "pajaro_dorado": ("amarillo", "cian", True),
    "pajaro_fantasma": ("blanco", "cian", True),
    "ala": ("blanco", "cian", True),
    "choque": ("rojo", "cian", True),
    "panel": ("negro", "blanco", False),
    "panel_titulo": ("azul", "blanco", True),
    "record": ("rojo", "blanco", True),
    "hud": ("negro", "blanco", True),
    "borde": ("blanco", "negro", False),
    "mensaje": ("amarillo", "negro", True),
    "ayuda": ("cian", "negro", False),
}
_COLORES = {"negro": "BLACK", "rojo": "RED", "verde": "GREEN", "amarillo": "YELLOW",
            "azul": "BLUE", "magenta": "MAGENTA", "cian": "CYAN", "blanco": "WHITE"}


class Estilos:
    """Traduce nombres de estilo a atributos de curses (con colores si la terminal puede)."""

    def __init__(self, con_color: bool = False):
        self.con_color = con_color
        self._atributos = {}
        negrita = getattr(curses, "A_BOLD", 0)
        inverso = getattr(curses, "A_REVERSE", 0)
        tenue = getattr(curses, "A_DIM", 0)
        mono = {"panel": inverso, "panel_titulo": inverso | negrita, "record": inverso | negrita,
                "hud": inverso, "destello": inverso, "choque": inverso | negrita, "nube": tenue,
                "tuberia_borde": negrita, "mensaje": negrita}
        for numero, (nombre, (letra, fondo, en_negrita)) in enumerate(ESTILOS.items(), start=1):
            if con_color:
                curses.init_pair(numero, getattr(curses, "COLOR_" + _COLORES[letra]),
                                 getattr(curses, "COLOR_" + _COLORES[fondo]))
                atributo = curses.color_pair(numero)
                if en_negrita:
                    atributo |= negrita
            else:
                atributo = mono.get(nombre, negrita if nombre.startswith("pajaro") else 0)
            self._atributos[nombre] = atributo

    @classmethod
    def para_terminal(cls) -> "Estilos":
        """Activa los colores si la terminal tiene al menos 8."""
        con_color = False
        try:
            if curses.has_colors():
                curses.start_color()
                con_color = getattr(curses, "COLORS", 0) >= 8
        except curses.error:
            con_color = False
        return cls(con_color)

    def atributo(self, nombre: str) -> int:
        return self._atributos.get(nombre, 0)


# ======================================================================= escena
NUBES = [(4, 2, 5), (22, 4, 7), (36, 1, 4)]          # (columna, fila, largo)
PERFIL_COLINAS = [1, 2, 3, 4, 3, 2, 1, 0, 0, 1, 2, 1, 0, 0, 0, 2, 3, 3, 2, 1, 0, 0]


def construir_escena(juego: Juego, skin: str = "clasico", estado: str = "jugando",
                     tema: Tema = TEMA_ASCII, fase: int = 0, destello: bool = False) -> list:
    """Devuelve una cuadrícula de (alto + suelo) filas x ancho columnas de celdas (carácter, estilo).

    ``fase`` es un contador de fotogramas solo para animaciones decorativas (nubes y ala);
    el movimiento de las tuberías, las colinas y el suelo depende de ``juego.ticks``.
    """
    ancho, alto = juego.ancho, juego.alto
    total = alto + FILAS_SUELO
    celdas = [[(" ", "cielo") for _ in range(ancho)] for _ in range(total)]

    def poner(fila: int, col: int, glifo: str, estilo: str) -> None:
        if 0 <= fila < total and 0 <= col < ancho:
            celdas[fila][col] = (glifo, estilo)

    # 1) nubes: se mueven despacio hacia la izquierda (efecto de profundidad)
    for x0, fila, largo in NUBES:
        x = (x0 - fase // 3) % (ancho + largo) - largo
        for i in range(largo):
            poner(fila, x + i, tema.nube, "nube")

    # 2) colinas lejanas, en la última fila del cielo
    desplazamiento = juego.ticks // 2
    for col in range(ancho):
        altura = PERFIL_COLINAS[(col + desplazamiento) % len(PERFIL_COLINAS)]
        if altura:
            poner(alto - 1, col, tema.colinas[altura], "colinas")

    # 3) obstáculos (polimorfismo: se dibuja lo que cada uno "bloquea")
    for obstaculo in juego.obstaculos:
        for i in range(obstaculo.ancho):
            col = obstaculo.x + i
            for fila in range(alto):
                if not obstaculo.bloquea(fila):
                    continue
                es_labio = hasattr(obstaculo, "hueco_y") and fila in (
                    obstaculo.hueco_y - 1, obstaculo.hueco_y + obstaculo.hueco)
                if es_labio:
                    poner(fila, col, tema.tapa, "tuberia_borde")
                else:
                    poner(fila, col, tema.bloque if i == 0 else tema.sombra, "tuberia")

    # 4) suelo con hierba y tierra que avanzan junto con las tuberías
    for col in range(ancho):
        poner(alto, col, tema.hierba[(col + juego.ticks) % len(tema.hierba)], "hierba")
        poner(alto + 1, col, tema.tierra[(col + juego.ticks) % len(tema.tierra)], "tierra")

    # 5) pájaro con ala que aletea (y balanceo suave mientras espera comenzar)
    fila_pajaro = min(max(juego.pajaro.fila, 0), alto - 1)   # siempre visible, aunque se haya salido
    if estado == "listo" and (fase // 4) % 2:
        fila_pajaro += 1
    if juego.terminado:
        poner(fila_pajaro, juego.pajaro.x, tema.choque, "choque")
    else:
        poner(fila_pajaro, juego.pajaro.x - 1, tema.ala[fase % 2], "ala")
        glifo = tema.pajaros.get(skin, tema.pajaros["clasico"])
        estilo = f"pajaro_{skin}" if skin in tema.pajaros else "pajaro_clasico"
        poner(fila_pajaro, juego.pajaro.x, glifo, estilo)

    # 6) cartel según el estado
    if estado == "listo":
        _panel(celdas, ["FLAPPY BIRD", "", "ESPACIO = saltar", "P = pausa    Q = salir"], tema)
    elif estado == "pausa":
        _panel(celdas, ["PAUSA", "", "P para continuar"], tema)

    # 7) destello blanco al chocar
    if destello:
        celdas = [[(g, "destello" if e == "cielo" else e) for g, e in fila] for fila in celdas]
    return celdas


def _panel(celdas: list, lineas: list, tema: Tema) -> None:
    """Dibuja un cartel con marco en el centro del campo (modifica ``celdas``)."""
    lineas = [_adaptar(linea, tema) for linea in lineas]
    ancho = len(celdas[0])
    w, h = max(len(linea) for linea in lineas) + 4, len(lineas) + 2
    x0, y0 = (ancho - w) // 2, 1   # arriba, para no tapar al pájaro
    sup_izq, horiz, sup_der, vert, inf_izq, inf_der = tema.borde
    for dy in range(h):
        for dx in range(w):
            if dy == 0:
                glifo = sup_izq if dx == 0 else sup_der if dx == w - 1 else horiz
            elif dy == h - 1:
                glifo = inf_izq if dx == 0 else inf_der if dx == w - 1 else horiz
            elif dx in (0, w - 1):
                glifo = vert
            else:
                glifo = " "
            celdas[y0 + dy][x0 + dx] = (glifo, "panel")
    for k, linea in enumerate(lineas):
        inicio = x0 + (w - len(linea)) // 2
        for j, letra in enumerate(linea):
            celdas[y0 + 1 + k][inicio + j] = (letra, "panel_titulo" if k == 0 else "panel")


def escena_a_texto(celdas: list, tema: Tema) -> list:
    """Convierte la cuadrícula en líneas de texto con marco (sirve para pruebas)."""
    sup_izq, horiz, sup_der, vert, inf_izq, inf_der = tema.borde
    ancho = len(celdas[0])
    return ([sup_izq + horiz * ancho + sup_der]
            + [vert + "".join(g for g, _ in fila) + vert for fila in celdas]
            + [inf_izq + horiz * ancho + inf_der])


def tablero_a_texto(juego: Juego, skin: str = "clasico", tema: Tema = TEMA_ASCII,
                    estado: str = "jugando", fase: int = 0) -> list:
    return escena_a_texto(construir_escena(juego, skin, estado, tema, fase), tema)


# ================================================================= pintar en curses
def _escribir(pantalla, y: int, x: int, texto: str, atributo: int = 0) -> None:
    try:
        pantalla.addstr(y, x, texto, atributo)
    except curses.error:  # texto fuera de la ventana: se ignora
        pass


def _tramos(fila: list) -> list:
    """Agrupa celdas consecutivas del mismo estilo: menos llamadas a addstr."""
    tramos = []
    for glifo, estilo in fila:
        if tramos and tramos[-1][0] == estilo:
            tramos[-1][1].append(glifo)
        else:
            tramos.append((estilo, [glifo]))
    return [(estilo, "".join(glifos)) for estilo, glifos in tramos]


def dibujar(pantalla, estilos: Estilos, tema: Tema, juego: Juego, nombre: str, skin: str,
            estado: str, fase: int = 0, record: int = 0, destello: bool = False) -> None:
    pantalla.erase()
    celdas = construir_escena(juego, skin, estado, tema, fase, destello)
    ancho = juego.ancho
    sup_izq, horiz, sup_der, vert, inf_izq, inf_der = tema.borde
    sep = tema.separador

    glifo = tema.pajaros.get(skin, tema.pajaros["clasico"])
    mejor = max(record, juego.puntaje)
    hud = _adaptar(f" {glifo} {nombre} {sep} {juego.dificultad.nombre.upper()} {sep} "
                   f"PUNTAJE {juego.puntaje:>3} {sep} MEJOR {mejor:>3}", tema)
    _escribir(pantalla, 0, 1, hud.ljust(ancho + 2)[:ancho + 2], estilos.atributo("hud"))

    borde = estilos.atributo("borde")
    _escribir(pantalla, 1, 1, sup_izq + horiz * ancho + sup_der, borde)
    for i, fila in enumerate(celdas):
        y, x = 2 + i, 2
        _escribir(pantalla, y, 1, vert, borde)
        for estilo, texto in _tramos(fila):
            _escribir(pantalla, y, x, texto, estilos.atributo(estilo))
            x += len(texto)
        _escribir(pantalla, y, x, vert, borde)
    y_pie = 2 + len(celdas)
    _escribir(pantalla, y_pie, 1, inf_izq + horiz * ancho + inf_der, borde)

    if estado == "listo":
        mensaje = "Presiona ESPACIO para comenzar"
    elif estado == "pausa":
        mensaje = "PAUSA"
    elif juego.terminado:
        mensaje = "¡Chocaste!"
    else:
        mensaje = "¡Esquiva las tuberías!"
    ayuda = f"ESPACIO/W/{tema.flecha} saltar  {sep}  P pausa  {sep}  Q salir"
    _escribir(pantalla, y_pie + 2, 1, _adaptar(mensaje, tema), estilos.atributo("mensaje"))
    _escribir(pantalla, y_pie + 3, 1, _adaptar(ayuda, tema), estilos.atributo("ayuda"))
    pantalla.refresh()


# ============================================================== pantalla final
_DIGITOS = {
    "0": ("###", "# #", "# #", "# #", "###"), "1": (" # ", "## ", " # ", " # ", "###"),
    "2": ("###", "  #", "###", "#  ", "###"), "3": ("###", "  #", "###", "  #", "###"),
    "4": ("# #", "# #", "###", "  #", "  #"), "5": ("###", "#  ", "###", "  #", "###"),
    "6": ("###", "#  ", "###", "# #", "###"), "7": ("###", "  #", "  #", "  #", "  #"),
    "8": ("###", "# #", "###", "# #", "###"), "9": ("###", "# #", "###", "  #", "###"),
}


def numero_grande(numero: int, tema: Tema) -> list:
    """Dibuja un número con dígitos de 3x5 (5 líneas de texto)."""
    digitos = str(numero)
    filas = []
    for r in range(5):
        filas.append(" ".join(_DIGITOS[d][r] for d in digitos).replace("#", tema.bloque))
    return filas


def lineas_final(juego: Juego, nombre: str, record_anterior: int, tema: Tema) -> list:
    """Contenido de la pantalla final como lista de (texto, estilo). Función pura."""
    puntaje = juego.puntaje
    lineas = [("FIN DE LA PARTIDA", "panel_titulo"), ("", "panel")]
    lineas += [(fila, "panel_titulo") for fila in numero_grande(puntaje, tema)]
    datos = [f"Jugador:    {nombre}", f"Dificultad: {juego.dificultad.nombre}",
             f"Medalla:    {reglas.medalla_para(puntaje)}",
             f"Monedas:    +{juego.dificultad.monedas_para(puntaje)}"]
    ancho_datos = max(len(d) for d in datos)          # mismo ancho: el bloque queda alineado
    lineas += [("", "panel")] + [(d.ljust(ancho_datos), "panel") for d in datos]
    if puntaje > record_anterior:
        lineas += [("", "panel"), ("¡NUEVO RÉCORD!", "record")]
    lineas += [("", "panel"), ("Presiona una tecla...", "panel")]
    return [(_adaptar(texto, tema), estilo) for texto, estilo in lineas]


def pantalla_final(pantalla, estilos: Estilos, tema: Tema, juego: Juego, nombre: str,
                   record_anterior: int = 0) -> None:
    """Muestra el resultado en un cartel centrado."""
    lineas = lineas_final(juego, nombre, record_anterior, tema)
    sup_izq, horiz, sup_der, vert, inf_izq, inf_der = tema.borde
    interior = max(len(texto) for texto, _ in lineas) + 6
    alto_pantalla, ancho_pantalla = pantalla.getmaxyx()
    y0 = max((alto_pantalla - (len(lineas) + 2)) // 2, 0)
    x0 = max((ancho_pantalla - (interior + 2)) // 2, 0)
    marco = estilos.atributo("panel")
    pantalla.erase()
    _escribir(pantalla, y0, x0, sup_izq + horiz * interior + sup_der, marco)
    for i, (texto, estilo) in enumerate(lineas, start=1):
        _escribir(pantalla, y0 + i, x0, vert, marco)
        _escribir(pantalla, y0 + i, x0 + 1, texto.center(interior), estilos.atributo(estilo))
        _escribir(pantalla, y0 + i, x0 + interior + 1, vert, marco)
    _escribir(pantalla, y0 + len(lineas) + 1, x0, inf_izq + horiz * interior + inf_der, marco)
    pantalla.refresh()
