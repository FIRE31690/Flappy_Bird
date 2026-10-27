"""Bitácora en archivo de texto plano (.txt): una línea por evento."""
from datetime import datetime
from pathlib import Path

from .excepciones import PersistenciaError


class Bitacora:
    def __init__(self, ruta):
        self.ruta = Path(ruta)

    def registrar(self, texto: str) -> bool:
        """Agrega una línea al final (modo 'a'). Devuelve False si no pudo escribir.

        Una bitácora que falla NO debe tumbar el programa, por eso no lanza error.
        """
        linea = f"{datetime.now():%Y-%m-%d %H:%M:%S} | {texto}\n"
        try:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            with self.ruta.open("a", encoding="utf-8") as f:
                f.write(linea)
        except OSError:
            return False
        else:
            return True

    def ultimas(self, cantidad: int = 10) -> list[str]:
        """Devuelve las últimas líneas (lista vacía si todavía no existe el archivo)."""
        try:
            lineas = self.ruta.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return []
        except OSError as e:
            raise PersistenciaError(f"No se pudo leer la bitácora '{self.ruta}': {e}") from e
        return lineas[-cantidad:]
