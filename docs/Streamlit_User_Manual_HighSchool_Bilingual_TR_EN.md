# Dark Photon Student Lab
## High School User Manual (Simple + Bilingual TR/EN)

Version: 1.0  
Date: 2026-02-16  
App: `streamlit_app.py`

---

## 1. What is this app? / Bu uygulama nedir?

### English

This app helps students test a dark photon beam-dump idea with simple simulations.
You can change setup values and see how the results change.

### Turkce

Bu uygulama, ogrencilerin karanlik foton beam-dump fikrini basit simulasyonlarla test etmesini saglar.
Duzenek degerlerini degistirip sonuclarin nasil degistigini gorebilirsiniz.

---

## 2. Quick start / Hizli baslangic

### English

1. Open terminal in project folder.
2. Install app packages.
3. Start Streamlit.

```bash
cd /Users/boraisildak/Downloads/dark_photon_search
pip install -r requirements-app.txt
streamlit run streamlit_app.py
```

### Turkce

1. Proje klasorunde terminal acin.
2. Gerekli paketleri kurun.
3. Streamlit'i baslatin.

---

## 3. How to study with this app / Bu uygulamayla nasil calisilir?

### English

Recommended order:

1. Set values in the sidebar.
2. Run `Sensitivity Scan`.
3. Run `Geometry Development`.
4. Use `Calibration Lab` only if needed.
5. Use `Geometry + Particle Visualizer` for understanding and presentation figures.

### Turkce

Onerilen sira:

1. Sol menude (sidebar) degerleri ayarlayin.
2. `Sensitivity Scan` sekmesini calistirin.
3. `Geometry Development` sekmesini calistirin.
4. Gerekirse `Calibration Lab` kullanin.
5. Anlama ve sunum gorselleri icin `Geometry + Particle Visualizer` kullanin.

---

## 4. Sidebar parameters / Sol menu parametreleri

All tabs use these values.

Tum sekmeler bu degerleri kullanir.

## 4.1 Beam + Geometry

### Beam energy (GeV)

- EN: Energy of incoming electrons.
- TR: Gelen elektronlarin enerjisi.
- EN: Higher energy can improve reach.
- TR: Daha yuksek enerji bazen hassasiyeti artirabilir.

### Electrons on target

- EN: Total beam amount (exposure).
- TR: Toplam isin miktari (maruziyet).
- EN: More electrons usually means more signal.
- TR: Daha fazla elektron genelde daha fazla sinyal demektir.

### Target atomic number Z

- EN: Material charge number.
- TR: Hedef malzemenin atom numarasi.
- EN: In this toy model, larger Z can increase production.
- TR: Bu basit modelde daha buyuk Z, uretimi arttirabilir.

### Target thickness (X0)

- EN: Target thickness in radiation lengths.
- TR: Hedef kalinligi (radyasyon uzunlugu cinsinden).
- EN: Larger thickness can increase production in this model.
- TR: Bu modelde kalinlik artisi uretimi artirabilir.

### Shield length (m)

- EN: Absorber after target.
- TR: Hedeften sonra gelen kalkan/soğurucu bolge.
- EN: Blocks background particles but may also reduce decays that happen later.
- TR: Arka plan parcaciklarini engeller ama bazi sinyal bozunmalarini da azaltabilir.

### Decay volume length (m)

- EN: Open space where dark photon decays are searched.
- TR: Karanlik foton bozunmalarinin arandigi acik bolge.
- EN: Longer volume often gives more decays.
- TR: Daha uzun bozunma bolgesi genelde daha fazla bozunma verir.

### Run time (s)

- EN: Data-taking time.
- TR: Veri toplama suresi.
- EN: Increases both signal and background counts.
- TR: Hem sinyal hem arka plan sayilarini arttirir.

---

## 4.2 Detector + PID

### Tracker acceptance

- EN: Fraction of tracks inside tracker acceptance.
- TR: Tracker tarafindan kabul edilen iz oranı.

### Pair reconstruction efficiency

- EN: Chance to reconstruct e+e- pair.
- TR: e+e- ciftini dogru kurma olasiligi.

### Cherenkov electron efficiency

- EN: Chance to tag true electrons correctly.
- TR: Gercek elektronlari dogru etiketleme olasiligi.

### Cherenkov muon mis-ID rate

- EN: Chance to mistake muon as electron.
- TR: Muonu elektron sanma olasiligi.

### Scintillator veto efficiency (muons)

- EN: Muon rejection power of veto detector.
- TR: Veto dedektorunun muon eleme gucu.

### Scintillator false veto rate

- EN: Chance to wrongly reject a true signal.
- TR: Gercek sinyali yanlislikla reddetme olasiligi.

### Minimum opening angle (rad)

- EN: Minimum pair separation needed by reconstruction.
- TR: Yeniden kurulum icin gereken minimum acilma acisi.

### Background mass spectrum beta

- EN: Controls how background changes with mass.
- TR: Arka planin kutleye gore degisim hizini belirler.

### Background reference mass (MeV)

- EN: Reference mass for background scaling.
- TR: Arka plan olceklemesi icin referans kutle.

---

## 4.3 Background + Model

### Beam muon rate (Hz)

- EN: Beam-related muon flow.
- TR: Isina bagli muon akis hizi.

### Cosmic muon rate (Hz)

- EN: Cosmic ray muon contribution.
- TR: Kozmik isin kaynakli muon katkisi.

### Accidental electron-like rate (Hz)

- EN: Random non-signal events that look like electrons.
- TR: Elektron gibi gorunen rastgele sinyal-disi olaylar.

### Background fractional uncertainty

- EN: Systematic uncertainty of background estimate.
- TR: Arka plan tahmininin sistematik belirsizligi.

### Production normalization

- EN: Global model scale for dark photon production.
- TR: Karanlik foton uretimi icin genel model olcegi.

### Production energy scale (GeV)

- EN: Controls production suppression behavior.
- TR: Uretimin baskilanma davranisini belirler.

### Min/Max dark-photon energy fraction

- EN: Lower/upper limits for sampled dark photon energy fraction.
- TR: Orneklenen karanlik foton enerji oraninin alt/ust sinirlari.

### Energy fraction shape parameter

- EN: Shapes the toy energy distribution.
- TR: Basit enerji dagiliminin seklini belirler.

---

## 4.4 Scan Grid

### Masses (MeV)

- EN: Mass values to test.
- TR: Test edilecek kutle degerleri.

### Epsilon values

- EN: Coupling values to test.
- TR: Test edilecek baglasim (epsilon) degerleri.

### MC samples per point

- EN: Simulation count per grid point.
- TR: Her grid noktasi icin simulasyon sayisi.
- EN: Bigger value = smoother results, slower runtime.
- TR: Daha buyuk deger = daha pürüzsüz sonuc, daha uzun sure.

### Random seed

- EN: Reproducibility control.
- TR: Tekrar uretilebilirlik kontrolu.

---

## 5. Tab 1: Sensitivity Scan

### English

This tab runs the full `(mass, epsilon)` scan and ranks the best points.

### Turkce

Bu sekme tam `(kutle, epsilon)` taramasini calistirir ve en iyi noktalari siralar.

### Controls / Kontroller

1. `Top points to show`
2. `Run Scan`

### Main outputs / Ana ciktilar

1. Best significance card
2. Best mass and epsilon cards
3. Best S/B card
4. Top points table
5. Heatmaps:
   - Significance
   - Expected Signal Counts
   - Signal-to-Background

### How to read plots / Grafikler nasil okunur?

- EN: Bright color in significance map means stronger sensitivity.
- TR: Significance haritasinda parlak renk daha yuksek hassasiyet demektir.
- EN: Signal map alone is not enough; always check S/B too.
- TR: Sadece sinyal haritasi yeterli degildir; mutlaka S/B haritasina da bakin.

---

## 6. Tab 2: Geometry Development

### English

This tab scans shield and decay lengths to find better geometry.

### Turkce

Bu sekme kalkan ve bozunma uzunluklarini tarayarak daha iyi geometri bulur.

### Controls / Kontroller

1. Shield start/stop/step
2. Decay start/stop/step
3. Ranking metric
4. Geometry MC samples
5. Benchmark points

### Outputs / Ciktilar

1. Best geometry cards
2. Ranking table
3. Geometry heatmap

### Interpretation / Yorum

- EN: Heatmap shows where geometry performs best.
- TR: Heatmap, hangi geometride performansin daha iyi oldugunu gosterir.
- EN: Flat region means diminishing return.
- TR: Duz bolge, ek iyilestirme kazancinin azaldigini gosterir.

---

## 7. Tab 3: Calibration Lab

### English

Use this tab to tune model scale with reference contour points.

### Turkce

Bu sekme, model olcegini referans kontur noktalarina gore ayarlamak icin kullanilir.

### Controls / Kontroller

1. Anchor points text
2. Target significance
3. Calibration MC samples
4. Background scale scan range and steps
5. Prior center and prior weight

### Outputs / Ciktilar

1. Fitted production_norm
2. Fitted background scale
3. Objective score
4. Anchor fit table
5. Calibrated config JSON download

### Interpretation / Yorum

- EN: Fractional error near 0 means better anchor agreement.
- TR: Fractional error degerinin 0'a yakin olmasi daha iyi uyum demektir.

---

## 8. Tab 4: Geometry + Particle Visualizer

### English

This tab gives intuitive visual understanding of the setup and events.

### Turkce

Bu sekme duzenek ve olaylar icin sezgisel (gorsel) anlama saglar.

### Controls / Kontroller

1. Visualization mass
2. Visualization epsilon
3. Random seed
4. Sampled dark photons
5. Sampled muon tracks
6. Detector gap
7. Vertex matching window
8. Plot half-width
9. Max tracks drawn

- EN: Cherenkov muon veto efficiency is now taken from Sidebar PID settings.
- TR: Cherenkov muon veto verimi artik yan paneldeki PID ayarlarindan alinir.

### Output plots / Cikti grafikleri

#### Beamline Schematic

- EN: Shows target, shield, decay volume, detector plane.
- TR: Hedef, kalkan, bozunma bolgesi ve dedektor duzlemini gosterir.

#### Particle Trajectory Overlay

- EN: Shows toy e+/e- tracks and muon background tracks.
- TR: Basit e+/e- izlerini ve muon arka plan izlerini gosterir.

#### Distribution Panel

1. Decay position distribution
2. Opening angle distribution
3. Detector hit-position distribution
4. Category counts

TR:

1. Bozunma konumu dagilimi
2. Acilma acisi dagilimi
3. Dedektor vurum konumu dagilimi
4. Olay kategori sayilari

#### Reconstructed e+e- Mass Histogram / Yeniden Kurulan e+e- Kutle Histogrami

- EN: Opposite-charge tracks are paired with vertex matching (`z_v` inside decay volume and small `|x_v|`).
- TR: Zit yuklu izler vertex matching ile eslestirilir (`z_v` bozunma bolgesinde ve `|x_v|` kucuk).
- EN: Histogram shows reconstructed pair mass and target-mass line.
- TR: Histogram, yeniden kurulan cift kutlesini ve hedef kutle cizgisini gosterir.

### Table outputs / Tablo ciktilari

- EN: Signal event table and muon track table can be downloaded.
- TR: Sinyal olay tablosu ve muon iz tablosu indirilebilir.
- EN: Electron-candidate and vertex-matched pair tables can also be downloaded.
- TR: Elektron-aday ve vertex-eslesmis cift tablolari da indirilebilir.

---

## 9. Exported files / Disari aktarilan dosyalar

### English

1. `scan_results_student_run.csv`
2. `geometry_optimization_student_run.csv`
3. `calibration_summary_student_run.json`
4. `baseline_calibrated_student_run.json`
5. `signal_events_visualization.csv`
6. `muon_tracks_visualization.csv`
7. `electron_candidates.csv`
8. `vertex_matched_pairs.csv`
9. `visualization_stats.json`

### Turkce

1. `scan_results_student_run.csv`
2. `geometry_optimization_student_run.csv`
3. `calibration_summary_student_run.json`
4. `baseline_calibrated_student_run.json`
5. `signal_events_visualization.csv`
6. `muon_tracks_visualization.csv`
7. `electron_candidates.csv`
8. `vertex_matched_pairs.csv`
9. `visualization_stats.json`

---

## 10. Simple classroom plan / Basit sinif calisma plani

### English

1. Keep baseline values.
2. Run Sensitivity Scan and save top points.
3. Run Geometry Development and compare best geometry.
4. Use Visualizer and take screenshots for slides.
5. Write short conclusion: what changed and why.

### Turkce

1. Baseline degerlerini koruyun.
2. Sensitivity Scan calistirin ve en iyi noktalari kaydedin.
3. Geometry Development calistirin ve en iyi geometriyi karsilastirin.
4. Visualizer kullanip sunum icin ekran goruntusu alin.
5. Kisa sonuc yazin: ne degisti ve neden.

---

## 11. Common mistakes / Sık yapilan hatalar

### English

1. Too few mass/epsilon points.
2. Very low MC samples (noisy results).
3. Looking only at signal, ignoring S/B.
4. Changing many parameters at once.

### Turkce

1. Cok az mass/epsilon noktasi secmek.
2. Cok dusuk MC sayisi (gurultulu sonuclar).
3. Sadece sinyale bakip S/B'yi ihmal etmek.
4. Bir anda cok fazla parametre degistirmek.

---

## 12. Troubleshooting / Sorun giderme

### App does not start / Uygulama acilmiyor

```bash
pip install -r requirements-app.txt
streamlit run streamlit_app.py
```

### Very slow / Cok yavas

- EN: Reduce grid size and MC samples first.
- TR: Once grid boyutunu ve MC sayisini azaltin.

### Strange results / Garip sonuclar

- EN: Check seed, epsilon range, and background settings.
- TR: Seed, epsilon araligi ve arka plan ayarlarini kontrol edin.

---

## 13. Final advice / Son tavsiye

### English

Use this app to learn cause-effect:

1. Change one parameter.
2. Rerun.
3. Compare plots.
4. Explain with physics words.

### Turkce

Bu uygulamayi neden-sonuc iliskisini ogrenmek icin kullanin:

1. Tek bir parametre degistirin.
2. Yeniden calistirin.
3. Grafiklerle karsilastirin.
4. Fiziksel kavramlarla aciklayin.
