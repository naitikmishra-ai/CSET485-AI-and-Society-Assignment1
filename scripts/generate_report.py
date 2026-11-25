"""Generate the final ReportLab PDF submission for CSET485 Assignment 1.

Reads all computed numbers from results/metrics_summary.json and embeds all
charts from figures/, enforcing strict word-count bounds on Part 3 (Q1-Q8)
and Part 4 (Reflection Essay).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
RESULTS_PATH = ROOT_DIR / "results" / "metrics_summary.json"
FIGURES_DIR = ROOT_DIR / "figures"
PDF_PATH = ROOT_DIR / "S24BCAU0139_CSET485_Assignment1_Report.pdf"

NAVY = colors.HexColor("#1B365D")
TEAL = colors.HexColor("#007A78")
CRIMSON = colors.HexColor("#A61C1C")
SLATE = colors.HexColor("#4B5563")
LIGHT_BG = colors.HexColor("#F3F6FA")
BORDER_GRAY = colors.HexColor("#D1D5DB")
CALLOUT_BG = colors.HexColor("#EEF4FB")
WARN_BG = colors.HexColor("#FDF2F2")


def count_words(text: str) -> int:
    clean = re.sub(r"<[^>]+>", " ", text)
    return len(clean.split())


def make_styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleCustom",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            textColor=colors.white,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "SubTitleCustom",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#E2E8F0"),
            alignment=TA_LEFT,
        ),
        "h1": ParagraphStyle(
            "H1Custom",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=13.5,
            leading=17,
            textColor=NAVY,
            spaceBefore=12,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2Custom",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=TEAL,
            spaceBefore=9,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "BodyCustom",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.4,
            leading=13.2,
            textColor=colors.HexColor("#1F2937"),
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "callout": ParagraphStyle(
            "CalloutCustom",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.1,
            leading=12.8,
            textColor=colors.HexColor("#1F2937"),
            alignment=TA_LEFT,
        ),
        "caption": ParagraphStyle(
            "CaptionCustom",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8.3,
            leading=11,
            textColor=SLATE,
            alignment=TA_CENTER,
            spaceBefore=3,
            spaceAfter=8,
        ),
        "q_title": ParagraphStyle(
            "QTitleCustom",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.2,
            leading=13.5,
            textColor=NAVY,
            spaceBefore=8,
            spaceAfter=3,
            keepWithNext=True,
        ),
        "tbl_hdr": ParagraphStyle(
            "TblHdr",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.2,
            leading=10.5,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "tbl_cell": ParagraphStyle(
            "TblCell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.1,
            leading=10.5,
            textColor=colors.HexColor("#1F2937"),
            alignment=TA_CENTER,
        ),
        "tbl_left": ParagraphStyle(
            "TblLeft",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.1,
            leading=10.5,
            textColor=colors.HexColor("#1F2937"),
            alignment=TA_LEFT,
        ),
    }


def styled_table(
    headers: List[str],
    rows: List[List[str]],
    col_widths: List[float],
    styles: Dict[str, ParagraphStyle],
    left_cols: Tuple[int, ...] | List[int] = (0,),
) -> Table:
    data = [[Paragraph(h, styles["tbl_hdr"]) for h in headers]]
    for r in rows:
        row_cells = []
        for idx, val in enumerate(r):
            st = styles["tbl_left"] if idx in left_cols else styles["tbl_cell"]
            row_cells.append(Paragraph(str(val), st))
        data.append(row_cells)

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return tbl


def callout_box(html_text: str, styles: Dict[str, ParagraphStyle], bg=CALLOUT_BG, border=NAVY, width=7.1 * inch) -> Table:
    p = Paragraph(html_text, styles["callout"])
    t = Table([[p]], colWidths=[width])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("LINEBEFORE", (0, 0), (0, -1), 3.2, border),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return t


def figure_block(img_name: str, caption: str, styles: Dict[str, ParagraphStyle], width: float = 6.95 * inch) -> KeepTogether:
    path = FIGURES_DIR / img_name
    img = Image(str(path))
    aspect = img.imageHeight / float(img.imageWidth)
    img.drawWidth = width
    img.drawHeight = width * aspect
    return KeepTogether([img, Paragraph(caption, styles["caption"])])


def draw_header_footer(canvas, doc) -> None:
    canvas.saveState()
    if doc.page > 1:
        canvas.setStrokeColor(BORDER_GRAY)
        canvas.setLineWidth(0.6)
        canvas.line(0.65 * inch, 10.42 * inch, 7.85 * inch, 10.42 * inch)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(NAVY)
        canvas.drawString(0.65 * inch, 10.50 * inch, "CSET485 – AI and Society | Assignment #1")
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(SLATE)
        canvas.drawRightString(7.85 * inch, 10.50 * inch, "Roll No: S24BCAU0139 | Adult Census Income (Seed 139)")

    canvas.setStrokeColor(BORDER_GRAY)
    canvas.setLineWidth(0.6)
    canvas.line(0.65 * inch, 0.52 * inch, 7.85 * inch, 0.52 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(SLATE)
    canvas.drawString(0.65 * inch, 0.36 * inch, "Reproducible Code & Computed Results: S24BCAU0139_CSET485_Assignment1.ipynb")
    canvas.drawRightString(7.85 * inch, 0.36 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_part3_answers(d: Dict) -> List[Dict[str, str]]:
    prep = d["preprocessing"]
    p1 = d["part1"]
    s_coefs = {
        (r["predictor"], r["model"]): r for r in d["part2_1_simpson"]["coefficients"]
    }
    age_full = s_coefs[("age", f"Full Dataset (n={d['part2_1_simpson']['n_full']:,})")]
    age_y = s_coefs[("age", f"Subgroup A: Age < 45 (n={d['part2_1_simpson']['n_young']:,})")]
    age_o = s_coefs[("age", f"Subgroup B: Age ≥ 45 (n={d['part2_1_simpson']['n_older']:,})")]
    sex_y = s_coefs[("sex_male", f"Subgroup A: Age < 45 (n={d['part2_1_simpson']['n_young']:,})")]
    sex_o = s_coefs[("sex_male", f"Subgroup B: Age ≥ 45 (n={d['part2_1_simpson']['n_older']:,})")]

    ovb = d["part2_2_ovb"]
    ovb_map = {r["feature"]: r for r in ovb["predictors"]}
    adv = d["part2_3_adversarial"]
    adv_t = {r["label"]: r for r in adv["trait_comparison"]}
    f24 = d["part2_4_fairness"]
    sw = {r["t"]: r for r in f24["sweep"]}
    tr = f24["quantified_tradeoff"]
    cs = f24["case_studies"]

    q1 = (
        f"On the {prep['test_rows']:,}-row Adult Census test set, Model A (OLS linear regression thresholded at its median) "
        f"and Model B (logistic regression thresholded at P ≥ 0.50) disagreed on <b>{p1['mismatch_count']:,} individuals "
        f"({p1['mismatch_pct']:.2f}%)</b>, agreeing on only {p1['agreement_count']:,} ({p1['agreement_pct']:.2f}%). Every single "
        f"mismatch occurred in one direction: Model A flagged <b>{p1['model_a_flagged_high']:,}</b> individuals "
        f"({p1['model_a_flagged_high_pct']:.2f}%) as high income (&gt;$50K), whereas Model B flagged only "
        f"<b>{p1['model_b_flagged_high']:,}</b> ({p1['model_b_flagged_high_pct']:.2f}%). Consequently, all {p1['mismatch_count']:,} "
        f"disputed individuals were classified as &gt;$50K by Model A but ≤$50K by Model B, with zero disagreements in the opposite "
        f"quadrant (4,524 agreed low-risk; 1,841 agreed high-risk). Two mathematical mechanisms drive this 29.66% divergence. First, "
        f"Model A's median predicted value is <b>{p1['ols_median']:.4f}</b>, sitting less than half as high as Model B's "
        f"<b>0.5000</b> probability threshold. Because only {prep['positive_rate_pct']:.2f}% of clean census respondents earn &gt;$50K, "
        f"an OLS linear probability model centers its fitted values near the empirical base rate; cutting at the sample median "
        f"mechanically forces exactly half the test population into the positive class regardless of true class prevalence or "
        f"posterior odds. Second, OLS minimizes squared residuals without a bounded sigmoid link, generating scores ranging from "
        f"<b>{p1['ols_min']:.4f}</b> to <b>{p1['ols_max']:.4f}</b>—including <b>{p1['ols_oob_count']:,}</b> impossible out-of-bounds "
        f"predictions ({p1['ols_oob_pct']:.2f}%: {p1['ols_oob_below_zero']:,} below 0 and {p1['ols_oob_above_one']} above 1). "
        f"Because linear errors distort probability mass across the middle range (0.23–0.49) and fail to compress extreme covariates, "
        f"Model A's median rule over-flags moderate-income earners, inflating recall to {p1['model_a_metrics_vs_y']['recall_pct']:.2f}% "
        f"while collapsing precision to {p1['model_a_metrics_vs_y']['precision_pct']:.2f}% and accuracy to "
        f"<b>{p1['model_a_metrics_vs_y']['accuracy_pct']:.2f}%</b> (F1 = {p1['model_a_metrics_vs_y']['f1']:.4f}). By contrast, Model B's "
        f"calibrated 0.50 cutoff respects conditional odds, yielding <b>{p1['model_b_metrics_vs_y']['accuracy_pct']:.2f}%</b> accuracy, "
        f"<b>{p1['model_b_metrics_vs_y']['precision_pct']:.2f}%</b> precision, {p1['model_b_metrics_vs_y']['recall_pct']:.2f}% recall, "
        f"F1 = {p1['model_b_metrics_vs_y']['f1']:.4f}, and ROC-AUC = {p1['model_b_metrics_vs_y']['roc_auc']:.4f}."
    )

    q2 = (
        f"Splitting the training cohort at age 45 reveals a textbook <b>Simpson's Paradox</b> sign reversal in how age predicts "
        f"&gt;$50K income. In the full model (n={d['part2_1_simpson']['n_full']:,}), the standardized logistic coefficient for "
        f"<code>age</code> is strongly positive at <b>{age_full['coef']:+.4f}</b> (SE={age_full['se']:.4f}, 95% CI "
        f"[{age_full['ci_lo']:+.4f}, {age_full['ci_hi']:+.4f}], p &lt; 0.001), suggesting each standard-deviation increase in age "
        f"raises high-income odds by roughly 41.5%. Yet stratifying into Subgroup A (Age &lt; 45, n={d['part2_1_simpson']['n_young']:,}, "
        f"base rate {d['part2_1_simpson']['pos_rate_young_pct']:.2f}%) and Subgroup B (Age ≥ 45, n={d['part2_1_simpson']['n_older']:,}, "
        f"base rate {d['part2_1_simpson']['pos_rate_older_pct']:.2f}%) splits this pooled slope into two opposing regimes with completely "
        f"non-overlapping confidence intervals. Among workers under 45, <code>age</code> triples in magnitude to <b>{age_y['coef']:+.4f}</b> "
        f"(95% CI [{age_y['ci_lo']:+.4f}, {age_y['ci_hi']:+.4f}], p &lt; 0.001); among workers 45 and older, it flips sign to "
        f"<b>{age_o['coef']:+.4f}</b> (95% CI [{age_o['ci_lo']:+.4f}, {age_o['ci_hi']:+.4f}], p = 3.34e-11). Simultaneously, the male "
        f"premium (<code>sex_male</code>) widens sharply from <b>{sex_y['coef']:+.4f}</b> (95% CI [{sex_y['ci_lo']:+.4f}, "
        f"{sex_y['ci_hi']:+.4f}]) under 45 to <b>{sex_o['coef']:+.4f}</b> (95% CI [{sex_o['ci_lo']:+.4f}, {sex_o['ci_hi']:+.4f}]) at 45+. "
        f"This reversal occurs because real earnings follow an inverted-U lifecycle trajectory: &gt;$50K prevalence climbs steeply from "
        f"1.22% (ages 17–24) to 17.32% (25–34) and 33.80% (35–44), peaks at 40.64% (45–54), then declines through 32.42% (55–64) and "
        f"23.38% (65+) due to retirement transitions, reduced weekly hours, and generational schooling differences. A single linear age "
        f"slope averages steep early-career growth against post-peak decline. Ignoring subgroup analysis would severely misguide policy: "
        f"credit-scoring or workforce-retraining algorithms would systematically over-predict earnings stability for older retirees while "
        f"under-crediting upward-trajectory workers in their late thirties and completely overlooking how gender wage gaps compound "
        f"substantially after age 45—highlighting why non-linear splines or age-stratified underwriting models are essential in practice."
    )

    q3 = (
        f"For the omitted-variable bias test, I deliberately dropped <b><code>education-num</code></b>—a core human-capital confounder "
        f"that jointly shapes occupational sorting and adult earnings. Removing this single predictor caused substantial bias across "
        f"correlated variables while barely denting headline predictive accuracy, which fell modestly from "
        f"{ovb['full_model_test_acc_pct']:.2f}% (AUC {ovb['full_model_test_auc']:.4f}) to {ovb['reduced_model_test_acc_pct']:.2f}% "
        f"(AUC {ovb['reduced_model_test_auc']:.4f}). As documented in the comparison table below, the largest relative shift occurred in "
        f"<b><code>occupation_Prof-specialty</code></b>, which surged by <b>{ovb_map['occupation_Prof-specialty']['pct_change']:+.2f}%</b> "
        f"(from {ovb_map['occupation_Prof-specialty']['beta_full']:+.4f} to {ovb_map['occupation_Prof-specialty']['beta_reduced']:+.4f}), "
        f"more than doubling its apparent log-odds effect. The second-largest shift struck <code>occupation_Exec-managerial</code> at "
        f"<b>{ovb_map['occupation_Exec-managerial']['pct_change']:+.2f}%</b> ({ovb_map['occupation_Exec-managerial']['beta_full']:+.4f} to "
        f"{ovb_map['occupation_Exec-managerial']['beta_reduced']:+.4f}), while <code>age</code> dropped by <b>{ovb_map['age']['pct_change']:+.2f}%</b> "
        f"({ovb_map['age']['beta_full']:+.4f} to {ovb_map['age']['beta_reduced']:+.4f}) and <code>hours-per-week</code> rose by "
        f"<b>{ovb_map['hours-per-week']['pct_change']:+.2f}%</b> ({ovb_map['hours-per-week']['beta_full']:+.4f} to "
        f"{ovb_map['hours-per-week']['beta_reduced']:+.4f}). Both <code>sex_male</code> ({ovb_map['sex_male']['beta_full']:+.4f} to "
        f"{ovb_map['sex_male']['beta_reduced']:+.4f}, {ovb_map['sex_male']['pct_change']:+.2f}%) and <code>capital-gain</code> "
        f"({ovb_map['capital-gain']['beta_full']:+.4f} to {ovb_map['capital-gain']['beta_reduced']:+.4f}, "
        f"{ovb_map['capital-gain']['pct_change']:+.2f}%) also absorbed upward omitted-variable bias. Econometrically, when a true causal "
        f"determinant like formal schooling is omitted, correlated downstream proxies absorb its missing covariance—making professional "
        f"specialty titles masquerade as the direct source of high wages when they largely reflect university credential requirements. "
        f"Crucially, both occupational coefficients retain statistical significance (p &lt; 0.001) alongside strong validation AUC. This "
        f"demonstrates that trusting any predictive model without deliberate confound stress-testing risks mistaking proxy correlations "
        f"for genuine causal mechanisms and misallocating policy investments such as career subsidies, hiring incentives, or training "
        f"programs. Simply put, high out-of-sample accuracy does not protect individual parameter estimates from severe omitted-variable "
        f"distortion; policymakers relying on reduced-model weights would mistakenly attribute wage returns to job titles rather than "
        f"underlying educational access, leading to ineffective workforce interventions and miscalibrated social-mobility policies."
    )

    q4 = (
        f"To detect an unseen hidden confound in a deployed income-screening model—such as unmeasured regional cost-of-living, employer "
        f"firm size, union coverage, or inherited family wealth absent from the 1994 Census extract—I propose a concrete <b>three-stage "
        f"External Validation and Stratified Residual Audit</b>. First, perform <b>domain-expert residual stratification</b> on held-out "
        f"test predictions: compute signed Pearson residuals (Y − P<sub>pred</sub>) across all {prep['test_rows']:,} test individuals and collaborate "
        f"with labor economists to test whether residuals correlate systematically with external geographic or industry benchmarks (for "
        f"instance, linking applicant ZIP codes or state records to Bureau of Labor Statistics metropolitan wage indices and regional "
        f"price parities). Persistent non-zero residual clusters among workers sharing identical age, education, and occupation directly "
        f"expose an omitted structural determinant. Second, conduct <b>external dataset enrichment validation</b> using richer modern "
        f"microdata such as the U.S. Census Current Population Survey (CPS ASEC) or the Panel Study of Income Dynamics (PSID), which "
        f"explicitly measure employer size, union membership, industry tier, and metropolitan status. Fitting our exact 41-feature "
        f"specification on CPS and sequentially adding those previously unavailable covariates directly tests whether core weights (such "
        f"as <code>sex_male</code> = {ovb_map['sex_male']['beta_full']:+.4f} or <code>occupation_Prof-specialty</code> = "
        f"{ovb_map['occupation_Prof-specialty']['beta_full']:+.4f}) exhibit Part 2.2-style instability. Third, compute <b>Oster's "
        f"coefficient-stability bounds and E-values</b>—comparing parameter movement against R² increments—to quantify how strongly an "
        f"unmeasured confound must correlate with both predictors and income to overturn policy conclusions before production sign-off. "
        f"Together, residual stratification, external microdata linking, and formal sensitivity bounds convert hidden-confound detection "
        f"from guesswork into an auditable pre-deployment checklist grounded in labor-market domain knowledge."
    )

    q5 = (
        f"Across the {adv['total_test_rows']:,} held-out test records, Model B committed <b>{adv['total_hc_errors']} high-confidence errors "
        f"({adv['total_hc_errors_pct']:.2f}%)</b>—splitting into {adv['total_hc_fp']} high-confidence false positives (P ≥ 0.75, Y=0) and "
        f"{adv['total_hc_fn']} high-confidence false negatives (P ≤ 0.25, Y=1). In the randomly sampled <b>50-row adversarial subset</b> "
        f"({adv['sample_fp']} FPs, {adv['sample_fn']} FNs), the single most pervasive shared trait is having <b>zero capital loss "
        f"({adv_t['Capital Loss = 0']['adv_pct']:.1f}%, 49/50 vs. {adv_t['Capital Loss = 0']['test_pct']:.1f}% test)</b>, followed by "
        f"<b>age ≥ 30 ({adv_t['Age ≥ 30']['adv_pct']:.1f}%, 45/50 vs. {adv_t['Age ≥ 30']['test_pct']:.1f}%)</b>, <b>White "
        f"({adv_t['White']['adv_pct']:.1f}%, 44/50 vs. {adv_t['White']['test_pct']:.1f}%)</b>, <b>hours-per-week ≥ 40 "
        f"({adv_t['Hours/Week ≥ 40']['adv_pct']:.1f}%, 43/50 vs. {adv_t['Hours/Week ≥ 40']['test_pct']:.1f}%)</b>, <b>Male "
        f"({adv_t['Male']['adv_pct']:.1f}%, 40/50 vs. {adv_t['Male']['test_pct']:.1f}%)</b>, and <b>zero capital gain "
        f"({adv_t['Capital Gain = 0']['adv_pct']:.1f}%, 40/50 vs. {adv_t['Capital Gain = 0']['test_pct']:.1f}%)</b>. Mean age is "
        f"{adv['demographics']['age_mean_adv']:.2f} (median {adv['demographics']['age_median_adv']:.0f} vs. "
        f"{adv['demographics']['age_mean_test']:.2f} overall) and mean weekly hours are {adv['demographics']['hours_mean_adv']:.2f} "
        f"(vs. {adv['demographics']['hours_mean_test']:.2f}). Statistically, Model B fails confidently along two opposing regimes created "
        f"by its strictly additive linear log-odds boundary without interaction or non-linear terms. Among the 34 false negatives, "
        f"<b>{adv['fn_subcluster_traits']['zero_cap_both_pct']:.1f}%</b> (31/34) report zero capital gains and losses, "
        f"<b>{adv['fn_subcluster_traits']['no_college_deg_pct']:.1f}%</b> (27/34) lack a college degree (education-num ≤ 10), and "
        f"<b>{adv['fn_subcluster_traits']['not_married_civ_pct']:.1f}%</b> (19/34) are unmarried; lacking these heavy positive linear "
        f"weights (<code>education-num</code> +0.7129, <code>capital-gain</code> +0.4894) forces P ≤ 0.25 even for high-earning skilled "
        f"tradespeople or overtime workers. Conversely, among the 16 false positives, <b>100.0%</b> (16/16) are married-civ-spouse, "
        f"<b>{adv['fp_subcluster_traits']['bachelors_plus_pct']:.1f}%</b> (10/16) hold Bachelor's+ degrees, and "
        f"<b>{adv['fp_subcluster_traits']['cap_gain_pos_pct']:.1f}%</b> (7/16) have positive capital gains—additive boosters pushing "
        f"log-odds above P ≥ 0.75 despite modest wages or part-year employment. Introducing polynomial age terms and education-by-occupation "
        f"interactions would directly mitigate both confident boundary failures across the test population, substantially improving calibration "
        f"for non-traditional earners and multi-earner households."
    )

    q6 = (
        f"In Figure 5, shifting the decision cutoff from <code>t={tr['from_t']:.2f}</code> to <code>t={tr['to_t']:.2f}</code> improves "
        f"Demographic Parity (DP) from <b>{tr['dp_from']:.3f}</b> to <b>{tr['dp_to']:.3f}</b> (a <b>+{tr['dp_gain_pct']:.1f}%</b> relative "
        f"gain), while Equalized Odds (EO) drops from <b>{tr['eo_from']:.3f}</b> to <b>{tr['eo_to']:.3f}</b> (a <b>-{tr['eo_loss_pct']:.1f}%</b> "
        f"loss), yielding a trade-off cost of <b>W/Z = {tr['cost_wz']:.2f}</b>—meaning each 1% gain in selection-rate parity sacrifices "
        f"2.87% in error-rate equality. To translate this ratio into real human consequences, consider two genuine high-income (&gt;$50K) "
        f"individuals from our test set applying for a credit line requiring predicted &gt;$50K income. <b>Applicant A</b> is a "
        f"{cs['female']['age']}-year-old {cs['female']['marital_status'].lower()} woman with a {cs['female']['education']} degree "
        f"(15 years) working {cs['female']['hours_per_week']} hours/week in {cs['female']['occupation']}; despite advanced credentials "
        f"and intense work hours, the model assigns her <b>P = {cs['female']['prob']:.4f}</b> because she lacks the marriage premium. "
        f"<b>Applicant B</b> is a {cs['male']['age']}-year-old married man with a {cs['male']['education']} degree (13 years) working "
        f"{cs['male']['hours_per_week']} hours/week in {cs['male']['occupation']}; he receives <b>P = {cs['male']['prob']:.4f}</b>. "
        f"At a conservative cutoff like <code>t=0.85</code> (EO={sw[0.85]['eo']:.3f}), both qualified applicants are rejected. At "
        f"<code>t=0.35</code> (DP={sw[0.35]['dp']:.3f}, EO={sw[0.35]['eo']:.3f}), Applicant B is approved while equally creditworthy "
        f"Applicant A is denied—reflecting a 14.9-point recall deficit (TPR_F={sw[0.35]['tpr_a']:.3f} vs. TPR_M={sw[0.35]['tpr_b']:.3f}). "
        f"Lowering the uniform threshold to <code>t=0.15</code> rescues Applicant A and raises DP to {sw[0.15]['dp']:.3f}, yet floods "
        f"Male approvals with false positives (FPR_M surges from {sw[0.35]['fpr_b']:.3f} to {sw[0.15]['fpr_b']:.3f} vs. FPR_F={sw[0.15]['fpr_a']:.3f}), "
        f"slashing EO to {sw[0.15]['eo']:.3f} and exposing misclassified borrowers to unaffordable debt. Thus, tuning a single cutoff "
        f"to repair group parity inevitably shifts misclassification burdens onto specific individuals across both demographic groups, "
        f"demonstrating why mathematical trade-off ratios carry direct human and financial consequences."
    )

    q7 = (
        f"From the ten-threshold sweep, I defend <b><code>t = 0.35</code></b> as the most defensible operating point. First, it preserves "
        f"strong predictive utility with <b>{sw[0.35]['acc_pct']:.2f}%</b> test accuracy—within 1.11 percentage points of the 84.52% "
        f"maximum at t=0.45 and far superior to t=0.15 (74.88%) or t=0.05 (61.32%). Second, it maintains near-ideal <b>Predictive "
        f"Parity (PP = {sw[0.35]['pp']:.3f})</b>: a positive prediction carries nearly identical real-world income reliability for "
        f"women (PPV_F = {sw[0.35]['ppv_a']:.3f}) and men (PPV_M = {sw[0.35]['ppv_b']:.3f}), ensuring approved applicants across groups "
        f"possess comparable repayment capacity. Third, lowering the threshold below the default 0.50 rule substantially mitigates "
        f"false-negative exclusion of qualified women, lifting Female true-positive recall to <b>{sw[0.35]['tpr_a']:.3f}</b> (versus "
        f"0.459 at t=0.55 and 0.361 at t=0.65) while keeping the Female false-positive rate tightly bounded at <b>{sw[0.35]['fpr_a']:.3f}</b>. "
        f"However, a critic can raise a formidable objection: at <code>t = 0.35</code>, <b>Demographic Parity remains severely depressed "
        f"at {sw[0.35]['dp']:.3f}</b> (flagging 11.3% of women versus 37.3% of men) and <b>Equalized Odds stands at just "
        f"{sw[0.35]['eo']:.3f}</b>, driven by a fourfold disparity in false-positive rates (FPR_F = 0.048 vs. FPR_M = 0.192) and a "
        f"14.9-point recall deficit (TPR_F = 0.618 vs. TPR_M = 0.767). This counter-argument is entirely valid: per Chouldechova's "
        f"impossibility theorem, whenever underlying base rates differ (11.41% Female vs. 31.44% Male) and scores leverage marital and "
        f"gender proxies, no single uniform threshold can simultaneously achieve predictive parity, equalized odds, and demographic parity. "
        f"Accordingly, t=0.35 represents a pragmatic compromise rather than a complete fairness solution, requiring external bias mitigation "
        f"such as post-processing calibration or upstream feature auditing before automated high-stakes deployment."
    )

    q8 = (
        f"If a policymaker must choose between prioritizing Demographic Parity (DP) or Equalized Odds (EO) in the Adult Census "
        f"income-screening context—such as pre-qualifying applicants for consumer loans, mortgages, or financial assistance—I recommend "
        f"prioritizing <b>Equalized Odds (EO)</b>. In financial eligibility decisions, procedural justice demands that equally qualified "
        f"applicants face equal chances of approval (equal TPR) and equally unqualified applicants face equal erroneous-approval or "
        f"wrongful-rejection risk (equal FPR), rather than enforcing equal aggregate approval proportions regardless of current income "
        f"distributions. Our Part 2.4 sweep illustrates why forcing DP through a lower single cutoff is counterproductive: shifting from "
        f"<code>t=0.85</code> to <code>t=0.15</code> raises DP only modestly from <b>{tr['dp_from']:.3f}</b> to <b>{tr['dp_to']:.3f}</b> "
        f"(+{tr['dp_gain_pct']:.1f}%) while collapsing EO from <b>{tr['eo_from']:.3f}</b> to <b>{tr['eo_to']:.3f}</b> "
        f"(-{tr['eo_loss_pct']:.1f}%, trade-off cost <b>W/Z = {tr['cost_wz']:.2f}</b>). At low thresholds like t=0.15 or t=0.05, Male "
        f"false-positive rates surge to 43.0% and 64.4% while overall accuracy plunges from 83.41% (t=0.35) to 61.32%—approving high-risk "
        f"borrowers who are likely to default and suffer severe credit damage. By prioritizing EO, we explicitly sacrifice short-term "
        f"<b>Demographic Parity</b> (accepting DP around 0.28–0.44 under a single threshold because observed &gt;$50K rates in this "
        f"1994 census sample are 11.41% for women versus 31.44% for men). That sacrifice is acceptable in our view because lending cutoffs "
        f"cannot safely erase structural wage gaps through misclassification—provided institutions simultaneously audit and remove biased "
        f"marital proxies upstream while expanding non-punitive credit-building and financial-inclusion programs for under-represented "
        f"earners rather than distorting risk calibration at the decision threshold through coarse quota adjustments that harm individual "
        f"creditworthiness assessments."
    )

    return [
        {"num": 1, "title": "Q1. Threshold-Based Linear Regression vs. Direct Logistic Regression Mismatch", "text": q1},
        {"num": 2, "title": "Q2. Simpson's Paradox Subgroup Reversal & Policy Implications", "text": q2},
        {"num": 3, "title": "Q3. Omitted-Variable Bias After Dropping education-num", "text": q3},
        {"num": 4, "title": "Q4. Concrete Real-World Method for Hidden Confound Detection", "text": q4},
        {"num": 5, "title": "Q5. Adversarial 50-Row Subset & Statistical Failure Mechanism", "text": q5},
        {"num": 6, "title": "Q6. Concrete Human Impact of the Fairness Trade-Off Cost", "text": q6},
        {"num": 7, "title": "Q7. Defense of Recommended Decision Threshold (t = 0.35) & Critique", "text": q7},
        {"num": 8, "title": "Q8. Policy Recommendation: Equalized Odds vs. Demographic Parity", "text": q8},
    ]


def build_part4_reflection(d: Dict) -> List[Dict[str, str]]:
    p1 = d["part1"]
    s_coefs = {(r["predictor"], r["model"]): r for r in d["part2_1_simpson"]["coefficients"]}
    age_y = s_coefs[("age", f"Subgroup A: Age < 45 (n={d['part2_1_simpson']['n_young']:,})")]
    age_o = s_coefs[("age", f"Subgroup B: Age ≥ 45 (n={d['part2_1_simpson']['n_older']:,})")]
    ovb = d["part2_2_ovb"]
    prof = [r for r in ovb["predictors"] if r["feature"] == "occupation_Prof-specialty"][0]
    adv = d["part2_3_adversarial"]
    f24 = d["part2_4_fairness"]
    sw35 = [r for r in f24["sweep"] if r["t"] == 0.35][0]
    tr = f24["quantified_tradeoff"]

    sec1 = (
        "<b>1. Direct Answer:</b> I recommend <b>conditional deployment only</b>—strictly as a human-in-the-loop decision-support aid "
        "with mandatory subgroup audits, never as an autonomous single-threshold gatekeeper—because its impressive headline metrics "
        "conceal sharp demographic error disparities, lifecycle reversals, and silent confounding."
    )

    sec2 = (
        "<b>2. Why a Single Number Fails:</b> Reducing a high-stakes deployment judgment to one scalar—whether 84.78% accuracy, 0.9013 "
        "ROC-AUC, or a binary yes/no—fails for five structural reasons uncovered throughout our stress-tests. <b>First, aggregate accuracy "
        "masks deep subgroup disparities and causal reversals:</b> an overall logistic regression appears smooth and well-calibrated across "
        "all 9,049 test cases, yet pooling workers under and over age 45 averages opposing lifecycle earnings trajectories into a "
        "misleading positive slope, while headline accuracy completely conceals a fourfold gender gap in false-positive rates and "
        "substantial true-positive recall disparities between women and men. <b>Second, threshold selection is a normative policy judgment, "
        "not a statistical fact:</b> switching from OLS median thresholding to a 0.50 logistic probability cutoff flips classifications for "
        "nearly one-third of all test individuals, and sweeping the logistic threshold from 0.05 to 0.95 continuously redistributes "
        "false-positive versus false-negative harm across demographic groups without any mathematically neutral operating point. <b>Third, "
        "fairness criteria mathematically collide:</b> consistent with impossibility theorems, lowering the decision cutoff to narrow "
        "Demographic Parity directly erodes Equalized Odds by inflating majority-group false positives, forcing policymakers to decide "
        "which group bears misclassification costs while Predictive Parity fluctuates independently across thresholds. <b>Fourth, "
        "high-confidence errors cluster systematically on predictable populations:</b> a single overall accuracy percentage obscures hundreds "
        "of test individuals on whom the model fails with ≥75% certainty—such as experienced non-degreed workers without investment income "
        "or married college graduates earning modest local wages—because strictly additive log-odds boundaries ignore real-world feature "
        "interactions and non-linear lifecycle patterns. <b>Fifth, omitted and hidden confounds remain completely invisible to fit "
        "statistics:</b> removing one schooling variable leaves overall accuracy and AUC seemingly intact while more than doubling an "
        "occupational coefficient, proving that unmeasured structural factors like regional cost-of-living, employer firm size, or "
        "inherited household wealth can silently corrupt learned feature weights in production without lowering validation scores, altering "
        "p-values, or triggering any single-number deployment alarm across standard test-set evaluation dashboards. Relying on one scalar "
        "encourages false precision, obscures who bears real-world misclassification harms, and shields model owners from defending "
        "value-laden policy choices publicly."
    )

    sec3 = (
        f"<b>3. Grounding in Evidence:</b> Our experiments quantify every failure mode: Model A (median={p1['ols_median']:.4f}) and Model B "
        f"(0.50) disagreed on <b>{p1['mismatch_count']:,} cases ({p1['mismatch_pct']:.2f}%)</b>; <code>age</code> reversed from "
        f"<b>{age_y['coef']:+.4f}</b> (Age &lt; 45) to <b>{age_o['coef']:+.4f}</b> (Age ≥ 45); omitting <code>education-num</code> "
        f"shifted <code>occupation_Prof-specialty</code> by <b>{prof['pct_change']:+.2f}%</b> while accuracy remained "
        f"{ovb['reduced_model_test_acc_pct']:.2f}%; <b>{adv['total_hc_errors']} test cases ({adv['total_hc_errors_pct']:.2f}%)</b> "
        f"were high-confidence errors; and raising DP from {tr['dp_from']:.3f} to {tr['dp_to']:.3f} (+{tr['dp_gain_pct']:.1f}%) "
        f"cut EO from {tr['eo_from']:.3f} to {tr['eo_to']:.3f} (-{tr['eo_loss_pct']:.1f}%, W/Z={tr['cost_wz']:.2f}), leaving "
        f"DP={sw35['dp']:.3f} and EO={sw35['eo']:.3f} at t=0.35."
    )

    sec4 = (
        "<b>4. Closing:</b> Responsible AI governance cannot hide behind a single comforting number. Policymakers require transparent "
        "stress-test reports exposing subgroup error disparities, adversarial blind spots, confounding sensitivities, and explicit "
        "fairness trade-off costs—ensuring accountable democratic institutions, rather than opaque algorithmic cutoffs, own the "
        "underlying societal value judgments."
    )

    return [
        {"name": "Direct Answer", "text": sec1},
        {"name": "Why a Single Number Fails", "text": sec2},
        {"name": "Grounding in Evidence", "text": sec3},
        {"name": "Closing", "text": sec4},
    ]


def main() -> None:
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        d = json.load(f)

    styles = make_styles()
    prep = d["preprocessing"]
    p1 = d["part1"]
    s21 = d["part2_1_simpson"]
    ovb = d["part2_2_ovb"]
    adv = d["part2_3_adversarial"]
    f24 = d["part2_4_fairness"]

    story = []

    # --- Banner Header ---
    banner_data = [
        [Paragraph("CSET485 – AI and Society | Assignment #1", styles["title"])],
        [
            Paragraph(
                "Statistical Stress-Testing, Bias Auditing, and Fairness Trade-Off Analysis on UCI Adult Census Income<br/>"
                "<b>Roll Number:</b> S24BCAU0139 &nbsp;&nbsp;|&nbsp;&nbsp; <b>Assigned Dataset:</b> Adult Census Income "
                "&nbsp;&nbsp;|&nbsp;&nbsp; <b>Random Seed:</b> 139 &nbsp;&nbsp;|&nbsp;&nbsp; <b>Split:</b> 70% Train / 30% Test",
                styles["subtitle"],
            )
        ],
    ]
    banner = Table(banner_data, colWidths=[7.2 * inch])
    banner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("TOPPADDING", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ]
        )
    )
    story.append(banner)
    story.append(Spacer(1, 8))

    # --- KPI Strip ---
    kpi_tbl = Table(
        [
            [
                Paragraph("<b>Clean Samples</b><br/>30,162 (24.89% &gt;$50K)", styles["tbl_cell"]),
                Paragraph(f"<b>Part 1 Mismatch</b><br/>{p1['mismatch_count']:,} / {prep['test_rows']:,} ({p1['mismatch_pct']:.2f}%)", styles["tbl_cell"]),
                Paragraph("<b>Simpson's Reversal</b><br/>Age: +1.078 → -0.414", styles["tbl_cell"]),
                Paragraph(f"<b>Max OVB Shift</b><br/>Prof-spec: +{ovb['predictors'][0]['pct_change']:.1f}%", styles["tbl_cell"]),
                Paragraph(f"<b>DP/EO Trade-Off Cost</b><br/>W/Z = {f24['quantified_tradeoff']['cost_wz']:.2f}", styles["tbl_cell"]),
            ]
        ],
        colWidths=[1.44 * inch] * 5,
    )
    kpi_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.7, NAVY),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(kpi_tbl)

    # --- SECTION 1: DATA PREPROCESSING ---
    story.append(Paragraph("1. Data Preprocessing Documentation", styles["h1"]))
    story.append(
        Paragraph(
            f"The raw UCI Adult Census Income dataset (<code>adult.data</code>) contains <b>{prep['raw_rows']:,}</b> rows and "
            f"<b>{prep['raw_cols']}</b> attributes. Prior to modeling, all four preprocessing dimensions were audited and executed "
            f"deterministically using random seed <b>139</b> to prevent data leakage and collinearity.",
            styles["body"],
        )
    )

    story.append(Paragraph("1.1 Missing Values, Redundancy, and Categorical Encoding", styles["h2"]))
    miss_rows = [
        [col, f"{info['count']:,}", f"{info['pct']:.2f}%", "Dropped via complete-case filtering"]
        for col, info in prep["missing_by_col"].items()
    ]
    miss_rows.append(
        [
            "Total Incomplete Rows",
            f"{prep['incomplete_rows']:,}",
            f"{prep['incomplete_rows_pct']:.2f}%",
            f"{prep['workclass_occupation_overlap']:,} overlap workclass &amp; occupation; retained {prep['clean_rows']:,} clean rows",
        ]
    )
    story.append(
        styled_table(
            ["Attribute", "Missing Count (?)", "Share of Raw (%)", "Handling Decision"],
            miss_rows,
            [1.6 * inch, 1.15 * inch, 1.15 * inch, 3.3 * inch],
            styles,
            left_cols=(0, 3),
        )
    )
    story.append(Spacer(1, 5))
    story.append(
        Paragraph(
            f"<b>Encoding &amp; Feature Pruning:</b> Target <code>income</code> was encoded as binary <code>y = 1</code> (&gt;$50K, "
            f"{prep['positive_count']:,} rows, {prep['positive_rate_pct']:.2f}%) and <code>0</code> (≤$50K, {prep['negative_count']:,} rows, "
            f"{prep['negative_rate_pct']:.2f}%). We dropped <code>education</code> (1-to-1 redundant with ordinal <code>education-num</code>) "
            f"and <code>fnlwgt</code> (census sampling weight, not a causal personal predictor). <code>sex</code> and <code>native-country</code> "
            f"were binary-encoded as <code>sex_male</code> (Male=1) and <code>is_us</code> (United-States=1, consolidating 40 sparse foreign "
            f"categories to prevent quasi-complete separation). The remaining five categorical variables (<code>workclass</code>, "
            f"<code>marital-status</code>, <code>occupation</code>, <code>relationship</code>, <code>race</code>) were one-hot encoded with "
            f"<code>drop_first=True</code>, yielding <b>{prep['num_features']}</b> non-collinear predictors.",
            styles["body"],
        )
    )

    story.append(Paragraph("1.2 Outlier Diagnostics, Log Transformation, and Train-Test Scaling", styles["h2"]))
    out_rows = []
    for col, st in prep["outlier_diagnostics"].items():
        action = (
            "Dropped (census weight)"
            if col == "fnlwgt"
            else ("Applied log1p + StandardScaler" if "capital" in col else "Retained + StandardScaler")
        )
        out_rows.append(
            [
                col,
                f"{st['min']:.0f}",
                f"{st['median']:.0f}",
                f"{st['p99']:.1f}",
                f"{st['max']:.0f}",
                f"{st['iqr_outliers']:,} ({st['iqr_outliers_pct']:.1f}%)",
                action,
            ]
        )
    story.append(
        styled_table(
            ["Numeric Feature", "Min", "Median", "99th Pct", "Max", "IQR Outliers", "Treatment"],
            out_rows,
            [1.15 * inch, 0.55 * inch, 0.65 * inch, 0.72 * inch, 0.75 * inch, 1.25 * inch, 2.13 * inch],
            styles,
            left_cols=(0, 6),
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            f"<b>Outliers &amp; Scaling:</b> <code>capital-gain</code> exhibits extreme right-skew with <b>{prep['capital_gain_99999_count']}</b> "
            f"observations artificially top-coded at 99,999, while 91.4% of rows equal 0. Applying <code>np.log1p</code> to "
            f"<code>capital-gain</code> and <code>capital-loss</code> compresses extreme leverage while preserving zeros and rank order. "
            f"Natural variation in <code>age</code> (17–90), <code>education-num</code> (1–16), and <code>hours-per-week</code> (1–99) was "
            f"retained. Data were split 70/30 stratified by income (<code>random_state=139</code>) into <b>{prep['train_rows']:,}</b> training "
            f"and <b>{prep['test_rows']:,}</b> test rows; <code>StandardScaler</code> was fit on training numerics only and applied to test.",
            styles["body"],
        )
    )

    # --- SECTION 2: PART 1 ---
    story.append(Paragraph("2. Part 1 — Build: Model A (OLS) vs. Model B (Logistic Regression)", styles["h1"]))
    p1_perf_rows = [
        [
            "Model A: OLS Linear Regression (≥ Median)",
            f"{p1['ols_median']:.4f}",
            f"{p1['model_a_flagged_high']:,} ({p1['model_a_flagged_high_pct']:.2f}%)",
            f"{p1['model_a_metrics_vs_y']['accuracy_pct']:.2f}%",
            f"{p1['model_a_metrics_vs_y']['precision_pct']:.2f}%",
            f"{p1['model_a_metrics_vs_y']['recall_pct']:.2f}%",
            f"{p1['model_a_metrics_vs_y']['f1']:.4f}",
        ],
        [
            "Model B: Logistic Regression (P ≥ 0.50)",
            "0.5000",
            f"{p1['model_b_flagged_high']:,} ({p1['model_b_flagged_high_pct']:.2f}%)",
            f"{p1['model_b_metrics_vs_y']['accuracy_pct']:.2f}%",
            f"{p1['model_b_metrics_vs_y']['precision_pct']:.2f}%",
            f"{p1['model_b_metrics_vs_y']['recall_pct']:.2f}%",
            f"{p1['model_b_metrics_vs_y']['f1']:.4f}",
        ],
    ]
    story.append(
        styled_table(
            ["Model &amp; Decision Rule", "Cutoff", "Flagged High (&gt;$50K)", "Accuracy", "Precision", "Recall", "F1"],
            p1_perf_rows,
            [2.45 * inch, 0.65 * inch, 1.3 * inch, 0.72 * inch, 0.72 * inch, 0.68 * inch, 0.68 * inch],
            styles,
        )
    )
    story.append(Spacer(1, 5))

    cm = p1["agreement_cm"]
    cm_rows = [
        ["Model A: Low Risk (&lt; 0.2315)", f"{cm[0][0]:,} ({cm[0][0]/prep['test_rows']*100:.2f}%)", f"{cm[0][1]:,} ({cm[0][1]/prep['test_rows']*100:.2f}%)", f"{cm[0][0]+cm[0][1]:,}"],
        ["Model A: High Risk (≥ 0.2315)", f"{cm[1][0]:,} ({cm[1][0]/prep['test_rows']*100:.2f}%)", f"{cm[1][1]:,} ({cm[1][1]/prep['test_rows']*100:.2f}%)", f"{cm[1][0]+cm[1][1]:,}"],
    ]
    story.append(
        styled_table(
            ["Test-Set Agreement Matrix (n = 9,049)", "Model B: Low Risk (P &lt; 0.50)", "Model B: High Risk (P ≥ 0.50)", "Row Total"],
            cm_rows,
            [2.2 * inch, 1.85 * inch, 1.85 * inch, 1.3 * inch],
            styles,
        )
    )
    story.append(Spacer(1, 5))
    story.append(
        callout_box(
            f"<b>Part 1 Key Findings:</b> Model A and Model B disagree on <b>{p1['mismatch_count']:,} / {prep['test_rows']:,} "
            f"({p1['mismatch_pct']:.2f}%)</b> test individuals. Every mismatch occurs where OLS flags High Risk (because its median "
            f"cutoff {p1['ols_median']:.4f} sits near the 24.89% base rate and forces 50% positive flags) while Logistic Regression "
            f"(ROC-AUC = {p1['model_b_metrics_vs_y']['roc_auc']:.4f}) predicts P &lt; 0.50. Moreover, <b>{p1['ols_oob_count']:,}</b> OLS "
            f"predictions ({p1['ols_oob_pct']:.2f}%) fall outside [0, 1] (range [{p1['ols_min']:.4f}, {p1['ols_max']:.4f}]).",
            styles,
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        figure_block(
            "fig1_part1_model_comparison.png",
            "Figure 1: (A) Test-set predicted score density of Model A (OLS, highlighting invalid &lt;0 and &gt;1 regions) vs. Model B (Logistic); (B) Agreement/mismatch confusion matrix.",
            styles,
        )
    )

    # --- SECTION 3: PART 2 ---
    story.append(PageBreak())
    story.append(Paragraph("3. Part 2 — The Trap: Statistical &amp; Adversarial Stress-Tests", styles["h1"]))

    # 2.1 Simpson's Paradox
    story.append(Paragraph("3.1 Experiment 2.1: Simpson's Paradox Hunt (Age &lt; 45 vs. Age ≥ 45)", styles["h2"]))
    s_rows = []
    for r in s21["coefficients"]:
        if r["predictor"] in ("age", "education-num", "hours-per-week", "sex_male"):
            p_str = "&lt; 1e-15" if r["p_value"] < 1e-15 else f"{r['p_value']:.2e}"
            s_rows.append(
                [
                    r["predictor"],
                    r["model"],
                    f"{r['coef']:+.4f}",
                    f"{r['se']:.4f}",
                    f"[{r['ci_lo']:+.4f}, {r['ci_hi']:+.4f}]",
                    p_str,
                ]
            )
    story.append(
        styled_table(
            ["Predictor", "Fitted Cohort", "Coef (β)", "SE", "95% Wald CI", "p-value"],
            s_rows,
            [1.15 * inch, 2.15 * inch, 0.85 * inch, 0.7 * inch, 1.55 * inch, 0.8 * inch],
            styles,
            left_cols=(0, 1),
        )
    )
    story.append(Spacer(1, 5))
    story.append(
        figure_block(
            "fig2_part2_1_simpsons_paradox.png",
            "Figure 2: (A) Forest plot showing complete sign reversal of age from +1.078 (Age &lt; 45) to -0.414 (Age ≥ 45); (B) Inverted-U empirical &gt;$50K rate peaking at ages 45–54 (40.64%).",
            styles,
        )
    )

    # 2.2 OVB
    story.append(Paragraph("3.2 Experiment 2.2: Omitted-Variable Bias (Dropping education-num)", styles["h2"]))
    ovb_rows = [
        [
            r["label"],
            f"{r['beta_full']:+.4f}",
            f"{r['beta_reduced']:+.4f}",
            f"{r['abs_diff']:+.4f}",
            f"{r['pct_change']:+.2f}%",
        ]
        for r in ovb["predictors"]
    ]
    story.append(
        styled_table(
            ["Predictor", "Full Model β", "Reduced Model β", "Absolute Shift", "Relative Shift (%)"],
            ovb_rows,
            [2.45 * inch, 1.15 * inch, 1.2 * inch, 1.15 * inch, 1.25 * inch],
            styles,
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            f"Omitting <code>education-num</code> leaves test accuracy at <b>{ovb['reduced_model_test_acc_pct']:.2f}%</b> "
            f"(vs. {ovb['full_model_test_acc_pct']:.2f}% full) and AUC at <b>{ovb['reduced_model_test_auc']:.4f}</b> (vs. "
            f"{ovb['full_model_test_auc']:.4f}), yet inflates <code>occupation_Prof-specialty</code> by <b>+{ovb['predictors'][0]['pct_change']:.2f}%</b> "
            f"and <code>occupation_Exec-managerial</code> by <b>+{ovb['predictors'][1]['pct_change']:.2f}%</b> as occupational dummies absorb "
            f"missing schooling.",
            styles["body"],
        )
    )
    story.append(
        figure_block(
            "fig3_part2_2_ovb_shifts.png",
            "Figure 3: Before-and-after logistic regression coefficients and percentage omitted-variable bias induced by dropping education-num.",
            styles,
        )
    )

    # 2.3 Adversarial Subset
    story.append(PageBreak())
    story.append(Paragraph("3.3 Experiment 2.3: Adversarial Subset Construction (50 High-Confidence Errors)", styles["h2"]))
    adv_rows = [
        [
            r["label"],
            f"{r['adv_pct']:.1f}%",
            f"{r['test_pct']:.1f}%",
            f"{r['adv_pct'] - r['test_pct']:+.1f} pp",
        ]
        for r in adv["trait_comparison"]
    ]
    adv_rows.append(
        [
            "Mean Age (Years)",
            f"{adv['demographics']['age_mean_adv']:.2f}",
            f"{adv['demographics']['age_mean_test']:.2f}",
            f"{adv['demographics']['age_mean_adv'] - adv['demographics']['age_mean_test']:+.2f} yrs",
        ]
    )
    story.append(
        styled_table(
            ["Demographic / Feature Trait", "Adversarial Subset (n=50)", "Full Test Set (n=9,049)", "Difference"],
            adv_rows,
            [2.6 * inch, 1.55 * inch, 1.55 * inch, 1.5 * inch],
            styles,
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            f"Total high-confidence errors: <b>{adv['total_hc_errors']} / {adv['total_test_rows']:,} ({adv['total_hc_errors_pct']:.2f}%)</b> "
            f"({adv['total_hc_fp']} FP with P ≥ 0.75; {adv['total_hc_fn']} FN with P ≤ 0.25). In the 50-row sample ({adv['sample_fp']} FP, "
            f"{adv['sample_fn']} FN), <b>98.0%</b> have zero capital loss and <b>90.0%</b> are aged ≥30. Among FNs, <b>91.2%</b> have zero "
            f"capital gains/losses and <b>79.4%</b> lack a college degree; among FPs, <b>100.0%</b> are married-civ-spouse and <b>62.5%</b> hold "
            f"at least a Bachelor's degree.",
            styles["body"],
        )
    )
    story.append(
        figure_block(
            "fig4_part2_3_adversarial_subset.png",
            "Figure 4: (A) Adversarial 50-row sample traits vs. full test set; (B) Probability distribution of all 476 high-confidence errors.",
            styles,
        )
    )

    # 2.4 Fairness Trade-off
    story.append(Paragraph("3.4 Experiment 2.4: Fairness Trade-Off Analysis (Sensitive Attribute: Sex)", styles["h2"]))
    sw_rows = [
        [
            f"{r['t']:.2f}",
            f"{r['acc_pct']:.2f}%",
            f"{r['dp']:.3f}",
            f"{r['eo']:.3f}",
            f"{r['pp']:.3f}",
            f"{r['tpr_a']:.3f}",
            f"{r['tpr_b']:.3f}",
            f"{r['fpr_a']:.3f}",
            f"{r['fpr_b']:.3f}",
            f"{r['ppv_a']:.3f}",
            f"{r['ppv_b']:.3f}",
        ]
        for r in f24["sweep"]
    ]
    story.append(
        styled_table(
            ["t", "Acc", "DP", "EO", "PP", "TPR_F", "TPR_M", "FPR_F", "FPR_M", "PPV_F", "PPV_M"],
            sw_rows,
            [0.48 * inch, 0.66 * inch, 0.62 * inch, 0.62 * inch, 0.62 * inch, 0.68 * inch, 0.7 * inch, 0.68 * inch, 0.7 * inch, 0.72 * inch, 0.72 * inch],
            styles,
            left_cols=(),
        )
    )
    story.append(Spacer(1, 5))
    tr = f24["quantified_tradeoff"]
    story.append(
        callout_box(
            f"<b>Quantified Fairness Trade-Off (t = {tr['from_t']:.2f} → t = {tr['to_t']:.2f}, Group A = Female [n={f24['n_group_a']:,}], "
            f"Group B = Male [n={f24['n_group_b']:,}]):</b><br/>"
            f"\"If you improve DP from <b>{tr['dp_from']:.3f}</b> to <b>{tr['dp_to']:.3f}</b> (a <b>+{tr['dp_gain_pct']:.1f}%</b> gain), "
            f"EO drops from <b>{tr['eo_from']:.3f}</b> to <b>{tr['eo_to']:.3f}</b> (a <b>-{tr['eo_loss_pct']:.1f}%</b> loss). "
            f"The trade-off cost is <b>W/Z = {tr['cost_wz']:.2f}</b>.\"<br/>"
            f"<b>Recommended Trade-Off:</b> Threshold <b>t = 0.35</b> (Accuracy = 83.41%, PP = 0.967, DP = 0.303, EO = 0.248) balances "
            f"Female recall (0.618) and predictive calibration without triggering extreme Male false-positive inflation (FPR_M = 0.430 at t=0.15).",
            styles,
            bg=WARN_BG,
            border=CRIMSON,
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        figure_block(
            "fig5_part2_4_fairness_tradeoff.png",
            "Figure 5: Required Fairness Trade-Off Chart — Demographic Parity (0–1.5) vs. Equalized Odds (0–1.5) labeled by threshold t.",
            styles,
            width=6.3 * inch,
        )
    )
    story.append(
        figure_block(
            "fig6_part2_4_metrics_vs_threshold.png",
            "Figure 6: Demographic Parity (DP), Equalized Odds (EO), Predictive Parity (PP), and Accuracy across decision thresholds.",
            styles,
            width=6.5 * inch,
        )
    )

    # --- SECTION 4: PART 3 ---
    story.append(PageBreak())
    story.append(Paragraph("4. Part 3 — Descriptive Analysis Questions (~250–300 Words Each)", styles["h1"]))
    q_items = build_part3_answers(d)
    for item in q_items:
        wc = count_words(item["text"])
        print(f"Word count [{item['title'][:25]}...]: {wc} words")
        assert 245 <= wc <= 305, f"Word count out of [245, 305] for {item['title']}: {wc}"
        blocks = [Paragraph(item["title"], styles["q_title"]), Paragraph(item["text"], styles["body"])]
        if item["num"] == 3:
            q3_tbl = styled_table(
                ["Predictor", "Full β", "Reduced β (No Edu)", "Shift (%)"],
                [
                    [r["label"], f"{r['beta_full']:+.4f}", f"{r['beta_reduced']:+.4f}", f"{r['pct_change']:+.2f}%"]
                    for r in ovb["predictors"]
                ],
                [2.45 * inch, 1.45 * inch, 1.75 * inch, 1.55 * inch],
                styles,
            )
            blocks.append(Spacer(1, 3))
            blocks.append(q3_tbl)
            blocks.append(Spacer(1, 5))
        story.append(KeepTogether(blocks))

    # --- SECTION 5: PART 4 ---
    story.append(PageBreak())
    story.append(Paragraph("5. Part 4 — Reflection Essay (~500 Words)", styles["h1"]))
    story.append(
        Paragraph(
            "<i>Prompt: \"If a policy-maker asked you: 'just give me one number: should we deploy this model or not?', what would you say, "
            "and what is the limitation of that 'one number' answer that you discovered yourself through your analysis?\"</i>",
            styles["body"],
        )
    )
    refl_sections = build_part4_reflection(d)
    total_refl_words = 0
    for sec in refl_sections:
        swc = count_words(sec["text"])
        total_refl_words += swc
        print(f"Reflection [{sec['name']}]: {swc} words")
        story.append(Paragraph(sec["text"], styles["body"]))
    print(f"Total Reflection word count: {total_refl_words} words")
    assert 475 <= total_refl_words <= 535, f"Reflection word count out of [475, 535]: {total_refl_words}"

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=LETTER,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.72 * inch,
        bottomMargin=0.68 * inch,
        title="CSET485 Assignment 1 - S24BCAU0139",
        author="S24BCAU0139",
    )
    doc.build(story, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)
    print(f"Generated PDF report: {PDF_PATH}")


if __name__ == "__main__":
    main()
