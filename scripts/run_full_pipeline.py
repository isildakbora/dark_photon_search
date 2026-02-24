#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run calibration, scan, geometry optimization, and report generation."
    )
    parser.add_argument("--base-config", default="configs/baseline_uncalibrated.json")
    parser.add_argument("--anchors", default="configs/published_limit_anchors.json")
    parser.add_argument("--calibrated-config", default="configs/baseline_calibrated.json")
    parser.add_argument("--calibration-summary", default="outputs/calibration_summary.json")
    parser.add_argument("--scan-csv", default="outputs/scan_results.csv")
    parser.add_argument("--scan-plot", default="outputs/significance_heatmap.png")
    parser.add_argument("--geometry-grid", default="configs/geometry_scan.json")
    parser.add_argument("--geometry-csv", default="outputs/geometry_optimization.csv")
    parser.add_argument(
        "--geometry-plot", default="outputs/geometry_optimization_heatmap.png"
    )
    parser.add_argument("--report-md", default="outputs/proposal_simulation_report.md")
    return parser.parse_args()


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True, cwd=REPO_ROOT)


def main() -> None:
    args = parse_args()
    py = sys.executable

    _run(
        [
            py,
            "scripts/calibrate_model.py",
            "--config",
            args.base_config,
            "--anchors",
            args.anchors,
            "--out-config",
            args.calibrated_config,
            "--out-summary",
            args.calibration_summary,
        ]
    )
    _run(
        [
            py,
            "scripts/run_scan.py",
            "--config",
            args.calibrated_config,
            "--out",
            args.scan_csv,
            "--top",
            "10",
        ]
    )
    _run(
        [
            py,
            "scripts/plot_scan.py",
            "--scan-csv",
            args.scan_csv,
            "--out",
            args.scan_plot,
        ]
    )
    _run(
        [
            py,
            "scripts/optimize_geometry.py",
            "--config",
            args.calibrated_config,
            "--grid",
            args.geometry_grid,
            "--out-csv",
            args.geometry_csv,
            "--out-plot",
            args.geometry_plot,
        ]
    )
    _run(
        [
            py,
            "scripts/generate_report.py",
            "--scan-csv",
            args.scan_csv,
            "--geometry-csv",
            args.geometry_csv,
            "--calibration-summary",
            args.calibration_summary,
            "--scan-plot",
            args.scan_plot,
            "--geometry-plot",
            args.geometry_plot,
            "--config",
            args.calibrated_config,
            "--out-md",
            args.report_md,
        ]
    )

    print("Full pipeline complete.")
    print(f"Report: {Path(args.report_md).resolve()}")


if __name__ == "__main__":
    main()
