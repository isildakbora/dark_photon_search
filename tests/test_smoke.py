from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from dark_photon_sim import ExperimentConfig, SimulationEngine  # noqa: E402


class SimulationSmokeTest(unittest.TestCase):
    def test_quick_scan_point(self) -> None:
        config_path = REPO_ROOT / "configs" / "quick_scan.json"
        config = ExperimentConfig.from_json(config_path)
        result = SimulationEngine(config).simulate_point(mass_mev=30.0, epsilon=1e-6)
        self.assertGreaterEqual(result.production_probability, 0.0)
        self.assertLessEqual(result.production_probability, 1.0)
        self.assertGreaterEqual(result.mean_decay_probability, 0.0)
        self.assertLessEqual(result.mean_decay_probability, 1.0)
        self.assertGreaterEqual(result.mean_reco_probability, 0.0)
        self.assertLessEqual(result.mean_reco_probability, 1.0)
        self.assertGreaterEqual(result.expected_background, 0.0)


if __name__ == "__main__":
    unittest.main()
