# Dark Photon Student Simulation Lab
## Detailed User Manual (for Students)

Version: 1.0  
Date: 2026-02-16  
App file: `streamlit_app.py`

---

## 1. Purpose of this manual

This manual explains every control and every plot in the Streamlit app so students can:

1. Run simulations correctly.
2. Understand what each parameter means physically.
3. Interpret plots without guessing.
4. Compare setups and defend choices in a competition proposal.

This is a toy-model analysis framework for learning and design iteration, not a final detector simulation.

---

## 2. App overview

The app has:

1. Sidebar (global assumptions shared by all tabs).
2. Four main tabs:
   - Sensitivity Scan
   - Geometry Development
   - Calibration Lab
   - Geometry + Particle Visualizer
3. Export options (CSV/JSON downloads).

Recommended order for students:

1. Set global assumptions in sidebar.
2. Run Sensitivity Scan.
3. Run Geometry Development to optimize layout.
4. Use Calibration Lab if you need model normalization tuning.
5. Use Geometry + Particle Visualizer for intuitive event/geometry understanding and presentation figures.

---

## 3. Quick start

### 3.1 Launch app

```bash
cd /Users/boraisildak/Downloads/dark_photon_search
pip install -r requirements-app.txt
streamlit run streamlit_app.py
```

### 3.2 Choose a preset

In sidebar:

1. `Calibrated baseline` - recommended default for classroom use.
2. `Uncalibrated baseline` - use for calibration exercises.
3. `Quick scan` - fast test profile.

### 3.3 Rich mode

`Rich mode` enables extra diagnostics and interactive Plotly charts.

---

## 4. Sidebar controls (global assumptions)

All tabs use these values. If you change them, every tab behavior changes.

## 4.1 Beam + Geometry block

### Beam energy (GeV)

- Meaning: incident electron beam energy.
- Physical effect: higher beam energy usually increases production phase space and boost.
- Plot effect:
  - Can shift high-significance region in scan heatmaps.
  - Can change decay-in-volume probability via boost/lifetime balance.
- Typical class exercise: compare 0.5 GeV vs 1.0 GeV and discuss changes in decay geometry.

### Electrons on target

- Meaning: total beam exposure (integrated intensity).
- Physical effect: scales expected signal almost linearly.
- Plot effect:
  - `Expected Signal Counts` heatmap scales strongly.
  - Significance usually increases if background systematics do not dominate.

### Target atomic number Z

- Meaning: effective target nuclear charge.
- Physical effect: enters production normalization in toy model.
- Plot effect:
  - Higher Z can increase production probability.
- Caution: real target optimization also depends on showering/material effects not fully modeled here.

### Target thickness (X0)

- Meaning: thickness in radiation lengths.
- Physical effect: larger thickness can increase production opportunities in this toy model.
- Plot effect:
  - Can increase produced A' rate.
- Caution: very thick targets in reality also alter secondary backgrounds and angular spread.

### Shield length (m)

- Meaning: passive absorber length between target and decay region.
- Physical effect:
  - Removes ordinary charged particles.
  - But longer shield also means fewer short-lived A' survive to decay region.
- Plot effect:
  - In geometry optimization heatmaps, increasing shield can improve/reduce significance depending on lifetime regime.

### Decay volume length (m)

- Meaning: open fiducial region where A' can decay into visible pairs.
- Physical effect: longer region usually increases decay acceptance.
- Plot effect:
  - Often increases signal until reaching diminishing returns.

### Run time (s)

- Meaning: beam running duration.
- Physical effect: scales total exposure and background counts.
- Plot effect:
  - Signal and background both rise; significance improvement depends on S/B and systematics.

---

## 4.2 Detector + PID block

### Tracker acceptance

- Meaning: geometric/kinematic fraction of relevant tracks entering tracker acceptance.
- Effect: multiplies both detectable signal and some background components.

### Pair reconstruction efficiency

- Meaning: probability to successfully reconstruct e+e- pair.
- Effect: direct signal efficiency multiplier.

### Cherenkov electron efficiency

- Meaning: probability true electrons pass PID.
- Effect: direct signal multiplier.

### Cherenkov muon mis-ID rate

- Meaning: probability muon is wrongly tagged as electron-like.
- Effect: key background leakage term.

### Scintillator veto efficiency (muons)

- Meaning: fraction of muons rejected by veto.
- Effect: larger value strongly reduces muon background.

### Scintillator false veto rate

- Meaning: fraction of true signal wrongly vetoed.
- Effect: reduces signal efficiency.

### Minimum opening angle (rad)

- Meaning: effective reconstruction threshold for pair separation.
- Effect:
  - Larger threshold can penalize collimated (small-angle) pairs.
  - Important at lower masses/higher boosts.

### Background mass spectrum beta

- Meaning: exponent controlling mass dependence of background model.
- Effect:
  - Higher beta makes background fall faster with mass.
  - Changes shape of significance vs mass.

### Background reference mass (MeV)

- Meaning: normalization reference point for mass-dependent background scaling.
- Effect:
  - Combined with beta controls background curve shape in scan outputs.

---

## 4.3 Background + Model block

### Beam muon rate (Hz)

- Meaning: beam-correlated muon flux before veto/rejection.
- Effect: increases expected background.

### Cosmic muon rate (Hz)

- Meaning: cosmogenic muon contribution.
- Effect: adds to muon background floor.

### Accidental electron-like rate (Hz)

- Meaning: non-muon accidental activity that appears electron-like.
- Effect: additive background floor.

### Background fractional uncertainty

- Meaning: systematic uncertainty fraction on background estimate.
- Effect:
  - Directly reduces significance when background is large.
  - Important for realistic proposal statements.

### Production normalization

- Meaning: global toy-model scale factor for A' production.
- Effect:
  - Strong global scaling of expected signal.
- Usage:
  - Usually fixed by calibration exercises in Calibration Lab.

### Production energy scale (GeV)

- Meaning: mass/energy suppression scale in production model.
- Effect:
  - Controls how quickly production drops for heavier masses.

### Min dark-photon energy fraction

- Meaning: lower bound of sampled `E_A'/E_beam`.
- Effect:
  - Changes boost distribution and therefore decay length distribution.

### Max dark-photon energy fraction

- Meaning: upper bound of sampled `E_A'/E_beam`.
- Effect: higher upper bound allows more boosted A' events.

### Energy fraction shape parameter

- Meaning: shape parameter for toy sampling of dark-photon energy fraction.
- Effect:
  - Alters energy spectrum skew and therefore decay acceptance/reconstruction behavior.

---

## 4.4 Scan Grid block

### Masses (MeV)

- Meaning: grid of dark photon masses to evaluate.
- Input format: comma or newline separated list.
- Example:
  - `5, 10, 20, 30, 40, 60, 80, 100`

### Epsilon values

- Meaning: grid of kinetic-mixing values.
- Input format: comma or newline separated list.
- Example:
  - `1e-7, 3e-7, 1e-6, 3e-6, 1e-5`

### MC samples per point

- Meaning: number of toy Monte Carlo samples used per `(mass, epsilon)` point.
- Effect:
  - Higher value = smoother/stabler estimates, slower runtime.

### Random seed

- Meaning: reproducibility seed.
- Best practice:
  - Keep seed fixed for comparison studies.
  - Change seed only when checking stability.

---

## 5. Tab 1: Sensitivity Scan

## 5.1 Inputs in this tab

### Top points to show

- Controls how many best-ranked points appear in top table.

### Run Scan button

- Executes full grid scan using current sidebar configuration.

## 5.2 Outputs and interpretation

### Metric cards

1. `Best significance`:
   - Highest approximate significance found on grid.
2. `Best mass (MeV)`:
   - Mass at best significance point.
3. `Best epsilon`:
   - Epsilon at best significance point.
4. `Best S/B`:
   - Signal/background ratio at best point.

Interpretation note:

- High significance with very low S/B can still be fragile under systematics.
- Always read significance together with S/B.

### Top Points table

Columns include:

- `mass_mev`, `epsilon`
- production/decay/reco probabilities
- expected signal/background
- `signal_to_background`
- `significance`

Use this table to identify candidate benchmark points for proposal text.

### Heatmap 1: Approximate Significance

- X-axis: mass
- Y-axis: epsilon
- Color: significance

How to read:

1. Bright regions = strongest sensitivity in this toy setup.
2. If bright area is only at one corner, your grid may be too narrow.
3. Compare shape before/after geometry changes.

### Heatmap 2: Expected Signal Counts

- Shows pure event-yield behavior, not significance.
- Useful for understanding production + decay acceptance pattern.

### Heatmap 3: Signal-to-Background (S/B)

- Highlights cleanliness, independent of pure yield.
- Useful for selecting robust operating points.

## 5.3 Rich mode diagnostics

### Plot: Significance vs epsilon at fixed mass

- Helps detect local optimum in epsilon direction.

### Plot: Significance vs mass at fixed epsilon

- Shows mass trend for one coupling.

### Plotly scatter: Signal vs background landscape

- X: expected background
- Y: expected signal
- Color: significance

Use this to discuss tradeoffs and outliers.

---

## 6. Tab 2: Geometry Development

## 6.1 Inputs

### Shield start/stop/step (m)

- Defines tested shield length grid.
- Example:
  - start = 1.0, stop = 4.0, step = 0.5

### Decay start/stop/step (m)

- Defines tested decay-volume grid.

### Ranking metric

Options:

1. `best_significance`
2. `benchmark_significance_total`

Guidance:

- `best_significance`: optimistic best-point scan metric.
- `benchmark_significance_total`: better for fixed benchmark planning.

### Geometry MC samples / point

- Monte Carlo granularity for each geometry point.
- Higher values improve smoothness, increase runtime.

### Benchmark points text area

- Format: one line per point, `mass_mev, epsilon`
- Example:
  - `10, 1e-5`
  - `30, 3e-6`
  - `80, 3e-6`

## 6.2 Outputs

### Top geometry metric cards

1. Best shield length
2. Best decay volume length
3. Best chosen metric value

### Top geometry table

Includes:

- `best_significance`
- best `(mass, epsilon)` for each geometry
- benchmark totals

### Geometry heatmap

- X-axis: shield length
- Y-axis: decay length
- Color: selected metric

How to interpret:

1. Horizontal gradient: shield sensitivity.
2. Vertical gradient: decay volume sensitivity.
3. Flat region: diminishing returns.

---

## 7. Tab 3: Calibration Lab

Calibration aligns toy model scales with external contour anchor points.

## 7.1 Inputs

### Anchor points text area

- Format per line:
  - `mass_mev, epsilon_limit, label`
- Label is optional but recommended.

### Target significance

- Significance value assigned to contour anchors (commonly around one-sided limit proxy).

### Calibration MC samples / point

- Monte Carlo precision for each anchor evaluation.

### log10 background scale min/max

- Search interval for global background scaling factor.
- Example:
  - min = -4, max = 2 means scale in `[1e-4, 1e2]`.

### Background scale scan steps

- Number of tested points in background scale search.

### Background prior center

- Preferred value for background scale prior (usually 1).

### Background prior weight

- Strength of penalty for moving away from prior center.

## 7.2 Outputs

### Calibration metric cards

1. Fitted `production_norm`
2. Fitted background scale
3. Objective value

### Anchor fit table

Key columns:

- `predicted_significance`
- `target_significance`
- `fractional_error`

Interpretation:

- Fractional error near 0 is good.
- Systematic one-direction errors indicate model shape mismatch.

### Rich mode bar chart

- Displays fractional error per anchor.
- Useful to identify which anchor masses are poorly described.

---

## 8. Tab 4: Geometry + Particle Visualizer

This tab builds intuition with toy event-level visuals.

## 8.1 Inputs

### Visualization mass (MeV)

- Mass used for toy event sampling.

### Visualization epsilon

- Coupling used for toy event sampling.

### Visualization random seed

- Reproducibility control for toy event sample.

### Sampled dark photons

- Number of generated A' candidates for display/statistics.

### Sampled muon tracks

- Number of toy muon background tracks.

### Cherenkov muon veto efficiency (from Sidebar PID settings)

- This is no longer set inside Tab 4.
- Tab 4 uses the global Sidebar value: `1 - cherenkov_muon_misid_rate`.
- Higher value means fewer muon fakes entering electron-candidate pool.

### Detector plane gap after decay volume (m)

- Distance from decay volume end to detector plane.
- Affects observed hit spread from opening angles.

### Plot half-width in x (m)

- Vertical view window for schematic/track plots.

### Max signal tracks drawn

- Rendering limit for e+/e- tracks in overlay plot.

### Max muon tracks drawn

- Rendering limit for muon tracks in overlay plot.

### Vertex matching window |x_v| (m)

- Opposite-charge tracks are paired only if reconstructed vertex transverse position satisfies `|x_v| < window` and vertex `z_v` is inside decay volume.
- Smaller window gives cleaner pairs but lower efficiency.

## 8.2 Outputs and interpretation

### Metric cards (sample-level + expectation-level)

1. Sampled decays in volume
2. Sampled detected signal
3. Expected S (run)
4. Expected significance
5. Muons past veto
6. Muon mis-ID tracks
7. Expected B (run)

Interpretation:

- Sample-level cards show what happened in this toy sample.
- Expected cards come from model expectations for run-scale counts.

### Beamline Schematic

Shows:

- target block
- shield block
- decay volume block
- detector plane marker

Use this figure for geometry communication in slides/reports.

### Particle Trajectory Overlay

Shows:

- dark photon line to decay point
- e+ and e- track branches
- muon background tracks

Use this to explain:

- where signal decays happen,
- how opening angle maps to detector separation,
- why muon contamination is a challenge.

### Distribution Plots (2x2 panel)

1. Decay-z distribution:
   - compare with fiducial boundaries.
2. Opening angle distribution:
   - shows pair-collimation behavior.
3. Detector hit-position distribution:
   - e+, e-, muon hit envelopes.
4. Toy event category counts:
   - signal vs background categories.

### Reconstructed Mass Histogram (Vertex-Matched e+e- Pairs)

- Tracks are first converted to electron-candidate pool:
  - true signal electrons from detected decays,
  - surviving muon fakes after Cherenkov veto.
- Opposite-charge candidates are paired by vertex matching.
- Reconstructed mass uses the paired track energies and opening angle.
- Plot overlays:
  - true signal pairs,
  - pairs containing muon fake(s),
  - target mass reference line.

### Rich mode interactive plots

1. Decay position vs opening angle scatter (colored by detected/not detected).
2. Muon track start position vs detector hit position (colored by mis-ID).

These are useful for interactive class discussion.

### Event tables and downloads

- Signal events table (first 200 rows preview).
- Muon tracks table (first 200 rows preview).
- Electron-candidate table (tracks entering vertex matching).
- Vertex-matched pair table (used for reconstructed-mass histogram).
- Download full CSV tables and stats JSON.

---

## 9. What each major output file means

Students may download many files. Use this mapping:

1. `scan_results_student_run.csv`
   - Full `(mass, epsilon)` sensitivity grid.
2. `geometry_optimization_student_run.csv`
   - Full geometry grid ranking results.
3. `calibration_summary_student_run.json`
   - Fitted calibration summary and anchor residuals.
4. `baseline_calibrated_student_run.json`
   - Updated config with calibration applied.
5. `signal_events_visualization.csv`
   - Toy signal event-level records.
6. `muon_tracks_visualization.csv`
   - Toy muon track records.
7. `electron_candidates.csv`
   - Candidate tracks after signal detection + muon Cherenkov veto.
8. `vertex_matched_pairs.csv`
   - Opposite-charge pairs passing vertex-matching cuts, with reconstructed mass.
9. `visualization_stats.json`
   - Summary counters and expected S/B/significance.

---

## 10. Recommended classroom workflow

### Exercise A: baseline understanding

1. Load calibrated baseline.
2. Run Sensitivity Scan.
3. Record top 5 points.
4. Explain why best point appears where it does.

### Exercise B: geometry optimization

1. Fix 2-3 benchmark points.
2. Scan shield and decay ranges.
3. Select top geometry by benchmark significance total.
4. Justify shield-decay tradeoff.

### Exercise C: detector systematics

1. Change muon mis-ID and veto efficiency.
2. Re-run scan.
3. Compare significance/S-B changes.
4. Conclude which detector improvement matters most.

### Exercise D: visual intuition

1. Use Geometry + Particle Visualizer.
2. Compare low-mass vs high-mass opening-angle patterns.
3. Relate hit distributions to tracker/cherenkov strategy.

---

## 11. Interpretation checklist before writing proposal text

Before claiming a setup is "better", verify:

1. Significance improved in scan and not only signal counts.
2. S/B did not collapse.
3. Geometry improvement holds for multiple benchmarks.
4. Calibration residuals are acceptable and not one-point dominated.
5. Visualizer output is consistent with your narrative (decay region, track separation, background behavior).

---

## 12. Common mistakes and fixes

### Mistake: extremely sparse mass/epsilon grid

- Symptom: unstable conclusions based on one or two points.
- Fix: densify scan grid around interesting region.

### Mistake: low MC samples per point

- Symptom: noisy heatmaps and inconsistent top points across runs.
- Fix: increase MC samples and keep seed fixed for comparisons.

### Mistake: reading signal heatmap as sensitivity

- Symptom: selecting high-signal region with poor background control.
- Fix: always check significance and S/B heatmaps too.

### Mistake: overfitting calibration to incompatible anchors

- Symptom: large residuals at several masses.
- Fix: use physically relevant anchor region for your beam energy.

### Mistake: changing many parameters at once

- Symptom: hard-to-interpret result shifts.
- Fix: one-parameter or one-block-at-a-time changes.

---

## 13. Troubleshooting

### App does not start

1. Install dependencies:
   - `pip install -r requirements-app.txt`
2. Run:
   - `streamlit run streamlit_app.py`

### Plotly charts do not appear

- Cause: Plotly may be missing.
- Fix:
  - `pip install plotly`
- Note: app still works with Matplotlib fallback.

### Very slow scans

Possible fixes:

1. Reduce grid size (fewer masses/epsilons).
2. Reduce MC samples per point during prototyping.
3. Use quick preset first, then full scan.

### Unexpected zero/near-zero significance

Check:

1. Production normalization too small?
2. Epsilon values too low?
3. Shield too long for chosen lifetime regime?
4. Background rates too high?

---

## 14. Glossary

### A' (dark photon)

Hypothetical mediator particle that can decay to visible pairs such as e+e-.

### Epsilon

Kinetic mixing parameter controlling interaction strength with Standard Model.

### Beam dump

Target + absorber setup where rare weakly coupled particles can be produced and decay downstream.

### Fiducial decay volume

Region where decays are counted for signal selection.

### PID

Particle identification. Here mainly tracker + cherenkov-based electron/muon separation.

### S/B

Signal-to-background ratio.

### Significance

Approximate statistical sensitivity metric including background uncertainty term.

---

## 15. Final notes for students

1. Treat this app as an engineering-design lab.
2. Always compare both sensitivity and robustness.
3. Keep a changelog of parameter sets and rationale.
4. Export tables/plots and cite exact settings in your proposal draft.

For competition-quality work:

1. Use calibrated assumptions.
2. Document optimization method.
3. Include both quantitative tables and intuitive visualization figures.
