"""Persistencia en JSON con pathlib (carga y guardado seguros)."""
import json
import os
import shutil
from pathlib import Path

from .excepciones import PersistenciaError
from .modelos import Jugador, Partida
from .repositorio import Repositorio


def guardar(repo: Repositorio, ruta) -> None:
    """Guarda el repositorio. Escritura atómica: primero a un .tmp y luego se reemplaza."""
    ruta = Path(ruta)
    tmp = ruta.with_name(ruta.name + ".tmp")
    datos = {
        "jugadores": [j.to_dict() for j in repo.jugadores.values()],
        "partidas": [p.to_dict() for p in repo.partidas],
    }
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        os.replace(tmp, ruta)  # el archivo bueno nunca queda a medias
    except OSError as e:
        raise PersistenciaError(f"No se pudo guardar '{ruta}': {e}") from e
    finally:
        # Se ejecuta SIEMPRE (con o sin error): no deja basura si algo falló.
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def _respaldar(ruta: Path) -> Path:
    """Copia el archivo dañado a '<nombre>.corrupto' para no perder nada."""
    respaldo = ruta.with_name(ruta.name + ".corrupto")
    shutil.copy(ruta, respaldo)
    return respaldo


def cargar(ruta) -> Repositorio:
    ruta = Path(ruta)
    repo = Repositorio()
    if not ruta.exists():
        return repo  # primera ejecución
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        jugadores = [Jugador.from_dict(d) for d in datos.get("jugadores", [])]
        partidas = [Partida.from_dict(d) for d in datos.get("partidas", [])]
    except (ValueError, AttributeError, PersistenciaError) as e:
        # JSON mal formado, raíz que no es un objeto, o campos inválidos:
        # en todos los casos se conserva una copia antes de seguir.
        respaldo = _respaldar(ruta)
        raise PersistenciaError(f"Archivo dañado; se copió a '{respaldo}'. Detalle: {e}") from e
    except OSError as e:
        raise PersistenciaError(f"No se pudo leer '{ruta}': {e}") from e
    else:
        # Solo se llena el repositorio si TODA la lectura salió bien.
        repo.cargar_datos(jugadores, partidas)
    return repo
