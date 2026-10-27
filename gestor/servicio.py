"""Casos de uso: combinan validación + reglas + repositorio (+ bitácora opcional)."""
from . import reglas, validadores as v
from .excepciones import ReglaNegocioError
from .modelos import Jugador, Partida
from .repositorio import Repositorio


class Servicio:
    def __init__(self, repo: Repositorio, bitacora=None):
        # Composición: un Servicio "tiene un" Repositorio (y opcionalmente una Bitácora).
        self._repo = repo
        self._bitacora = bitacora

    @property
    def repo(self) -> Repositorio:
        return self._repo

    @property
    def bitacora(self):
        return self._bitacora

    def _anotar(self, texto: str) -> None:
        if self._bitacora is not None:
            self._bitacora.registrar(texto)

    # ---------- jugadores ----------
    def registrar_jugador(self, nombre) -> Jugador:
        nombre = v.validar_nombre(nombre)
        if self._repo.buscar_por_nombre(nombre, exacto=True):
            raise ReglaNegocioError(f"Ya existe un jugador llamado '{nombre}'.")
        jugador = self._repo.agregar_jugador(nombre)
        self._anotar(f"Jugador registrado: {jugador.nombre} (id {jugador.id})")
        return jugador

    def renombrar_jugador(self, jugador_id: int, nuevo_nombre) -> Jugador:
        jugador = self._repo.obtener_jugador(jugador_id)
        nuevo = v.validar_nombre(nuevo_nombre)
        otros = [j for j in self._repo.buscar_por_nombre(nuevo, exacto=True) if j.id != jugador_id]
        if otros:
            raise ReglaNegocioError(f"Ya existe un jugador llamado '{nuevo}'.")
        anterior, jugador.nombre = jugador.nombre, nuevo
        self._anotar(f"Jugador {jugador_id} renombrado: {anterior} -> {nuevo}")
        return jugador

    def cambiar_estado(self, jugador_id: int, activo: bool) -> Jugador:
        jugador = self._repo.obtener_jugador(jugador_id)
        jugador.activo = activo
        self._anotar(f"Jugador {jugador.nombre} {'activado' if activo else 'bloqueado'}")
        return jugador

    # ---------- partidas ----------
    def registrar_partida(self, jugador_id: int, puntaje, dificultad) -> Partida:
        jugador = self._repo.obtener_jugador(jugador_id)
        if jugador.bloqueado:
            raise ReglaNegocioError("El jugador está bloqueado y no puede registrar partidas.")
        puntaje = v.validar_puntaje(puntaje)
        dificultad = v.validar_dificultad(dificultad)
        medalla = reglas.medalla_para(puntaje)
        monedas = reglas.monedas_para(puntaje, dificultad)
        partida = self._repo.agregar_partida(jugador_id, puntaje, dificultad, medalla, monedas)
        jugador.aplicar_partida(puntaje, monedas)
        self._anotar(f"Partida #{partida.id}: {jugador.nombre} hizo {puntaje} en {dificultad} "
                     f"-> medalla {medalla}, +{monedas} monedas")
        return partida

    # ---------- tienda ----------
    def comprar_skin(self, jugador_id: int, skin) -> Jugador:
        jugador = self._repo.obtener_jugador(jugador_id)
        skin = v.validar_skin(skin)
        if skin in jugador.skins:
            raise ReglaNegocioError("El jugador ya posee esa skin.")
        costo = reglas.SKINS[skin]
        if jugador.monedas < costo:
            raise ReglaNegocioError(f"Monedas insuficientes: necesita {costo}, tiene {jugador.monedas}.")
        jugador.monedas -= costo      # el setter vuelve a validar que no quede negativo
        jugador.adquirir_skin(skin)
        self._anotar(f"{jugador.nombre} compró la skin '{skin}' por {costo} monedas")
        return jugador

    def equipar_skin(self, jugador_id: int, skin) -> Jugador:
        jugador = self._repo.obtener_jugador(jugador_id)
        jugador.equipar(v.validar_skin(skin))
        return jugador
