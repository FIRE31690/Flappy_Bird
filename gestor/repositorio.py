"""Gestión de colecciones: jugadores (por id) y partidas.

Las colecciones son privadas (``_jugadores``, ``_partidas``). Desde fuera solo se
pueden *leer* a través de propiedades de solo lectura; para cambiarlas hay que
usar los métodos del repositorio (encapsulamiento).
"""
from datetime import datetime
from types import MappingProxyType

from .excepciones import NoEncontradoError
from .modelos import Jugador, Partida


class Repositorio:
    def __init__(self):
        self._jugadores: dict[int, Jugador] = {}
        self._partidas: list[Partida] = []

    # ---------- vistas de solo lectura ----------
    @property
    def jugadores(self):
        """Diccionario id -> Jugador, de solo lectura."""
        return MappingProxyType(self._jugadores)

    @property
    def partidas(self) -> tuple:
        """Partidas en orden cronológico, como tupla (inmutable)."""
        return tuple(self._partidas)

    def cargar_datos(self, jugadores, partidas) -> None:
        """Reemplaza el contenido (lo usa el módulo de almacenamiento)."""
        self._jugadores = {j.id: j for j in jugadores}
        self._partidas = list(partidas)

    # ---------- jugadores ----------
    def _siguiente_id_jugador(self) -> int:
        return max(self._jugadores, default=0) + 1

    def agregar_jugador(self, nombre: str) -> Jugador:
        jugador = Jugador(id=self._siguiente_id_jugador(), nombre=nombre)
        self._jugadores[jugador.id] = jugador
        return jugador

    def obtener_jugador(self, jugador_id: int) -> Jugador:
        try:
            return self._jugadores[jugador_id]
        except KeyError:
            raise NoEncontradoError(f"No existe el jugador con id {jugador_id}.") from None

    def buscar_por_nombre(self, texto: str, exacto: bool = False) -> list[Jugador]:
        t = texto.strip().lower()
        if exacto:
            return [j for j in self._jugadores.values() if j.nombre.lower() == t]
        return [j for j in self._jugadores.values() if t in j.nombre.lower()]

    # ---------- partidas ----------
    def agregar_partida(self, jugador_id, puntaje, dificultad, medalla, monedas) -> Partida:
        partida = Partida(
            id=max((p.id for p in self._partidas), default=0) + 1,
            jugador_id=jugador_id, puntaje=puntaje, dificultad=dificultad,
            medalla=medalla, monedas=monedas,
            fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self._partidas.append(partida)
        return partida

    def filtrar_partidas(self, jugador_id=None, dificultad=None, puntaje_min=None) -> list[Partida]:
        resultado = self._partidas
        if jugador_id is not None:
            resultado = [p for p in resultado if p.jugador_id == jugador_id]
        if dificultad is not None:
            resultado = [p for p in resultado if p.dificultad == dificultad]
        if puntaje_min is not None:
            resultado = [p for p in resultado if p.puntaje >= puntaje_min]
        return list(resultado)

    def verificar_integridad(self) -> list[str]:
        """Devuelve una lista de problemas encontrados (vacía = datos íntegros)."""
        problemas = []
        # Conjuntos: ids que aparecen en partidas MENOS ids de jugadores que existen
        ids_jugadores = set(self._jugadores)
        ids_en_partidas = {p.jugador_id for p in self._partidas}
        for jid in sorted(ids_en_partidas - ids_jugadores):
            problemas.append(f"Hay partidas que apuntan al jugador inexistente {jid}.")
        for j in self._jugadores.values():
            partidas_j = [p for p in self._partidas if p.jugador_id == j.id]
            if j.partidas_jugadas != len(partidas_j):
                problemas.append(f"Jugador {j.id}: contador de partidas no coincide.")
            if partidas_j and j.mejor_puntaje != max(p.puntaje for p in partidas_j):
                problemas.append(f"Jugador {j.id}: mejor puntaje no coincide.")
        return problemas
