from __future__ import annotations

import math
import random

from .config import BackgroundConfig, BeamConfig, DetectorConfig, ModelConfig

ALPHA_EM = 1.0 / 137.035999084
HBAR_C_GEV_M = 1.973269804e-16
ELECTRON_MASS_GEV = 0.00051099895


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def production_probability(
    epsilon: float,
    mass_mev: float,
    beam: BeamConfig,
    model: ModelConfig,
) -> float:
    mass_gev = max(mass_mev, 1e-6) / 1000.0
    target_factor = (
        beam.target_atomic_number * beam.target_thickness_radiation_lengths / 1000.0
    )
    beam_factor = beam.beam_energy_gev / (beam.beam_energy_gev + mass_gev)
    mass_suppression = math.exp(-mass_gev / model.production_energy_scale_gev)
    epsilon_factor = (epsilon / 1.0e-4) ** 2
    probability = (
        model.production_norm
        * epsilon_factor
        * target_factor
        * beam_factor
        * mass_suppression
    )
    return _clamp01(probability)


def sample_dark_photon_energy_gev(
    rng: random.Random,
    mass_mev: float,
    beam: BeamConfig,
    model: ModelConfig,
) -> float:
    span = model.max_energy_fraction - model.min_energy_fraction
    unit = rng.random() ** (1.0 / model.energy_fraction_shape)
    frac = model.min_energy_fraction + span * unit
    energy_gev = frac * beam.beam_energy_gev
    mass_gev = mass_mev / 1000.0
    return max(1.001 * mass_gev, energy_gev)


def partial_width_to_electron_gev(epsilon: float, mass_mev: float) -> float:
    mass_gev = mass_mev / 1000.0
    threshold = 2.0 * ELECTRON_MASS_GEV
    if mass_gev <= threshold:
        return 0.0
    me2_over_m2 = (ELECTRON_MASS_GEV**2) / (mass_gev**2)
    beta_sq = 1.0 - 4.0 * me2_over_m2
    if beta_sq <= 0.0:
        return 0.0
    beta = math.sqrt(beta_sq)
    return (1.0 / 3.0) * ALPHA_EM * epsilon**2 * mass_gev * beta * (1.0 + 2.0 * me2_over_m2)


def lab_decay_length_m(
    epsilon: float,
    mass_mev: float,
    dark_photon_energy_gev: float,
) -> float:
    width = partial_width_to_electron_gev(epsilon, mass_mev)
    if width <= 0.0:
        return math.inf
    mass_gev = mass_mev / 1000.0
    gamma = dark_photon_energy_gev / max(mass_gev, 1e-12)
    ctau_m = HBAR_C_GEV_M / width
    return gamma * ctau_m


def decay_probability_in_volume(
    epsilon: float,
    mass_mev: float,
    dark_photon_energy_gev: float,
    beam: BeamConfig,
) -> float:
    mean_length = lab_decay_length_m(epsilon, mass_mev, dark_photon_energy_gev)
    if not math.isfinite(mean_length) or mean_length <= 0.0:
        return 0.0
    z0 = beam.shield_length_m
    z1 = beam.shield_length_m + beam.decay_volume_length_m
    p_decay = math.exp(-z0 / mean_length) - math.exp(-z1 / mean_length)
    return _clamp01(p_decay)


def pair_separation_acceptance(
    mass_mev: float,
    dark_photon_energy_gev: float,
    detector: DetectorConfig,
) -> float:
    mass_gev = mass_mev / 1000.0
    opening_angle = 2.0 * mass_gev / max(dark_photon_energy_gev, 1e-12)
    detector_scale = max(detector.minimum_pair_opening_angle_rad, 1e-9)
    acceptance = opening_angle / (opening_angle + detector_scale)
    return _clamp01(acceptance)


def signal_detection_efficiency(
    mass_mev: float,
    dark_photon_energy_gev: float,
    detector: DetectorConfig,
) -> float:
    geometric_eff = pair_separation_acceptance(mass_mev, dark_photon_energy_gev, detector)
    detector_eff = (
        detector.tracker_acceptance
        * detector.pair_reco_efficiency
        * detector.cherenkov_electron_efficiency
        * (1.0 - detector.scintillator_false_veto_rate)
    )
    return _clamp01(geometric_eff * detector_eff)


def expected_background_counts(
    mass_mev: float,
    beam: BeamConfig,
    detector: DetectorConfig,
    background: BackgroundConfig,
) -> float:
    total_muons = (background.beam_muon_rate_hz + background.cosmic_muon_rate_hz) * beam.run_time_s
    muons_after_veto = total_muons * (1.0 - detector.scintillator_veto_efficiency_muons)
    muon_misid = muons_after_veto * detector.cherenkov_muon_misid_rate * detector.tracker_acceptance
    accidental_e_like = (
        background.accidental_electron_like_rate_hz * beam.run_time_s * detector.tracker_acceptance
    )
    base_count = max(0.0, muon_misid + accidental_e_like)
    spectral_factor = (mass_mev / detector.background_reference_mass_mev) ** (
        -detector.background_mass_spectrum_beta
    )
    return max(0.0, base_count * spectral_factor)
