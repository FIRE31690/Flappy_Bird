"""Interacción con el usuario: menú de consola del gestor. No contiene reglas de negocio."""
from . import almacenamiento, reportes
from .bitacora import Bitacora
from .config import CARPETA_EXPORT, RUTA_BITACORA, RUTA_JSON
from .dificultad import DIFICULTADES
from .excepciones import GestorError
from .exportador import ExportadorCSV, ExportadorTXT
from .reglas import SKINS
from .repositorio import Repositorio
from .servicio import Servicio
from .validadores import validar_dificultad, validar_entero, validar_puntaje

MENU = """
===== GESTOR FLAPPY BIRD =====
 1. Registrar jugador
 2. Listar jugadores
 3. Buscar jugador por nombre
 4. Renombrar jugador
 5. Bloquear / activar jugador
 6. Registrar partida (manual)
 7. Consultar partidas (filtros)
 8. Comprar skin
 9. Equipar skin
10. Reportes
11. Exportar a CSV y TXT
12. Verificar integridad de datos
13. Ver bitácora
 0. Volver
"""

# ---------- alcance de variables ----------
# Variable GLOBAL del módulo: vive mientras el programa esté abierto.
_acciones_en_sesion = 0


def _contar_accion() -> int:
    """Para MODIFICAR una variable global desde una función hay que declararla 'global'.

    Leerla no lo necesita; asignarla sí (si no, Python crearía una variable local nueva).
    """
    global _acciones_en_sesion
    _acciones_en_sesion += 1
    total = _acciones_en_sesion  # 'total' es LOCAL: solo existe dentro de esta función
    return total


def pedir(texto: str) -> str:
    return input(texto).strip()


def pedir_id(texto="ID del jugador: ") -> int:
    return validar_entero(pedir(texto), "El ID")


def mostrar_partida(p, repo) -> None:
    nombre = repo.jugadores[p.jugador_id].nombre if p.jugador_id in repo.jugadores else "?"
    print(f"#{p.id:<3} {nombre:<15} {p.puntaje:<5} {p.dificultad:<8} {p.medalla:<8} +{p.monedas} monedas  {p.fecha}")


# ---------- opciones ----------
def op_registrar(s: Servicio):
    j = s.registrar_jugador(pedir("Nombre: "))
    print(f"Jugador registrado con ID {j.id}.")


def op_listar(s: Servicio):
    if not s.repo.jugadores:
        print("No hay jugadores registrados.")
    for j in s.repo.jugadores.values():
        print(j)  # usa Jugador.__str__


def op_buscar(s: Servicio):
    encontrados = s.repo.buscar_por_nombre(pedir("Texto a buscar: "))
    print("Sin resultados." if not encontrados else "")
    for j in encontrados:
        print(j)


def op_renombrar(s: Servicio):
    j = s.renombrar_jugador(pedir_id(), pedir("Nuevo nombre: "))
    print("Nombre actualizado.")
    print(j)


def op_estado(s: Servicio):
    jid = pedir_id()
    actual = s.repo.obtener_jugador(jid).bloqueado
    j = s.cambiar_estado(jid, actual)  # si estaba bloqueado -> activo=True, y viceversa
    print("Jugador activado." if j.activo else "Jugador bloqueado.")


def op_partida(s: Servicio):
    jid = pedir_id()
    puntaje = pedir("Puntaje: ")
    dif = pedir(f"Dificultad ({'/'.join(DIFICULTADES)}): ")
    p = s.registrar_partida(jid, puntaje, dif)
    print(f"Partida #{p.id}: medalla {p.medalla}, +{p.monedas} monedas.")


def op_consultar(s: Servicio):
    jid = pedir("ID jugador (Enter = todos): ")
    dif = pedir("Dificultad (Enter = todas): ")
    minimo = pedir("Puntaje mínimo (Enter = ninguno): ")
    resultado = s.repo.filtrar_partidas(
        jugador_id=validar_entero(jid, "El ID") if jid else None,
        dificultad=validar_dificultad(dif) if dif else None,
        puntaje_min=validar_puntaje(minimo) if minimo else None,
    )
    print(f"{len(resultado)} partida(s):")
    for p in resultado:
        mostrar_partida(p, s.repo)


def op_comprar(s: Servicio):
    print("Skins:", ", ".join(f"{k} ({v} monedas)" for k, v in SKINS.items()))
    j = s.comprar_skin(pedir_id(), pedir("Skin: "))
    print(f"Compra realizada. Saldo: {j.monedas} monedas.")


def op_equipar(s: Servicio):
    j = s.equipar_skin(pedir_id(), pedir("Skin: "))
    print(f"Skin activa: {j.skin_activa}")


def op_reportes(s: Servicio):
    g = reportes.resumen_general(s.repo)
    print("\n-- Resumen general --")
    for k, v in g.items():
        print(f"{k}: {v}")
    print("\n-- Top 5 ranking --")
    for i, j in enumerate(reportes.ranking(s.repo.jugadores.values()), 1):
        print(f"{i}. {j.nombre} - {j.mejor_puntaje} ({j.categoria})")
    print("\n-- Por dificultad --")
    for d, datos in reportes.resumen_por_dificultad(s.repo.partidas).items():
        print(d, datos)
    print("\n-- Medallas --")
    print(reportes.conteo_medallas(s.repo.partidas))
    sin = reportes.jugadores_sin_partidas(s.repo)
    print("\n-- Jugadores que aún no han jugado --")
    print(", ".join(j.nombre for j in sin) if sin else "(todos han jugado)")


def op_exportar(s: Servicio):
    top = reportes.ranking(s.repo.jugadores.values(), top=len(s.repo.jugadores))
    # Polimorfismo: se llama igual a los dos exportadores; cada uno escribe su formato.
    for exportador in (ExportadorCSV(CARPETA_EXPORT), ExportadorTXT(CARPETA_EXPORT)):
        n1 = exportador.exportar_partidas(s.repo, s.repo.partidas)
        n2 = exportador.exportar_ranking(top)
        print(f"{exportador.extension}: {n1} partidas y {n2} jugadores en '{CARPETA_EXPORT}'.")


def op_integridad(s: Servicio):
    problemas = s.repo.verificar_integridad()
    print("Datos íntegros." if not problemas else "\n".join(problemas))


def op_bitacora(s: Servicio):
    if s.bitacora is None:
        print("Este servicio no tiene bitácora.")
        return
    lineas = s.bitacora.ultimas(10)
    print("Últimos eventos:" if lineas else "La bitácora está vacía.")
    for linea in lineas:
        print(" ", linea)


ACCIONES = {
    "1": op_registrar, "2": op_listar, "3": op_buscar, "4": op_renombrar,
    "5": op_estado, "6": op_partida, "7": op_consultar, "8": op_comprar,
    "9": op_equipar, "10": op_reportes, "11": op_exportar, "12": op_integridad,
    "13": op_bitacora,
}


# ---------- carga / guardado ----------
def cargar_servicio() -> Servicio:
    """Carga el JSON (o arranca vacío si falla) y arma el Servicio con su bitácora."""
    try:
        repo = almacenamiento.cargar(RUTA_JSON)
    except GestorError as e:
        print(f"Aviso: {e}\nSe iniciará con datos vacíos (el archivo original quedó respaldado).")
        repo = Repositorio()
    return Servicio(repo, Bitacora(RUTA_BITACORA))


def guardar_servicio(servicio: Servicio) -> None:
    almacenamiento.guardar(servicio.repo, RUTA_JSON)


# ---------- bucle del menú ----------
def menu_gestor(servicio: Servicio) -> None:
    """Menú del gestor. Termina con la opción 0 (o Ctrl+C / fin de entrada)."""
    while True:
        print(MENU)
        print(f"  (acciones realizadas en esta sesión: {_acciones_en_sesion})")
        try:
            opcion = pedir("Opción: ")
        except (EOFError, KeyboardInterrupt):
            return
        if opcion == "0":
            return
        accion = ACCIONES.get(opcion)
        if accion is None:
            print("Opción inválida.")
            continue
        try:
            accion(servicio)
            _contar_accion()
            guardar_servicio(servicio)  # guarda tras cada cambio
        except GestorError as e:
            print(f"⚠ {e}")
        except (EOFError, KeyboardInterrupt):
            print("\nOperación cancelada.")


def ejecutar() -> None:
    """Modo independiente: solo el gestor (sin juego)."""
    servicio = cargar_servicio()
    menu_gestor(servicio)
    try:
        guardar_servicio(servicio)
        print("Datos guardados. ¡Hasta pronto!")
    except GestorError as e:
        print(f"Error al guardar: {e}")
