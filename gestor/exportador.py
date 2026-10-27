"""Exportación de datos. Una clase base y dos formatos (CSV y TXT).

Herencia + sobrescritura + polimorfismo:
la base define el *proceso* (preparar carpeta, abrir archivo, contar filas) y cada
subclase sobrescribe solo *cómo se escribe* cada formato. Quien exporta llama
siempre a ``exportar_partidas`` / ``exportar_ranking`` sin importar el formato.
"""
import csv
from pathlib import Path

from .excepciones import PersistenciaError

_CAMPOS_PARTIDA = ["id", "jugador_id", "jugador", "puntaje", "dificultad", "medalla", "monedas", "fecha"]
_CAMPOS_RANKING = ["posicion", "nombre", "mejor_puntaje", "nivel", "partidas"]


class Exportador:
    extension = ""
    codificacion = "utf-8"

    def __init__(self, carpeta):
        self.carpeta = Path(carpeta)

    def ruta_de(self, nombre: str) -> Path:
        return self.carpeta / f"{nombre}{self.extension}"

    # ---------- proceso común ----------
    def exportar_partidas(self, repo, partidas) -> int:
        filas = []
        for p in partidas:
            fila = p.to_dict()
            fila["jugador"] = repo.jugadores[p.jugador_id].nombre if p.jugador_id in repo.jugadores else "?"
            filas.append(fila)
        self._abrir_y_escribir("partidas", lambda f: self._escribir_partidas(f, filas))
        return len(filas)

    def exportar_ranking(self, jugadores) -> int:
        filas = [[i, j.nombre, j.mejor_puntaje, j.nivel, j.partidas_jugadas]
                 for i, j in enumerate(jugadores, 1)]
        self._abrir_y_escribir("ranking", lambda f: self._escribir_ranking(f, filas))
        return len(filas)

    def _abrir_y_escribir(self, nombre: str, escribir) -> None:
        ruta = self.ruta_de(nombre)
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            with ruta.open("w", newline="", encoding=self.codificacion) as f:
                escribir(f)
        except OSError as e:
            raise PersistenciaError(f"No se pudo exportar a '{ruta}': {e}") from e

    # ---------- lo que cada formato sobrescribe ----------
    def _escribir_partidas(self, f, filas) -> None:
        raise NotImplementedError

    def _escribir_ranking(self, f, filas) -> None:
        raise NotImplementedError


class ExportadorCSV(Exportador):
    extension = ".csv"
    codificacion = "utf-8-sig"  # con BOM: Excel en Windows muestra bien tildes y ñ

    def __init__(self, carpeta, delimitador: str = ","):
        super().__init__(carpeta)  # reutiliza el __init__ de la clase base
        self.delimitador = delimitador

    def _escribir_partidas(self, f, filas) -> None:
        w = csv.DictWriter(f, fieldnames=_CAMPOS_PARTIDA, delimiter=self.delimitador)
        w.writeheader()
        w.writerows(filas)

    def _escribir_ranking(self, f, filas) -> None:
        w = csv.writer(f, delimiter=self.delimitador)
        w.writerow(_CAMPOS_RANKING)
        w.writerows(filas)


class ExportadorTXT(Exportador):
    extension = ".txt"

    def _escribir_partidas(self, f, filas) -> None:
        f.write(f"{'ID':<4}{'JUGADOR':<16}{'PUNTAJE':<9}{'DIFICULTAD':<12}{'MEDALLA':<10}{'MONEDAS':<9}FECHA\n")
        for r in filas:
            f.write(f"{r['id']:<4}{r['jugador']:<16}{r['puntaje']:<9}{r['dificultad']:<12}"
                    f"{r['medalla']:<10}{r['monedas']:<9}{r['fecha']}\n")

    def _escribir_ranking(self, f, filas) -> None:
        f.write(f"{'#':<4}{'NOMBRE':<16}{'MEJOR':<8}{'NIVEL':<7}PARTIDAS\n")
        for pos, nombre, mejor, nivel, partidas in filas:
            f.write(f"{pos:<4}{nombre:<16}{mejor:<8}{nivel:<7}{partidas}\n")
