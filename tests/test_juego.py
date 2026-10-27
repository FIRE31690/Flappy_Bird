import random
import unittest
from unittest import mock

from gestor.dificultad import DIFICULTADES
from gestor.excepciones import EntornoNoSoportadoError
from juego import controlador, vista
from juego.modelo import Juego, Obstaculo, Pajaro, Tuberia, TuberiaMovil


def bot(dificultad, semilla, max_ticks=1500):
    """Jugador automático: salta cuando está por debajo del centro del próximo hueco."""
    juego = Juego(dificultad, rng=random.Random(semilla))
    while not juego.terminado and juego.ticks < max_ticks:
        objetivo = juego.alto // 2
        for o in juego.obstaculos:
            if o.x + o.ancho > juego.pajaro.x:
                objetivo = o.hueco_y + o.hueco // 2
                break
        juego.tick(saltar=juego.pajaro.fila >= objetivo + 1)
    return juego


class TestPajaro(unittest.TestCase):
    def test_cae_por_gravedad_y_sube_al_saltar(self):
        p = Pajaro(8)
        for _ in range(4):
            p.actualizar()
        self.assertGreater(p.fila, 8)
        abajo = p.fila
        p.saltar()
        for _ in range(3):      # el impulso se nota en la fila entera tras unos tics
            p.actualizar()
        self.assertLess(p.fila, abajo)


class TestObstaculos(unittest.TestCase):
    def test_base_es_abstracta(self):
        o = Obstaculo(5)
        with self.assertRaises(NotImplementedError):
            o.bloquea(3)
        with self.assertRaises(NotImplementedError):
            o.choca_con(Pajaro(3))

    def test_tuberia_bloquea_fuera_del_hueco(self):
        t = Tuberia(x=10, hueco_y=5, hueco=4)
        self.assertTrue(t.bloquea(4))
        self.assertFalse(t.bloquea(5))
        self.assertFalse(t.bloquea(8))
        self.assertTrue(t.bloquea(9))

    def test_choque_solo_en_su_columna(self):
        t = Tuberia(x=10, hueco_y=5, hueco=4)          # pájaro en x=10 (COLUMNA_PAJARO)
        self.assertTrue(t.choca_con(Pajaro(2)))
        self.assertFalse(t.choca_con(Pajaro(6)))
        lejos = Tuberia(x=30, hueco_y=5, hueco=4)
        self.assertFalse(lejos.choca_con(Pajaro(2)))

    def test_tuberia_movil_es_una_tuberia_y_mueve_el_hueco(self):
        t = TuberiaMovil(x=30, hueco_y=5, hueco=4, limite_inferior=15)
        self.assertIsInstance(t, Tuberia)
        for _ in range(3):
            t.actualizar()
        self.assertEqual(t.x, 27)           # lo de la clase padre (super)
        self.assertEqual(t.hueco_y, 6)      # lo propio de la subclase

    def test_tuberia_movil_rebota_en_los_limites(self):
        t = TuberiaMovil(x=100, hueco_y=5, hueco=4, limite_inferior=12)
        posiciones = []
        for _ in range(90):
            t.actualizar()
            posiciones.append(t.hueco_y)
        self.assertGreaterEqual(min(posiciones), 1)
        self.assertLessEqual(max(posiciones) + 4, 12)


class TestJuego(unittest.TestCase):
    def test_cae_y_termina_si_no_se_salta(self):
        j = Juego(DIFICULTADES["facil"], rng=random.Random(1))
        for _ in range(30):
            j.tick()
        self.assertTrue(j.terminado)
        self.assertEqual(j.puntaje, 0)

    def test_despues_de_terminar_no_cambia(self):
        j = Juego(DIFICULTADES["facil"], rng=random.Random(1))
        for _ in range(30):
            j.tick()
        ticks = j.ticks
        j.tick(saltar=True)
        self.assertEqual(j.ticks, ticks)

    def test_dificil_usa_tuberias_moviles_y_facil_no(self):
        facil = Juego(DIFICULTADES["facil"], rng=random.Random(1))
        dificil = Juego(DIFICULTADES["dificil"], rng=random.Random(1))
        self.assertNotIsInstance(facil.obstaculos[0], TuberiaMovil)
        self.assertIsInstance(dificil.obstaculos[0], TuberiaMovil)

    def test_el_hueco_siempre_cabe_en_pantalla(self):
        for nombre, dif in DIFICULTADES.items():
            j = Juego(dif, rng=random.Random(7))
            for _ in range(600):
                j.tick(saltar=j.pajaro.fila > 7)
                for o in j.obstaculos:
                    self.assertGreaterEqual(o.hueco_y, 1, nombre)
                    self.assertLessEqual(o.hueco_y + o.hueco, j.alto, nombre)

    def test_el_juego_es_jugable_en_las_tres_dificultades(self):
        for nombre, dif in DIFICULTADES.items():
            j = bot(dif, semilla=3)
            self.assertGreaterEqual(j.puntaje, 10, f"el bot no pudo avanzar en {nombre}")

    def test_semilla_hace_el_juego_reproducible(self):
        a = bot(DIFICULTADES["normal"], 5, max_ticks=300)
        b = bot(DIFICULTADES["normal"], 5, max_ticks=300)
        self.assertEqual((a.puntaje, a.ticks), (b.puntaje, b.ticks))


class TestVista(unittest.TestCase):
    def setUp(self):
        self.j = Juego(DIFICULTADES["facil"], rng=random.Random(1))
        self.j.obstaculos[0].x = 20

    def test_tablero_tiene_marco_pajaro_y_tuberias_en_ascii(self):
        lineas = vista.tablero_a_texto(self.j, "rojo", vista.TEMA_ASCII)
        self.assertEqual(len(lineas), self.j.alto + vista.FILAS_SUELO + 2)
        self.assertTrue(lineas[0].startswith("+") and lineas[0].endswith("+"))
        fila_pajaro = lineas[1 + self.j.pajaro.fila]
        self.assertEqual(fila_pajaro[1 + self.j.pajaro.x], "R")
        self.assertTrue(any("#" in linea for linea in lineas))

    def test_tema_unicode_usa_bloques_y_marco_doble(self):
        lineas = vista.tablero_a_texto(self.j, "clasico", vista.TEMA_UNICODE)
        self.assertTrue(lineas[0].startswith("╔"))
        self.assertTrue(any("█" in linea for linea in lineas))
        self.assertEqual(lineas[1 + self.j.pajaro.fila][1 + self.j.pajaro.x], "●")

    def test_todas_las_filas_miden_lo_mismo(self):
        for tema in (vista.TEMA_UNICODE, vista.TEMA_ASCII):
            anchos = {len(l) for l in vista.tablero_a_texto(self.j, "dorado", tema)}
            self.assertEqual(anchos, {self.j.ancho + 2})

    def test_tema_ascii_solo_usa_caracteres_ascii(self):
        for estado in ("listo", "jugando", "pausa"):
            texto = "".join(vista.tablero_a_texto(self.j, "fantasma", vista.TEMA_ASCII, estado))
            self.assertTrue(texto.isascii(), estado)

    def test_pajaro_choca_se_muestra_como_x_o_cruz(self):
        self.j.terminado = True
        self.assertIn("X", "".join(vista.tablero_a_texto(self.j, "clasico", vista.TEMA_ASCII)))
        self.assertIn("✖", "".join(vista.tablero_a_texto(self.j, "clasico", vista.TEMA_UNICODE)))

    def test_el_ala_aletea_entre_fotogramas(self):
        fila, col = self.j.pajaro.fila, self.j.pajaro.x - 1
        a = vista.construir_escena(self.j, "clasico", "jugando", vista.TEMA_ASCII, fase=0)
        b = vista.construir_escena(self.j, "clasico", "jugando", vista.TEMA_ASCII, fase=1)
        self.assertNotEqual(a[fila][col][0], b[fila][col][0])

    def test_el_suelo_y_las_colinas_avanzan_con_los_ticks(self):
        antes = vista.tablero_a_texto(self.j, "clasico", vista.TEMA_UNICODE)
        self.j.ticks += 1
        despues = vista.tablero_a_texto(self.j, "clasico", vista.TEMA_UNICODE)
        self.assertNotEqual(antes[-3], despues[-3])    # fila de hierba

    def test_carteles_segun_el_estado(self):
        listo = "".join(vista.tablero_a_texto(self.j, "clasico", vista.TEMA_ASCII, "listo"))
        pausa = "".join(vista.tablero_a_texto(self.j, "clasico", vista.TEMA_ASCII, "pausa"))
        juego = "".join(vista.tablero_a_texto(self.j, "clasico", vista.TEMA_ASCII, "jugando"))
        self.assertIn("FLAPPY BIRD", listo)
        self.assertIn("PAUSA", pausa)
        self.assertNotIn("FLAPPY BIRD", juego)
        self.assertNotIn("PAUSA", juego)

    def test_destello_cambia_el_estilo_del_cielo(self):
        normal = vista.construir_escena(self.j, destello=False, tema=vista.TEMA_ASCII)
        flash = vista.construir_escena(self.j, destello=True, tema=vista.TEMA_ASCII)
        self.assertEqual(normal[0][0][1], "cielo")
        self.assertEqual(flash[0][0][1], "destello")

    def test_cada_estilo_usado_esta_definido(self):
        usados = {e for fila in vista.construir_escena(self.j, "rojo", "listo", vista.TEMA_ASCII)
                  for _, e in fila}
        self.assertTrue(usados <= set(vista.ESTILOS))

    def test_numero_grande_tiene_cinco_lineas(self):
        lineas = vista.numero_grande(42, vista.TEMA_ASCII)
        self.assertEqual(len(lineas), 5)
        self.assertEqual(len({len(l) for l in lineas}), 1)

    def test_pantalla_final_muestra_record_solo_si_se_supera(self):
        self.j.puntaje = 12
        con = [t for t, _ in vista.lineas_final(self.j, "Ana", 5, vista.TEMA_UNICODE)]
        sin = [t for t, _ in vista.lineas_final(self.j, "Ana", 20, vista.TEMA_UNICODE)]
        self.assertIn("¡NUEVO RÉCORD!", con)
        self.assertNotIn("¡NUEVO RÉCORD!", sin)
        self.assertTrue(any(t.startswith("Medalla:    bronce") for t in con))

    def test_pantalla_final_ascii_sin_tildes(self):
        self.j.puntaje = 12
        textos = [t for t, _ in vista.lineas_final(self.j, "Ana", 5, vista.TEMA_ASCII)]
        self.assertTrue("".join(textos).isascii())
        self.assertIn("NUEVO RECORD!", textos)

    def test_elegir_tema_respeta_variables_de_entorno(self):
        with mock.patch.dict("os.environ", {"FLAPPY_ASCII": "1"}):
            self.assertIs(vista.elegir_tema(), vista.TEMA_ASCII)
        with mock.patch.dict("os.environ", {"FLAPPY_UNICODE": "1"}, clear=True):
            self.assertIs(vista.elegir_tema(), vista.TEMA_UNICODE)

    def test_cada_skin_tiene_glifo_en_ambos_temas(self):
        skins = {"clasico", "rojo", "dorado", "fantasma"}
        self.assertEqual(set(vista.TEMA_ASCII.pajaros), skins)
        self.assertEqual(set(vista.TEMA_UNICODE.pajaros), skins)

    def test_dibujar_en_pantalla_falsa_no_falla(self):
        pantalla = mock.Mock()
        pantalla.getmaxyx.return_value = (30, 80)
        estilos = vista.Estilos(con_color=False)
        vista.dibujar(pantalla, estilos, vista.TEMA_UNICODE, self.j, "Ana", "rojo", "jugando")
        vista.pantalla_final(pantalla, estilos, vista.TEMA_UNICODE, self.j, "Ana", 0)
        self.assertTrue(pantalla.addstr.called)
        self.assertTrue(pantalla.refresh.called)


class TestControlador(unittest.TestCase):
    def test_accion_para_if_elif_else(self):
        self.assertEqual(controlador.accion_para(ord(" ")), "saltar")
        self.assertEqual(controlador.accion_para(259), "saltar")
        self.assertEqual(controlador.accion_para(ord("P")), "pausa")
        self.assertEqual(controlador.accion_para(ord("q")), "salir")
        self.assertEqual(controlador.accion_para(27), "salir")
        self.assertEqual(controlador.accion_para(ord("z")), "nada")

    def test_sin_curses_lanza_error_claro(self):
        with mock.patch.object(controlador, "curses", None):
            with self.assertRaises(EntornoNoSoportadoError) as cm:
                controlador.jugar("Ana", "clasico", DIFICULTADES["facil"])
        self.assertIn("windows-curses", str(cm.exception))

    def test_terminal_pequena_lanza_error_claro(self):
        pantalla = mock.Mock()
        pantalla.getmaxyx.return_value = (10, 20)
        with self.assertRaises(EntornoNoSoportadoError):
            controlador._partida(pantalla, "Ana", "clasico", DIFICULTADES["facil"])


if __name__ == "__main__":
    unittest.main()
