# Dark Photon Beam-Dump Simulation Report

- Date: 2026-02-16
- Config: `/Users/boraisildak/Downloads/dark_photon_search/configs/baseline_calibrated.json`
- Scan table: `/Users/boraisildak/Downloads/dark_photon_search/outputs/scan_results.csv`
- Geometry table: `/Users/boraisildak/Downloads/dark_photon_search/outputs/geometry_optimization.csv`

## Methods (Short)

A toy Monte Carlo beam-dump model was used to estimate visible dark-photon sensitivity in a 0.5 GeV electron fixed-target setup.
For each `(m_A', epsilon)` point, the chain `production -> survive shield -> decay in fiducial region -> detector acceptance/PID` was evaluated.
Background was modeled from beam-muon leakage, cosmic muons, and accidental electron-like activity, with a mass-spectrum scaling and systematic term.
Model normalization and global background scale were calibrated to published beam-dump exclusion anchor points at fixed target significance.

## Calibration Summary

- Fitted `production_norm`: `5.049578e-06`
- Fitted global background scale: `9.923414e-01`
- Target contour significance: `1.640`
- Objective value: `1.4526e-01`

| Anchor mass (MeV) | Anchor epsilon | Predicted Z | Fractional error |
|---:|---:|---:|---:|
| 10.0 | 1.00e-05 | 2.186 | +0.333 |
| 20.0 | 8.00e-06 | 1.209 | -0.263 |
| 30.0 | 5.00e-06 | 0.811 | -0.506 |

## Best Sensitivity Points

| Rank | Mass (MeV) | Epsilon | Expected S | Expected B | Significance | S/B |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 5.0 | 3.00e-05 | 216255.872 | 232170.1 | 4.657 | 9.31e-01 |
| 2 | 10.0 | 1.00e-05 | 56322.287 | 128804.4 | 2.186 | 4.37e-01 |
| 3 | 20.0 | 1.00e-05 | 11007.009 | 71458.7 | 0.770 | 1.54e-01 |
| 4 | 5.0 | 1.00e-05 | 33996.189 | 232170.1 | 0.732 | 1.46e-01 |
| 5 | 40.0 | 3.00e-06 | 4530.879 | 39644.2 | 0.571 | 1.14e-01 |
| 6 | 30.0 | 3.00e-06 | 5741.646 | 50626.5 | 0.567 | 1.13e-01 |
| 7 | 20.0 | 3.00e-06 | 4871.635 | 71458.7 | 0.341 | 6.82e-02 |
| 8 | 60.0 | 3.00e-06 | 1450.330 | 28086.8 | 0.258 | 5.16e-02 |

## Best Geometries

| Rank | Shield (m) | Decay volume (m) | Best Z | Best mass (MeV) | Best epsilon | Benchmark Z sum |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1.00 | 6.00 | 10.779 | 5.0 | 3.00e-05 | 5.016 |
| 2 | 1.00 | 5.00 | 10.640 | 5.0 | 3.00e-05 | 4.746 |
| 3 | 1.00 | 4.00 | 10.359 | 5.0 | 3.00e-05 | 4.369 |
| 4 | 1.00 | 3.00 | 9.782 | 5.0 | 3.00e-05 | 3.836 |
| 5 | 1.00 | 2.00 | 8.571 | 5.0 | 3.00e-05 | 3.071 |
| 6 | 1.50 | 6.00 | 7.227 | 5.0 | 3.00e-05 | 4.007 |

## Figures

- Scan heatmap: `/Users/boraisildak/Downloads/dark_photon_search/outputs/significance_heatmap.png`
- Geometry heatmap: `/Users/boraisildak/Downloads/dark_photon_search/outputs/geometry_optimization_heatmap.png`

## Recommended Next Beamline Inputs

1. Replace anchor approximations with collaboration-approved limit data points from the final reference set.
2. Constrain background rates with measured muon leakage from your planned shielding material and detector area.
3. Validate geometry winner points with a Geant4-level detector/transport model before final proposal submission.

## Configuration Snapshot

```json
{
  "beam": {
    "beam_energy_gev": 0.5,
    "electrons_on_target": 10000000000000.0,
    "target_atomic_number": 82,
    "target_thickness_radiation_lengths": 10.0,
    "shield_length_m": 2.0,
    "decay_volume_length_m": 4.0,
    "run_time_s": 172800.0
  },
  "detector": {
    "tracker_acceptance": 0.75,
    "pair_reco_efficiency": 0.82,
    "cherenkov_electron_efficiency": 0.9,
    "cherenkov_muon_misid_rate": 0.005,
    "scintillator_veto_efficiency_muons": 0.98,
    "scintillator_false_veto_rate": 0.01,
    "minimum_pair_opening_angle_rad": 0.02,
    "background_mass_spectrum_beta": 0.85,
    "background_reference_mass_mev": 50.0
  },
  "background": {
    "beam_muon_rate_hz": 496.1706903445436,
    "cosmic_muon_rate_hz": 49.61706903445436,
    "accidental_electron_like_rate_hz": 0.19846827613781745,
    "background_uncertainty_fraction": 0.2
  },
  "model": {
    "production_norm": 5.049577948487112e-06,
    "production_energy_scale_gev": 0.3,
    "min_energy_fraction": 0.2,
    "max_energy_fraction": 0.95,
    "energy_fraction_shape": 2.0
  },
  "scan": {
    "mass_mev_values": [
      5.0,
      10.0,
      20.0,
      30.0,
      40.0,
      60.0,
      80.0,
      100.0,
      150.0,
      200.0
    ],
    "epsilon_values": [
      1e-07,
      3e-07,
      1e-06,
      3e-06,
      1e-05,
      3e-05,
      0.0001
    ],
    "mc_samples_per_point": 8000,
    "seed": 7
  }
}
```