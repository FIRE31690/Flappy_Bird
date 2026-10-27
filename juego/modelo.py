"""MODELO del juego: lógica pura. No usa curses ni imprime nada, por eso se puede probar.

Clases:
    Pajaro        -> posición y velocidad vertical.
    Obstaculo     -> clase base ABSTRACTA (define qué debe saber hacer un obstáculo).
    Tuberia       -> hereda de Obstaculo y sobrescribe sus métodos.
    TuberiaMovil  -> hereda de Tuberia: el hueco sube y baja (dificultad "dificil").
    Juego         -> COMPONE (tiene) un Pajaro y una lista de obstáculos.
"""
import random

from gestor.dificultad import Dificultad

ANCHO, ALTO = 44, 16        # tamaño del campo de juego (columnas x filas)
COLUMNA_PAJARO = 10
GRAVEDAD = 0.25             # cuánto aumenta la velocidad hacia abajo en cada tic
IMPULSO = -1.2              # velocidad hacia arriba al saltar
VELOCIDAD_MAX = 1.6         # velocidad máxima de caída


class Pajaro:
    def __init__(self, fila: float):
        self.x = COLUMNA_PAJARO
        self._y = float(fila)
        self._velocidad = 0.0

    @property
    def fila(self) -> int:
        """Fila de la pantalla donde se dibuja (la posición interna es decimal)."""
        return int(round(self._y))

    def saltar(self) -> None:
        self._velocidad = IMPULSO

    def actualizar(self) -> None:
        self._velocidad = min(self._velocidad + GRAVEDAD, VELOCIDAD_MAX)
        self._y += self._velocidad


class Obstaculo:
    """Clase base: define la interfaz común. Las subclases sobrescriben los métodos."""

    def __init__(self, x: int, ancho: int = 2):
        self.x = x
        self.ancho = ancho
        self.superada = False       # ¿el pájaro ya lo pasó? (para sumar puntos una sola vez)

    def actualizar(self) -> None:
        """Avanza un tic: todos los obstáculos se desplazan una columna a la izquierda."""
        self.x -= 1

    def bloquea(self, fila: int) -> bool:
        """¿Esta fila está ocupada por el obstáculo?"""
        raise NotImplementedError

    def choca_con(self, pajaro: Pajaro) -> bool:
        raise NotImplementedError

    @property
    def fuera_de_pantalla(self) -> bool:
        return self.x + self.ancho <= 0


class Tuberia(Obstaculo):
    def __init__(self, x: int, hueco_y: int, hueco: int, ancho: int = 2):
        super().__init__(x, ancho)
        self.hueco_y = hueco_y      # primera fila libre
        self.hueco = hueco          # cuántas filas libres

    def bloquea(self, fila: int) -> bool:  # sobrescrito
        return not (self.hueco_y <= fila < self.hueco_y + self.hueco)

    def choca_con(self, pajaro: Pajaro) -> bool:  # sobrescrito
        en_columna = self.x <= pajaro.x < self.x + self.ancho
        return en_columna and self.bloquea(pajaro.fila)


class TuberiaMovil(Tuberia):
    """Igual que Tuberia, pero el hueco sube y baja mientras avanza."""

    def __init__(self, x: int, hueco_y: int, hueco: int, limite_inferior: int, ancho: int = 2):
        super().__init__(x, hueco_y, hueco, ancho)
        self._direccion = 1
        self._limite = limite_inferior
        self._tics = 0

    def actualizar(self) -> None:  # sobrescrito: primero hace lo del padre, luego lo suyo
        super().actualizar()
        self._tics += 1
        if self._tics % 3 == 0:
            nuevo = self.hueco_y + self._direccion
            if nuevo < 1 or nuevo + self.hueco > self._limite:
                self._direccion *= -1   # rebota en el techo / el suelo
            else:
                self.hueco_y = nuevo


class Juego:
    def __init__(self, dificultad: Dificultad, rng=None, ancho: int = ANCHO, alto: int = ALTO):
        self.dificultad = dificultad
        self.ancho = ancho
        self.alto = alto
        self._rng = rng if rng is not None else random.Random()
        self.pajaro = Pajaro(alto / 2)               # composición
        self.obstaculos: list[Obstaculo] = []        # composición
        self.puntaje = 0
        self.ticks = 0
        self.terminado = False
        self._ultimo_hueco = (alto - dificultad.hueco()) // 2
        self._agregar_tuberia()

    def _agregar_tuberia(self) -> None:
        hueco = self.dificultad.hueco()
        desplazamiento = self._rng.randint(-4, 4)
        hueco_y = min(max(self._ultimo_hueco + desplazamiento, 1), self.alto - hueco - 1)
        self._ultimo_hueco = hueco_y
        if self.dificultad.tuberias_moviles():
            tuberia = TuberiaMovil(self.ancho, hueco_y, hueco, self.alto - 1)
        else:
            tuberia = Tuberia(self.ancho, hueco_y, hueco)
        self.obstaculos.append(tuberia)

    def tick(self, saltar: bool = False) -> None:
        """Avanza el juego un tic."""
        if self.terminado:
            return
        self.ticks += 1
        if saltar:
            self.pajaro.saltar()
        self.pajaro.actualizar()
        for o in self.obstaculos:       # polimorfismo: cada obstáculo se actualiza a su manera
            o.actualizar()
        self.obstaculos = [o for o in self.obstaculos if not o.fuera_de_pantalla]
        if self.ancho - self.obstaculos[-1].x >= self.dificultad.separacion():
            self._agregar_tuberia()
        for o in self.obstaculos:
            if not o.superada and o.x + o.ancho <= self.pajaro.x:
                o.superada = True
                self.puntaje += 1
        fuera = self.pajaro.fila < 0 or self.pajaro.fila >= self.alto
        if fuera or any(o.choca_con(self.pajaro) for o in self.obstaculos):
            self.terminado = True
