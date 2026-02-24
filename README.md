# Dark Photon Beam-Dump Simulation Framework

This repository now contains a full starter framework to test your proposal idea before submission to a CERN high-school beamline program.

Important: this is a **toy model framework** for rapid feasibility studies, not a precision experiment simulation. It is designed so you can quickly swap in validated cross-sections, detector responses, and beamline-specific rates later.

## What this framework simulates

1. Dark photon production in a fixed-target beam dump:
   - `e Z -> e Z A'` in a simplified parameterized form.
2. Propagation through shield and decay in a fiducial decay volume:
   - survival through shield and decay probability in open volume.
3. Detector chain:
   - scintillator veto behavior,
   - tracker + pair reconstruction acceptance,
   - Cherenkov electron ID and muon mis-identification.
4. Background model:
   - beam muons,
   - cosmic muons,
   - accidental electron-like activity,
   - mass-window scaling for background under resonance searches.
5. Scan over `(m_A', epsilon)` with ranking by approximate significance.
6. Calibration step:
   - fit `production_norm` and global background scale to published beam-dump contour anchors.
7. Geometry optimization:
   - scan shield and decay-volume lengths and rank sensitivity.

## Repository layout

- `/Users/boraisildak/Downloads/dark_photon_search/src/dark_photon_sim/config.py`: typed config loader/validator.
- `/Users/boraisildak/Downloads/dark_photon_search/src/dark_photon_sim/physics.py`: production, decay, acceptance, background functions.
- `/Users/boraisildak/Downloads/dark_photon_search/src/dark_photon_sim/engine.py`: scan engine and result objects.
- `/Users/boraisildak/Downloads/dark_photon_search/src/dark_photon_sim/analysis.py`: significance metric.
- `/Users/boraisildak/Downloads/dark_photon_search/src/dark_photon_sim/calibration.py`: calibration against published-limit anchors.
- `/Users/boraisildak/Downloads/dark_photon_search/src/dark_photon_sim/geometry.py`: geometry optimization scan.
- `/Users/boraisildak/Downloads/dark_photon_search/src/dark_photon_sim/io_utils.py`: CSV export and ranking helpers.
- `/Users/boraisildak/Downloads/dark_photon_search/configs/baseline_uncalibrated.json`: source-of-truth assumptions before calibration.
- `/Users/boraisildak/Downloads/dark_photon_search/configs/baseline.json`: calibrated baseline used for scans.
- `/Users/boraisildak/Downloads/dark_photon_search/configs/published_limit_anchors.json`: exclusion-contour anchor points for calibration.
- `/Users/boraisildak/Downloads/dark_photon_search/configs/geometry_scan.json`: shield/decay scan grid + benchmark points.
- `/Users/boraisildak/Downloads/dark_photon_search/configs/quick_scan.json`: faster smoke-test config.
- `/Users/boraisildak/Downloads/dark_photon_search/scripts/run_scan.py`: full grid scan.
- `/Users/boraisildak/Downloads/dark_photon_search/scripts/run_single_point.py`: evaluate one point.
- `/Users/boraisildak/Downloads/dark_photon_search/scripts/plot_scan.py`: optional significance heatmap.
- `/Users/boraisildak/Downloads/dark_photon_search/scripts/calibrate_model.py`: produce calibrated config from anchor points.
- `/Users/boraisildak/Downloads/dark_photon_search/scripts/optimize_geometry.py`: scan geometry and produce heatmap/CSV.
- `/Users/boraisildak/Downloads/dark_photon_search/scripts/generate_report.py`: create proposal-ready markdown report.
- `/Users/boraisildak/Downloads/dark_photon_search/scripts/run_full_pipeline.py`: end-to-end automation.

## Quick start

Run a quick scan:

```bash
python3 scripts/run_scan.py --config configs/quick_scan.json --out outputs/quick_scan.csv --top 5
```

Launch the interactive student app:

```bash
streamlit run streamlit_app.py
```

If needed, install app dependencies:

```bash
pip install -r requirements-app.txt
```

Generate standalone geometry/particle visuals without Streamlit:

```bash
python3 scripts/generate_visualizations.py \
  --config configs/baseline.json \
  --mass-mev 10 \
  --epsilon 1e-5 \
  --cherenkov-muon-veto-eff 0.995 \
  --vertex-match-window-m 0.01 \
  --out-prefix outputs/student_visual
```

Build the detailed student manual PDF:

```bash
python3 scripts/build_streamlit_manual_pdf.py \
  --source docs/Streamlit_User_Manual.md \
  --out outputs/Streamlit_User_Manual.pdf
```

Build the simpler high-school bilingual (TR/EN) manual PDF:

```bash
python3 scripts/build_streamlit_manual_pdf.py \
  --source docs/Streamlit_User_Manual_HighSchool_Bilingual_TR_EN.md \
  --out outputs/Streamlit_User_Manual_HighSchool_Bilingual_TR_EN.pdf \
  --title "Dark Photon Lab High School Manual (TR/EN)"
```

Calibrate model + background against anchors:

```bash
python3 scripts/calibrate_model.py \
  --config configs/baseline_uncalibrated.json \
  --anchors configs/published_limit_anchors.json \
  --out-config configs/baseline_calibrated.json \
  --out-summary outputs/calibration_summary.json
```

Run the calibrated baseline scan:

```bash
python3 scripts/run_scan.py --config configs/baseline_calibrated.json --out outputs/scan_results.csv --top 10
```

Evaluate one `(mass, epsilon)` point:

```bash
python3 scripts/run_single_point.py --config configs/baseline_calibrated.json --mass-mev 30 --epsilon 3e-6 --pretty
```

Create a heatmap figure (requires matplotlib):

```bash
python3 scripts/plot_scan.py --scan-csv outputs/scan_results.csv --out outputs/significance_heatmap.png
```

Run geometry optimization:

```bash
python3 scripts/optimize_geometry.py \
  --config configs/baseline_calibrated.json \
  --grid configs/geometry_scan.json \
  --out-csv outputs/geometry_optimization.csv \
  --out-plot outputs/geometry_optimization_heatmap.png
```

Generate proposal-ready report:

```bash
python3 scripts/generate_report.py \
  --scan-csv outputs/scan_results.csv \
  --geometry-csv outputs/geometry_optimization.csv \
  --calibration-summary outputs/calibration_summary.json \
  --scan-plot outputs/significance_heatmap.png \
  --geometry-plot outputs/geometry_optimization_heatmap.png \
  --config configs/baseline_calibrated.json \
  --out-md outputs/proposal_simulation_report.md
```

Run full pipeline with one command:

```bash
python3 scripts/run_full_pipeline.py
```

Run smoke test:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

## Pipeline you can present

1. Define beam and geometry assumptions:
   - beam energy, target material/thickness, shield length, decay volume length.
2. Define detector/PID assumptions:
   - scintillator veto, tracker acceptance, Cherenkov electron efficiency, muon mis-ID.
3. Define background rates, background mass-shape, and systematic uncertainty.
4. Calibrate model to published exclusion anchors:
   - fit `production_norm` and global background scale.
5. Scan dark photon hypothesis space:
   - masses and kinetic-mixing values.
6. Rank points by expected signal significance:
   - produce candidate sensitivity region and benchmark points.
7. Optimize setup geometry:
   - shield length, decay volume, detector efficiencies, run time.
8. Auto-generate report package:
   - tables + heatmaps + short methods text.

## Streamlit student lab

`streamlit_app.py` includes four tabs:

1. `Sensitivity Scan`:
   - edit beam/detector/background/model assumptions in sidebar,
   - run full `(mass, epsilon)` scans,
   - view detailed heatmaps and diagnostics,
   - export CSV tables.
2. `Geometry Development`:
   - scan shield and decay volume ranges,
   - rank geometries by significance metrics,
   - inspect optimization heatmaps,
   - export geometry study CSV.
3. `Calibration Lab`:
   - enter custom anchor points,
   - fit `production_norm` and global background scale,
   - inspect anchor residuals,
   - export calibrated config JSON and summary JSON.
4. `Geometry + Particle Visualizer`:
   - beamline schematic (target/shield/decay/detector),
   - toy particle trajectory overlays (`A' -> e+ e-` plus muon backgrounds),
   - Cherenkov muon-veto stage with configurable efficiency,
   - reconstructed `e+e-` mass histogram from vertex-matched opposite-charge pairs,
   - decay/opening-angle/hit-position distributions,
   - exportable per-event CSV tables and summary JSON.

Enable `Rich mode` in the sidebar for extra plots and interactive charts.

## Notes on calibration anchors

The default anchor file (`configs/published_limit_anchors.json`) uses approximate contour points intended for pre-proposal tuning. Replace these with collaboration-approved digitized points from your final reference set before submission.

## Next upgrades toward CERN-level realism

1. Replace the production parameterization with a validated differential cross-section from literature or MadGraph/CalcHEP.
2. Integrate Geant4 (or equivalent) for showering, leakage, and detector material effects.
3. Replace rate-only background with event-level timing/spatial coincidence.
4. Add full detector resolution and trigger logic.
5. Cross-check with published beam-dump limits to calibrate model normalization.
