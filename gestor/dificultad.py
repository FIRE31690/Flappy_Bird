"""Dificultades: una clase base y tres subclases.

Aquí se ven juntos tres conceptos de POO:

* **Herencia:** Facil, Normal y Dificil heredan de Dificultad.
* **Sobrescritura:** cada subclase redefine hueco(), intervalo() y separacion()
  (y Dificil además redefine tuberias_moviles() y descripcion()).
* **Polimorfismo:** quien usa una dificultad (el gestor para las monedas, el
  juego para la velocidad) llama a los mismos métodos sin preguntar de cuál
  subclase se trata.
"""


class Dificultad:
    """Clase base. Las subclases sobrescriben lo que cambia."""

    nombre = "base"
    multiplicador = 1  # multiplicador de monedas

    def monedas_para(self, puntaje: int) -> int:
        return (puntaje // 5) * self.multiplicador

    def hueco(self) -> int:
        """Filas libres entre la tubería de arriba y la de abajo."""
        raise NotImplementedError("La subclase debe definir hueco().")

    def intervalo(self) -> float:
        """Segundos entre fotogramas (menor = más rápido)."""
        raise NotImplementedError("La subclase debe definir intervalo().")

    def separacion(self) -> int:
        """Columnas entre una tubería y la siguiente."""
        raise NotImplementedError("La subclase debe definir separacion().")

    def tuberias_moviles(self) -> bool:
        return False

    def descripcion(self) -> str:
        return f"{self.nombre}: monedas x{self.multiplicador}, hueco de {self.hueco()} filas"

    def __str__(self) -> str:
        return self.nombre

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class Facil(Dificultad):
    nombre = "facil"
    multiplicador = 1

    def hueco(self) -> int:
        return 8

    def intervalo(self) -> float:
        return 0.12

    def separacion(self) -> int:
        return 18


class Normal(Dificultad):
    nombre = "normal"
    multiplicador = 2

    def hueco(self) -> int:
        return 6

    def intervalo(self) -> float:
        return 0.09

    def separacion(self) -> int:
        return 16


class Dificil(Dificultad):
    nombre = "dificil"
    multiplicador = 3

    def hueco(self) -> int:
        return 5

    def intervalo(self) -> float:
        return 0.07

    def separacion(self) -> int:
        return 15

    def tuberias_moviles(self) -> bool:  # sobrescribe el False de la base
        return True

    def descripcion(self) -> str:
        # super() reutiliza el texto de la base y le agrega algo propio
        return super().descripcion() + ", tuberías móviles"


# Registro: nombre -> objeto. Se usa para validar y para elegir la dificultad.
DIFICULTADES = {d.nombre: d for d in (Facil(), Normal(), Dificil())}
