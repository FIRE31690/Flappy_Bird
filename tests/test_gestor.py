import json
import tempfile
import unittest
from pathlib import Path

from gestor import almacenamiento, reglas, reportes, validadores as v
from gestor.bitacora import Bitacora
from gestor.excepciones import (NoEncontradoError, PersistenciaError,
                                ReglaNegocioError, ValidacionError)
from gestor.modelos import Jugador
from gestor.repositorio import Repositorio
from gestor.servicio import Servicio


class TestValidadores(unittest.TestCase):
    def test_nombre_valido_y_recortado(self):
        self.assertEqual(v.validar_nombre("  Ana  "), "Ana")

    def test_nombre_corto_o_con_simbolos(self):
        for malo in ["ab", "x" * 16, "Ana!!", ""]:
            with self.assertRaises(ValidacionError):
                v.validar_nombre(malo)

    def test_puntaje(self):
        self.assertEqual(v.validar_puntaje("25"), 25)
        for malo in ["abc", "-1", "10000", ""]:
            with self.assertRaises(ValidacionError):
                v.validar_puntaje(malo)

    def test_dificultad(self):
        self.assertEqual(v.validar_dificultad(" DIFICIL "), "dificil")
        with self.assertRaises(ValidacionError):
            v.validar_dificultad("imposible")


class TestReglas(unittest.TestCase):
    def test_medallas(self):
        casos = {0: "ninguna", 9: "ninguna", 10: "bronce", 20: "plata", 40: "oro", 100: "platino"}
        for puntaje, esperado in casos.items():
            self.assertEqual(reglas.medalla_para(puntaje), esperado)

    def test_monedas_y_nivel(self):
        self.assertEqual(reglas.monedas_para(50, "dificil"), 30)
        self.assertEqual(reglas.nivel_para(0), 1)
        self.assertEqual(reglas.nivel_para(100), 3)

    def test_categoria_if_elif_else(self):
        self.assertEqual(reglas.categoria_para(1, 0, 0), "sin jugar")
        self.assertEqual(reglas.categoria_para(4, 40, 3), "experto")
        self.assertEqual(reglas.categoria_para(4, 5, 3), "regular")   # nivel alto pero puntaje bajo
        self.assertEqual(reglas.categoria_para(1, 12, 1), "regular")  # puntaje >= 10
        self.assertEqual(reglas.categoria_para(1, 5, 2), "novato")


class TestJugador(unittest.TestCase):
    def setUp(self):
        self.j = Jugador(id=1, nombre="Ana")

    def test_saldo_no_puede_ser_negativo(self):
        with self.assertRaises(ReglaNegocioError):
            self.j.monedas = -5
        self.j.monedas = 10
        with self.assertRaises(ReglaNegocioError):
            self.j.monedas -= 20
        self.assertEqual(self.j.monedas, 10)

    def test_monedas_totales_es_solo_lectura(self):
        with self.assertRaises(AttributeError):
            self.j.monedas_totales = 99

    def test_nivel_se_calcula_solo(self):
        self.j.aplicar_partida(100, 120)
        self.assertEqual(self.j.nivel, 3)
        self.assertEqual(self.j.monedas_totales, 120)

    def test_skins_son_inmutables_desde_fuera(self):
        self.assertIsInstance(self.j.skins, tuple)
        self.j.adquirir_skin("rojo")
        self.assertIn("rojo", self.j.skins)
        with self.assertRaises(ReglaNegocioError):
            self.j.adquirir_skin("rojo")
        with self.assertRaises(ReglaNegocioError):
            self.j.equipar("dorado")

    def test_str_y_repr_sobrescritos(self):
        texto = str(self.j)
        self.assertIn("Ana", texto)
        self.assertIn("sin jugar", texto)
        self.assertEqual(repr(self.j), "Jugador(id=1, nombre='Ana')")

    def test_ida_y_vuelta_dict_ignora_nivel(self):
        self.j.aplicar_partida(50, 20)
        d = self.j.to_dict()
        self.assertIn("nivel", d)
        d["nivel"] = 99  # un valor falso no debe afectar: el nivel se recalcula
        copia = Jugador.from_dict(d)
        self.assertEqual(copia.nivel, 1)
        self.assertEqual(copia.monedas, 20)


class TestServicio(unittest.TestCase):
    def setUp(self):
        self.repo = Repositorio()
        self.s = Servicio(self.repo)
        self.ana = self.s.registrar_jugador("Ana")

    def test_nombre_duplicado(self):
        with self.assertRaises(ReglaNegocioError):
            self.s.registrar_jugador("ana")

    def test_registrar_partida_actualiza_estado(self):
        p = self.s.registrar_partida(self.ana.id, "50", "normal")
        self.assertEqual(p.medalla, "oro")
        self.assertEqual(self.ana.mejor_puntaje, 50)
        self.assertEqual(self.ana.monedas, 20)
        self.assertEqual(self.ana.partidas_jugadas, 1)

    def test_jugador_bloqueado_no_juega(self):
        self.s.cambiar_estado(self.ana.id, False)
        with self.assertRaises(ReglaNegocioError):
            self.s.registrar_partida(self.ana.id, 10, "facil")
        self.assertEqual(len(self.repo.partidas), 0)

    def test_jugador_inexistente(self):
        with self.assertRaises(NoEncontradoError):
            self.s.registrar_partida(99, 10, "facil")

    def test_comprar_skin(self):
        with self.assertRaises(ReglaNegocioError):  # sin monedas
            self.s.comprar_skin(self.ana.id, "rojo")
        self.s.registrar_partida(self.ana.id, 100, "dificil")  # 60 monedas
        self.s.comprar_skin(self.ana.id, "rojo")
        self.assertEqual(self.ana.monedas, 10)
        self.assertIn("rojo", self.ana.skins)
        with self.assertRaises(ReglaNegocioError):  # ya la tiene
            self.s.comprar_skin(self.ana.id, "rojo")

    def test_equipar_skin_no_poseida(self):
        with self.assertRaises(ReglaNegocioError):
            self.s.equipar_skin(self.ana.id, "dorado")

    def test_repositorio_es_de_solo_lectura(self):
        with self.assertRaises(TypeError):
            self.repo.jugadores[5] = Jugador(5, "Intruso")  # MappingProxyType no permite asignar
        self.assertIsInstance(self.repo.partidas, tuple)

    def test_filtros_e_integridad(self):
        luis = self.s.registrar_jugador("Luis")
        self.s.registrar_partida(self.ana.id, 30, "facil")
        self.s.registrar_partida(luis.id, 80, "dificil")
        self.assertEqual(len(self.repo.filtrar_partidas(dificultad="dificil")), 1)
        self.assertEqual(len(self.repo.filtrar_partidas(puntaje_min=30)), 2)
        self.assertEqual(self.repo.verificar_integridad(), [])
        self.ana.mejor_puntaje = 999  # corrupción simulada
        self.assertTrue(self.repo.verificar_integridad())

    def test_integridad_detecta_partidas_huerfanas_con_conjuntos(self):
        self.repo.agregar_partida(77, 10, "facil", "bronce", 2)  # jugador 77 no existe
        problemas = self.repo.verificar_integridad()
        self.assertTrue(any("77" in p for p in problemas))

    def test_jugadores_sin_partidas(self):
        luis = self.s.registrar_jugador("Luis")
        self.s.registrar_partida(self.ana.id, 30, "facil")
        sin = reportes.jugadores_sin_partidas(self.repo)
        self.assertEqual([j.nombre for j in sin], ["Luis"])
        self.assertEqual(luis.categoria, "sin jugar")


class TestBitacora(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ruta = Path(self.tmp.name) / "sub" / "bitacora.txt"

    def test_registrar_y_leer(self):
        b = Bitacora(self.ruta)
        self.assertEqual(b.ultimas(), [])          # aún no existe
        self.assertTrue(b.registrar("uno"))
        self.assertTrue(b.registrar("dos"))
        lineas = b.ultimas(1)
        self.assertEqual(len(lineas), 1)
        self.assertTrue(lineas[0].endswith("| dos"))

    def test_registrar_devuelve_false_si_no_puede_escribir(self):
        bloqueo = Path(self.tmp.name) / "archivo"
        bloqueo.write_text("x")                     # un archivo, no una carpeta
        self.assertFalse(Bitacora(bloqueo / "b.txt").registrar("hola"))

    def test_servicio_anota_eventos(self):
        s = Servicio(Repositorio(), Bitacora(self.ruta))
        j = s.registrar_jugador("Ana")
        s.registrar_partida(j.id, 50, "normal")
        texto = self.ruta.read_text(encoding="utf-8")
        self.assertIn("Jugador registrado: Ana", texto)
        self.assertIn("medalla oro", texto)


class TestPersistencia(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ruta = Path(self.tmp.name) / "d.json"
        self.repo = Repositorio()
        s = Servicio(self.repo)
        a, b = s.registrar_jugador("Ana"), s.registrar_jugador("Beto")
        s.registrar_partida(a.id, 45, "normal")
        s.registrar_partida(b.id, 12, "facil")
        s.registrar_partida(b.id, 60, "normal")

    def test_ida_y_vuelta_json(self):
        almacenamiento.guardar(self.repo, self.ruta)
        nuevo = almacenamiento.cargar(self.ruta)
        self.assertEqual(nuevo.jugadores[2].mejor_puntaje, 60)
        self.assertEqual(len(nuevo.partidas), 3)
        self.assertEqual(nuevo.verificar_integridad(), [])

    def test_acepta_ruta_como_texto(self):
        almacenamiento.guardar(self.repo, str(self.ruta))
        self.assertEqual(len(almacenamiento.cargar(str(self.ruta)).jugadores), 2)

    def test_archivo_inexistente_da_repo_vacio(self):
        self.assertEqual(len(almacenamiento.cargar(Path(self.tmp.name) / "no.json").jugadores), 0)

    def test_json_corrupto_se_respalda(self):
        self.ruta.write_text("{ esto no es json", encoding="utf-8")
        with self.assertRaises(PersistenciaError):
            almacenamiento.cargar(self.ruta)
        self.assertTrue(self.ruta.with_name("d.json.corrupto").exists())

    def test_json_con_campos_invalidos_tambien_se_respalda(self):
        self.ruta.write_text(json.dumps({"jugadores": [{"id": 1}], "partidas": []}), encoding="utf-8")
        with self.assertRaises(PersistenciaError):
            almacenamiento.cargar(self.ruta)
        self.assertTrue(self.ruta.with_name("d.json.corrupto").exists())

    def test_saldo_negativo_en_json_es_error_de_persistencia(self):
        dato = {"jugadores": [{"id": 1, "nombre": "Ana", "monedas": -4}], "partidas": []}
        self.ruta.write_text(json.dumps(dato), encoding="utf-8")
        with self.assertRaises(PersistenciaError):
            almacenamiento.cargar(self.ruta)

    def test_finally_limpia_el_temporal_si_falla_el_guardado(self):
        destino = Path(self.tmp.name) / "soy_una_carpeta"
        destino.mkdir()                              # no se puede reemplazar una carpeta por un archivo
        with self.assertRaises(PersistenciaError):
            almacenamiento.guardar(self.repo, destino)
        self.assertFalse(destino.with_name("soy_una_carpeta.tmp").exists())

    def test_reportes(self):
        top = reportes.ranking(self.repo.jugadores.values(), 1)
        self.assertEqual(top[0].nombre, "Beto")
        r = reportes.resumen_por_dificultad(self.repo.partidas)
        self.assertEqual(r["normal"]["promedio"], 52.5)
        self.assertEqual(reportes.conteo_medallas(self.repo.partidas)["oro"], 2)
        self.assertEqual(reportes.resumen_general(self.repo)["partidas"], 3)


if __name__ == "__main__":
    unittest.main()
