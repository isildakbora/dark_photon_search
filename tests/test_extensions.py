from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from dark_photon_sim.calibration import (  # noqa: E402
    CalibrationAnchor,
    CalibrationProblem,
    apply_calibration,
    calibrate_against_limits,
)
from dark_photon_sim.config import ExperimentConfig  # noqa: E402
from dark_photon_sim.geometry import BenchmarkPoint, GeometryScanGrid, run_geometry_scan  # noqa: E402


class ExtensionSmokeTest(unittest.TestCase):
    def test_calibration_and_geometry(self) -> None:
        config = ExperimentConfig.from_json(REPO_ROOT / "configs" / "quick_scan.json")

        problem = CalibrationProblem(
            target_significance=1.64,
            anchors=[
                CalibrationAnchor(
                    mass_mev=10.0,
                    epsilon_limit=3.0e-6,
                    source="test-anchor-a",
                ),
                CalibrationAnchor(
                    mass_mev=30.0,
                    epsilon_limit=1.0e-5,
                    source="test-anchor-b",
                ),
            ],
            log10_background_scale_min=-2.0,
            log10_background_scale_max=1.0,
            background_scale_steps=50,
            calibration_mc_samples_per_point=400,
            prior_background_scale_center=1.0,
            prior_background_scale_weight=0.01,
        )

        summary = calibrate_against_limits(config, problem)
        self.assertGreater(summary.production_norm, 0.0)
        self.assertGreater(summary.background_scale, 0.0)

        calibrated_config = apply_calibration(config, summary)
        self.assertGreater(calibrated_config.model.production_norm, 0.0)

        grid = GeometryScanGrid(
            shield_length_m_values=[1.0, 2.0],
            decay_volume_length_m_values=[2.0],
            benchmark_points=[BenchmarkPoint(mass_mev=30.0, epsilon=1e-5)],
            mc_samples_per_point=300,
        )
        rows = run_geometry_scan(calibrated_config, grid)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row.best_significance >= 0.0 for row in rows))


if __name__ == "__main__":
    unittest.main()
