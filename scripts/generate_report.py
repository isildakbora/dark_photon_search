#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a proposal-ready markdown report with methods, tables, and plot references."
    )
    parser.add_argument("--scan-csv", default="outputs/scan_results.csv")
    parser.add_argument("--geometry-csv", default="outputs/geometry_optimization.csv")
    parser.add_argument("--calibration-summary", default="outputs/calibration_summary.json")
    parser.add_argument("--scan-plot", default="outputs/significance_heatmap.png")
    parser.add_argument("--geometry-plot", default="outputs/geometry_optimization_heatmap.png")
    parser.add_argument("--config", default="configs/baseline_calibrated.json")
    parser.add_argument("--out-md", default="outputs/proposal_simulation_report.md")
    parser.add_argument("--top-scan", type=int, default=8)
    parser.add_argument("--top-geometry", type=int, default=6)
    return parser.parse_args()


def _read_csv_rows(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append({key: float(value) for key, value in row.items()})
    return rows


def _fmt_sig(value: float) -> str:
    return f"{value:.3f}"


def _fmt_sci(value: float) -> str:
    return f"{value:.2e}"


def main() -> None:
    args = parse_args()

    scan_rows = _read_csv_rows(Path(args.scan_csv))
    geom_rows = _read_csv_rows(Path(args.geometry_csv))
    calib = json.loads(Path(args.calibration_summary).read_text(encoding="utf-8"))
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))

    scan_sorted = sorted(scan_rows, key=lambda row: row["significance"], reverse=True)
    geom_sorted = sorted(geom_rows, key=lambda row: row["best_significance"], reverse=True)

    today = dt.date.today().isoformat()
    lines: list[str] = []
    lines.append("# Dark Photon Beam-Dump Simulation Report")
    lines.append("")
    lines.append(f"- Date: {today}")
    lines.append(f"- Config: `{Path(args.config).resolve()}`")
    lines.append(f"- Scan table: `{Path(args.scan_csv).resolve()}`")
    lines.append(f"- Geometry table: `{Path(args.geometry_csv).resolve()}`")
    lines.append("")
    lines.append("## Methods (Short)")
    lines.append("")
    lines.append(
        "A toy Monte Carlo beam-dump model was used to estimate visible dark-photon sensitivity in a 0.5 GeV electron fixed-target setup."
    )
    lines.append(
        "For each `(m_A', epsilon)` point, the chain `production -> survive shield -> decay in fiducial region -> detector acceptance/PID` was evaluated."
    )
    lines.append(
        "Background was modeled from beam-muon leakage, cosmic muons, and accidental electron-like activity, with a mass-spectrum scaling and systematic term."
    )
    lines.append(
        "Model normalization and global background scale were calibrated to published beam-dump exclusion anchor points at fixed target significance."
    )
    lines.append("")
    lines.append("## Calibration Summary")
    lines.append("")
    lines.append(
        f"- Fitted `production_norm`: `{calib['production_norm']:.6e}`"
    )
    lines.append(
        f"- Fitted global background scale: `{calib['background_scale']:.6e}`"
    )
    lines.append(
        f"- Target contour significance: `{calib['target_significance']:.3f}`"
    )
    lines.append(
        f"- Objective value: `{calib['objective_value']:.4e}`"
    )
    lines.append("")
    lines.append("| Anchor mass (MeV) | Anchor epsilon | Predicted Z | Fractional error |")
    lines.append("|---:|---:|---:|---:|")
    for row in calib["fit_points"]:
        lines.append(
            f"| {row['mass_mev']:.1f} | {_fmt_sci(row['epsilon_limit'])} | {_fmt_sig(row['predicted_significance'])} | {row['fractional_error']:+.3f} |"
        )
    lines.append("")
    lines.append("## Best Sensitivity Points")
    lines.append("")
    lines.append("| Rank | Mass (MeV) | Epsilon | Expected S | Expected B | Significance | S/B |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|")
    for idx, row in enumerate(scan_sorted[: max(1, args.top_scan)], start=1):
        lines.append(
            f"| {idx} | {row['mass_mev']:.1f} | {_fmt_sci(row['epsilon'])} | {row['expected_signal']:.3f} | {row['expected_background']:.1f} | {_fmt_sig(row['significance'])} | {_fmt_sci(row['signal_to_background'])} |"
        )
    lines.append("")
    lines.append("## Best Geometries")
    lines.append("")
    lines.append("| Rank | Shield (m) | Decay volume (m) | Best Z | Best mass (MeV) | Best epsilon | Benchmark Z sum |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|")
    for idx, row in enumerate(geom_sorted[: max(1, args.top_geometry)], start=1):
        lines.append(
            f"| {idx} | {row['shield_length_m']:.2f} | {row['decay_volume_length_m']:.2f} | {_fmt_sig(row['best_significance'])} | {row['best_mass_mev']:.1f} | {_fmt_sci(row['best_epsilon'])} | {_fmt_sig(row['benchmark_significance_total'])} |"
        )
    lines.append("")
    lines.append("## Figures")
    lines.append("")
    lines.append(f"- Scan heatmap: `{Path(args.scan_plot).resolve()}`")
    lines.append(f"- Geometry heatmap: `{Path(args.geometry_plot).resolve()}`")
    lines.append("")
    lines.append("## Recommended Next Beamline Inputs")
    lines.append("")
    lines.append(
        "1. Replace anchor approximations with collaboration-approved limit data points from the final reference set."
    )
    lines.append(
        "2. Constrain background rates with measured muon leakage from your planned shielding material and detector area."
    )
    lines.append(
        "3. Validate geometry winner points with a Geant4-level detector/transport model before final proposal submission."
    )
    lines.append("")
    lines.append("## Configuration Snapshot")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(config, indent=2))
    lines.append("```")

    output_path = Path(args.out_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report generated: {output_path.resolve()}")


if __name__ == "__main__":
    main()
