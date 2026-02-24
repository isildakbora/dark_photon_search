from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
import math
from pathlib import Path

from .config import BackgroundConfig, ExperimentConfig, ModelConfig, ScanConfig
from .engine import SimulationEngine


@dataclass(frozen=True)
class CalibrationAnchor:
    mass_mev: float
    epsilon_limit: float
    source: str


@dataclass(frozen=True)
class CalibrationProblem:
    target_significance: float
    anchors: list[CalibrationAnchor]
    log10_background_scale_min: float
    log10_background_scale_max: float
    background_scale_steps: int
    calibration_mc_samples_per_point: int
    prior_background_scale_center: float
    prior_background_scale_weight: float

    @staticmethod
    def from_json(path: str | Path) -> "CalibrationProblem":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        anchors: list[CalibrationAnchor] = []
        for row in raw["anchor_points"]:
            anchors.append(
                CalibrationAnchor(
                    mass_mev=float(row["mass_mev"]),
                    epsilon_limit=float(row["epsilon_limit"]),
                    source=str(row["source"]),
                )
            )

        scan_cfg = raw.get("background_scale_scan", {})
        prior_cfg = raw.get("background_scale_prior", {})
        return CalibrationProblem(
            target_significance=float(raw.get("target_significance", 1.64)),
            anchors=anchors,
            log10_background_scale_min=float(scan_cfg.get("log10_min", -3.0)),
            log10_background_scale_max=float(scan_cfg.get("log10_max", 3.0)),
            background_scale_steps=int(scan_cfg.get("steps", 500)),
            calibration_mc_samples_per_point=int(
                raw.get("calibration_mc_samples_per_point", 12000)
            ),
            prior_background_scale_center=float(prior_cfg.get("center", 1.0)),
            prior_background_scale_weight=float(prior_cfg.get("weight", 0.01)),
        )


@dataclass(frozen=True)
class AnchorFitResult:
    mass_mev: float
    epsilon_limit: float
    source: str
    predicted_significance: float
    target_significance: float
    fractional_error: float
    expected_signal: float
    expected_background: float


@dataclass(frozen=True)
class CalibrationSummary:
    production_norm: float
    background_scale: float
    objective_value: float
    target_significance: float
    fit_points: list[AnchorFitResult]

    def to_dict(self) -> dict[str, object]:
        return {
            "production_norm": self.production_norm,
            "background_scale": self.background_scale,
            "objective_value": self.objective_value,
            "target_significance": self.target_significance,
            "fit_points": [asdict(point) for point in self.fit_points],
        }


def _linspace(start: float, stop: float, count: int) -> list[float]:
    if count <= 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + index * step for index in range(count)]


def _build_calibration_engine(
    config: ExperimentConfig, mc_samples_per_point: int
) -> SimulationEngine:
    calibration_scan = ScanConfig(
        mass_mev_values=config.scan.mass_mev_values,
        epsilon_values=config.scan.epsilon_values,
        mc_samples_per_point=mc_samples_per_point,
        seed=config.scan.seed,
    )
    calibration_model = ModelConfig(
        production_norm=1.0,
        production_energy_scale_gev=config.model.production_energy_scale_gev,
        min_energy_fraction=config.model.min_energy_fraction,
        max_energy_fraction=config.model.max_energy_fraction,
        energy_fraction_shape=config.model.energy_fraction_shape,
    )
    calibration_cfg = ExperimentConfig(
        beam=config.beam,
        detector=config.detector,
        background=config.background,
        model=calibration_model,
        scan=calibration_scan,
    )
    return SimulationEngine(calibration_cfg)


def _fit_production_norm(
    target_significance: float,
    signal_coefficients: list[float],
    bg_terms: list[float],
) -> float:
    weighted_sum = 0.0
    weighted_square_sum = 0.0
    for signal_coeff, bg_term in zip(signal_coefficients, bg_terms, strict=True):
        if bg_term <= 0.0:
            continue
        a_i = signal_coeff / bg_term
        weighted_sum += a_i
        weighted_square_sum += a_i * a_i

    if weighted_square_sum <= 0.0:
        return 0.0
    return target_significance * weighted_sum / weighted_square_sum


def calibrate_against_limits(
    config: ExperimentConfig, problem: CalibrationProblem
) -> CalibrationSummary:
    if not problem.anchors:
        raise ValueError("No calibration anchors provided.")
    if problem.target_significance <= 0:
        raise ValueError("target_significance must be > 0")

    engine = _build_calibration_engine(
        config=config, mc_samples_per_point=problem.calibration_mc_samples_per_point
    )

    signal_coefficients: list[float] = []
    base_backgrounds: list[float] = []
    for anchor in problem.anchors:
        result = engine.simulate_point(
            mass_mev=anchor.mass_mev, epsilon=anchor.epsilon_limit
        )
        signal_coefficients.append(max(result.expected_signal, 1e-24))
        base_backgrounds.append(max(result.expected_background, 1e-12))

    best_objective = math.inf
    best_norm = 0.0
    best_bg_scale = 1.0

    center = max(problem.prior_background_scale_center, 1e-9)
    for log10_bg_scale in _linspace(
        problem.log10_background_scale_min,
        problem.log10_background_scale_max,
        problem.background_scale_steps,
    ):
        bg_scale = 10.0 ** log10_bg_scale
        bg_terms: list[float] = []
        for base_b in base_backgrounds:
            scaled_b = bg_scale * base_b
            variance = scaled_b + (config.background.background_uncertainty_fraction * scaled_b) ** 2
            bg_terms.append(math.sqrt(max(variance, 1e-24)))

        norm = _fit_production_norm(
            target_significance=problem.target_significance,
            signal_coefficients=signal_coefficients,
            bg_terms=bg_terms,
        )
        if norm <= 0.0:
            continue

        err_sq = 0.0
        for signal_coeff, bg_term in zip(signal_coefficients, bg_terms, strict=True):
            predicted_z = norm * signal_coeff / bg_term
            delta = (predicted_z / problem.target_significance) - 1.0
            err_sq += delta * delta
        fit_error = err_sq / len(signal_coefficients)

        prior_error = (
            math.log10(bg_scale / center) ** 2 if problem.prior_background_scale_weight > 0 else 0.0
        )
        objective = fit_error + problem.prior_background_scale_weight * prior_error
        if objective < best_objective:
            best_objective = objective
            best_norm = norm
            best_bg_scale = bg_scale

    scaled_backgrounds = [best_bg_scale * value for value in base_backgrounds]
    fit_points: list[AnchorFitResult] = []
    for anchor, signal_coeff, scaled_b in zip(
        problem.anchors, signal_coefficients, scaled_backgrounds, strict=True
    ):
        variance = scaled_b + (config.background.background_uncertainty_fraction * scaled_b) ** 2
        predicted_z = best_norm * signal_coeff / math.sqrt(max(variance, 1e-24))
        fit_points.append(
            AnchorFitResult(
                mass_mev=anchor.mass_mev,
                epsilon_limit=anchor.epsilon_limit,
                source=anchor.source,
                predicted_significance=predicted_z,
                target_significance=problem.target_significance,
                fractional_error=(predicted_z / problem.target_significance) - 1.0,
                expected_signal=best_norm * signal_coeff,
                expected_background=scaled_b,
            )
        )

    return CalibrationSummary(
        production_norm=best_norm,
        background_scale=best_bg_scale,
        objective_value=best_objective,
        target_significance=problem.target_significance,
        fit_points=fit_points,
    )


def apply_calibration(
    config: ExperimentConfig, calibration: CalibrationSummary
) -> ExperimentConfig:
    scaled_background = BackgroundConfig(
        beam_muon_rate_hz=config.background.beam_muon_rate_hz * calibration.background_scale,
        cosmic_muon_rate_hz=config.background.cosmic_muon_rate_hz * calibration.background_scale,
        accidental_electron_like_rate_hz=config.background.accidental_electron_like_rate_hz
        * calibration.background_scale,
        background_uncertainty_fraction=config.background.background_uncertainty_fraction,
    )
    scaled_model = ModelConfig(
        production_norm=calibration.production_norm,
        production_energy_scale_gev=config.model.production_energy_scale_gev,
        min_energy_fraction=config.model.min_energy_fraction,
        max_energy_fraction=config.model.max_energy_fraction,
        energy_fraction_shape=config.model.energy_fraction_shape,
    )
    return ExperimentConfig(
        beam=config.beam,
        detector=config.detector,
        background=scaled_background,
        model=scaled_model,
        scan=config.scan,
    )


def config_to_dict(config: ExperimentConfig) -> dict[str, object]:
    return asdict(config)
