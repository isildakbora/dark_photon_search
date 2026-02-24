#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from dark_photon_sim.calibration import (  # noqa: E402
    CalibrationProblem,
    apply_calibration,
    calibrate_against_limits,
    config_to_dict,
)
from dark_photon_sim.config import ExperimentConfig  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calibrate production normalization and background rates against published exclusion anchors."
    )
    parser.add_argument(
        "--config",
        default=str(REPO_ROOT / "configs" / "baseline_uncalibrated.json"),
        help="Input experiment config JSON.",
    )
    parser.add_argument(
        "--anchors",
        default=str(REPO_ROOT / "configs" / "published_limit_anchors.json"),
        help="Calibration anchor JSON.",
    )
    parser.add_argument(
        "--out-config",
        default=str(REPO_ROOT / "configs" / "baseline_calibrated.json"),
        help="Path for calibrated config JSON.",
    )
    parser.add_argument(
        "--out-summary",
        default=str(REPO_ROOT / "outputs" / "calibration_summary.json"),
        help="Path for calibration summary JSON.",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Also overwrite --config with calibrated values.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_config = ExperimentConfig.from_json(args.config)
    problem = CalibrationProblem.from_json(args.anchors)
    calibration = calibrate_against_limits(base_config, problem)
    calibrated_config = apply_calibration(base_config, calibration)

    out_config = Path(args.out_config)
    out_config.parent.mkdir(parents=True, exist_ok=True)
    out_config.write_text(
        json.dumps(config_to_dict(calibrated_config), indent=2, sort_keys=False),
        encoding="utf-8",
    )

    out_summary = Path(args.out_summary)
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    out_summary.write_text(
        json.dumps(calibration.to_dict(), indent=2, sort_keys=False), encoding="utf-8"
    )

    if args.in_place:
        Path(args.config).write_text(
            json.dumps(config_to_dict(calibrated_config), indent=2, sort_keys=False),
            encoding="utf-8",
        )

    print(f"Calibrated config: {out_config.resolve()}")
    print(f"Calibration summary: {out_summary.resolve()}")
    print("")
    print(f"production_norm = {calibration.production_norm:.6e}")
    print(f"background_scale = {calibration.background_scale:.6e}")
    print(f"objective = {calibration.objective_value:.6e}")
    print("")
    print("Anchor fit:")
    for row in calibration.fit_points:
        print(
            f"m={row.mass_mev:6.1f} MeV, eps={row.epsilon_limit:.2e}, "
            f"Z_pred={row.predicted_significance:.3f}, "
            f"frac_err={row.fractional_error:+.3f}, source={row.source}"
        )


if __name__ == "__main__":
    main()
