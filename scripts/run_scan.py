#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from dark_photon_sim import ExperimentConfig, SimulationEngine  # noqa: E402
from dark_photon_sim.io_utils import top_results_by_significance, write_results_csv  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run dark photon scan over mass and epsilon grids.")
    parser.add_argument(
        "--config",
        default=str(REPO_ROOT / "configs" / "baseline.json"),
        help="Path to experiment config JSON.",
    )
    parser.add_argument(
        "--out",
        default=str(REPO_ROOT / "outputs" / "scan_results.csv"),
        help="Output CSV path.",
    )
    parser.add_argument(
        "--top",
        default=10,
        type=int,
        help="Number of best points (by significance) to print.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = ExperimentConfig.from_json(args.config)
    engine = SimulationEngine(config)
    results = engine.run_scan()
    write_results_csv(args.out, results)

    best_points = top_results_by_significance(results, top_n=max(1, args.top))
    print(f"Scan completed with {len(results)} grid points.")
    print(f"Results written to: {Path(args.out).resolve()}")
    print("")
    print("Top points by significance:")
    for index, row in enumerate(best_points, start=1):
        print(
            f"{index:02d}. mA'={row.mass_mev:7.2f} MeV, eps={row.epsilon:.2e}, "
            f"S={row.expected_signal:.3f}, B={row.expected_background:.3f}, "
            f"Z={row.significance:.3f}, S/B={row.signal_to_background:.3e}"
        )


if __name__ == "__main__":
    main()
