import tempfile
import unittest
from pathlib import Path

from gestor import reportes
from gestor.dificultad import DIFICULTADES, Dificil, Dificultad, Facil, Normal
from gestor.exportador import Exportador, ExportadorCSV, ExportadorTXT
from gestor.excepciones import PersistenciaError
from gestor.repositorio import Repositorio
from gestor.servicio import Servicio


class TestDificultad(unittest.TestCase):
    def test_herencia(self):
        for clase in (Facil, Normal, Dificil):
            self.assertTrue(issubclass(clase, Dificultad))

    def test_polimorfismo_mismo_metodo_distinto_resultado(self):
        huecos = [d.hueco() for d in DIFICULTADES.values()]
        self.assertEqual(huecos, [8, 6, 5])
        monedas = [d.monedas_para(50) for d in DIFICULTADES.values()]
        self.assertEqual(monedas, [10, 20, 30])

    def test_sobrescritura_con_super(self):
        self.assertFalse(Normal().tuberias_moviles())
        self.assertTrue(Dificil().tuberias_moviles())
        descripcion = Dificil().descripcion()
        self.assertTrue(descripcion.startswith("dificil: monedas x3"))  # parte heredada (super)
        self.assertTrue(descripcion.endswith("tuberías móviles"))       # parte propia

    def test_base_abstracta(self):
        with self.assertRaises(NotImplementedError):
            Dificultad().hueco()

    def test_str_y_repr(self):
        self.assertEqual(str(Facil()), "facil")
        self.assertEqual(repr(Dificil()), "Dificil()")


class TestExportadores(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.carpeta = Path(self.tmp.name) / "salida"
        self.repo = Repositorio()
        s = Servicio(self.repo)
        a = s.registrar_jugador("Andrés")
        s.registrar_partida(a.id, 45, "normal")
        s.registrar_partida(a.id, 12, "facil")

    def test_csv(self):
        exp = ExportadorCSV(self.carpeta)
        self.assertEqual(exp.exportar_partidas(self.repo, self.repo.partidas), 2)
        lineas = exp.ruta_de("partidas").read_text(encoding="utf-8-sig").splitlines()
        self.assertEqual(len(lineas), 3)
        self.assertTrue(lineas[0].startswith("id,jugador_id,jugador"))
        self.assertIn("Andrés", lineas[1])

    def test_csv_con_bom_para_excel(self):
        ExportadorCSV(self.carpeta).exportar_ranking(reportes.ranking(self.repo.jugadores.values()))
        crudo = (self.carpeta / "ranking.csv").read_bytes()
        self.assertTrue(crudo.startswith(b"\xef\xbb\xbf"))

    def test_csv_delimitador_punto_y_coma(self):
        exp = ExportadorCSV(self.carpeta, delimitador=";")
        exp.exportar_partidas(self.repo, self.repo.partidas)
        primera = exp.ruta_de("partidas").read_text(encoding="utf-8-sig").splitlines()[0]
        self.assertTrue(primera.startswith("id;jugador_id;jugador"))

    def test_txt(self):
        exp = ExportadorTXT(self.carpeta)
        exp.exportar_ranking(reportes.ranking(self.repo.jugadores.values()))
        texto = exp.ruta_de("ranking").read_text(encoding="utf-8")
        self.assertIn("NOMBRE", texto)
        self.assertIn("Andrés", texto)

    def test_polimorfismo_misma_llamada_distinto_formato(self):
        for exp in (ExportadorCSV(self.carpeta), ExportadorTXT(self.carpeta)):
            self.assertEqual(exp.exportar_partidas(self.repo, self.repo.partidas), 2)
        self.assertTrue((self.carpeta / "partidas.csv").exists())
        self.assertTrue((self.carpeta / "partidas.txt").exists())

    def test_base_exige_subclase(self):
        with self.assertRaises(NotImplementedError):
            Exportador(self.carpeta).exportar_partidas(self.repo, self.repo.partidas)

    def test_error_de_escritura(self):
        ocupado = Path(self.tmp.name) / "archivo"
        ocupado.write_text("x")
        with self.assertRaises(PersistenciaError):
            ExportadorTXT(ocupado / "sub").exportar_ranking([])


if __name__ == "__main__":
    unittest.main()
