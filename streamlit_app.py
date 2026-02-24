#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import asdict
import json
import math
from pathlib import Path
import random
import sys
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
import numpy as np
import pandas as pd
import streamlit as st

from dark_photon_sim.calibration import (
    CalibrationAnchor,
    CalibrationProblem,
    apply_calibration,
    calibrate_against_limits,
    config_to_dict,
)
from dark_photon_sim.config import (
    BackgroundConfig,
    BeamConfig,
    DetectorConfig,
    ExperimentConfig,
    ModelConfig,
    ScanConfig,
)
from dark_photon_sim.engine import SimulationEngine
from dark_photon_sim.geometry import BenchmarkPoint, GeometryScanGrid, run_geometry_scan
from dark_photon_sim.physics import (
    lab_decay_length_m,
    sample_dark_photon_energy_gev,
    signal_detection_efficiency,
)

try:
    import plotly.express as px
    import plotly.graph_objects as go

    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False


def parse_float_list(raw: str) -> list[float]:
    parts = raw.replace("\n", ",").split(",")
    values: list[float] = []
    for token in parts:
        token = token.strip()
        if not token:
            continue
        values.append(float(token))
    if not values:
        raise ValueError("List input cannot be empty.")
    return values


def parse_benchmark_points(raw: str) -> list[BenchmarkPoint]:
    rows = [line.strip() for line in raw.strip().splitlines() if line.strip()]
    points: list[BenchmarkPoint] = []
    for row in rows:
        chunks = [part.strip() for part in row.split(",")]
        if len(chunks) < 2:
            raise ValueError(
                "Benchmark lines must be in 'mass_mev, epsilon' format."
            )
        points.append(BenchmarkPoint(mass_mev=float(chunks[0]), epsilon=float(chunks[1])))
    return points


def fmt_values(values: Iterable[float]) -> str:
    return ", ".join(f"{value:g}" for value in values)


def load_config(path: Path) -> ExperimentConfig:
    return ExperimentConfig.from_json(path)


def result_rows_to_dataframe(rows: list[object]) -> pd.DataFrame:
    return pd.DataFrame([asdict(row) for row in rows])


def render_heatmap(
    df: pd.DataFrame,
    value_col: str,
    title: str,
    rich_mode: bool,
    x_label: str,
    y_label: str,
) -> None:
    pivot = df.pivot(index="epsilon", columns="mass_mev", values=value_col)
    pivot = pivot.sort_index()
    x_values = np.array(pivot.columns, dtype=float)
    y_values = np.array(pivot.index, dtype=float)
    z_values = np.array(pivot.values, dtype=float)
    z_min = float(np.nanmin(z_values))
    z_max = float(np.nanmax(z_values))
    contour_levels = (
        np.linspace(z_min, z_max, 10)
        if z_max > z_min
        else np.array([z_min], dtype=float)
    )

    if rich_mode and HAS_PLOTLY:
        if value_col == "significance":
            figure = go.Figure()
            figure.add_trace(
                go.Heatmap(
                    x=x_values,
                    y=y_values,
                    z=z_values,
                    colorscale="Viridis",
                    zsmooth="best",
                    colorbar={"title": value_col},
                )
            )
            if z_max > z_min:
                figure.add_trace(
                    go.Contour(
                        x=x_values,
                        y=y_values,
                        z=z_values,
                        contours={
                            "start": float(contour_levels[0]),
                            "end": float(contour_levels[-1]),
                            "size": float((contour_levels[-1] - contour_levels[0]) / 9.0),
                            "coloring": "none",
                            "showlabels": True,
                        },
                        line={"color": "white", "width": 1.1},
                        showscale=False,
                    )
                )
            figure.update_layout(
                title=title,
                xaxis_title=x_label,
                yaxis_title=y_label,
                yaxis_type="log",
            )
        else:
            figure = px.imshow(
                z_values,
                x=[f"{mass:.0f}" for mass in pivot.columns],
                y=[f"{eps:.1e}" for eps in pivot.index],
                labels=dict(x=x_label, y=y_label, color=value_col),
                color_continuous_scale="Viridis",
                aspect="auto",
                title=title,
            )
        st.plotly_chart(figure, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(10, 5))
        if value_col == "significance":
            x_grid, y_grid = np.meshgrid(x_values, y_values)
            heat = ax.contourf(x_grid, y_grid, z_values, levels=180, cmap="viridis")
            if z_max > z_min:
                lines = ax.contour(
                    x_grid,
                    y_grid,
                    z_values,
                    levels=contour_levels,
                    colors="white",
                    linewidths=0.8,
                    alpha=0.9,
                )
                ax.clabel(lines, fmt="%.2f", fontsize=7, inline=True)
            ax.set_yscale("log")
            ax.set_xticks(x_values)
            ax.set_xticklabels([f"{mass:.0f}" for mass in x_values], rotation=45)
            ax.set_yticks(y_values)
            ax.set_yticklabels([f"{eps:.1e}" for eps in y_values])
            fig.colorbar(heat, ax=ax, label=value_col)
        else:
            image = ax.imshow(z_values, origin="lower", aspect="auto", cmap="viridis")
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_xticklabels([f"{mass:.0f}" for mass in pivot.columns], rotation=45)
            ax.set_yticks(range(len(pivot.index)))
            ax.set_yticklabels([f"{eps:.1e}" for eps in pivot.index])
            fig.colorbar(image, ax=ax, label=value_col)
        ax.set_title(title)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        fig.tight_layout()
        st.pyplot(fig)


def _geometry_positions(config: ExperimentConfig, detector_gap_m: float) -> dict[str, float]:
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


def _estimate_pair_vertex(
    x1: float, slope1: float, x2: float, slope2: float, z_detector: float
) -> tuple[float, float]:
    denom = slope1 - slope2
    if abs(denom) < 1e-12:
        return float("nan"), float("nan")
    z_vertex = z_detector - (x1 - x2) / denom
    x_vertex = x1 - slope1 * (z_detector - z_vertex)
    return z_vertex, x_vertex


def _build_vertex_matched_pairs(
    candidates: pd.DataFrame,
    geometry: dict[str, float],
    vertex_window_m: float,
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

    for i, p_row in positives.iterrows():
        for j, n_row in negatives.iterrows():
            z_v, x_v = _estimate_pair_vertex(
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
                    "pos_source": str(p_row["source"]),
                    "neg_source": str(n_row["source"]),
                    "pos_parent_event_id": float(p_row["parent_event_id"]),
                    "neg_parent_event_id": float(n_row["parent_event_id"]),
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


def sample_visual_events(
    config: ExperimentConfig,
    mass_mev: float,
    epsilon: float,
    n_dark_photons: int,
    n_muons: int,
    detector_gap_m: float,
    cherenkov_muon_veto_efficiency: float,
    vertex_match_window_m: float,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, float], dict[str, float]]:
    rng = random.Random(seed)
    geometry = _geometry_positions(config, detector_gap_m=detector_gap_m)
    z_detector = float(geometry["detector_plane"])
    cherenkov_muon_veto_efficiency = max(0.0, min(1.0, float(cherenkov_muon_veto_efficiency)))

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
                        "true_vertex_z_m": decay_z,
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
                        "true_vertex_z_m": decay_z,
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
        cherenkov_rejected = passed_veto and (rng.random() < cherenkov_muon_veto_efficiency)
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
                    "true_vertex_z_m": float("nan"),
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
    pairs_df = _build_vertex_matched_pairs(
        candidates=candidates_df,
        geometry=geometry,
        vertex_window_m=float(vertex_match_window_m),
    )

    point = SimulationEngine(config).simulate_point(mass_mev=mass_mev, epsilon=epsilon)
    n_pairs = float(len(pairs_df))
    n_true_pairs = (
        float(pairs_df["is_true_signal_pair"].sum()) if (not pairs_df.empty) else 0.0
    )
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
        "vertex_match_window_m": float(vertex_match_window_m),
        "cherenkov_muon_veto_efficiency": float(cherenkov_muon_veto_efficiency),
        "expected_signal_count": point.expected_signal,
        "expected_background_count": point.expected_background,
        "expected_significance": point.significance,
        "reco_mass_mean_mev": (
            float(pairs_df["reco_mass_mev"].mean()) if (not pairs_df.empty) else 0.0
        ),
        "reco_mass_std_mev": (
            float(pairs_df["reco_mass_mev"].std()) if (not pairs_df.empty) else 0.0
        ),
    }
    return signal_df, muon_df, candidates_df, pairs_df, stats, geometry


def draw_geometry_schematic(
    geometry: dict[str, float], aperture_half_width_m: float
) -> plt.Figure:
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
    ax.axvline(
        geometry["detector_plane"],
        color="#2e7d32",
        linestyle="--",
        linewidth=2.0,
        label="Detector plane",
    )
    ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    ax.set_xlim(geometry["target_start"] - 0.05, geometry["detector_plane"] + 0.2)
    ax.set_ylim(-aperture_half_width_m * 1.3, aperture_half_width_m * 1.3)
    ax.set_xlabel("z [m] (beam direction)")
    ax.set_ylabel("x [m]")
    ax.set_title("Beamline Geometry Schematic")
    ax.grid(alpha=0.20)
    ax.legend(loc="upper right")
    fig.tight_layout()
    return fig


def draw_particle_tracks(
    signal_df: pd.DataFrame,
    muon_df: pd.DataFrame,
    geometry: dict[str, float],
    aperture_half_width_m: float,
    max_signal_tracks: int,
    max_muon_tracks: int,
) -> plt.Figure:
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

    visible = signal_df[signal_df["in_decay_volume"]].head(max_signal_tracks)
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

    muon_subset = muon_df.head(max_muon_tracks)
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
    return fig


def draw_particle_distributions(
    signal_df: pd.DataFrame,
    muon_df: pd.DataFrame,
    geometry: dict[str, float],
) -> plt.Figure:
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))

    decay_values = signal_df[np.isfinite(signal_df["decay_z_m"])]["decay_z_m"]
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

    hits = []
    hit_plus = signal_df["x_plus_at_detector_m"].dropna().values
    hit_minus = signal_df["x_minus_at_detector_m"].dropna().values
    if len(hit_plus) > 0:
        hits.append(("e+ hits", hit_plus, "#1565c0"))
    if len(hit_minus) > 0:
        hits.append(("e- hits", hit_minus, "#c62828"))
    mu_hits = muon_df["x_at_detector_m"].values
    hits.append(("muon hits", mu_hits, "#fb8c00"))
    for label, values, color in hits:
        axs[1, 0].hist(values, bins=30, alpha=0.45, label=label, color=color)
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
    return fig


def draw_reconstructed_mass_histogram(
    pairs_df: pd.DataFrame,
    target_mass_mev: float,
) -> plt.Figure:
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
        return fig

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
    return fig


def draw_sidebar_config(base_config: ExperimentConfig) -> ExperimentConfig:
    st.sidebar.header("Global Assumptions")
    st.sidebar.caption("These values are shared by all tabs.")

    with st.sidebar.expander("Beam + Geometry", expanded=True):
        beam_energy_gev = st.number_input(
            "Beam energy (GeV)",
            min_value=0.01,
            max_value=20.0,
            value=float(base_config.beam.beam_energy_gev),
            step=0.01,
        )
        electrons_on_target = st.number_input(
            "Electrons on target",
            min_value=1e6,
            max_value=1e20,
            value=float(base_config.beam.electrons_on_target),
            format="%.3e",
        )
        target_atomic_number = st.number_input(
            "Target atomic number Z",
            min_value=1,
            max_value=118,
            value=int(base_config.beam.target_atomic_number),
            step=1,
        )
        target_thickness = st.number_input(
            "Target thickness (X0)",
            min_value=0.1,
            max_value=50.0,
            value=float(base_config.beam.target_thickness_radiation_lengths),
            step=0.1,
        )
        shield_length_m = st.number_input(
            "Shield length (m)",
            min_value=0.1,
            max_value=20.0,
            value=float(base_config.beam.shield_length_m),
            step=0.1,
        )
        decay_volume_length_m = st.number_input(
            "Decay volume length (m)",
            min_value=0.1,
            max_value=30.0,
            value=float(base_config.beam.decay_volume_length_m),
            step=0.1,
        )
        run_time_s = st.number_input(
            "Run time (s)",
            min_value=100.0,
            max_value=1e8,
            value=float(base_config.beam.run_time_s),
            step=100.0,
        )

    with st.sidebar.expander("Detector + PID", expanded=False):
        tracker_acceptance = st.slider(
            "Tracker acceptance", 0.0, 1.0, float(base_config.detector.tracker_acceptance), 0.01
        )
        pair_reco_eff = st.slider(
            "Pair reconstruction efficiency",
            0.0,
            1.0,
            float(base_config.detector.pair_reco_efficiency),
            0.01,
        )
        cherenkov_e_eff = st.slider(
            "Cherenkov electron efficiency",
            0.0,
            1.0,
            float(base_config.detector.cherenkov_electron_efficiency),
            0.01,
        )
        cherenkov_mu_misid = st.number_input(
            "Cherenkov muon mis-ID rate",
            min_value=0.0,
            max_value=1.0,
            value=float(base_config.detector.cherenkov_muon_misid_rate),
            step=0.001,
            format="%.4f",
        )
        scint_veto_mu = st.slider(
            "Scintillator veto efficiency (muons)",
            0.0,
            1.0,
            float(base_config.detector.scintillator_veto_efficiency_muons),
            0.01,
        )
        scint_false_veto = st.number_input(
            "Scintillator false veto rate",
            min_value=0.0,
            max_value=1.0,
            value=float(base_config.detector.scintillator_false_veto_rate),
            step=0.001,
            format="%.4f",
        )
        min_opening_angle = st.number_input(
            "Minimum opening angle (rad)",
            min_value=1e-5,
            max_value=1.0,
            value=float(base_config.detector.minimum_pair_opening_angle_rad),
            step=0.001,
            format="%.5f",
        )
        bkg_mass_beta = st.number_input(
            "Background mass spectrum beta",
            min_value=0.0,
            max_value=5.0,
            value=float(base_config.detector.background_mass_spectrum_beta),
            step=0.05,
        )
        bkg_ref_mass = st.number_input(
            "Background reference mass (MeV)",
            min_value=0.1,
            max_value=10000.0,
            value=float(base_config.detector.background_reference_mass_mev),
            step=1.0,
        )

    with st.sidebar.expander("Background + Model", expanded=False):
        beam_muon_rate = st.number_input(
            "Beam muon rate (Hz)",
            min_value=0.0,
            max_value=1e7,
            value=float(base_config.background.beam_muon_rate_hz),
            step=1.0,
        )
        cosmic_muon_rate = st.number_input(
            "Cosmic muon rate (Hz)",
            min_value=0.0,
            max_value=1e6,
            value=float(base_config.background.cosmic_muon_rate_hz),
            step=1.0,
        )
        accidental_rate = st.number_input(
            "Accidental electron-like rate (Hz)",
            min_value=0.0,
            max_value=1e6,
            value=float(base_config.background.accidental_electron_like_rate_hz),
            step=0.01,
        )
        bkg_unc = st.slider(
            "Background fractional uncertainty",
            0.0,
            1.0,
            float(base_config.background.background_uncertainty_fraction),
            0.01,
        )
        production_norm = st.number_input(
            "Production normalization",
            min_value=1e-20,
            max_value=1e20,
            value=float(base_config.model.production_norm),
            format="%.3e",
        )
        prod_e_scale = st.number_input(
            "Production energy scale (GeV)",
            min_value=0.001,
            max_value=20.0,
            value=float(base_config.model.production_energy_scale_gev),
            step=0.01,
        )
        min_energy_frac = st.slider(
            "Min dark-photon energy fraction",
            0.0,
            0.99,
            float(base_config.model.min_energy_fraction),
            0.01,
        )
        max_energy_frac = st.slider(
            "Max dark-photon energy fraction",
            0.01,
            1.0,
            float(base_config.model.max_energy_fraction),
            0.01,
        )
        energy_shape = st.number_input(
            "Energy fraction shape parameter",
            min_value=0.1,
            max_value=10.0,
            value=float(base_config.model.energy_fraction_shape),
            step=0.1,
        )

    with st.sidebar.expander("Scan Grid", expanded=True):
        masses_raw = st.text_area(
            "Masses (MeV), comma/newline separated",
            value=fmt_values(base_config.scan.mass_mev_values),
            height=90,
        )
        eps_raw = st.text_area(
            "Epsilon values, comma/newline separated",
            value=fmt_values(base_config.scan.epsilon_values),
            height=90,
        )
        mc_samples = st.number_input(
            "MC samples per point",
            min_value=100,
            max_value=500000,
            value=int(base_config.scan.mc_samples_per_point),
            step=100,
        )
        seed = st.number_input(
            "Random seed",
            min_value=0,
            max_value=999999,
            value=int(base_config.scan.seed),
            step=1,
        )

    mass_values = parse_float_list(masses_raw)
    epsilon_values = parse_float_list(eps_raw)

    config = ExperimentConfig(
        beam=BeamConfig(
            beam_energy_gev=beam_energy_gev,
            electrons_on_target=electrons_on_target,
            target_atomic_number=int(target_atomic_number),
            target_thickness_radiation_lengths=target_thickness,
            shield_length_m=shield_length_m,
            decay_volume_length_m=decay_volume_length_m,
            run_time_s=run_time_s,
        ),
        detector=DetectorConfig(
            tracker_acceptance=tracker_acceptance,
            pair_reco_efficiency=pair_reco_eff,
            cherenkov_electron_efficiency=cherenkov_e_eff,
            cherenkov_muon_misid_rate=cherenkov_mu_misid,
            scintillator_veto_efficiency_muons=scint_veto_mu,
            scintillator_false_veto_rate=scint_false_veto,
            minimum_pair_opening_angle_rad=min_opening_angle,
            background_mass_spectrum_beta=bkg_mass_beta,
            background_reference_mass_mev=bkg_ref_mass,
        ),
        background=BackgroundConfig(
            beam_muon_rate_hz=beam_muon_rate,
            cosmic_muon_rate_hz=cosmic_muon_rate,
            accidental_electron_like_rate_hz=accidental_rate,
            background_uncertainty_fraction=bkg_unc,
        ),
        model=ModelConfig(
            production_norm=production_norm,
            production_energy_scale_gev=prod_e_scale,
            min_energy_fraction=min_energy_frac,
            max_energy_fraction=max_energy_frac,
            energy_fraction_shape=energy_shape,
        ),
        scan=ScanConfig(
            mass_mev_values=mass_values,
            epsilon_values=epsilon_values,
            mc_samples_per_point=int(mc_samples),
            seed=int(seed),
        ),
    )
    config.validate()
    return config


def scan_tab(config: ExperimentConfig, rich_mode: bool) -> None:
    st.subheader("Interactive Sensitivity Scan")
    st.caption("Change assumptions in the sidebar, then run the scan.")

    top_n = st.slider("Top points to show", min_value=3, max_value=30, value=10, step=1)
    run = st.button("Run Scan", type="primary")

    if not run:
        st.info("Press 'Run Scan' to generate results.")
        return

    with st.spinner("Running dark-photon parameter scan..."):
        engine = SimulationEngine(config)
        results = engine.run_scan()
        df = result_rows_to_dataframe(results)
        df = df.sort_values(by="significance", ascending=False).reset_index(drop=True)

    best = df.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Best significance", f"{best['significance']:.3f}")
    col2.metric("Best mass (MeV)", f"{best['mass_mev']:.1f}")
    col3.metric("Best epsilon", f"{best['epsilon']:.2e}")
    col4.metric("Best S/B", f"{best['signal_to_background']:.2e}")

    st.markdown("### Top Points")
    st.dataframe(df.head(top_n), use_container_width=True)
    st.download_button(
        "Download scan results CSV",
        data=df.to_csv(index=False),
        file_name="scan_results_student_run.csv",
        mime="text/csv",
    )

    st.markdown("### Heatmaps")
    render_heatmap(
        df=df,
        value_col="significance",
        title="Approximate Significance",
        rich_mode=rich_mode,
        x_label="Mass [MeV]",
        y_label="epsilon",
    )
    render_heatmap(
        df=df,
        value_col="expected_signal",
        title="Expected Signal Counts",
        rich_mode=rich_mode,
        x_label="Mass [MeV]",
        y_label="epsilon",
    )
    render_heatmap(
        df=df,
        value_col="signal_to_background",
        title="Signal-to-Background (S/B)",
        rich_mode=rich_mode,
        x_label="Mass [MeV]",
        y_label="epsilon",
    )

    if rich_mode:
        st.markdown("### Detailed Diagnostics")
        mass_pick = st.selectbox(
            "Mass for epsilon trend",
            options=sorted(df["mass_mev"].unique()),
            format_func=lambda item: f"{item:.1f} MeV",
        )
        eps_pick = st.selectbox(
            "Epsilon for mass trend",
            options=sorted(df["epsilon"].unique()),
            format_func=lambda item: f"{item:.2e}",
        )
        mass_slice = df[df["mass_mev"] == mass_pick].sort_values("epsilon")
        eps_slice = df[df["epsilon"] == eps_pick].sort_values("mass_mev")

        c1, c2 = st.columns(2)
        with c1:
            fig1, ax1 = plt.subplots(figsize=(5.5, 3.8))
            ax1.plot(mass_slice["epsilon"], mass_slice["significance"], marker="o")
            ax1.set_xscale("log")
            ax1.set_xlabel("epsilon")
            ax1.set_ylabel("significance")
            ax1.set_title(f"Significance vs epsilon at {mass_pick:.1f} MeV")
            ax1.grid(alpha=0.2)
            st.pyplot(fig1)
        with c2:
            fig2, ax2 = plt.subplots(figsize=(5.5, 3.8))
            ax2.plot(eps_slice["mass_mev"], eps_slice["significance"], marker="o")
            ax2.set_xlabel("mass [MeV]")
            ax2.set_ylabel("significance")
            ax2.set_title(f"Significance vs mass at epsilon={eps_pick:.2e}")
            ax2.grid(alpha=0.2)
            st.pyplot(fig2)

        if HAS_PLOTLY:
            scatter = px.scatter(
                df,
                x="expected_background",
                y="expected_signal",
                color="significance",
                hover_data=["mass_mev", "epsilon", "signal_to_background"],
                title="Signal vs background landscape",
                color_continuous_scale="Turbo",
                log_x=True,
                log_y=True,
            )
            st.plotly_chart(scatter, use_container_width=True)


def geometry_tab(config: ExperimentConfig, rich_mode: bool) -> None:
    st.subheader("Geometry Development Lab")
    st.caption("Explore shield and decay volume tradeoffs while keeping detector assumptions fixed.")

    c1, c2, c3 = st.columns(3)
    with c1:
        shield_start = st.number_input("Shield start (m)", 0.1, 20.0, 1.0, 0.1)
        shield_stop = st.number_input("Shield stop (m)", 0.2, 30.0, 4.0, 0.1)
        shield_step = st.number_input("Shield step (m)", 0.1, 5.0, 0.5, 0.1)
    with c2:
        decay_start = st.number_input("Decay start (m)", 0.1, 20.0, 1.0, 0.1)
        decay_stop = st.number_input("Decay stop (m)", 0.2, 40.0, 8.0, 0.1)
        decay_step = st.number_input("Decay step (m)", 0.1, 5.0, 0.5, 0.1)
    with c3:
        metric = st.selectbox(
            "Ranking metric",
            options=["best_significance", "benchmark_significance_total"],
            index=0,
        )
        geometry_mc_samples = st.number_input(
            "Geometry MC samples / point",
            min_value=100,
            max_value=100000,
            value=min(3000, int(config.scan.mc_samples_per_point)),
            step=100,
        )

    benchmark_default = "10, 1e-5\n30, 3e-6\n80, 3e-6"
    benchmark_raw = st.text_area(
        "Benchmark points (one per line: mass_mev, epsilon)",
        value=benchmark_default,
        height=90,
    )

    if st.button("Run Geometry Optimization", type="primary"):
        try:
            shield_values = np.arange(shield_start, shield_stop + 1e-9, shield_step).tolist()
            decay_values = np.arange(decay_start, decay_stop + 1e-9, decay_step).tolist()
            benchmarks = parse_benchmark_points(benchmark_raw)
            grid = GeometryScanGrid(
                shield_length_m_values=[float(x) for x in shield_values],
                decay_volume_length_m_values=[float(x) for x in decay_values],
                benchmark_points=benchmarks,
                mc_samples_per_point=int(geometry_mc_samples),
            )
        except ValueError as exc:
            st.error(f"Input error: {exc}")
            return

        with st.spinner("Scanning geometry grid..."):
            rows = run_geometry_scan(config, grid)
            df = pd.DataFrame([row.to_dict() for row in rows])
            df = df.sort_values(by=metric, ascending=False).reset_index(drop=True)

        best = df.iloc[0]
        m1, m2, m3 = st.columns(3)
        m1.metric("Best shield (m)", f"{best['shield_length_m']:.2f}")
        m2.metric("Best decay volume (m)", f"{best['decay_volume_length_m']:.2f}")
        m3.metric("Best metric value", f"{best[metric]:.3f}")

        st.dataframe(df.head(15), use_container_width=True)
        st.download_button(
            "Download geometry CSV",
            data=df.to_csv(index=False),
            file_name="geometry_optimization_student_run.csv",
            mime="text/csv",
        )

        pivot = df.pivot(index="decay_volume_length_m", columns="shield_length_m", values=metric)
        pivot = pivot.sort_index()
        if rich_mode and HAS_PLOTLY:
            fig = px.imshow(
                pivot.values,
                x=[f"{value:.2f}" for value in pivot.columns],
                y=[f"{value:.2f}" for value in pivot.index],
                labels=dict(x="shield length [m]", y="decay length [m]", color=metric),
                color_continuous_scale="Plasma",
                title=f"Geometry heatmap: {metric}",
                aspect="auto",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            fig, ax = plt.subplots(figsize=(8, 5))
            image = ax.imshow(pivot.values, origin="lower", aspect="auto", cmap="plasma")
            ax.set_title(f"Geometry heatmap: {metric}")
            ax.set_xlabel("shield length [m]")
            ax.set_ylabel("decay length [m]")
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_xticklabels([f"{value:.2f}" for value in pivot.columns], rotation=45)
            ax.set_yticks(range(len(pivot.index)))
            ax.set_yticklabels([f"{value:.2f}" for value in pivot.index])
            fig.colorbar(image, ax=ax, label=metric)
            fig.tight_layout()
            st.pyplot(fig)


def calibration_tab(config: ExperimentConfig, rich_mode: bool) -> None:
    st.subheader("Calibration Lab")
    st.caption("Fit production normalization and global background scale to contour anchors.")

    anchors_default = "10, 1e-5, anchor-1\n20, 8e-6, anchor-2\n30, 5e-6, anchor-3"
    anchor_raw = st.text_area(
        "Anchor points (mass_mev, epsilon_limit, label)",
        value=anchors_default,
        height=120,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        target_significance = st.number_input("Target significance", 0.1, 10.0, 1.64, 0.01)
        calibration_samples = st.number_input(
            "Calibration MC samples / point",
            min_value=100,
            max_value=200000,
            value=max(500, int(config.scan.mc_samples_per_point)),
            step=100,
        )
    with c2:
        log_min = st.number_input("log10 background scale min", -8.0, 2.0, -4.0, 0.1)
        log_max = st.number_input("log10 background scale max", -2.0, 8.0, 2.0, 0.1)
        bg_steps = st.number_input("Background scale scan steps", 10, 4000, 500, 10)
    with c3:
        prior_center = st.number_input("Background prior center", 1e-6, 1e6, 1.0, format="%.3e")
        prior_weight = st.number_input("Background prior weight", 0.0, 10.0, 0.03, 0.01)

    if st.button("Run Calibration", type="primary"):
        try:
            anchors: list[CalibrationAnchor] = []
            for line in [item for item in anchor_raw.splitlines() if item.strip()]:
                parts = [x.strip() for x in line.split(",")]
                if len(parts) < 2:
                    raise ValueError(
                        "Each anchor must include at least mass_mev and epsilon_limit."
                    )
                label = parts[2] if len(parts) > 2 else "user-anchor"
                anchors.append(
                    CalibrationAnchor(
                        mass_mev=float(parts[0]),
                        epsilon_limit=float(parts[1]),
                        source=label,
                    )
                )
            if not anchors:
                raise ValueError("Provide at least one anchor.")
        except ValueError as exc:
            st.error(f"Input error: {exc}")
            return

        problem = CalibrationProblem(
            target_significance=float(target_significance),
            anchors=anchors,
            log10_background_scale_min=float(log_min),
            log10_background_scale_max=float(log_max),
            background_scale_steps=int(bg_steps),
            calibration_mc_samples_per_point=int(calibration_samples),
            prior_background_scale_center=float(prior_center),
            prior_background_scale_weight=float(prior_weight),
        )

        with st.spinner("Calibrating model..."):
            summary = calibrate_against_limits(config, problem)
            calibrated = apply_calibration(config, summary)
            fit_df = pd.DataFrame([asdict(row) for row in summary.fit_points])

        m1, m2, m3 = st.columns(3)
        m1.metric("Fitted production_norm", f"{summary.production_norm:.3e}")
        m2.metric("Fitted background scale", f"{summary.background_scale:.3e}")
        m3.metric("Objective", f"{summary.objective_value:.3e}")

        st.dataframe(fit_df, use_container_width=True)
        st.download_button(
            "Download calibration summary JSON",
            data=json.dumps(summary.to_dict(), indent=2),
            file_name="calibration_summary_student_run.json",
            mime="application/json",
        )
        st.download_button(
            "Download calibrated config JSON",
            data=json.dumps(config_to_dict(calibrated), indent=2),
            file_name="baseline_calibrated_student_run.json",
            mime="application/json",
        )

        if rich_mode:
            fig, ax = plt.subplots(figsize=(8, 4))
            x = np.arange(len(fit_df))
            ax.bar(x, fit_df["fractional_error"].values, color="#1f77b4")
            ax.axhline(0.0, color="black", linewidth=1)
            ax.set_xticks(x)
            ax.set_xticklabels(
                [f"{m:.0f} MeV" for m in fit_df["mass_mev"].values], rotation=35
            )
            ax.set_ylabel("fractional error")
            ax.set_title("Calibration fractional errors by anchor")
            ax.grid(alpha=0.2)
            fig.tight_layout()
            st.pyplot(fig)


def visualization_tab(config: ExperimentConfig, rich_mode: bool) -> None:
    st.subheader("Geometry + Particle Visualizer")
    st.caption(
        "Create beamline schematics and toy particle-level event displays for your selected mass and epsilon."
    )

    default_mass = float(config.scan.mass_mev_values[min(1, len(config.scan.mass_mev_values) - 1)])
    default_eps = float(config.scan.epsilon_values[min(3, len(config.scan.epsilon_values) - 1)])
    cherenkov_muon_veto_eff = max(
        0.0,
        min(1.0, float(1.0 - config.detector.cherenkov_muon_misid_rate)),
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        mass_mev = st.number_input(
            "Visualization mass (MeV)",
            min_value=0.1,
            max_value=5000.0,
            value=default_mass,
            step=0.5,
        )
        epsilon = st.number_input(
            "Visualization epsilon",
            min_value=1e-9,
            max_value=1.0,
            value=default_eps,
            format="%.3e",
        )
        seed = st.number_input("Visualization random seed", 0, 999999, int(config.scan.seed), 1)
    with c2:
        n_dark = st.slider("Sampled dark photons", 200, 50000, 4000, 200)
        n_muons = st.slider("Sampled muon tracks", 50, 30000, 2000, 50)
        st.caption(
            f"Cherenkov muon veto efficiency is set from sidebar PID settings: {cherenkov_muon_veto_eff:.3f}"
        )
        detector_gap_m = st.number_input(
            "Detector plane gap after decay volume (m)",
            min_value=0.05,
            max_value=20.0,
            value=0.6,
            step=0.05,
        )
    with c3:
        vertex_match_window_m = st.number_input(
            "Vertex matching window |x_v| (m)",
            min_value=0.0005,
            max_value=0.10,
            value=0.01,
            step=0.0005,
            format="%.4f",
            help="Opposite-charge tracks are paired only if reconstructed vertex |x_v| is below this value and z_v is in decay volume.",
        )
        aperture_half_width = st.number_input(
            "Plot half-width in x (m)",
            min_value=0.02,
            max_value=5.0,
            value=0.35,
            step=0.01,
        )
        max_signal_tracks = st.slider("Max signal tracks drawn", 20, 4000, 300, 20)
        max_muon_tracks = st.slider("Max muon tracks drawn", 20, 3000, 250, 10)

    run_vis = st.button("Generate Geometry + Particle Visualizations", type="primary")
    if not run_vis:
        st.info("Press the button to generate schematic and particle-level visualizations.")
        return

    with st.spinner("Generating toy particle samples and plots..."):
        signal_df, muon_df, candidates_df, pairs_df, stats, geometry = sample_visual_events(
            config=config,
            mass_mev=mass_mev,
            epsilon=epsilon,
            n_dark_photons=int(n_dark),
            n_muons=int(n_muons),
            detector_gap_m=float(detector_gap_m),
            cherenkov_muon_veto_efficiency=float(cherenkov_muon_veto_eff),
            vertex_match_window_m=float(vertex_match_window_m),
            seed=int(seed),
        )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sampled decays in volume", f"{int(stats['n_decays_in_volume'])}")
    m2.metric("Sampled detected signal", f"{int(stats['n_detected_signal'])}")
    m3.metric("Expected S (run)", f"{stats['expected_signal_count']:.2f}")
    m4.metric("Expected significance", f"{stats['expected_significance']:.3f}")

    m5, m6, m7 = st.columns(3)
    m5.metric("Muons past veto", f"{int(stats['n_muons_passed_veto'])}")
    m6.metric("Muons rejected by Cherenkov", f"{int(stats['n_muons_rejected_cherenkov'])}")
    m7.metric("Expected B (run)", f"{stats['expected_background_count']:.2f}")

    m8, m9, m10 = st.columns(3)
    m8.metric("Muon tracks after Cherenkov", f"{int(stats['n_muons_after_cherenkov'])}")
    m9.metric("Vertex-matched e+e- pairs", f"{int(stats['n_vertex_matched_pairs'])}")
    m10.metric("Pair purity", f"{100.0 * stats['pair_purity']:.1f}%")

    st.markdown("### Beamline Schematic")
    st.pyplot(draw_geometry_schematic(geometry, aperture_half_width_m=float(aperture_half_width)))

    st.markdown("### Particle Trajectory Overlay")
    st.pyplot(
        draw_particle_tracks(
            signal_df=signal_df,
            muon_df=muon_df,
            geometry=geometry,
            aperture_half_width_m=float(aperture_half_width),
            max_signal_tracks=int(max_signal_tracks),
            max_muon_tracks=int(max_muon_tracks),
        )
    )

    st.markdown("### Distribution Plots")
    st.pyplot(draw_particle_distributions(signal_df=signal_df, muon_df=muon_df, geometry=geometry))

    st.markdown("### Reconstructed Mass Histogram (Vertex-Matched e+e- Pairs)")
    st.pyplot(draw_reconstructed_mass_histogram(pairs_df=pairs_df, target_mass_mev=float(mass_mev)))

    if rich_mode and HAS_PLOTLY:
        st.markdown("### Rich Interactive Views")
        vis_df = signal_df[signal_df["in_decay_volume"]].copy()
        vis_df["detected_label"] = np.where(vis_df["detected"], "Detected", "Not detected")

        if len(vis_df) > 0:
            scatter = px.scatter(
                vis_df,
                x="decay_z_m",
                y="opening_angle_rad",
                color="detected_label",
                hover_data=["energy_gev", "x_plus_at_detector_m", "x_minus_at_detector_m"],
                title="Decay position vs opening angle",
                color_discrete_map={"Detected": "#1565c0", "Not detected": "#00897b"},
            )
            st.plotly_chart(scatter, use_container_width=True)

        muon_scatter = px.scatter(
            muon_df,
            x="x0_m",
            y="x_at_detector_m",
            color=np.where(
                muon_df["misidentified_as_electron"], "mis-ID", "regular muon"
            ),
            title="Muon track start vs detector hit position",
            labels={"x0_m": "x at target [m]", "x_at_detector_m": "x at detector [m]"},
            color_discrete_map={"mis-ID": "#d81b60", "regular muon": "#fb8c00"},
        )
        st.plotly_chart(muon_scatter, use_container_width=True)

    st.markdown("### Event Tables")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.dataframe(signal_df.head(200), use_container_width=True)
        st.download_button(
            "Download signal event table CSV",
            data=signal_df.to_csv(index=False),
            file_name="signal_events_visualization.csv",
            mime="text/csv",
        )
    with c2:
        st.dataframe(muon_df.head(200), use_container_width=True)
        st.download_button(
            "Download muon track table CSV",
            data=muon_df.to_csv(index=False),
            file_name="muon_tracks_visualization.csv",
            mime="text/csv",
        )
    with c3:
        st.dataframe(candidates_df.head(200), use_container_width=True)
        st.download_button(
            "Download electron-candidate track table CSV",
            data=candidates_df.to_csv(index=False),
            file_name="electron_candidates.csv",
            mime="text/csv",
        )
        st.markdown("---")
        st.dataframe(pairs_df.head(200), use_container_width=True)
        st.download_button(
            "Download vertex-matched pair table CSV",
            data=pairs_df.to_csv(index=False),
            file_name="vertex_matched_pairs.csv",
            mime="text/csv",
        )

    st.download_button(
        "Download visualization stats JSON",
        data=json.dumps(stats, indent=2),
        file_name="visualization_stats.json",
        mime="application/json",
    )


def main() -> None:
    st.set_page_config(
        page_title="Dark Photon Student Simulation Lab",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("Dark Photon Student Simulation Lab")
    st.markdown(
        "Interactive environment for beam-dump development: tune assumptions, optimize geometry, and calibrate your toy model."
    )

    config_options = {
        "Calibrated baseline": REPO_ROOT / "configs" / "baseline.json",
        "Uncalibrated baseline": REPO_ROOT / "configs" / "baseline_uncalibrated.json",
        "Quick scan": REPO_ROOT / "configs" / "quick_scan.json",
    }
    selected_label = st.sidebar.selectbox("Config preset", options=list(config_options.keys()), index=0)
    rich_mode = st.sidebar.toggle(
        "Rich mode (extra diagnostics + interactive charts)",
        value=True,
    )

    config_path = config_options[selected_label]
    st.sidebar.caption(f"Preset file: `{config_path.name}`")
    try:
        base_config = load_config(config_path)
        config = draw_sidebar_config(base_config)
    except Exception as exc:
        st.error(f"Failed to load or validate configuration: {exc}")
        return

    tab_scan, tab_geometry, tab_calib, tab_vis = st.tabs(
        [
            "Sensitivity Scan",
            "Geometry Development",
            "Calibration Lab",
            "Geometry + Particle Visualizer",
        ]
    )

    with tab_scan:
        scan_tab(config, rich_mode=rich_mode)
    with tab_geometry:
        geometry_tab(config, rich_mode=rich_mode)
    with tab_calib:
        calibration_tab(config, rich_mode=rich_mode)
    with tab_vis:
        visualization_tab(config, rich_mode=rich_mode)

    st.download_button(
        "Download current config JSON",
        data=json.dumps(asdict(config), indent=2),
        file_name="current_student_config.json",
        mime="application/json",
    )

    with st.expander("Current config JSON", expanded=False):
        st.code(json.dumps(asdict(config), indent=2), language="json")


if __name__ == "__main__":
    main()
