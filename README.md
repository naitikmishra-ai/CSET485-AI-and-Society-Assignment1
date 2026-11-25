# CSET485 – AI and Society | Assignment #1

**Student Roll Number:** `S24BCAU0139`  
**Assigned Dataset:** UCI Adult Census Income (`adult.data`)  
**Random Seed (`random_state`):** `139` (Stratified 70% Train / 30% Test Split)

---

## Repository Structure

```text
.
├── Assignment 1 - CSET485.pdf                  # Official assignment specification
├── S24BCAU0139_CSET485_Assignment1.ipynb       # Fully reproducible, pre-executed Jupyter Notebook
├── S24BCAU0139_CSET485_Assignment1_Report.pdf  # Final PDF report (Preprocessing, Parts 1–4)
├── data/
│   └── adult.data                              # Cached UCI Adult Census dataset (32,561 rows)
├── src/
│   └── analysis.py                             # End-to-end statistical & fairness pipeline
├── scripts/
│   ├── build_and_run_notebook.py               # Programmatic notebook builder & kernel runner
│   └── generate_report.py                      # ReportLab PDF report generator + word-count assertions
├── results/
│   └── metrics_summary.json                    # Canonical computed metrics & case studies
├── figures/                                    # Six 300-DPI publication-grade charts
├── requirements.txt
└── .gitignore
```

---

## Headline Experimental Results (`random_state = 139`)

| Section | Key Finding |
|---|---|
| **Preprocessing** | 32,561 raw rows → 2,399 incomplete rows (7.37%) dropped → **30,162 complete rows** (24.89% `>$50K`); 41 non-collinear features; `log1p` on `capital-gain`/`capital-loss`; stratified 70/30 split (**21,113 train / 9,049 test**) with `StandardScaler` fit on train only. |
| **Part 1: Build** | Model A (OLS median `0.2315`, 50.01% flagged high, 71.92% acc, 20.82% out-of-bounds `[−0.3424, 1.1949]`) vs. Model B (Logistic `P ≥ 0.50`, 20.34% flagged high, 84.78% acc, AUC `0.9013`): **2,684 / 9,049 (29.66%) mismatched individuals**. |
| **Part 2.1: Simpson's Paradox** | `age` reverses sign across cohorts: Full = `+0.3473` (`[+0.2968, +0.3979]`), `Age < 45` = **`+1.0783`** (`[+0.9480, +1.2087]`), `Age ≥ 45` = **`-0.4141`** (`[-0.5365, -0.2917]`, `p = 3.34e-11`). |
| **Part 2.2: Omitted-Variable Bias** | Dropping `education-num` leaves accuracy at 83.21% (`AUC 0.8881`) while shifting `occupation_Prof-specialty` by **`+127.37%`** (`+0.5324 → +1.2105`) and `occupation_Exec-managerial` by `+31.46%`. |
| **Part 2.3: Adversarial Subset** | **476 / 9,049 (5.26%)** high-confidence errors (`111` FP with `P ≥ 0.75`, `365` FN with `P ≤ 0.25`); in the 50-row sample (`16` FP, `34` FN), 98.0% have zero capital loss and 90.0% are aged `≥ 30`. |
| **Part 2.4: Fairness Trade-Off** | Sensitive attribute `sex` (`Female` vs. `Male`): improving DP from `0.299` (`t=0.85`) to `0.337` (`t=0.15`, `+12.7%` gain) drops EO from `0.439` to `0.279` (`-36.4%` loss); **trade-off cost `W/Z = 2.87`**. Recommended threshold: **`t = 0.35`** (Acc `83.41%`, PP `0.967`, DP `0.303`, EO `0.248`). |

---

## Reproducing All Results From Scratch

```bash
pip install -r requirements.txt
python3 src/analysis.py
python3 scripts/build_and_run_notebook.py
python3 scripts/generate_report.py
```

Or open and run `S24BCAU0139_CSET485_Assignment1.ipynb` in Jupyter (`Run All`). Every table, chart, and number in `S24BCAU0139_CSET485_Assignment1_Report.pdf` is programmatically populated from `results/metrics_summary.json`.
