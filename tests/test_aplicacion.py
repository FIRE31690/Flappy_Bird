import contextlib
import io
import unittest
from unittest import mock

import aplicacion
from gestor.excepciones import NoEncontradoError, ReglaNegocioError
from gestor.repositorio import Repositorio
from gestor.servicio import Servicio
from juego.controlador import ResultadoJuego


def entradas(*respuestas):
    """Reemplaza input(): devuelve las respuestas en orden."""
    return mock.patch("gestor.interfaz.pedir", side_effect=list(respuestas))


def correr(servicio, resultado, *respuestas):
    jugar_falso = mock.Mock(return_value=resultado)
    salida = io.StringIO()
    with entradas(*respuestas), contextlib.redirect_stdout(salida):
        aplicacion.opcion_jugar(servicio, jugar=jugar_falso)
    return salida.getvalue(), jugar_falso


class TestOpcionJugar(unittest.TestCase):
    def setUp(self):
        self.s = Servicio(Repositorio())

    def test_jugador_nuevo_se_crea_y_la_partida_se_registra(self):
        texto, jugar = correr(self.s, ResultadoJuego(45, False), "Camila", "normal", "")
        jugador = self.s.repo.buscar_por_nombre("Camila", exacto=True)[0]
        self.assertEqual(jugador.partidas_jugadas, 1)
        self.assertEqual(jugador.mejor_puntaje, 45)
        self.assertEqual(jugador.monedas, 18)          # (45 // 5) * 2
        jugar.assert_called_once()
        self.assertEqual(jugar.call_args.args[0], "Camila")
        self.assertIn("medalla oro", texto)
        self.assertIn("Nuevo récord", texto)

    def test_jugador_existente_por_id_y_dificultad_por_defecto(self):
        ana = self.s.registrar_jugador("Ana")
        _, jugar = correr(self.s, ResultadoJuego(10, False), str(ana.id), "", "")
        self.assertEqual(jugar.call_args.args[2].nombre, "normal")
        self.assertEqual(ana.partidas_jugadas, 1)

    def test_nombre_existente_reutiliza_al_jugador(self):
        ana = self.s.registrar_jugador("Ana")
        correr(self.s, ResultadoJuego(10, False), "ana", "facil", "")
        self.assertEqual(len(self.s.repo.jugadores), 1)
        self.assertEqual(ana.partidas_jugadas, 1)

    def test_partida_abandonada_no_se_registra(self):
        texto, _ = correr(self.s, ResultadoJuego(30, True), "Luis", "facil", "")
        self.assertIn("abandonada", texto)
        self.assertEqual(len(self.s.repo.partidas), 0)

    def test_jugador_bloqueado_no_puede_jugar(self):
        ana = self.s.registrar_jugador("Ana")
        self.s.cambiar_estado(ana.id, False)
        with self.assertRaises(ReglaNegocioError):
            correr(self.s, ResultadoJuego(10, False), "Ana")

    def test_id_inexistente(self):
        with self.assertRaises(NoEncontradoError):
            correr(self.s, ResultadoJuego(10, False), "99")

    def test_no_hay_nuevo_record_si_no_supera_el_anterior(self):
        ana = self.s.registrar_jugador("Ana")
        self.s.registrar_partida(ana.id, 50, "facil")
        texto, _ = correr(self.s, ResultadoJuego(20, False), "Ana", "facil", "")
        self.assertNotIn("Nuevo récord", texto)


if __name__ == "__main__":
    unittest.main()
