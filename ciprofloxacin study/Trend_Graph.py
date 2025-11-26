import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os
from pathlib import Path
import os

###############################################
# config
###############################################

# הסדר *הרצוי* של הפייזים בציר X
PHASE_ORDER = [
    "pre-9w",
    "pre-2d",
    "pre-1d",
    "day0",
    "day1",
    "day2",
    "day3",
    "day4",
    "day5",
    "day6",
    "day7",
    "day8",
    "day10",
    "day18",
    "day28",
    "day77",
]

DEBUG = True
LOG_FILE = open("trend_debug.log", "w")

###############################################
# utilities
###############################################

def debug(msg):
    if DEBUG:
        print(msg)
    LOG_FILE.write(str(msg) + "\n")
    LOG_FILE.flush()

###############################################
# assign buckets per subject (purely by order)
###############################################

def assign_buckets(df):
    """
    df: כל הדגימות של נבדק אחד.
    ממיין לפי day וממפה:
    היום הראשון -> pre-9w
    השני        -> pre-2d
    השלישי      -> pre-1d
    הרביעי      -> day0
    וכו' לפי PHASE_ORDER.
    אם יש יותר ימים ממה שמופיע ב-PHASE_ORDER -> "other".
    """
    df = df.sort_values("day").copy()
    days = df["day"].tolist()

    subj = df["subject"].iloc[0]
    debug(f"\nAssigning buckets for subject {subj}")
    debug(f"days: {days}")

    buckets = {}
    for idx, day in enumerate(days):
        if idx < len(PHASE_ORDER):
            buckets[day] = PHASE_ORDER[idx]
        else:
            buckets[day] = "other"

    df["bucket"] = df["day"].map(buckets)
    debug(f"buckets: {df[['day','bucket']].values.tolist()}")

    return df

###############################################
# add relative-to-baseline columns
###############################################

def add_relative_to_baseline(df):
    """
    df: כל הדגימות של נבדק אחד אחרי bucket.
    baseline: קודם ננסה pre-9w, אם אין – day0.
    מוסיף pct_vir_rel, pct_cel_rel.
    """
    subj = df["subject"].iloc[0]

    # Samples that can be used as a baseline
    baseline_candidates = df[df["bucket"].isin(["pre-9w", "day0"])].copy()

    if baseline_candidates.empty:
        debug(f"Subject {subj}: no baseline (pre-9w/day0), setting rel=NaN")
        df["pct_vir_rel"] = pd.NA
        df["pct_cel_rel"] = pd.NA
        return df

    # עדיפות ל-pre-9w על פני day0
    baseline_candidates["baseline_order"] = pd.Categorical(
        baseline_candidates["bucket"],
        categories=["pre-9w", "day0"],
        ordered=True
    )
    baseline_row = baseline_candidates.sort_values("baseline_order").iloc[0]

    b_vir = baseline_row["pct_vir"]
    b_cel = baseline_row["pct_cel"]

    debug(
        f"Subject {subj}: baseline bucket={baseline_row['bucket']}, "
        f"pct_vir={b_vir}, pct_cel={b_cel}"
    )

    df["pct_vir_rel"] = df["pct_vir"] - b_vir
    df["pct_cel_rel"] = df["pct_cel"] - b_cel

    return df

###############################################
# load & reshape
###############################################

debug("=== RUN START ===")
debug("Loading datasets...")
base_dir = os.getcwd()
vir_cel = pd.read_csv(
    base_dir + "/sample_to_virus_and_cellular_org_pct.csv"
)
mapdf = pd.read_excel(
    base_dir + "/Subject To Sample.xlsx",
    sheet_name="Supp. Table 1",
)

debug("Pivot viruses / cellular organisms to wide format...")

wide = (
    vir_cel
    .pivot_table(
        index=["acc", "sample_name"],
        columns="name",
        values="pct"
    )
    .reset_index()
)

wide = wide.rename(
    columns={
        "Viruses": "pct_vir",
        "cellular organisms": "pct_cel",
    }
)


###############################################
# merge with sample metadata
###############################################

debug("Merging with sample metadata...")

merged = wide.merge(
    mapdf,
    left_on="sample_name",
    right_on="library",
    how="inner",
)

merged["day"] = pd.to_numeric(merged["day"], errors="coerce")
merged = merged.sort_values(["subject", "day"])

debug(f"merged shape: {merged.shape}")
debug(merged.head())

###############################################
# Filter Control subject
###############################################

control_subjects_to_delete = ["CAN", "CAC", "CAM", "CAK", "CAA"]

merged = merged[~merged["subject"].isin(control_subjects_to_delete)].copy()

debug(f"After removing controls {control_subjects_to_delete}, shape: {merged.shape}")
debug(f"Remaining subjects: {sorted(merged['subject'].unique())}")

###############################################
# assign buckets per subject
###############################################

debug("Assigning buckets per subject...")

merged = (
    merged
    .groupby("subject", group_keys=False)
    .apply(assign_buckets)
)

###############################################
# relative-to-baseline per subject
###############################################

debug("Adding relative-to-baseline columns per subject...")

merged = (
    merged
    .groupby("subject", group_keys=False)
    .apply(add_relative_to_baseline)
)

debug("Bucket distribution:")
debug(merged["bucket"].value_counts())

###############################################
# aggregate per bucket (vir + cel) – absolute
###############################################

debug("\nAggregating per bucket (excluding 'other')...")

summary = (
    merged[merged["bucket"] != "other"]
    .groupby("bucket")
    .agg(
        mean_vir=("pct_vir", "mean"),
        std_vir=("pct_vir", "std"),
        mean_cel=("pct_cel", "mean"),
        std_cel=("pct_cel", "std"),
        n_rows=("pct_vir", "count"),
        n_subjects=("subject", "nunique"),
    )
    .reset_index()
)

summary["se_vir"] = summary["std_vir"] / summary["n_rows"] ** 0.5
summary["se_cel"] = summary["std_cel"] / summary["n_rows"] ** 0.5

# מסדרים את ה-buckets לפי PHASE_ORDER
summary = (
    summary
    .set_index("bucket")
    .reindex(PHASE_ORDER)          # יכניס NaN לפייזים שלא קיימים
    .dropna(subset=["mean_vir"])   # משאיר רק מה שבפועל יש לו מדידות
    .reset_index()
)

debug("\nFinal summary table (absolute):")
debug(summary)

###############################################
# aggregate per bucket – relative to baseline
###############################################

debug("\nAggregating per bucket (relative to baseline, excluding 'other')...")

summary_rel = (
    merged[
        (merged["bucket"] != "other") &
        (merged["pct_vir_rel"].notna()) &
        (merged["pct_cel_rel"].notna())
    ]
    .groupby("bucket")
    .agg(
        mean_vir_rel=("pct_vir_rel", "mean"),
        std_vir_rel=("pct_vir_rel", "std"),
        mean_cel_rel=("pct_cel_rel", "mean"),
        std_cel_rel=("pct_cel_rel", "std"),
        n_rows=("pct_vir_rel", "count"),
        n_subjects=("subject", "nunique"),
    )
    .reset_index()
)

summary_rel["se_vir_rel"] = summary_rel["std_vir_rel"] / summary_rel["n_rows"] ** 0.5
summary_rel["se_cel_rel"] = summary_rel["std_cel_rel"] / summary_rel["n_rows"] ** 0.5

summary_rel = (
    summary_rel
    .set_index("bucket")
    .reindex(PHASE_ORDER)
    .dropna(subset=["mean_vir_rel"])
    .reset_index()
)

debug("\nFinal summary table (relative):")
debug(summary_rel)

###############################################
# PDF
###############################################

pdf_path = "per_subject_trends.pdf"

subjects = sorted(merged["subject"].unique())
x_abs = range(len(summary))
x_rel = range(len(summary_rel))

with PdfPages(pdf_path) as pdf:

    ################################################
    # PAGE 1 — COVER
    ################################################
    cover = plt.figure(figsize=(8.27, 11.69))

    cover.text(
        0.5, 0.9,
        "Brief antibiotic use drives human gut bacteria\n towards low-cost resistance",
        ha="center", fontsize=16, weight="bold"
    )

    cover.text(
        0.5, 0.84,
        "Ciprofloxacin study\nVirus + Cellular organism trajectories",
        ha="center", fontsize=11
    )

    cover.text(
        0.1, 0.78,
        "Subjects included:",
        fontsize=11,
        va="top"
    )

    cover.text(
        0.12, 0.745,
        "\n".join(subjects),
        fontsize=9,
        va="top"
    )

    pdf.savefig(cover)
    plt.close(cover)

    ################################################
    # PAGE 2 — SUMMARY VIR + CEL (absolute)
    ################################################

    fig_abs, axes_abs = plt.subplots(
        2, 1,
        figsize=(8.27, 11.69),
        sharex=False
    )

    # VIR absolute
    axes_abs[0].errorbar(
        x_abs,
        summary["mean_vir"],
        yerr=summary["se_vir"],
        marker="o",
        linestyle="-",
        capsize=3,
    )

    for xi, (_, row) in enumerate(summary.iterrows()):
        se = row["se_vir"] if pd.notna(row["se_vir"]) else 0
        axes_abs[0].text(
            xi,
            row["mean_vir"] + se + 0.05,
            str(int(row["n_subjects"])),
            fontsize=8,
            ha="center",
            va="bottom",
            clip_on=True
        )

    axes_abs[0].set_ylabel("% Viruses")
    axes_abs[0].set_title("Mean VIRUS % per bucket (absolute)")
    axes_abs[0].grid(alpha=0.3)

    # CEL absolute
    axes_abs[1].errorbar(
        x_abs,
        summary["mean_cel"],
        yerr=summary["se_cel"],
        marker="s",
        linestyle="-",
        capsize=3,
    )

    for xi, (_, row) in enumerate(summary.iterrows()):
        se = row["se_cel"] if pd.notna(row["se_cel"]) else 0
        axes_abs[1].text(
            xi,
            row["mean_cel"] + se + 0.05,
            str(int(row["n_subjects"])),
            fontsize=8,
            ha="center",
            va="bottom",
            clip_on=True
        )

    axes_abs[1].set_ylabel("% cellular organisms")
    axes_abs[1].set_title("Mean cellular organisms % per bucket (absolute)")
    axes_abs[1].grid(alpha=0.3)

    for ax in axes_abs:
        ax.set_xticks(x_abs)
        ax.set_xticklabels(summary["bucket"], rotation=45)

    plt.tight_layout(rect=[0.08, 0.06, 0.97, 0.96])
    pdf.savefig(fig_abs)
    plt.close(fig_abs)

    ################################################
    # PAGE 3 — SUMMARY VIR + CEL (relative to baseline)
    ################################################

    fig_rel, axes_rel = plt.subplots(
        2, 1,
        figsize=(8.27, 11.69),
        sharex=False
    )

    # VIR relative
    axes_rel[0].errorbar(
        x_rel,
        summary_rel["mean_vir_rel"],
        yerr=summary_rel["se_vir_rel"],
        marker="o",
        linestyle="-",
        capsize=3,
    )

    axes_rel[0].axhline(0, linestyle="--", linewidth=0.8)
    axes_rel[0].set_ylabel("Δ% Viruses (relative to baseline)")
    axes_rel[0].set_title("Mean VIRUS % per bucket (relative to baseline)")
    axes_rel[0].grid(alpha=0.3)

    # CEL relative
    axes_rel[1].errorbar(
        x_rel,
        summary_rel["mean_cel_rel"],
        yerr=summary_rel["se_cel_rel"],
        marker="s",
        linestyle="-",
        capsize=3,
    )

    axes_rel[1].axhline(0, linestyle="--", linewidth=0.8)
    axes_rel[1].set_ylabel("Δ% cellular (relative to baseline)")
    axes_rel[1].set_title("Mean cellular organisms % per bucket (relative to baseline)")
    axes_rel[1].grid(alpha=0.3)

    for ax in axes_rel:
        ax.set_xticks(x_rel)
        ax.set_xticklabels(summary_rel["bucket"], rotation=45)

    plt.tight_layout(rect=[0.08, 0.06, 0.97, 0.96])
    pdf.savefig(fig_rel)
    plt.close(fig_rel)

    ################################################
    # PER SUBJECT PAGES – ABSOLUTE ONLY
    ################################################

    for subj in subjects:
        debug(f"\nBuilding per-subject page for {subj}")

        subj_grp = merged[merged["subject"] == subj].copy()
        subj_grp = subj_grp[subj_grp["bucket"] != "other"]

        if subj_grp.empty:
            debug(f"Subject {subj} has no non-'other' buckets, skipping.")
            continue

        # סדר לפי PHASE_ORDER
        subj_grp["bucket"] = pd.Categorical(
            subj_grp["bucket"],
            categories=PHASE_ORDER,
            ordered=True
        )
        subj_grp = subj_grp.sort_values("bucket")

        # per-subject absolute
        subj_summary_abs = (
            subj_grp
            .groupby("bucket", observed=True)
            .agg(
                mean_vir=("pct_vir", "mean"),
                mean_cel=("pct_cel", "mean"),
            )
            .reset_index()
        )

        debug(f"Subject {subj} summary (absolute):")
        debug(subj_summary_abs)

        xs_abs = range(len(subj_summary_abs))

        fig_s_abs, axes_s_abs = plt.subplots(
            2, 1,
            figsize=(8.27, 11.69),
            sharex=False
        )
        fig_s_abs.suptitle(f"Subject {subj} – absolute", fontsize=14)

        # VIR absolute
        axes_s_abs[0].plot(xs_abs, subj_summary_abs["mean_vir"], marker="o")
        axes_s_abs[0].grid(alpha=0.3)
        axes_s_abs[0].set_ylabel("% Viruses")
        axes_s_abs[0].set_title("VIRUSES trend (per phase, absolute)")
        axes_s_abs[0].set_xlabel("Bucket")
        axes_s_abs[0].set_xticks(xs_abs)
        axes_s_abs[0].set_xticklabels(subj_summary_abs["bucket"], rotation=45)

        # CELLULAR absolute
        axes_s_abs[1].plot(xs_abs, subj_summary_abs["mean_cel"], marker="o")
        axes_s_abs[1].grid(alpha=0.3)
        axes_s_abs[1].set_ylabel("% cellular")
        axes_s_abs[1].set_title("CELLULAR ORGANISMS trend (per phase, absolute)")
        axes_s_abs[1].set_xlabel("Bucket")
        axes_s_abs[1].set_xticks(xs_abs)
        axes_s_abs[1].set_xticklabels(subj_summary_abs["bucket"], rotation=45)

        plt.tight_layout(rect=[0, 0.04, 1, 0.94])
        pdf.savefig(fig_s_abs)
        plt.close(fig_s_abs)

debug(f"\n\nPDF written to {pdf_path}\n")
LOG_FILE.close()