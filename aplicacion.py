"""Menú principal: une el JUEGO y el GESTOR en una sola aplicación.

Los dos comparten el mismo Servicio (y por tanto los mismos jugadores, monedas,
skins y el mismo archivo JSON): lo que se gana jugando aparece en el gestor.
"""
from gestor import interfaz
from gestor.dificultad import DIFICULTADES
from gestor.excepciones import GestorError, ReglaNegocioError
from gestor.modelos import Jugador
from gestor.servicio import Servicio
from gestor.validadores import validar_dificultad
from juego import controlador

MENU = """
╔══════════════════════════════╗
║   FLAPPY BIRD  ·  TERMINAL   ║
╚══════════════════════════════╝
 1. Jugar
 2. Gestor de jugadores y partidas
 3. Ver bitácora (últimos eventos)
 0. Guardar y salir
"""


def elegir_jugador(servicio: Servicio) -> Jugador:
    """Pide un ID o un nombre. Si el nombre no existe, crea al jugador."""
    texto = interfaz.pedir("ID o nombre del jugador (si no existe, se crea): ")
    existentes = [] if texto.isdigit() else servicio.repo.buscar_por_nombre(texto, exacto=True)
    if texto.isdigit():
        return servicio.repo.obtener_jugador(int(texto))
    elif existentes:
        return existentes[0]
    else:
        jugador = servicio.registrar_jugador(texto)
        print(f"Jugador nuevo creado con ID {jugador.id}.")
        return jugador


def opcion_jugar(servicio: Servicio, jugar=controlador.jugar) -> None:
    """Flujo completo: elegir jugador -> dificultad -> jugar -> registrar la partida.

    ``jugar`` se recibe como parámetro para poder reemplazarlo en las pruebas.
    """
    jugador = elegir_jugador(servicio)
    if jugador.bloqueado:
        raise ReglaNegocioError("El jugador está bloqueado y no puede jugar.")
    texto = interfaz.pedir(f"Dificultad ({'/'.join(DIFICULTADES)}) [normal]: ") or "normal"
    dificultad = DIFICULTADES[validar_dificultad(texto)]
    print(f"\n{dificultad.descripcion()}")
    print(f"Skin equipada: {jugador.skin_activa}")
    interfaz.pedir("Presiona Enter para empezar...")

    record_anterior = jugador.mejor_puntaje
    resultado = jugar(jugador.nombre, jugador.skin_activa, dificultad, record_anterior)

    if resultado.abandonado:
        print("Partida abandonada: no se registró.")
        return
    partida = servicio.registrar_partida(jugador.id, resultado.puntaje, dificultad.nombre)
    print(f"\nPartida #{partida.id}: {partida.puntaje} puntos · medalla {partida.medalla} "
          f"· +{partida.monedas} monedas")
    print(f"Saldo: {jugador.monedas} monedas · nivel {jugador.nivel} · {jugador.categoria}")
    if partida.puntaje > record_anterior:
        print("¡Nuevo récord personal!")


def opcion_bitacora(servicio: Servicio) -> None:
    interfaz.op_bitacora(servicio)


ACCIONES = {"1": opcion_jugar, "3": opcion_bitacora}


def ejecutar() -> None:
    servicio = interfaz.cargar_servicio()
    while True:
        print(MENU)
        try:
            opcion = interfaz.pedir("Opción: ")
        except (EOFError, KeyboardInterrupt):
            break
        if opcion == "0":
            break
        elif opcion == "2":
            interfaz.menu_gestor(servicio)
        elif opcion in ACCIONES:
            try:
                ACCIONES[opcion](servicio)
            except GestorError as e:
                print(f"⚠ {e}")
            except (EOFError, KeyboardInterrupt):
                print("\nOperación cancelada.")
        else:
            print("Opción inválida.")
        try:
            interfaz.guardar_servicio(servicio)
        except GestorError as e:
            print(f"Error al guardar: {e}")
    try:
        interfaz.guardar_servicio(servicio)
        print("Datos guardados. ¡Hasta pronto!")
    except GestorError as e:
        print(f"Error al guardar: {e}")
