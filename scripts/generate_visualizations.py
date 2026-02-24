#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from matplotlib.lines import Line2D
from pathlib import Path
import random
import sys

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.patches import Patch
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from dark_photon_sim.config import ExperimentConfig  # noqa: E402
from dark_photon_sim.engine import SimulationEngine  # noqa: E402
from dark_photon_sim.physics import (  # noqa: E402
    lab_decay_length_m,
    sample_dark_photon_energy_gev,
    signal_detection_efficiency,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate geometry and particle-level toy visualizations."
    )
    parser.add_argument(
        "--config",
        default=str(REPO_ROOT / "configs" / "baseline.json"),
        help="Config JSON path.",
    )
    parser.add_argument("--mass-mev", type=float, default=10.0, help="Dark photon mass [MeV].")
    parser.add_argument("--epsilon", type=float, default=1e-5, help="Kinetic mixing epsilon.")
    parser.add_argument(
        "--n-dark",
        type=int,
        default=4000,
        help="Sampled dark photons for toy event display.",
    )
    parser.add_argument(
        "--n-muons",
        type=int,
        default=2000,
        help="Sampled muon tracks for toy event display.",
    )
    parser.add_argument(
        "--detector-gap",
        type=float,
        default=0.6,
        help="Gap between decay volume and detector plane [m].",
    )
    parser.add_argument(
        "--cherenkov-muon-veto-eff",
        type=float,
        default=0.995,
        help="Cherenkov muon veto efficiency in [0,1].",
    )
    parser.add_argument(
        "--vertex-match-window-m",
        type=float,
        default=0.01,
        help="Vertex matching requirement |x_v| < value [m].",
    )
    parser.add_argument(
        "--aperture-half-width",
        type=float,
        default=0.35,
        help="Plot half-width in x [m].",
    )
    parser.add_argument("--seed", type=int, default=7, help="Random seed.")
    parser.add_argument(
        "--out-prefix",
        default=str(REPO_ROOT / "outputs" / "student_visual"),
        help="Prefix for output files (without extension).",
    )
    return parser.parse_args()


def geometry_positions(config: ExperimentConfig, detector_gap_m: float) -> dict[str, float]:
    target_length = max(0.05, 0.02 * config.beam.target_thickness_radiation_lengths)
    shield_start = target_length
    shield_end = shield_start + config.beam.shield_length_m
    decay_start = shield_end
    decay_end = decay_start + config.beam.decay_volume_length_m
    detector_plane = decay_end + detector_gap_m
    return {
        "target_start": 0.0,
        "target_end": target_length,
        "shield_start": shield_start,
        "shield_end": shield_end,
        "decay_start": decay_start,
        "decay_end": decay_end,
        "detector_plane": detector_plane,
    }


def estimate_pair_vertex(
    x1: float, slope1: float, x2: float, slope2: float, z_detector: float
) -> tuple[float, float]:
    denom = slope1 - slope2
    if abs(denom) < 1e-12:
        return float("nan"), float("nan")
    z_vertex = z_detector - (x1 - x2) / denom
    x_vertex = x1 - slope1 * (z_detector - z_vertex)
    return z_vertex, x_vertex


def build_vertex_matched_pairs(
    candidates: pd.DataFrame, geometry: dict[str, float], vertex_window_m: float
) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame()

    z_detector = float(geometry["detector_plane"])
    z_min = float(geometry["decay_start"])
    z_max = float(geometry["decay_end"])
    z_center = 0.5 * (z_min + z_max)

    positives = candidates[candidates["charge"] > 0].reset_index(drop=True)
    negatives = candidates[candidates["charge"] < 0].reset_index(drop=True)
    potentials: list[dict[str, float | bool | str]] = []

    for _, p_row in positives.iterrows():
        for _, n_row in negatives.iterrows():
            z_v, x_v = estimate_pair_vertex(
                float(p_row["x_hit_m"]),
                float(p_row["slope_rad"]),
                float(n_row["x_hit_m"]),
                float(n_row["slope_rad"]),
                z_detector,
            )
            if not (math.isfinite(z_v) and math.isfinite(x_v)):
                continue
            if not (z_min <= z_v <= z_max):
                continue
            if abs(x_v) > vertex_window_m:
                continue

            theta = abs(math.atan(float(p_row["slope_rad"])) - math.atan(float(n_row["slope_rad"])))
            e1 = max(float(p_row["energy_gev"]), 1e-9)
            e2 = max(float(n_row["energy_gev"]), 1e-9)
            m2 = max(0.0, 2.0 * e1 * e2 * (1.0 - math.cos(theta)))
            mass_mev = 1000.0 * math.sqrt(m2)
            score = abs(x_v) + 0.03 * abs(z_v - z_center)
            true_pair = (
                str(p_row["source"]) == "signal_electron"
                and str(n_row["source"]) == "signal_electron"
                and float(p_row["parent_event_id"]) == float(n_row["parent_event_id"])
            )
            potentials.append(
                {
                    "pos_candidate_id": float(p_row["candidate_id"]),
                    "neg_candidate_id": float(n_row["candidate_id"]),
                    "z_vertex_m": z_v,
                    "x_vertex_m": x_v,
                    "opening_angle_rad": theta,
                    "reco_mass_mev": mass_mev,
                    "score": score,
                    "is_true_signal_pair": bool(true_pair),
                }
            )

    if not potentials:
        return pd.DataFrame()

    potentials_df = pd.DataFrame(potentials).sort_values("score").reset_index(drop=True)
    used_pos: set[float] = set()
    used_neg: set[float] = set()
    rows: list[dict[str, float | bool | str]] = []
    for _, row in potentials_df.iterrows():
        pos_id = float(row["pos_candidate_id"])
        neg_id = float(row["neg_candidate_id"])
        if pos_id in used_pos or neg_id in used_neg:
            continue
        used_pos.add(pos_id)
        used_neg.add(neg_id)
        rows.append(row.to_dict())

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def sample_events(
    config: ExperimentConfig,
    mass_mev: float,
    epsilon: float,
    n_dark_photons: int,
    n_muons: int,
    detector_gap_m: float,
    cherenkov_muon_veto_eff: float,
    vertex_match_window_m: float,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, float], dict[str, float]]:
    rng = random.Random(seed)
    geometry = geometry_positions(config, detector_gap_m=detector_gap_m)
    z_detector = float(geometry["detector_plane"])
    cherenkov_muon_veto_eff = max(0.0, min(1.0, float(cherenkov_muon_veto_eff)))

    signal_rows: list[dict[str, float | bool]] = []
    candidate_rows: list[dict[str, float | str]] = []
    next_candidate_id = 0
    for event_id in range(n_dark_photons):
        energy = sample_dark_photon_energy_gev(
            rng=rng, mass_mev=mass_mev, beam=config.beam, model=config.model
        )
        mean_decay_length = lab_decay_length_m(
            epsilon=epsilon, mass_mev=mass_mev, dark_photon_energy_gev=energy
        )

        if math.isfinite(mean_decay_length) and mean_decay_length > 0:
            sample = max(1e-15, 1.0 - rng.random())
            decay_z = -mean_decay_length * math.log(sample)
        else:
            decay_z = math.inf

        in_decay_volume = (
            math.isfinite(decay_z)
            and geometry["decay_start"] <= decay_z <= geometry["decay_end"]
        )
        opening_angle = 2.0 * (mass_mev / 1000.0) / max(energy, 1e-12)
        opening_angle *= rng.lognormvariate(0.0, 0.20)
        p_detect = signal_detection_efficiency(
            mass_mev=mass_mev,
            dark_photon_energy_gev=energy,
            detector=config.detector,
        )
        detected = in_decay_volume and (rng.random() < p_detect)

        x_plus = float("nan")
        x_minus = float("nan")
        slope_plus = float("nan")
        slope_minus = float("nan")
        e_plus = float("nan")
        e_minus = float("nan")
        if in_decay_volume:
            dz = z_detector - decay_z
            phi = rng.uniform(0.0, 2.0 * math.pi)
            half_angle = 0.5 * opening_angle
            transverse = dz * math.tan(half_angle) * math.cos(phi)
            x_plus = transverse
            x_minus = -transverse
            slope_plus = x_plus / max(dz, 1e-12)
            slope_minus = x_minus / max(dz, 1e-12)
            share = 0.5 + 0.22 * (rng.random() - 0.5)
            e_plus = max(0.001, energy * share * (1.0 + rng.gauss(0.0, 0.03)))
            e_minus = max(0.001, energy * (1.0 - share) * (1.0 + rng.gauss(0.0, 0.03)))

            if detected:
                candidate_rows.append(
                    {
                        "candidate_id": float(next_candidate_id),
                        "source": "signal_electron",
                        "parent_event_id": float(event_id),
                        "charge": 1.0,
                        "x_hit_m": x_plus,
                        "slope_rad": slope_plus,
                        "energy_gev": e_plus,
                    }
                )
                next_candidate_id += 1
                candidate_rows.append(
                    {
                        "candidate_id": float(next_candidate_id),
                        "source": "signal_electron",
                        "parent_event_id": float(event_id),
                        "charge": -1.0,
                        "x_hit_m": x_minus,
                        "slope_rad": slope_minus,
                        "energy_gev": e_minus,
                    }
                )
                next_candidate_id += 1

        signal_rows.append(
            {
                "event_id": float(event_id),
                "energy_gev": energy,
                "mean_decay_length_m": mean_decay_length,
                "decay_z_m": decay_z,
                "opening_angle_rad": opening_angle,
                "in_decay_volume": in_decay_volume,
                "detected": detected,
                "x_plus_at_detector_m": x_plus,
                "x_minus_at_detector_m": x_minus,
                "slope_plus_rad": slope_plus,
                "slope_minus_rad": slope_minus,
                "energy_plus_gev": e_plus,
                "energy_minus_gev": e_minus,
            }
        )

    muon_rows: list[dict[str, float | bool]] = []
    for track_id in range(n_muons):
        x0 = rng.gauss(0.0, 0.02)
        slope = rng.gauss(0.0, 0.015)
        x_detector = x0 + slope * geometry["detector_plane"]
        passed_veto = rng.random() > config.detector.scintillator_veto_efficiency_muons
        cherenkov_rejected = passed_veto and (rng.random() < cherenkov_muon_veto_eff)
        survives_cherenkov = passed_veto and (not cherenkov_rejected)
        misidentified = survives_cherenkov
        fake_charge = 0.0
        fake_energy = float("nan")
        if survives_cherenkov:
            fake_charge = 1.0 if rng.random() < 0.5 else -1.0
            fake_energy = max(0.02, abs(rng.gauss(0.20, 0.07)))
            candidate_rows.append(
                {
                    "candidate_id": float(next_candidate_id),
                    "source": "muon_fake",
                    "parent_event_id": float(-1),
                    "charge": fake_charge,
                    "x_hit_m": x_detector,
                    "slope_rad": slope,
                    "energy_gev": fake_energy,
                }
            )
            next_candidate_id += 1
        muon_rows.append(
            {
                "track_id": float(track_id),
                "x0_m": x0,
                "slope_rad": slope,
                "x_at_detector_m": x_detector,
                "passed_veto": passed_veto,
                "cherenkov_rejected": cherenkov_rejected,
                "survives_cherenkov": survives_cherenkov,
                "misidentified_as_electron": misidentified,
                "fake_charge": fake_charge,
                "fake_energy_gev": fake_energy,
            }
        )

    signal_df = pd.DataFrame(signal_rows)
    muon_df = pd.DataFrame(muon_rows)
    candidates_df = pd.DataFrame(candidate_rows)
    pairs_df = build_vertex_matched_pairs(
        candidates=candidates_df,
        geometry=geometry,
        vertex_window_m=float(vertex_match_window_m),
    )
    point = SimulationEngine(config).simulate_point(mass_mev=mass_mev, epsilon=epsilon)
    n_pairs = float(len(pairs_df))
    n_true_pairs = float(pairs_df["is_true_signal_pair"].sum()) if not pairs_df.empty else 0.0
    stats = {
        "sampled_dark_photons": float(n_dark_photons),
        "sampled_muons": float(n_muons),
        "n_decays_in_volume": float(signal_df["in_decay_volume"].sum()),
        "n_detected_signal": float(signal_df["detected"].sum()),
        "n_muons_passed_veto": float(muon_df["passed_veto"].sum()),
        "n_muons_rejected_cherenkov": float(muon_df["cherenkov_rejected"].sum()),
        "n_muons_after_cherenkov": float(muon_df["survives_cherenkov"].sum()),
        "n_muons_misidentified": float(muon_df["misidentified_as_electron"].sum()),
        "n_electron_candidates_total": float(len(candidates_df)),
        "n_vertex_matched_pairs": n_pairs,
        "n_true_signal_pairs": n_true_pairs,
        "pair_purity": (n_true_pairs / n_pairs) if n_pairs > 0 else 0.0,
        "cherenkov_muon_veto_efficiency": float(cherenkov_muon_veto_eff),
        "vertex_match_window_m": float(vertex_match_window_m),
        "expected_signal_count": point.expected_signal,
        "expected_background_count": point.expected_background,
        "expected_significance": point.significance,
        "reco_mass_mean_mev": (
            float(pairs_df["reco_mass_mev"].mean()) if not pairs_df.empty else 0.0
        ),
        "reco_mass_std_mev": (
            float(pairs_df["reco_mass_mev"].std()) if not pairs_df.empty else 0.0
        ),
    }
    return signal_df, muon_df, candidates_df, pairs_df, stats, geometry


def save_geometry_plot(path: Path, geometry: dict[str, float], aperture_half_width_m: float) -> None:
    fig, ax = plt.subplots(figsize=(12, 3.8))
    ax.add_patch(
        Rectangle(
            (geometry["target_start"], -aperture_half_width_m),
            geometry["target_end"] - geometry["target_start"],
            2.0 * aperture_half_width_m,
            facecolor="#8d6e63",
            alpha=0.35,
            edgecolor="black",
            label="Target",
        )
    )
    ax.add_patch(
        Rectangle(
            (geometry["shield_start"], -aperture_half_width_m),
            geometry["shield_end"] - geometry["shield_start"],
            2.0 * aperture_half_width_m,
            facecolor="#9e9e9e",
            alpha=0.35,
            edgecolor="black",
            label="Shield",
        )
    )
    ax.add_patch(
        Rectangle(
            (geometry["decay_start"], -aperture_half_width_m),
            geometry["decay_end"] - geometry["decay_start"],
            2.0 * aperture_half_width_m,
            facecolor="#90caf9",
            alpha=0.28,
            edgecolor="black",
            label="Decay volume",
        )
    )
    ax.axvline(geometry["detector_plane"], color="#2e7d32", linestyle="--", linewidth=2.0, label="Detector plane")
    ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    ax.set_xlim(geometry["target_start"] - 0.05, geometry["detector_plane"] + 0.2)
    ax.set_ylim(-aperture_half_width_m * 1.3, aperture_half_width_m * 1.3)
    ax.set_xlabel("z [m] (beam direction)")
    ax.set_ylabel("x [m]")
    ax.set_title("Beamline Geometry Schematic")
    ax.grid(alpha=0.20)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_track_plot(
    path: Path,
    signal_df: pd.DataFrame,
    muon_df: pd.DataFrame,
    geometry: dict[str, float],
    aperture_half_width_m: float,
) -> None:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.add_patch(
        Rectangle(
            (geometry["target_start"], -aperture_half_width_m),
            geometry["target_end"] - geometry["target_start"],
            2.0 * aperture_half_width_m,
            facecolor="#8d6e63",
            alpha=0.25,
            edgecolor="none",
        )
    )
    ax.add_patch(
        Rectangle(
            (geometry["shield_start"], -aperture_half_width_m),
            geometry["shield_end"] - geometry["shield_start"],
            2.0 * aperture_half_width_m,
            facecolor="#9e9e9e",
            alpha=0.25,
            edgecolor="none",
        )
    )
    ax.add_patch(
        Rectangle(
            (geometry["decay_start"], -aperture_half_width_m),
            geometry["decay_end"] - geometry["decay_start"],
            2.0 * aperture_half_width_m,
            facecolor="#90caf9",
            alpha=0.18,
            edgecolor="none",
        )
    )
    ax.axvline(geometry["detector_plane"], color="#2e7d32", linestyle="--", linewidth=1.8)

    visible = signal_df[signal_df["in_decay_volume"]].head(300)
    decay_z_points: list[float] = []
    decay_x_points: list[float] = []
    for _, row in visible.iterrows():
        z_decay = float(row["decay_z_m"])
        x_plus = float(row["x_plus_at_detector_m"])
        x_minus = float(row["x_minus_at_detector_m"])
        ax.plot([geometry["target_end"], z_decay], [0.0, 0.0], color="#b9e769", alpha=0.55, linewidth=1.1)
        ax.plot([z_decay, geometry["detector_plane"]], [0.0, x_plus], color="#1565c0", alpha=0.75, linewidth=1.2)
        ax.plot([z_decay, geometry["detector_plane"]], [0.0, x_minus], color="#c62828", alpha=0.75, linewidth=1.2)
        decay_z_points.append(z_decay)
        decay_x_points.append(0.0)

    muon_subset = muon_df.head(250)
    for _, row in muon_subset.iterrows():
        x0 = float(row["x0_m"])
        xdet = float(row["x_at_detector_m"])
        color = "#f57f17" if bool(row["misidentified_as_electron"]) else "#fb8c00"
        alpha = 0.35 if bool(row["misidentified_as_electron"]) else 0.20
        ax.plot([geometry["target_start"], geometry["detector_plane"]], [x0, xdet], color=color, alpha=alpha, linewidth=0.9)

    if decay_z_points:
        ax.scatter(
            decay_z_points,
            decay_x_points,
            color="#00acc1",
            edgecolors="#004d40",
            marker="o",
            s=26,
            linewidths=0.6,
            alpha=0.95,
            zorder=4,
        )

    ax.axhline(aperture_half_width_m, color="black", linestyle=":", linewidth=0.8, alpha=0.6)
    ax.axhline(-aperture_half_width_m, color="black", linestyle=":", linewidth=0.8, alpha=0.6)
    ax.set_xlim(geometry["target_start"] - 0.05, geometry["detector_plane"] + 0.2)
    ax.set_ylim(-aperture_half_width_m * 1.15, aperture_half_width_m * 1.15)
    ax.set_xlabel("z [m] (beam direction)")
    ax.set_ylabel("x [m]")
    ax.set_title("Toy Particle Trajectories (x-z projection)")
    ax.grid(alpha=0.16)
    legend_handles = [
        Patch(facecolor="#8d6e63", alpha=0.25, label="Target"),
        Patch(facecolor="#9e9e9e", alpha=0.25, label="Shield"),
        Patch(facecolor="#90caf9", alpha=0.18, label="Decay volume"),
        Line2D([0], [0], color="#2e7d32", linestyle="--", linewidth=1.8, label="Detector plane"),
        Line2D([0], [0], color="#b9e769", linewidth=1.2, label="A' flight"),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor="#00acc1",
            markeredgecolor="#004d40",
            markersize=6,
            linewidth=0,
            label="A' decay point",
        ),
        Line2D([0], [0], color="#1565c0", linewidth=1.2, label="e+ track"),
        Line2D([0], [0], color="#c62828", linewidth=1.2, label="e- track"),
        Line2D([0], [0], color="#fb8c00", linewidth=1.2, label="Muon track"),
        Line2D([0], [0], color="#f57f17", linewidth=1.2, label="Muon mis-ID"),
    ]
    ax.legend(handles=legend_handles, loc="upper right", ncol=2, fontsize=8, framealpha=0.95)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_distribution_plot(
    path: Path,
    signal_df: pd.DataFrame,
    muon_df: pd.DataFrame,
    geometry: dict[str, float],
) -> None:
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))
    decay_values = signal_df[pd.to_numeric(signal_df["decay_z_m"], errors="coerce").notnull()]["decay_z_m"]
    axs[0, 0].hist(decay_values, bins=35, color="#4fc3f7", alpha=0.8)
    axs[0, 0].axvline(geometry["decay_start"], color="black", linestyle="--", linewidth=1.0)
    axs[0, 0].axvline(geometry["decay_end"], color="black", linestyle="--", linewidth=1.0)
    axs[0, 0].set_xlabel("decay z [m]")
    axs[0, 0].set_ylabel("count")
    axs[0, 0].set_title("Dark-photon decay position distribution")

    opening = signal_df["opening_angle_rad"].values
    axs[0, 1].hist(opening, bins=30, color="#7cb342", alpha=0.85)
    axs[0, 1].set_xlabel("opening angle [rad]")
    axs[0, 1].set_ylabel("count")
    axs[0, 1].set_title("e+/e- opening angle distribution")

    hit_plus = signal_df["x_plus_at_detector_m"].dropna().values
    hit_minus = signal_df["x_minus_at_detector_m"].dropna().values
    mu_hits = muon_df["x_at_detector_m"].values
    axs[1, 0].hist(hit_plus, bins=30, alpha=0.45, label="e+ hits", color="#1565c0")
    axs[1, 0].hist(hit_minus, bins=30, alpha=0.45, label="e- hits", color="#c62828")
    axs[1, 0].hist(mu_hits, bins=30, alpha=0.45, label="muon hits", color="#fb8c00")
    axs[1, 0].set_xlabel("x at detector [m]")
    axs[1, 0].set_ylabel("count")
    axs[1, 0].set_title("Detector hit-position distribution")
    axs[1, 0].legend()

    counts = [
        int(signal_df["in_decay_volume"].sum()),
        int(signal_df["detected"].sum()),
        int(muon_df["passed_veto"].sum()),
        int(muon_df["misidentified_as_electron"].sum()),
    ]
    labels = ["Signal decays", "Detected signal", "Muons past veto", "Muon mis-ID"]
    axs[1, 1].bar(labels, counts, color=["#26a69a", "#1976d2", "#ef6c00", "#ad1457"])
    axs[1, 1].set_title("Toy event category counts")
    axs[1, 1].set_ylabel("count")
    axs[1, 1].tick_params(axis="x", rotation=25)

    for ax in axs.flat:
        ax.grid(alpha=0.18)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_reco_mass_plot(path: Path, pairs_df: pd.DataFrame, target_mass_mev: float) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.2))
    if pairs_df.empty:
        ax.text(
            0.5,
            0.5,
            "No vertex-matched e+e- pairs found.",
            ha="center",
            va="center",
            fontsize=12,
        )
        ax.set_axis_off()
    else:
        true_pairs = pairs_df[pairs_df["is_true_signal_pair"]]
        fake_pairs = pairs_df[~pairs_df["is_true_signal_pair"]]
        if len(fake_pairs) > 0:
            ax.hist(
                fake_pairs["reco_mass_mev"].values,
                bins=45,
                alpha=0.45,
                color="#fb8c00",
                label="Pairs with at least one muon fake",
            )
        if len(true_pairs) > 0:
            ax.hist(
                true_pairs["reco_mass_mev"].values,
                bins=45,
                alpha=0.70,
                color="#1565c0",
                label="True signal pairs (vertex-matched)",
            )
        ax.axvline(
            float(target_mass_mev),
            color="#d32f2f",
            linestyle="--",
            linewidth=1.6,
            label=f"Target mass = {target_mass_mev:.1f} MeV",
        )
        ax.set_xlabel("Reconstructed pair mass [MeV]")
        ax.set_ylabel("Count")
        ax.set_title("Reconstructed e+e- Mass (vertex-matched pairs)")
        ax.grid(alpha=0.2)
        ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    config = ExperimentConfig.from_json(args.config)
    signal_df, muon_df, candidates_df, pairs_df, stats, geometry = sample_events(
        config=config,
        mass_mev=args.mass_mev,
        epsilon=args.epsilon,
        n_dark_photons=args.n_dark,
        n_muons=args.n_muons,
        detector_gap_m=args.detector_gap,
        cherenkov_muon_veto_eff=args.cherenkov_muon_veto_eff,
        vertex_match_window_m=args.vertex_match_window_m,
        seed=args.seed,
    )

    prefix = Path(args.out_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)

    geometry_png = prefix.with_name(prefix.name + "_geometry.png")
    tracks_png = prefix.with_name(prefix.name + "_tracks.png")
    dist_png = prefix.with_name(prefix.name + "_distributions.png")
    mass_png = prefix.with_name(prefix.name + "_reco_mass.png")
    signal_csv = prefix.with_name(prefix.name + "_signal_events.csv")
    muon_csv = prefix.with_name(prefix.name + "_muon_tracks.csv")
    candidate_csv = prefix.with_name(prefix.name + "_electron_candidates.csv")
    pair_csv = prefix.with_name(prefix.name + "_vertex_pairs.csv")
    stats_json = prefix.with_name(prefix.name + "_stats.json")

    save_geometry_plot(geometry_png, geometry, args.aperture_half_width)
    save_track_plot(tracks_png, signal_df, muon_df, geometry, args.aperture_half_width)
    save_distribution_plot(dist_png, signal_df, muon_df, geometry)
    save_reco_mass_plot(mass_png, pairs_df, target_mass_mev=args.mass_mev)
    signal_df.to_csv(signal_csv, index=False)
    muon_df.to_csv(muon_csv, index=False)
    candidates_df.to_csv(candidate_csv, index=False)
    pairs_df.to_csv(pair_csv, index=False)
    stats_json.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    print(f"Saved geometry schematic: {geometry_png.resolve()}")
    print(f"Saved track overlay: {tracks_png.resolve()}")
    print(f"Saved distribution panel: {dist_png.resolve()}")
    print(f"Saved reconstructed mass plot: {mass_png.resolve()}")
    print(f"Saved signal events CSV: {signal_csv.resolve()}")
    print(f"Saved muon tracks CSV: {muon_csv.resolve()}")
    print(f"Saved electron candidate CSV: {candidate_csv.resolve()}")
    print(f"Saved vertex-matched pairs CSV: {pair_csv.resolve()}")
    print(f"Saved stats JSON: {stats_json.resolve()}")


if __name__ == "__main__":
    main()
