from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path

from .engine import SimulationResult


def write_results_csv(path: str | Path, results: list[SimulationResult]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def top_results_by_significance(
    results: list[SimulationResult],
    top_n: int,
) -> list[SimulationResult]:
    return sorted(results, key=lambda item: item.significance, reverse=True)[:top_n]
