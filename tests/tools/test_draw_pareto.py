import tempfile
import unittest
from pathlib import Path

from tools.draw_pareto import render_pareto_chart


class DrawParetoTests(unittest.TestCase):
    def test_render_pareto_chart_creates_file(self) -> None:
        rows = [
            {"config_id": "cfg-a", "recall_at_10": 0.6, "p95_ms": 120.0, "cost": 0.01},
            {"config_id": "cfg-b", "recall_at_10": 0.62, "p95_ms": 130.0, "cost": 0.02},
            {"config_id": "cfg-c", "recall_at_10": 0.58, "p95_ms": 110.0, "cost": 0.015},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "pareto.png"
            path = render_pareto_chart(rows, output_path)
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()

