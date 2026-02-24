from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from .config import BeamConfig, ExperimentConfig, ScanConfig
from .engine import SimulationEngine


@dataclass(frozen=True)
class BenchmarkPoint:
    mass_mev: float
    epsilon: float


@dataclass(frozen=True)
class GeometryScanGrid:
    shield_length_m_values: list[float]
    decay_volume_length_m_values: list[float]
    benchmark_points: list[BenchmarkPoint]
    mc_samples_per_point: int

    @staticmethod
    def from_json(path: str | Path, fallback_mc_samples: int) -> "GeometryScanGrid":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        benchmark_points: list[BenchmarkPoint] = []
        for row in raw.get("benchmark_points", []):
            benchmark_points.append(
                BenchmarkPoint(mass_mev=float(row["mass_mev"]), epsilon=float(row["epsilon"]))
            )
        return GeometryScanGrid(
            shield_length_m_values=[float(v) for v in raw["shield_length_m_values"]],
            decay_volume_length_m_values=[float(v) for v in raw["decay_volume_length_m_values"]],
            benchmark_points=benchmark_points,
            mc_samples_per_point=int(raw.get("mc_samples_per_point", fallback_mc_samples)),
        )


@dataclass(frozen=True)
class GeometryScanResult:
    shield_length_m: float
    decay_volume_length_m: float
    best_significance: float
    best_mass_mev: float
    best_epsilon: float
    best_signal: float
    best_background: float
    benchmark_signal_total: float
    benchmark_significance_total: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def _with_geometry(
    config: ExperimentConfig, shield_length_m: float, decay_volume_length_m: float, mc_samples_per_point: int
) -> ExperimentConfig:
    beam = BeamConfig(
        beam_energy_gev=config.beam.beam_energy_gev,
        electrons_on_target=config.beam.electrons_on_target,
        target_atomic_number=config.beam.target_atomic_number,
        target_thickness_radiation_lengths=config.beam.target_thickness_radiation_lengths,
        shield_length_m=shield_length_m,
        decay_volume_length_m=decay_volume_length_m,
        run_time_s=config.beam.run_time_s,
    )
    scan = ScanConfig(
        mass_mev_values=config.scan.mass_mev_values,
        epsilon_values=config.scan.epsilon_values,
        mc_samples_per_point=mc_samples_per_point,
        seed=config.scan.seed,
    )
    return ExperimentConfig(
        beam=beam,
        detector=config.detector,
        background=config.background,
        model=config.model,
        scan=scan,
    )


def run_geometry_scan(
    config: ExperimentConfig, grid: GeometryScanGrid
) -> list[GeometryScanResult]:
    rows: list[GeometryScanResult] = []
    for shield_length_m in grid.shield_length_m_values:
        for decay_volume_length_m in grid.decay_volume_length_m_values:
            local_config = _with_geometry(
                config=config,
                shield_length_m=shield_length_m,
                decay_volume_length_m=decay_volume_length_m,
                mc_samples_per_point=grid.mc_samples_per_point,
            )
            engine = SimulationEngine(local_config)
            scan_results = engine.run_scan()
            best = max(scan_results, key=lambda row: row.significance)

            benchmark_signal_total = 0.0
            benchmark_significance_total = 0.0
            for benchmark in grid.benchmark_points:
                point = engine.simulate_point(
                    mass_mev=benchmark.mass_mev, epsilon=benchmark.epsilon
                )
                benchmark_signal_total += point.expected_signal
                benchmark_significance_total += point.significance

            rows.append(
                GeometryScanResult(
                    shield_length_m=shield_length_m,
                    decay_volume_length_m=decay_volume_length_m,
                    best_significance=best.significance,
                    best_mass_mev=best.mass_mev,
                    best_epsilon=best.epsilon,
                    best_signal=best.expected_signal,
                    best_background=best.expected_background,
                    benchmark_signal_total=benchmark_signal_total,
                    benchmark_significance_total=benchmark_significance_total,
                )
            )
    return rows
