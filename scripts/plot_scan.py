#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a significance heatmap from scan_results.csv."
    )
    parser.add_argument(
        "--scan-csv",
        default="outputs/scan_results.csv",
        help="Input CSV produced by scripts/run_scan.py",
    )
    parser.add_argument(
        "--out",
        default="outputs/significance_heatmap.png",
        help="Output image path.",
    )
    return parser.parse_args()


def main() -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as exc:
        raise SystemExit(
            "matplotlib is required for plotting. Install it with: pip install matplotlib"
        ) from exc

    args = parse_args()
    rows: list[dict[str, float]] = []
    with Path(args.scan_csv).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "mass_mev": float(row["mass_mev"]),
                    "epsilon": float(row["epsilon"]),
                    "significance": float(row["significance"]),
                }
            )

    if not rows:
        raise SystemExit(f"No rows found in {args.scan_csv}")

    masses = sorted({row["mass_mev"] for row in rows})
    epsilons = sorted({row["epsilon"] for row in rows})
    mass_index = {value: idx for idx, value in enumerate(masses)}
    epsilon_index = {value: idx for idx, value in enumerate(epsilons)}

    grid = [[0.0 for _ in masses] for _ in epsilons]
    for row in rows:
        i = epsilon_index[row["epsilon"]]
        j = mass_index[row["mass_mev"]]
        grid[i][j] = row["significance"]

    x_values = np.array(masses, dtype=float)
    y_values = np.array(epsilons, dtype=float)
    z_values = np.array(grid, dtype=float)
    z_min = float(np.nanmin(z_values))
    z_max = float(np.nanmax(z_values))
    contour_levels = (
        np.linspace(z_min, z_max, 10)
        if z_max > z_min
        else np.array([z_min], dtype=float)
    )
    x_grid, y_grid = np.meshgrid(x_values, y_values)

    fig, ax = plt.subplots(figsize=(10, 6))
    image = ax.contourf(x_grid, y_grid, z_values, levels=180, cmap="viridis")
    if z_max > z_min:
        lines = ax.contour(
            x_grid,
            y_grid,
            z_values,
            levels=contour_levels,
            colors="white",
            linewidths=0.9,
            alpha=0.9,
        )
        ax.clabel(lines, fmt="%.2f", fontsize=7, inline=True)
    ax.set_title("Dark Photon Significance Scan")
    ax.set_xlabel("Mass [MeV]")
    ax.set_ylabel("epsilon")
    ax.set_yscale("log")
    ax.set_xticks(x_values)
    ax.set_xticklabels([f"{mass:.0f}" for mass in x_values], rotation=45)
    ax.set_yticks(y_values)
    ax.set_yticklabels([f"{eps:.1e}" for eps in y_values])
    fig.colorbar(image, ax=ax, label="Approx. significance")
    fig.tight_layout()
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    print(f"Saved: {output_path.resolve()}")


if __name__ == "__main__":
    main()
