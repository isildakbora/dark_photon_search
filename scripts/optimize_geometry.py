#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from dark_photon_sim.config import ExperimentConfig  # noqa: E402
from dark_photon_sim.geometry import GeometryScanGrid, run_geometry_scan  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan shield/decay lengths and rank geometries by sensitivity."
    )
    parser.add_argument(
        "--config",
        default=str(REPO_ROOT / "configs" / "baseline_calibrated.json"),
        help="Experiment config JSON.",
    )
    parser.add_argument(
        "--grid",
        default=str(REPO_ROOT / "configs" / "geometry_scan.json"),
        help="Geometry scan grid JSON.",
    )
    parser.add_argument(
        "--out-csv",
        default=str(REPO_ROOT / "outputs" / "geometry_optimization.csv"),
        help="CSV output path.",
    )
    parser.add_argument(
        "--out-plot",
        default=str(REPO_ROOT / "outputs" / "geometry_optimization_heatmap.png"),
        help="Heatmap output path.",
    )
    parser.add_argument(
        "--metric",
        choices=["best_significance", "benchmark_significance_total"],
        default="best_significance",
        help="Metric used for ranking and heatmap values.",
    )
    return parser.parse_args()


def _write_csv(path: Path, rows: list[dict[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _save_heatmap(path: Path, rows: list[dict[str, float]], metric: str) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit(
            "matplotlib is required for --out-plot. Install with: pip install matplotlib"
        ) from exc

    shields = sorted({row["shield_length_m"] for row in rows})
    decays = sorted({row["decay_volume_length_m"] for row in rows})
    shield_index = {value: idx for idx, value in enumerate(shields)}
    decay_index = {value: idx for idx, value in enumerate(decays)}
    grid = [[0.0 for _ in shields] for _ in decays]

    for row in rows:
        i = decay_index[row["decay_volume_length_m"]]
        j = shield_index[row["shield_length_m"]]
        grid[i][j] = row[metric]

    fig, ax = plt.subplots(figsize=(8, 5))
    image = ax.imshow(grid, origin="lower", aspect="auto", cmap="plasma")
    ax.set_title(f"Geometry optimization: {metric}")
    ax.set_xlabel("Shield length [m]")
    ax.set_ylabel("Decay volume length [m]")
    ax.set_xticks(range(len(shields)))
    ax.set_xticklabels([f"{value:.1f}" for value in shields])
    ax.set_yticks(range(len(decays)))
    ax.set_yticklabels([f"{value:.1f}" for value in decays])
    fig.colorbar(image, ax=ax, label=metric)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)


def main() -> None:
    args = parse_args()
    config = ExperimentConfig.from_json(args.config)
    grid = GeometryScanGrid.from_json(args.grid, fallback_mc_samples=config.scan.mc_samples_per_point)

    results = run_geometry_scan(config, grid)
    rows = [row.to_dict() for row in results]
    rows_sorted = sorted(rows, key=lambda row: row[args.metric], reverse=True)
    _write_csv(Path(args.out_csv), rows_sorted)
    _save_heatmap(Path(args.out_plot), rows, metric=args.metric)

    print(f"Geometry scan rows: {len(rows_sorted)}")
    print(f"CSV: {Path(args.out_csv).resolve()}")
    print(f"Heatmap: {Path(args.out_plot).resolve()}")
    print("")
    print("Top geometries:")
    for index, row in enumerate(rows_sorted[:10], start=1):
        print(
            f"{index:02d}. shield={row['shield_length_m']:.2f} m, decay={row['decay_volume_length_m']:.2f} m, "
            f"{args.metric}={row[args.metric]:.4f}, best(m,eps)=({row['best_mass_mev']:.1f} MeV, {row['best_epsilon']:.2e})"
        )


if __name__ == "__main__":
    main()
