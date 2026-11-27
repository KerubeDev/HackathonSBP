import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.rankings import calculate_from_files, compare_rankings, validate_at03

ROOT = Path(__file__).parents[2]
DATA = ROOT / "docs" / "track" / "datos"


class RankingEngineTests(unittest.TestCase):
  def test_supplied_at03_has_expected_shape(self):
    rows = __import__("app.rankings", fromlist=["read_csv"]).read_csv(DATA / "AT03_sintetico_202607.csv")
    self.assertEqual(validate_at03(rows, "20260731"), [])

  def test_rankings_include_all_banks_and_exact_quality_reconciliation(self):
    result = calculate_from_files(
        DATA / "AT03_sintetico_202607.csv",
        DATA / "Catalogo_CINU_SB109_reto.csv",
        DATA / "Bancos_ficticios.csv",
        DATA / "Tabla_SB21_simplificada.csv",
    )
    self.assertTrue(result["quality"]["reconciles"])
    self.assertGreater(result["quality"]["valid_universe"], 0)
    self.assertEqual(len(result["rankings"]), 72)
    self.assertEqual({row["Posicion"] for row in result["rankings"] if row["Ranking"] == "CONSUMO"}, set(range(1, 13)))

  def test_comparison_is_deterministic_and_reports_position_delta(self):
    previous = calculate_from_files(DATA / "AT03_sintetico_202608.csv", DATA / "Catalogo_CINU_SB109_reto.csv", DATA / "Bancos_ficticios.csv")
    current = calculate_from_files(DATA / "AT03_sintetico_202609.csv", DATA / "Catalogo_CINU_SB109_reto.csv", DATA / "Bancos_ficticios.csv")
    movements = compare_rankings(previous, current)
    self.assertEqual(len(movements), 72)
    self.assertTrue(all("Cambio_Posicion" in item and "Var_Saldo_Pct" in item for item in movements))


if __name__ == "__main__":
    unittest.main()
