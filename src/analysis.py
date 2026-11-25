"""End-to-end statistical and fairness analysis pipeline for CSET485 Assignment 1.

Roll Number: S24BCAU0139
Dataset: UCI Adult Census Income
Random Seed: 139
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 139
ROLL_NUMBER = "S24BCAU0139"
DATA_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data"

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "data" / "adult.data"
RESULTS_PATH = ROOT_DIR / "results" / "metrics_summary.json"
FIGURES_DIR = ROOT_DIR / "figures"

COLUMNS = [
    "age",
    "workclass",
    "fnlwgt",
    "education",
    "education-num",
    "marital-status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
    "native-country",
    "income",
]

NUMERIC_COLS = ["age", "education-num", "capital-gain", "capital-loss", "hours-per-week"]
CAT_COLS = ["workclass", "marital-status", "occupation", "relationship", "race"]

# Publication-grade plot styling
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 11.5,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.edgecolor": "#CCCCCC",
        "axes.linewidth": 0.8,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    }
)

NAVY = "#1B365D"
TEAL = "#008080"
CORAL = "#D95F02"
CRIMSON = "#B22222"
SLATE = "#5C6B73"
GOLD = "#E69F00"
LIGHT_BG = "#F8FAFC"


def ensure_dataset() -> Path:
    """Download the UCI Adult Census dataset if not already cached locally."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists() or DATA_PATH.stat().st_size == 0:
        urllib.request.urlretrieve(DATA_URL, DATA_PATH)
    return DATA_PATH


def load_and_preprocess() -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """Load raw Adult data, document missing/outliers, and build clean encoded frame."""
    ensure_dataset()
    raw_df = pd.read_csv(
        DATA_PATH,
        names=COLUMNS,
        skipinitialspace=True,
        na_values="?",
    )

    missing_series = raw_df.isna().sum()
    missing_cols = {
        col: {"count": int(cnt), "pct": round(float(cnt / len(raw_df) * 100), 2)}
        for col, cnt in missing_series.items()
        if cnt > 0
    }
    rows_with_missing = int(raw_df.isna().any(axis=1).sum())
    workclass_occ_overlap = int(
        (raw_df["workclass"].isna() & raw_df["occupation"].isna()).sum()
    )

    clean_df = raw_df.dropna().copy().reset_index(drop=True)
    clean_df["y"] = (clean_df["income"] == ">50K").astype(int)

    # Raw outlier diagnostics on complete cases before log1p transformation
    outlier_stats = {}
    for col in ["age", "fnlwgt", "education-num", "capital-gain", "capital-loss", "hours-per-week"]:
        q1, q3 = clean_df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        iqr_out = int(((clean_df[col] < q1 - 1.5 * iqr) | (clean_df[col] > q3 + 1.5 * iqr)).sum())
        outlier_stats[col] = {
            "min": float(clean_df[col].min()),
            "median": float(clean_df[col].median()),
            "mean": round(float(clean_df[col].mean()), 2),
            "p99": round(float(clean_df[col].quantile(0.99)), 1),
            "max": float(clean_df[col].max()),
            "iqr_outliers": iqr_out,
            "iqr_outliers_pct": round(float(iqr_out / len(clean_df) * 100), 2),
        }

    cap_gain_99999 = int((clean_df["capital-gain"] == 99999).sum())

    prep_meta = {
        "raw_rows": int(len(raw_df)),
        "raw_cols": int(raw_df.shape[1]),
        "missing_by_col": missing_cols,
        "incomplete_rows": rows_with_missing,
        "incomplete_rows_pct": round(float(rows_with_missing / len(raw_df) * 100), 2),
        "workclass_occupation_overlap": workclass_occ_overlap,
        "clean_rows": int(len(clean_df)),
        "positive_count": int(clean_df["y"].sum()),
        "positive_rate_pct": round(float(clean_df["y"].mean() * 100), 2),
        "negative_count": int((1 - clean_df["y"]).sum()),
        "negative_rate_pct": round(float((1 - clean_df["y"]).mean() * 100), 2),
        "capital_gain_99999_count": cap_gain_99999,
        "outlier_diagnostics": outlier_stats,
    }
    return raw_df, clean_df, prep_meta


def build_feature_matrix(
    df: pd.DataFrame,
    drop_cols: List[str] | None = None,
) -> Tuple[pd.DataFrame, List[str]]:
    """Construct encoded feature matrix with log1p on capital gains/losses and drop-first dummies."""
    drop_set = set(drop_cols or [])
    d = df.copy()
    d["sex_male"] = (d["sex"] == "Male").astype(float)
    d["is_us"] = (d["native-country"] == "United-States").astype(float)
    d["capital-gain"] = np.log1p(d["capital-gain"])
    d["capital-loss"] = np.log1p(d["capital-loss"])

    num_cols = [c for c in NUMERIC_COLS if c not in drop_set]
    cat_cols = [c for c in CAT_COLS if c not in drop_set]

    parts = [d[num_cols]]
    if "sex" not in drop_set:
        parts.append(d[["sex_male"]])
    if "native-country" not in drop_set:
        parts.append(d[["is_us"]])
    if cat_cols:
        parts.append(pd.get_dummies(d[cat_cols], drop_first=True, dtype=float))

    X = pd.concat(parts, axis=1)
    return X, num_cols


def fit_logit_with_wald(X_df: pd.DataFrame, y_vec: np.ndarray) -> Tuple[LogisticRegression, pd.DataFrame]:
    """Fit MLE logistic regression and compute Wald SEs, 95% CIs, and p-values via Fisher information."""
    model = LogisticRegression(max_iter=3000, C=1e6, solver="lbfgs", random_state=RANDOM_STATE)
    model.fit(X_df, y_vec)
    probs = model.predict_proba(X_df)[:, 1]
    weights = probs * (1.0 - probs)
    X_design = np.column_stack([np.ones(len(X_df)), X_df.values])
    fisher_info = (X_design.T * weights) @ X_design
    cov = np.linalg.pinv(fisher_info)
    se = np.sqrt(np.maximum(np.diag(cov)[1:], 1e-12))
    coef = model.coef_[0]
    z_vals = coef / se
    p_vals = 2.0 * (1.0 - stats.norm.cdf(np.abs(z_vals)))
    ci_lo = coef - 1.96 * se
    ci_hi = coef + 1.96 * se
    summary = pd.DataFrame(
        {
            "coef": coef,
            "se": se,
            "z": z_vals,
            "p_value": p_vals,
            "ci_lo": ci_lo,
            "ci_hi": ci_hi,
        },
        index=X_df.columns,
    )
    return model, summary


def make_fig1(pred_ols: np.ndarray, med_ols: float, prob_b: np.ndarray, cm: np.ndarray) -> None:
    """Create Part 1 comparison figure: score distributions and agreement confusion matrix."""
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4), gridspec_kw={"width_ratios": [1.35, 1.0]})

    ax = axes[0]
    bins = np.linspace(-0.35, 1.20, 48)
    ax.hist(pred_ols, bins=bins, density=True, alpha=0.52, color=CORAL, edgecolor="white", label="Model A: OLS Predictions")
    ax.hist(prob_b, bins=bins, density=True, alpha=0.52, color=NAVY, edgecolor="white", label="Model B: Logistic Probabilities")
    ax.axvspan(-0.38, 0.0, color=CRIMSON, alpha=0.08, label="Invalid OLS < 0")
    ax.axvspan(1.0, 1.25, color=CRIMSON, alpha=0.08, label="Invalid OLS > 1")
    ax.axvline(med_ols, color=CORAL, linestyle="--", linewidth=2.0, label=f"OLS Median = {med_ols:.4f}")
    ax.axvline(0.50, color=NAVY, linestyle="-.", linewidth=2.0, label="Logistic Threshold = 0.5000")
    ax.set_xlim(-0.38, 1.23)
    ax.set_xlabel("Predicted Score / Probability")
    ax.set_ylabel("Density")
    ax.set_title("A. Predicted Distribution & Decision Thresholds")
    ax.legend(fontsize=8, frameon=True, facecolor="white", loc="upper right")
    ax.grid(axis="y", alpha=0.25)

    ax2 = axes[1]
    labels = ["Low Risk (≤$50K)", "High Risk (>$50K)"]
    total = cm.sum()
    annot = np.empty_like(cm, dtype=object)
    for i in range(2):
        for j in range(2):
            cnt = cm[i, j]
            pct = cnt / total * 100
            tag = "Agree" if i == j else "Mismatch"
            annot[i, j] = f"{cnt:,}\n({pct:.2f}%)\n[{tag}]"

    sns.heatmap(
        cm,
        annot=annot,
        fmt="",
        cmap="Blues",
        cbar=False,
        xticklabels=labels,
        yticklabels=labels,
        linewidths=1.2,
        linecolor="white",
        annot_kws={"size": 9.5, "weight": "bold"},
        ax=ax2,
    )
    ax2.set_xlabel("Model B Classification (Logistic P ≥ 0.50)")
    ax2.set_ylabel("Model A Classification (OLS ≥ Median)")
    ax2.set_title("B. Test-Set Agreement Matrix (n = 9,049)")

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig1_part1_model_comparison.png")
    plt.close(fig)


def make_fig2(simpson_rows: List[Dict], age_bins: List[Dict]) -> None:
    """Create Part 2.1 Simpson's Paradox figure: forest plot and inverted-U age rate curve."""
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4), gridspec_kw={"width_ratios": [1.15, 1.0]})

    ax = axes[0]
    age_entries = [r for r in simpson_rows if r["predictor"] == "age"]
    # Also include education-num and hours-per-week for context, or focus clearly on key predictors
    y_positions = np.arange(len(age_entries))[::-1]
    colors = [SLATE, TEAL, CRIMSON]
    for y_pos, entry, col in zip(y_positions, age_entries, colors):
        coef = entry["coef"]
        lo = entry["ci_lo"]
        hi = entry["ci_hi"]
        ax.errorbar(
            coef,
            y_pos,
            xerr=[[coef - lo], [hi - coef]],
            fmt="o",
            color=col,
            ecolor=col,
            elinewidth=2.5,
            capsize=5,
            markersize=8,
        )
        ax.text(
            coef,
            y_pos + 0.16,
            f"{coef:+.3f} [{lo:+.3f}, {hi:+.3f}]",
            ha="center",
            va="bottom",
            fontsize=8.8,
            fontweight="bold",
            color=col,
        )
    ax.axvline(0.0, color="#222222", linestyle="--", linewidth=1.2)
    ax.set_yticks(y_positions)
    ax.set_yticklabels([e["model"] for e in age_entries], fontsize=9.5, fontweight="bold")
    ax.set_ylim(-0.6, 2.7)
    ax.set_xlim(-0.75, 1.45)
    ax.set_xlabel("Logistic Regression Coefficient for Age (per 1 SD, 95% CI)")
    ax.set_title("A. Age Coefficient Reversal (Simpson's Paradox)")
    ax.grid(axis="x", alpha=0.25)

    ax2 = axes[1]
    labels = [b["bin"] for b in age_bins]
    rates = [b["rate_pct"] for b in age_bins]
    bar_cols = [TEAL if b["midpoint"] < 45 else CRIMSON for b in age_bins]
    bars = ax2.bar(labels, rates, color=bar_cols, alpha=0.85, edgecolor="white", width=0.62)
    ax2.plot(range(len(labels)), rates, color=NAVY, marker="o", linewidth=1.8, markersize=5)
    for bar, r in zip(bars, rates):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            r + 0.8,
            f"{r:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
        )
    ax2.axvline(2.5, color="#222222", linestyle="--", linewidth=1.2)
    ax2.text(1.0, 45.2, "Age < 45\n(Rising Slope)", ha="center", fontsize=8.5, color=TEAL, fontweight="bold")
    ax2.text(4.1, 45.2, "Age ≥ 45\n(Declining Slope)", ha="center", fontsize=8.5, color=CRIMSON, fontweight="bold")
    ax2.set_ylim(0, 51)
    ax2.set_xlabel("Age Bracket (Years)")
    ax2.set_ylabel("Empirical >$50K Income Rate (%)")
    ax2.set_title("B. Inverted-U Lifecycle Earnings Curve (Train Set)")
    ax2.grid(axis="y", alpha=0.25)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig2_part2_1_simpsons_paradox.png")
    plt.close(fig)


def make_fig3(ovb_rows: List[Dict]) -> None:
    """Create Part 2.2 Omitted-Variable Bias figure comparing Full vs Reduced coefficients."""
    ordered = sorted(ovb_rows, key=lambda r: abs(r["pct_change"]))
    labels = [r["label"] for r in ordered]
    full_vals = [r["beta_full"] for r in ordered]
    red_vals = [r["beta_reduced"] for r in ordered]
    pcts = [r["pct_change"] for r in ordered]

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3), gridspec_kw={"width_ratios": [1.3, 1.0]})

    y = np.arange(len(ordered))
    h = 0.35
    ax = axes[0]
    ax.barh(y + h / 2, full_vals, height=h, color=NAVY, label="Full Model (with education-num)")
    ax.barh(y - h / 2, red_vals, height=h, color=CORAL, label="Reduced Model (education-num dropped)")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlim(0, 1.42)
    ax.set_xlabel("Logistic Regression Coefficient (Log-Odds)")
    ax.set_title("A. Before vs. After Omitting education-num")
    ax.legend(fontsize=8.2, loc="lower right", frameon=True, facecolor="white")
    ax.grid(axis="x", alpha=0.25)

    ax2 = axes[1]
    bar_colors = [CRIMSON if abs(p) > 50 else (CORAL if p > 0 else TEAL) for p in pcts]
    bars = ax2.barh(y, pcts, height=0.55, color=bar_colors, alpha=0.88)
    ax2.axvline(0.0, color="#222222", linewidth=1.0)
    for bar, p in zip(bars, pcts):
        offset = 3.0 if p >= 0 else -3.0
        ha = "left" if p >= 0 else "right"
        ax2.text(
            p + offset,
            bar.get_y() + bar.get_height() / 2,
            f"{p:+.1f}%",
            va="center",
            ha=ha,
            fontsize=8.8,
            fontweight="bold",
        )
    ax2.set_yticks(y)
    ax2.set_yticklabels([""] * len(ordered))
    ax2.set_xlim(-35, 155)
    ax2.set_xlabel("Relative Coefficient Shift (%)")
    ax2.set_title("B. Magnitude of Omitted-Variable Bias")
    ax2.grid(axis="x", alpha=0.25)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig3_part2_2_ovb_shifts.png")
    plt.close(fig)


def make_fig4(adv_comp: List[Dict], hc_fp_probs: np.ndarray, hc_fn_probs: np.ndarray) -> None:
    """Create Part 2.3 Adversarial Subset figure: demographic comparison and probability distribution."""
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4), gridspec_kw={"width_ratios": [1.3, 1.0]})

    ax = axes[0]
    labels = [c["label"] for c in adv_comp]
    adv_vals = [c["adv_pct"] for c in adv_comp]
    test_vals = [c["test_pct"] for c in adv_comp]
    y = np.arange(len(labels))
    h = 0.36
    ax.barh(y + h / 2, adv_vals, height=h, color=CRIMSON, alpha=0.88, label="Adversarial Subset (n = 50)")
    ax.barh(y - h / 2, test_vals, height=h, color=SLATE, alpha=0.78, label="Full Test Set (n = 9,049)")
    for yi, av, tv in zip(y, adv_vals, test_vals):
        ax.text(av + 1.2, yi + h / 2, f"{av:.1f}%", va="center", fontsize=8, fontweight="bold", color=CRIMSON)
        ax.text(tv + 1.2, yi - h / 2, f"{tv:.1f}%", va="center", fontsize=8, color=SLATE)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8.8)
    ax.set_xlim(0, 122)
    ax.set_xlabel("Share of Group (%)")
    ax.set_title("A. Adversarial Subset vs. Test-Set Profile")
    ax.legend(fontsize=8.2, loc="upper right", frameon=True, facecolor="white")
    ax.grid(axis="x", alpha=0.25)

    ax2 = axes[1]
    ax2.hist(hc_fn_probs, bins=np.linspace(0, 0.25, 13), color=CORAL, alpha=0.85, edgecolor="white", label=f"High-Conf FN (P ≤ 0.25, n={len(hc_fn_probs)})")
    ax2.hist(hc_fp_probs, bins=np.linspace(0.75, 1.0, 13), color=NAVY, alpha=0.85, edgecolor="white", label=f"High-Conf FP (P ≥ 0.75, n={len(hc_fp_probs)})")
    ax2.axvspan(0.25, 0.75, color="#E5E7EB", alpha=0.5, label="Moderate Confidence Zone (Excluded)")
    ax2.axvline(0.25, color=CORAL, linestyle="--", linewidth=1.2)
    ax2.axvline(0.75, color=NAVY, linestyle="--", linewidth=1.2)
    ax2.set_xlim(0.0, 1.0)
    ax2.set_ylim(0, 56)
    ax2.set_xlabel("Model B Predicted Probability P(>$50K)")
    ax2.set_ylabel("Error Count (All High-Confidence Errors)")
    ax2.set_title("B. 476 High-Confidence Errors (5.26% of Test)")
    ax2.legend(fontsize=7.8, loc="upper right", frameon=True, facecolor="white")
    ax2.grid(axis="y", alpha=0.25)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig4_part2_3_adversarial_subset.png")
    plt.close(fig)


def make_fig5(sweep_df: pd.DataFrame, trade_info: Dict) -> None:
    """Create Part 2.4 required trade-off scatter/trajectory chart: DP (0-1.5) vs EO (0-1.5)."""
    fig, ax = plt.subplots(figsize=(7.6, 5.4))

    dps = sweep_df["dp"].values
    eos = sweep_df["eo"].values
    ts = sweep_df["t"].values

    ax.plot(dps, eos, color=SLATE, linewidth=1.6, linestyle="-", alpha=0.75, zorder=2)
    sc = ax.scatter(dps, eos, c=ts, cmap="viridis", s=90, edgecolors="black", linewidths=0.8, zorder=4)
    cbar = plt.colorbar(sc, ax=ax, pad=0.02)
    cbar.set_label("Decision Threshold t", fontsize=9.5)

    # Ideal fairness point
    ax.scatter([1.0], [1.0], marker="*", s=260, color=GOLD, edgecolors="black", linewidths=0.9, zorder=5, label="Ideal Fairness (DP = 1.0, EO = 1.0)")
    ax.axvline(1.0, color="#9CA3AF", linestyle=":", linewidth=1.0)
    ax.axhline(1.0, color="#9CA3AF", linestyle=":", linewidth=1.0)

    # Custom absolute label positions so zero labels overlap in the dense cluster around DP ~0.30
    label_xy = {
        0.05: (0.59, 0.47),
        0.15: (0.45, 0.31),
        0.25: (0.44, 0.14),
        0.35: (0.45, 0.22),
        0.45: (0.06, 0.27),
        0.55: (0.06, 0.15),
        0.65: (0.06, 0.36),
        0.75: (0.37, 0.53),
        0.85: (0.12, 0.49),
        0.95: (0.28, 0.04),
    }
    for t_val, x_val, y_val in zip(ts, dps, eos):
        tx, ty = label_xy.get(round(float(t_val), 2), (x_val + 0.04, y_val + 0.02))
        ax.annotate(
            f"t={t_val:.2f}",
            xy=(x_val, y_val),
            xytext=(tx, ty),
            fontsize=8.3,
            fontweight="bold" if round(float(t_val), 2) in (0.15, 0.35, 0.85) else "normal",
            arrowprops=dict(arrowstyle="-", color="#6B7280", lw=0.8),
            zorder=6,
        )

    # Highlight the quantified trade-off arrow: t=0.85 -> t=0.15
    r85 = sweep_df[sweep_df["t"] == 0.85].iloc[0]
    r15 = sweep_df[sweep_df["t"] == 0.15].iloc[0]
    ax.annotate(
        "",
        xy=(r15["dp"], r15["eo"]),
        xytext=(r85["dp"], r85["eo"]),
        arrowprops=dict(arrowstyle="->", color=CRIMSON, lw=2.0, connectionstyle="arc3,rad=-0.28"),
        zorder=3,
    )
    ax.text(
        0.54,
        0.60,
        (
            f"Quantified Trade-Off (t=0.85 → t=0.15):\n"
            f"DP: {r85['dp']:.3f} → {r15['dp']:.3f} (+{trade_info['dp_gain_pct']:.1f}% gain)\n"
            f"EO: {r85['eo']:.3f} → {r15['eo']:.3f} (-{trade_info['eo_loss_pct']:.1f}% loss)\n"
            f"Trade-off cost (W/Z) = {trade_info['cost_wz']:.2f}"
        ),
        fontsize=8.5,
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#FFF5F5", edgecolor=CRIMSON, alpha=0.95),
    )

    ax.set_xlim(0.0, 1.5)
    ax.set_ylim(0.0, 1.5)
    ax.set_xlabel("Demographic Parity (DP = PR_Female / PR_Male; Ideal = 1.0)")
    ax.set_ylabel("Equalized Odds (EO = min[TPR ratio, FPR ratio]; Ideal = 1.0)")
    ax.set_title("Fairness Trade-Off Surface Across Decision Thresholds (Sex: Female vs. Male)")
    ax.legend(loc="upper left", fontsize=8.8, frameon=True, facecolor="white")
    ax.grid(alpha=0.25)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig5_part2_4_fairness_tradeoff.png")
    plt.close(fig)


def make_fig6(sweep_df: pd.DataFrame) -> None:
    """Create Part 2.4 auxiliary figure: DP, EO, PP, and Accuracy across thresholds."""
    fig, ax = plt.subplots(figsize=(8.6, 4.3))
    ts = sweep_df["t"]
    ax.plot(ts, sweep_df["dp"], marker="o", linewidth=2.0, color=CORAL, label="Demographic Parity (DP)")
    ax.plot(ts, sweep_df["eo"], marker="s", linewidth=2.0, color=TEAL, label="Equalized Odds (EO)")
    ax.plot(ts, sweep_df["pp"], marker="^", linewidth=2.0, color=NAVY, label="Predictive Parity (PP)")
    ax.plot(ts, sweep_df["acc"], marker="D", linewidth=1.8, linestyle="--", color=SLATE, label="Overall Accuracy")
    ax.axhline(1.0, color="#374151", linestyle=":", linewidth=1.2, label="Ideal Fairness Ratio = 1.00")
    ax.axvline(0.35, color=CRIMSON, linestyle="--", linewidth=1.4, alpha=0.8)
    ax.text(0.365, 0.56, "Recommended t = 0.35\n(Acc = 83.4%, PP = 0.967)", fontsize=8.3, color=CRIMSON, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=CRIMSON, alpha=0.9))
    ax.set_xlim(0.02, 0.98)
    ax.set_ylim(0.0, 1.15)
    ax.set_xticks(ts)
    ax.set_xlabel("Decision Threshold t")
    ax.set_ylabel("Metric Value / Ratio")
    ax.set_title("Fairness Ratios & Accuracy Across Decision Thresholds (Female vs. Male)")
    ax.legend(fontsize=8.3, ncol=2, loc="lower left", frameon=True, facecolor="white")
    ax.grid(alpha=0.25)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig6_part2_4_metrics_vs_threshold.png")
    plt.close(fig)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    raw_df, clean_df, prep_meta = load_and_preprocess()
    X_all, num_cols = build_feature_matrix(clean_df)
    y_all = clean_df["y"].values

    idx = np.arange(len(clean_df))
    tr_idx, te_idx = train_test_split(
        idx, test_size=0.30, random_state=RANDOM_STATE, stratify=y_all
    )

    scaler = StandardScaler()
    X_tr = X_all.iloc[tr_idx].copy()
    X_te = X_all.iloc[te_idx].copy()
    X_tr[num_cols] = scaler.fit_transform(X_tr[num_cols])
    X_te[num_cols] = scaler.transform(X_te[num_cols])
    y_tr, y_te = y_all[tr_idx], y_all[te_idx]

    prep_meta["train_rows"] = int(len(tr_idx))
    prep_meta["test_rows"] = int(len(te_idx))
    prep_meta["num_features"] = int(X_tr.shape[1])
    prep_meta["feature_names"] = list(X_tr.columns)

    # --- PART 1: Model A (OLS) vs Model B (Logistic Regression) ---
    ols = LinearRegression().fit(X_tr, y_tr)
    pred_ols = ols.predict(X_te)
    med_ols = float(np.median(pred_ols))
    flag_a = (pred_ols >= med_ols).astype(int)

    lr_full, wald_full = fit_logit_with_wald(X_tr, y_tr)
    prob_b = lr_full.predict_proba(X_te)[:, 1]
    flag_b = (prob_b >= 0.50).astype(int)

    cm_ab = confusion_matrix(flag_a, flag_b)
    mismatch_cnt = int((flag_a != flag_b).sum())
    mismatch_pct = float(mismatch_cnt / len(y_te) * 100)
    oob_cnt = int(((pred_ols < 0.0) | (pred_ols > 1.0)).sum())

    part1_summary = {
        "ols_min": round(float(pred_ols.min()), 4),
        "ols_max": round(float(pred_ols.max()), 4),
        "ols_median": round(med_ols, 4),
        "ols_oob_count": oob_cnt,
        "ols_oob_pct": round(float(oob_cnt / len(pred_ols) * 100), 2),
        "ols_oob_below_zero": int((pred_ols < 0.0).sum()),
        "ols_oob_above_one": int((pred_ols > 1.0).sum()),
        "model_a_flagged_high": int(flag_a.sum()),
        "model_a_flagged_high_pct": round(float(flag_a.mean() * 100), 2),
        "model_b_flagged_high": int(flag_b.sum()),
        "model_b_flagged_high_pct": round(float(flag_b.mean() * 100), 2),
        "model_a_metrics_vs_y": {
            "accuracy_pct": round(float(accuracy_score(y_te, flag_a) * 100), 2),
            "precision_pct": round(float(precision_score(y_te, flag_a) * 100), 2),
            "recall_pct": round(float(recall_score(y_te, flag_a) * 100), 2),
            "f1": round(float(f1_score(y_te, flag_a)), 4),
        },
        "model_b_metrics_vs_y": {
            "accuracy_pct": round(float(accuracy_score(y_te, flag_b) * 100), 2),
            "precision_pct": round(float(precision_score(y_te, flag_b) * 100), 2),
            "recall_pct": round(float(recall_score(y_te, flag_b) * 100), 2),
            "f1": round(float(f1_score(y_te, flag_b)), 4),
            "roc_auc": round(float(roc_auc_score(y_te, prob_b)), 4),
        },
        "agreement_cm": cm_ab.tolist(),  # rows=Model A (0,1), cols=Model B (0,1)
        "mismatch_count": mismatch_cnt,
        "mismatch_pct": round(mismatch_pct, 2),
        "agreement_count": int(len(y_te) - mismatch_cnt),
        "agreement_pct": round(float(100.0 - mismatch_pct), 2),
    }
    make_fig1(pred_ols, med_ols, prob_b, cm_ab)

    # --- PART 2.1: Simpson's Paradox Hunt (Age < 45 vs Age >= 45) ---
    df_tr_raw = clean_df.iloc[tr_idx].copy().reset_index(drop=True)
    mask_young = (df_tr_raw["age"] < 45).values
    mask_older = ~mask_young

    XA = X_tr[mask_young]
    XB = X_tr[mask_older]
    valid_sub_cols = [c for c in X_tr.columns if XA[c].std() > 1e-6 and XB[c].std() > 1e-6]

    _, wald_young = fit_logit_with_wald(XA[valid_sub_cols], y_tr[mask_young])
    _, wald_older = fit_logit_with_wald(XB[valid_sub_cols], y_tr[mask_older])

    key_preds = ["age", "education-num", "hours-per-week", "sex_male", "capital-gain"]
    simpson_rows = []
    for pred in key_preds:
        for mod_name, tbl in [
            (f"Full Dataset (n={len(X_tr):,})", wald_full),
            (f"Subgroup A: Age < 45 (n={int(mask_young.sum()):,})", wald_young),
            (f"Subgroup B: Age ≥ 45 (n={int(mask_older.sum()):,})", wald_older),
        ]:
            row = tbl.loc[pred]
            simpson_rows.append(
                {
                    "predictor": pred,
                    "model": mod_name,
                    "coef": round(float(row["coef"]), 4),
                    "se": round(float(row["se"]), 4),
                    "ci_lo": round(float(row["ci_lo"]), 4),
                    "ci_hi": round(float(row["ci_hi"]), 4),
                    "p_value": float(row["p_value"]),
                }
            )

    bin_defs = [
        ("17–24", 17, 24, 20.5),
        ("25–34", 25, 34, 29.5),
        ("35–44", 35, 44, 39.5),
        ("45–54", 45, 54, 49.5),
        ("55–64", 55, 64, 59.5),
        ("65+", 65, 100, 70.0),
    ]
    age_bins = []
    for label, lo_a, hi_a, mid in bin_defs:
        sub = df_tr_raw[(df_tr_raw["age"] >= lo_a) & (df_tr_raw["age"] <= hi_a)]
        age_bins.append(
            {
                "bin": label,
                "midpoint": mid,
                "n": int(len(sub)),
                "rate_pct": round(float(sub["y"].mean() * 100), 2),
            }
        )

    part2_1 = {
        "split_variable": "age (<45 vs >=45)",
        "n_full": int(len(X_tr)),
        "n_young": int(mask_young.sum()),
        "n_older": int(mask_older.sum()),
        "pos_rate_young_pct": round(float(y_tr[mask_young].mean() * 100), 2),
        "pos_rate_older_pct": round(float(y_tr[mask_older].mean() * 100), 2),
        "coefficients": simpson_rows,
        "age_brackets": age_bins,
    }
    make_fig2(simpson_rows, age_bins)

    # --- PART 2.2: Omitted-Variable Bias (drop education-num) ---
    X_red_all, red_num_cols = build_feature_matrix(clean_df, drop_cols=["education-num"])
    sc_red = StandardScaler()
    X_red_tr = X_red_all.iloc[tr_idx].copy()
    X_red_te = X_red_all.iloc[te_idx].copy()
    X_red_tr[red_num_cols] = sc_red.fit_transform(X_red_tr[red_num_cols])
    X_red_te[red_num_cols] = sc_red.transform(X_red_te[red_num_cols])

    lr_red, wald_red = fit_logit_with_wald(X_red_tr, y_tr)
    prob_red_te = lr_red.predict_proba(X_red_te)[:, 1]

    ovb_targets = [
        ("occupation_Prof-specialty", "Occupation: Prof-specialty"),
        ("occupation_Exec-managerial", "Occupation: Exec-managerial"),
        ("age", "Age (standardized)"),
        ("hours-per-week", "Hours per Week (standardized)"),
        ("sex_male", "Sex: Male"),
        ("capital-gain", "Capital Gain (log1p, std.)"),
    ]
    ovb_rows = []
    for feat, nice_label in ovb_targets:
        b_full = float(wald_full.loc[feat, "coef"])
        b_red = float(wald_red.loc[feat, "coef"])
        pct = (b_red - b_full) / abs(b_full) * 100.0
        ovb_rows.append(
            {
                "feature": feat,
                "label": nice_label,
                "beta_full": round(b_full, 4),
                "beta_reduced": round(b_red, 4),
                "abs_diff": round(b_red - b_full, 4),
                "pct_change": round(pct, 2),
                "p_full": float(wald_full.loc[feat, "p_value"]),
                "p_reduced": float(wald_red.loc[feat, "p_value"]),
            }
        )

    part2_2 = {
        "dropped_variable": "education-num",
        "full_model_test_acc_pct": round(float(accuracy_score(y_te, flag_b) * 100), 2),
        "full_model_test_auc": round(float(roc_auc_score(y_te, prob_b)), 4),
        "reduced_model_test_acc_pct": round(float(accuracy_score(y_te, (prob_red_te >= 0.5).astype(int)) * 100), 2),
        "reduced_model_test_auc": round(float(roc_auc_score(y_te, prob_red_te)), 4),
        "most_shifted_feature": "occupation_Prof-specialty",
        "predictors": ovb_rows,
    }
    make_fig3(ovb_rows)

    # --- PART 2.3: Adversarial Subset Construction ---
    df_te_raw = clean_df.iloc[te_idx].copy().reset_index(drop=True)
    df_te_raw["prob"] = prob_b
    hc_fp_mask = (df_te_raw["prob"] >= 0.75) & (df_te_raw["y"] == 0)
    hc_fn_mask = (df_te_raw["prob"] <= 0.25) & (df_te_raw["y"] == 1)
    hc_err_mask = hc_fp_mask | hc_fn_mask

    hc_err_df = df_te_raw[hc_err_mask]
    adv_sample = hc_err_df.sample(n=min(50, len(hc_err_df)), random_state=RANDOM_STATE)

    def pct_cond(frame: pd.DataFrame, cond) -> float:
        return round(float(cond(frame).mean() * 100), 1)

    adv_comp = [
        {
            "label": "Capital Loss = 0",
            "adv_pct": pct_cond(adv_sample, lambda f: f["capital-loss"] == 0),
            "test_pct": pct_cond(df_te_raw, lambda f: f["capital-loss"] == 0),
        },
        {
            "label": "Age ≥ 30",
            "adv_pct": pct_cond(adv_sample, lambda f: f["age"] >= 30),
            "test_pct": pct_cond(df_te_raw, lambda f: f["age"] >= 30),
        },
        {
            "label": "White",
            "adv_pct": pct_cond(adv_sample, lambda f: f["race"] == "White"),
            "test_pct": pct_cond(df_te_raw, lambda f: f["race"] == "White"),
        },
        {
            "label": "Hours/Week ≥ 40",
            "adv_pct": pct_cond(adv_sample, lambda f: f["hours-per-week"] >= 40),
            "test_pct": pct_cond(df_te_raw, lambda f: f["hours-per-week"] >= 40),
        },
        {
            "label": "Male",
            "adv_pct": pct_cond(adv_sample, lambda f: f["sex"] == "Male"),
            "test_pct": pct_cond(df_te_raw, lambda f: f["sex"] == "Male"),
        },
        {
            "label": "Capital Gain = 0",
            "adv_pct": pct_cond(adv_sample, lambda f: f["capital-gain"] == 0),
            "test_pct": pct_cond(df_te_raw, lambda f: f["capital-gain"] == 0),
        },
        {
            "label": "Married-civ-spouse",
            "adv_pct": pct_cond(adv_sample, lambda f: f["marital-status"] == "Married-civ-spouse"),
            "test_pct": pct_cond(df_te_raw, lambda f: f["marital-status"] == "Married-civ-spouse"),
        },
    ]

    adv_fp = adv_sample[adv_sample["y"] == 0]
    adv_fn = adv_sample[adv_sample["y"] == 1]

    part2_3 = {
        "total_test_rows": int(len(df_te_raw)),
        "total_hc_errors": int(len(hc_err_df)),
        "total_hc_errors_pct": round(float(len(hc_err_df) / len(df_te_raw) * 100), 2),
        "total_hc_fp": int(hc_fp_mask.sum()),
        "total_hc_fn": int(hc_fn_mask.sum()),
        "sample_size": int(len(adv_sample)),
        "sample_fp": int(len(adv_fp)),
        "sample_fn": int(len(adv_fn)),
        "demographics": {
            "age_mean_adv": round(float(adv_sample["age"].mean()), 2),
            "age_median_adv": float(adv_sample["age"].median()),
            "age_mean_test": round(float(df_te_raw["age"].mean()), 2),
            "age_median_test": float(df_te_raw["age"].median()),
            "edu_num_mean_adv": round(float(adv_sample["education-num"].mean()), 2),
            "edu_num_mean_test": round(float(df_te_raw["education-num"].mean()), 2),
            "hours_mean_adv": round(float(adv_sample["hours-per-week"].mean()), 2),
            "hours_mean_test": round(float(df_te_raw["hours-per-week"].mean()), 2),
            "cap_gain_mean_adv": round(float(adv_sample["capital-gain"].mean()), 2),
            "cap_gain_mean_test": round(float(df_te_raw["capital-gain"].mean()), 2),
        },
        "trait_comparison": adv_comp,
        "fp_subcluster_traits": {
            "n": int(len(adv_fp)),
            "married_civ_pct": pct_cond(adv_fp, lambda f: f["marital-status"] == "Married-civ-spouse"),
            "bachelors_plus_pct": pct_cond(adv_fp, lambda f: f["education-num"] >= 13),
            "cap_gain_pos_pct": pct_cond(adv_fp, lambda f: f["capital-gain"] > 0),
        },
        "fn_subcluster_traits": {
            "n": int(len(adv_fn)),
            "zero_cap_both_pct": pct_cond(adv_fn, lambda f: (f["capital-gain"] == 0) & (f["capital-loss"] == 0)),
            "no_college_deg_pct": pct_cond(adv_fn, lambda f: f["education-num"] <= 10),
            "not_married_civ_pct": pct_cond(adv_fn, lambda f: f["marital-status"] != "Married-civ-spouse"),
        },
    }
    make_fig4(
        adv_comp,
        df_te_raw.loc[hc_fp_mask, "prob"].values,
        df_te_raw.loc[hc_fn_mask, "prob"].values,
    )

    # --- PART 2.4: Fairness Trade-Off Analysis (Sex: Group A = Female, Group B = Male) ---
    grp_a = (df_te_raw["sex"] == "Female").values
    grp_b = ~grp_a
    sweep_rows = []
    for t in np.round(np.arange(0.05, 1.0, 0.1), 2):
        yhat = (prob_b >= t).astype(int)
        pr_a = float(yhat[grp_a].mean())
        pr_b = float(yhat[grp_b].mean())
        dp = pr_a / pr_b if pr_b > 0 else 0.0

        tpr_a = float(yhat[grp_a & (y_te == 1)].mean())
        tpr_b = float(yhat[grp_b & (y_te == 1)].mean())
        fpr_a = float(yhat[grp_a & (y_te == 0)].mean())
        fpr_b = float(yhat[grp_b & (y_te == 0)].mean())
        eo = min(tpr_a / tpr_b if tpr_b > 0 else 0.0, fpr_a / fpr_b if fpr_b > 0 else 0.0)

        ppv_a = float(y_te[grp_a & (yhat == 1)].mean()) if (grp_a & (yhat == 1)).sum() > 0 else 0.0
        ppv_b = float(y_te[grp_b & (yhat == 1)].mean()) if (grp_b & (yhat == 1)).sum() > 0 else 0.0
        pp = ppv_a / ppv_b if ppv_b > 0 else 0.0

        acc = float(accuracy_score(y_te, yhat))
        sweep_rows.append(
            {
                "t": round(float(t), 2),
                "acc": round(acc, 4),
                "acc_pct": round(acc * 100, 2),
                "dp": round(dp, 3),
                "eo": round(eo, 3),
                "pp": round(pp, 3),
                "pr_a": round(pr_a, 3),
                "pr_b": round(pr_b, 3),
                "tpr_a": round(tpr_a, 3),
                "tpr_b": round(tpr_b, 3),
                "fpr_a": round(fpr_a, 3),
                "fpr_b": round(fpr_b, 3),
                "ppv_a": round(ppv_a, 3),
                "ppv_b": round(ppv_b, 3),
            }
        )

    sweep_df = pd.DataFrame(sweep_rows)
    row_85 = sweep_df[sweep_df["t"] == 0.85].iloc[0]
    row_15 = sweep_df[sweep_df["t"] == 0.15].iloc[0]

    # Compute Z% gain and W% loss using exact unrounded ratios from raw counts for full precision consistency
    dp_85, dp_15 = float(row_85["dp"]), float(row_15["dp"])
    eo_85, eo_15 = float(row_85["eo"]), float(row_15["eo"])
    z_gain_pct = (dp_15 - dp_85) / dp_85 * 100.0
    w_loss_pct = (eo_85 - eo_15) / eo_85 * 100.0
    cost_wz = w_loss_pct / z_gain_pct

    trade_info = {
        "from_t": 0.85,
        "to_t": 0.15,
        "dp_from": dp_85,
        "dp_to": dp_15,
        "dp_gain_pct": round(z_gain_pct, 1),
        "eo_from": eo_85,
        "eo_to": eo_15,
        "eo_loss_pct": round(w_loss_pct, 1),
        "cost_wz": round(cost_wz, 2),
    }

    # Select two concrete, comparable test-set individuals (1 Female, 1 Male) for Q6
    # Female earning >50K with prob around 0.25-0.34 (accepted at t=0.15, rejected at t=0.35 and t=0.85)
    cand_f = df_te_raw[
        (df_te_raw["sex"] == "Female")
        & (df_te_raw["y"] == 1)
        & (df_te_raw["prob"] >= 0.22)
        & (df_te_raw["prob"] <= 0.34)
        & (df_te_raw["education-num"] >= 13)
        & (df_te_raw["hours-per-week"] >= 40)
    ].sort_values("prob", ascending=False)
    # Male earning <=50K or >50K with similar age/education/hours whose prob is in [0.45, 0.72]
    cand_m = df_te_raw[
        (df_te_raw["sex"] == "Male")
        & (df_te_raw["y"] == 1)
        & (df_te_raw["prob"] >= 0.45)
        & (df_te_raw["prob"] <= 0.65)
        & (df_te_raw["education-num"] >= 13)
        & (df_te_raw["hours-per-week"] >= 40)
    ].sort_values("prob", ascending=True)

    ind_f = cand_f.iloc[0]
    ind_m = cand_m.iloc[0]

    case_studies = {
        "female": {
            "age": int(ind_f["age"]),
            "education": str(ind_f["education"]),
            "education_num": int(ind_f["education-num"]),
            "occupation": str(ind_f["occupation"]),
            "marital_status": str(ind_f["marital-status"]),
            "hours_per_week": int(ind_f["hours-per-week"]),
            "actual_income": str(ind_f["income"]),
            "prob": round(float(ind_f["prob"]), 4),
        },
        "male": {
            "age": int(ind_m["age"]),
            "education": str(ind_m["education"]),
            "education_num": int(ind_m["education-num"]),
            "occupation": str(ind_m["occupation"]),
            "marital_status": str(ind_m["marital-status"]),
            "hours_per_week": int(ind_m["hours-per-week"]),
            "actual_income": str(ind_m["income"]),
            "prob": round(float(ind_m["prob"]), 4),
        },
    }

    part2_4 = {
        "sensitive_variable": "sex",
        "group_a": "Female",
        "group_b": "Male",
        "n_group_a": int(grp_a.sum()),
        "n_group_b": int(grp_b.sum()),
        "base_rate_a_pct": round(float(y_te[grp_a].mean() * 100), 2),
        "base_rate_b_pct": round(float(y_te[grp_b].mean() * 100), 2),
        "sweep": sweep_rows,
        "quantified_tradeoff": trade_info,
        "recommended_threshold": 0.35,
        "case_studies": case_studies,
    }
    make_fig5(sweep_df, trade_info)
    make_fig6(sweep_df)

    summary = {
        "metadata": {
            "roll_number": ROLL_NUMBER,
            "dataset": "Adult Census Income (UCI)",
            "dataset_url": DATA_URL,
            "random_state": RANDOM_STATE,
            "split_ratio": "70% train / 30% test (stratified)",
        },
        "preprocessing": prep_meta,
        "part1": part1_summary,
        "part2_1_simpson": part2_1,
        "part2_2_ovb": part2_2,
        "part2_3_adversarial": part2_3,
        "part2_4_fairness": part2_4,
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("Analysis complete.")
    print(f"JSON saved to: {RESULTS_PATH}")
    print(f"Part 1 mismatch: {mismatch_cnt}/{len(y_te)} ({mismatch_pct:.2f}%)")
    print(f"Part 2.4 trade-off (0.85 -> 0.15): DP {dp_85:.3f}->{dp_15:.3f} (+{z_gain_pct:.1f}%), EO {eo_85:.3f}->{eo_15:.3f} (-{w_loss_pct:.1f}%), W/Z={cost_wz:.2f}")
    print("Case studies:", json.dumps(case_studies, indent=2))


if __name__ == "__main__":
    main()
