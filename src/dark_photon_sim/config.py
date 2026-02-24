from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


def _require(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise KeyError(f"Missing required config key: '{key}'")
    return mapping[key]


def _positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be > 0, got {value}")


def _fraction(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be in [0, 1], got {value}")


@dataclass(frozen=True)
class BeamConfig:
    beam_energy_gev: float
    electrons_on_target: float
    target_atomic_number: int
    target_thickness_radiation_lengths: float
    shield_length_m: float
    decay_volume_length_m: float
    run_time_s: float

    def validate(self) -> None:
        _positive("beam.beam_energy_gev", self.beam_energy_gev)
        _positive("beam.electrons_on_target", self.electrons_on_target)
        _positive("beam.target_atomic_number", float(self.target_atomic_number))
        _positive(
            "beam.target_thickness_radiation_lengths",
            self.target_thickness_radiation_lengths,
        )
        _positive("beam.shield_length_m", self.shield_length_m)
        _positive("beam.decay_volume_length_m", self.decay_volume_length_m)
        _positive("beam.run_time_s", self.run_time_s)


@dataclass(frozen=True)
class DetectorConfig:
    tracker_acceptance: float
    pair_reco_efficiency: float
    cherenkov_electron_efficiency: float
    cherenkov_muon_misid_rate: float
    scintillator_veto_efficiency_muons: float
    scintillator_false_veto_rate: float
    minimum_pair_opening_angle_rad: float
    background_mass_spectrum_beta: float
    background_reference_mass_mev: float

    def validate(self) -> None:
        _fraction("detector.tracker_acceptance", self.tracker_acceptance)
        _fraction("detector.pair_reco_efficiency", self.pair_reco_efficiency)
        _fraction(
            "detector.cherenkov_electron_efficiency",
            self.cherenkov_electron_efficiency,
        )
        _fraction("detector.cherenkov_muon_misid_rate", self.cherenkov_muon_misid_rate)
        _fraction(
            "detector.scintillator_veto_efficiency_muons",
            self.scintillator_veto_efficiency_muons,
        )
        _fraction(
            "detector.scintillator_false_veto_rate",
            self.scintillator_false_veto_rate,
        )
        _positive(
            "detector.minimum_pair_opening_angle_rad",
            self.minimum_pair_opening_angle_rad,
        )
        if self.background_mass_spectrum_beta < 0:
            raise ValueError("detector.background_mass_spectrum_beta must be >= 0")
        _positive(
            "detector.background_reference_mass_mev",
            self.background_reference_mass_mev,
        )


@dataclass(frozen=True)
class BackgroundConfig:
    beam_muon_rate_hz: float
    cosmic_muon_rate_hz: float
    accidental_electron_like_rate_hz: float
    background_uncertainty_fraction: float

    def validate(self) -> None:
        if self.beam_muon_rate_hz < 0:
            raise ValueError("background.beam_muon_rate_hz must be >= 0")
        if self.cosmic_muon_rate_hz < 0:
            raise ValueError("background.cosmic_muon_rate_hz must be >= 0")
        if self.accidental_electron_like_rate_hz < 0:
            raise ValueError("background.accidental_electron_like_rate_hz must be >= 0")
        _fraction(
            "background.background_uncertainty_fraction",
            self.background_uncertainty_fraction,
        )


@dataclass(frozen=True)
class ModelConfig:
    production_norm: float
    production_energy_scale_gev: float
    min_energy_fraction: float
    max_energy_fraction: float
    energy_fraction_shape: float

    def validate(self) -> None:
        _positive("model.production_norm", self.production_norm)
        _positive("model.production_energy_scale_gev", self.production_energy_scale_gev)
        _fraction("model.min_energy_fraction", self.min_energy_fraction)
        _fraction("model.max_energy_fraction", self.max_energy_fraction)
        if self.max_energy_fraction <= self.min_energy_fraction:
            raise ValueError(
                "model.max_energy_fraction must be > model.min_energy_fraction"
            )
        _positive("model.energy_fraction_shape", self.energy_fraction_shape)


@dataclass(frozen=True)
class ScanConfig:
    mass_mev_values: list[float]
    epsilon_values: list[float]
    mc_samples_per_point: int
    seed: int

    def validate(self) -> None:
        if not self.mass_mev_values:
            raise ValueError("scan.mass_mev_values must be non-empty")
        if not self.epsilon_values:
            raise ValueError("scan.epsilon_values must be non-empty")
        for mass in self.mass_mev_values:
            _positive("scan.mass_mev_values[]", mass)
        for epsilon in self.epsilon_values:
            _positive("scan.epsilon_values[]", epsilon)
        if self.mc_samples_per_point < 100:
            raise ValueError("scan.mc_samples_per_point must be >= 100")
        if self.seed < 0:
            raise ValueError("scan.seed must be >= 0")


@dataclass(frozen=True)
class ExperimentConfig:
    beam: BeamConfig
    detector: DetectorConfig
    background: BackgroundConfig
    model: ModelConfig
    scan: ScanConfig

    @staticmethod
    def from_json(path: str | Path) -> "ExperimentConfig":
        config_path = Path(path)
        raw = json.loads(config_path.read_text(encoding="utf-8"))

        beam_raw = _require(raw, "beam")
        detector_raw = _require(raw, "detector")
        background_raw = _require(raw, "background")
        model_raw = _require(raw, "model")
        scan_raw = _require(raw, "scan")

        cfg = ExperimentConfig(
            beam=BeamConfig(
                beam_energy_gev=float(_require(beam_raw, "beam_energy_gev")),
                electrons_on_target=float(_require(beam_raw, "electrons_on_target")),
                target_atomic_number=int(_require(beam_raw, "target_atomic_number")),
                target_thickness_radiation_lengths=float(
                    _require(beam_raw, "target_thickness_radiation_lengths")
                ),
                shield_length_m=float(_require(beam_raw, "shield_length_m")),
                decay_volume_length_m=float(_require(beam_raw, "decay_volume_length_m")),
                run_time_s=float(_require(beam_raw, "run_time_s")),
            ),
            detector=DetectorConfig(
                tracker_acceptance=float(_require(detector_raw, "tracker_acceptance")),
                pair_reco_efficiency=float(
                    _require(detector_raw, "pair_reco_efficiency")
                ),
                cherenkov_electron_efficiency=float(
                    _require(detector_raw, "cherenkov_electron_efficiency")
                ),
                cherenkov_muon_misid_rate=float(
                    _require(detector_raw, "cherenkov_muon_misid_rate")
                ),
                scintillator_veto_efficiency_muons=float(
                    _require(detector_raw, "scintillator_veto_efficiency_muons")
                ),
                scintillator_false_veto_rate=float(
                    _require(detector_raw, "scintillator_false_veto_rate")
                ),
                minimum_pair_opening_angle_rad=float(
                    _require(detector_raw, "minimum_pair_opening_angle_rad")
                ),
                background_mass_spectrum_beta=float(
                    _require(detector_raw, "background_mass_spectrum_beta")
                ),
                background_reference_mass_mev=float(
                    _require(detector_raw, "background_reference_mass_mev")
                ),
            ),
            background=BackgroundConfig(
                beam_muon_rate_hz=float(_require(background_raw, "beam_muon_rate_hz")),
                cosmic_muon_rate_hz=float(
                    _require(background_raw, "cosmic_muon_rate_hz")
                ),
                accidental_electron_like_rate_hz=float(
                    _require(background_raw, "accidental_electron_like_rate_hz")
                ),
                background_uncertainty_fraction=float(
                    _require(background_raw, "background_uncertainty_fraction")
                ),
            ),
            model=ModelConfig(
                production_norm=float(_require(model_raw, "production_norm")),
                production_energy_scale_gev=float(
                    _require(model_raw, "production_energy_scale_gev")
                ),
                min_energy_fraction=float(
                    _require(model_raw, "min_energy_fraction")
                ),
                max_energy_fraction=float(
                    _require(model_raw, "max_energy_fraction")
                ),
                energy_fraction_shape=float(_require(model_raw, "energy_fraction_shape")),
            ),
            scan=ScanConfig(
                mass_mev_values=[float(v) for v in _require(scan_raw, "mass_mev_values")],
                epsilon_values=[float(v) for v in _require(scan_raw, "epsilon_values")],
                mc_samples_per_point=int(_require(scan_raw, "mc_samples_per_point")),
                seed=int(_require(scan_raw, "seed")),
            ),
        )
        cfg.validate()
        return cfg

    def validate(self) -> None:
        self.beam.validate()
        self.detector.validate()
        self.background.validate()
        self.model.validate()
        self.scan.validate()
