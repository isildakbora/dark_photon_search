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

from dark_photon_sim import ExperimentConfig, SimulationEngine  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate one dark photon parameter point.")
    parser.add_argument(
        "--config",
        default=str(REPO_ROOT / "configs" / "baseline.json"),
        help="Path to experiment config JSON.",
    )
    parser.add_argument("--mass-mev", required=True, type=float, help="Dark photon mass in MeV.")
    parser.add_argument("--epsilon", required=True, type=float, help="Kinetic-mixing epsilon.")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = ExperimentConfig.from_json(args.config)
    engine = SimulationEngine(config)
    result = engine.simulate_point(mass_mev=args.mass_mev, epsilon=args.epsilon)
    payload = result.__dict__
    if args.pretty:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
