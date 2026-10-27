"""Entidades del dominio.

* ``Jugador`` es una clase normal con atributos protegidos (``_monedas``) y
  propiedades (``@property``): así nadie puede dejar el saldo en negativo.
* ``Partida`` es un ``dataclass``: solo guarda datos, Python genera el resto.
"""
from dataclasses import asdict, dataclass

from . import reglas
from .excepciones import PersistenciaError, ReglaNegocioError


class Jugador:
    def __init__(self, id, nombre, activo=True, mejor_puntaje=0, partidas_jugadas=0,
                 monedas=0, monedas_totales=0, skins=None, skin_activa="clasico"):
        self.id = id
        self.nombre = nombre
        self.activo = activo
        self.mejor_puntaje = mejor_puntaje
        self.partidas_jugadas = partidas_jugadas
        # Atributos protegidos (convención: guion bajo). Se usan vía propiedades.
        self._monedas = 0
        if monedas_totales < 0:
            raise ReglaNegocioError("Las monedas totales no pueden ser negativas.")
        self._monedas_totales = monedas_totales
        self._skins = list(skins) if skins is not None else ["clasico"]
        self.skin_activa = skin_activa
        self.monedas = monedas  # pasa por el setter, que valida

    # ---------- propiedades ----------
    @property
    def monedas(self) -> int:
        """Saldo gastable. El setter impide valores negativos."""
        return self._monedas

    @monedas.setter
    def monedas(self, valor: int) -> None:
        if valor < 0:
            raise ReglaNegocioError("El saldo de monedas no puede ser negativo.")
        self._monedas = valor

    @property
    def monedas_totales(self) -> int:
        """Acumulado histórico: solo lectura (no tiene setter)."""
        return self._monedas_totales

    @property
    def nivel(self) -> int:
        """Se calcula a partir de las monedas totales; no se guarda por separado."""
        return reglas.nivel_para(self._monedas_totales)

    @property
    def skins(self) -> tuple:
        """Skins poseídas, como tupla: no se puede modificar desde fuera."""
        return tuple(self._skins)

    @property
    def bloqueado(self) -> bool:
        return not self.activo

    @property
    def categoria(self) -> str:
        return reglas.categoria_para(self.nivel, self.mejor_puntaje, self.partidas_jugadas)

    # ---------- comportamiento ----------
    def aplicar_partida(self, puntaje: int, monedas: int) -> None:
        """Modifica el estado del jugador tras una partida."""
        self.partidas_jugadas += 1
        self.mejor_puntaje = max(self.mejor_puntaje, puntaje)
        self.monedas += monedas            # usa el setter
        self._monedas_totales += monedas   # dentro de la clase sí se puede

    def adquirir_skin(self, skin: str) -> None:
        if skin in self._skins:
            raise ReglaNegocioError("El jugador ya posee esa skin.")
        self._skins.append(skin)

    def equipar(self, skin: str) -> None:
        if skin not in self._skins:
            raise ReglaNegocioError("El jugador no posee esa skin.")
        self.skin_activa = skin

    # ---------- persistencia ----------
    def to_dict(self) -> dict:
        return {
            "id": self.id, "nombre": self.nombre, "activo": self.activo,
            "mejor_puntaje": self.mejor_puntaje, "partidas_jugadas": self.partidas_jugadas,
            "monedas": self._monedas, "monedas_totales": self._monedas_totales,
            "nivel": self.nivel,  # informativo: se recalcula al cargar
            "skins": list(self._skins), "skin_activa": self.skin_activa,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Jugador":
        try:
            datos = dict(d)
            datos.pop("nivel", None)  # el nivel es una propiedad calculada
            return cls(**datos)
        except (TypeError, ValueError, ReglaNegocioError) as e:
            raise PersistenciaError(f"Registro de jugador inválido: {e}") from e

    # ---------- sobrescritura de métodos especiales de object ----------
    def __str__(self) -> str:
        estado = "activo" if self.activo else "BLOQUEADO"
        return (f"[{self.id}] {self.nombre:<15} {estado:<9} mejor={self.mejor_puntaje:<5} "
                f"monedas={self._monedas:<5} nivel={self.nivel} skin={self.skin_activa} "
                f"({self.categoria})")

    def __repr__(self) -> str:
        return f"Jugador(id={self.id}, nombre={self.nombre!r})"


@dataclass
class Partida:
    id: int
    jugador_id: int
    puntaje: int
    dificultad: str
    medalla: str
    monedas: int
    fecha: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Partida":
        try:
            return cls(**d)
        except TypeError as e:
            raise PersistenciaError(f"Registro de partida inválido: {e}") from e
