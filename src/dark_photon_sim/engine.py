from __future__ import annotations

from dataclasses import dataclass
import random

from .analysis import approximate_significance
from .config import ExperimentConfig
from .physics import (
    decay_probability_in_volume,
    expected_background_counts,
    production_probability,
    sample_dark_photon_energy_gev,
    signal_detection_efficiency,
)


@dataclass(frozen=True)
class SimulationResult:
    mass_mev: float
    epsilon: float
    production_probability: float
    mean_decay_probability: float
    mean_reco_probability: float
    expected_produced: float
    expected_decays: float
    expected_signal: float
    expected_background: float
    signal_to_background: float
    significance: float


class SimulationEngine:
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.rng = random.Random(config.scan.seed)

    def simulate_point(self, mass_mev: float, epsilon: float) -> SimulationResult:
        mc_samples = self.config.scan.mc_samples_per_point
        p_prod = production_probability(
            epsilon=epsilon,
            mass_mev=mass_mev,
            beam=self.config.beam,
            model=self.config.model,
        )

        decay_accumulator = 0.0
        reco_accumulator = 0.0
        for _ in range(mc_samples):
            dark_photon_energy = sample_dark_photon_energy_gev(
                rng=self.rng,
                mass_mev=mass_mev,
                beam=self.config.beam,
                model=self.config.model,
            )
            p_decay = decay_probability_in_volume(
                epsilon=epsilon,
                mass_mev=mass_mev,
                dark_photon_energy_gev=dark_photon_energy,
                beam=self.config.beam,
            )
            p_detect = signal_detection_efficiency(
                mass_mev=mass_mev,
                dark_photon_energy_gev=dark_photon_energy,
                detector=self.config.detector,
            )
            decay_accumulator += p_decay
            reco_accumulator += p_decay * p_detect

        mean_decay_probability = decay_accumulator / mc_samples
        mean_reco_probability = reco_accumulator / mc_samples

        expected_produced = self.config.beam.electrons_on_target * p_prod
        expected_decays = expected_produced * mean_decay_probability
        expected_signal = expected_produced * mean_reco_probability

        expected_background = expected_background_counts(
            mass_mev=mass_mev,
            beam=self.config.beam,
            detector=self.config.detector,
            background=self.config.background,
        )
        significance = approximate_significance(
            signal=expected_signal,
            background=expected_background,
            background_fractional_uncertainty=self.config.background.background_uncertainty_fraction,
        )
        signal_to_background = (
            expected_signal / expected_background if expected_background > 0.0 else float("inf")
        )

        return SimulationResult(
            mass_mev=mass_mev,
            epsilon=epsilon,
            production_probability=p_prod,
            mean_decay_probability=mean_decay_probability,
            mean_reco_probability=mean_reco_probability,
            expected_produced=expected_produced,
            expected_decays=expected_decays,
            expected_signal=expected_signal,
            expected_background=expected_background,
            signal_to_background=signal_to_background,
            significance=significance,
        )

    def run_scan(self) -> list[SimulationResult]:
        results: list[SimulationResult] = []
        for mass_mev in self.config.scan.mass_mev_values:
            for epsilon in self.config.scan.epsilon_values:
                results.append(self.simulate_point(mass_mev=mass_mev, epsilon=epsilon))
        return results
