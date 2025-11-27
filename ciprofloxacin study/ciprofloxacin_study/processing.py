import os
from pathlib import Path
import pandas as pd

from .config import PHASE_ORDER, CONTROL_SUBJECTS_TO_DELETE
from .logger import get_logger

logger = get_logger(__name__)


def assign_buckets(df, phase_order=PHASE_ORDER):
    """Assign bucket labels to a single subject's samples by ordering them in time.

    The earliest sample gets the first label in phase_order, the second sample the
    next label, etc. Any extra samples beyond the phase_order list are labelled
    "other".
    """
    df = df.sort_values("day").copy()
    days = df["day"].tolist()

    subj = df["subject"].iloc[0]
    logger.debug(f"\nAssigning buckets for subject {subj}")
    logger.debug(f"days: {days}")

    buckets = {}
    for idx, day in enumerate(days):
        if idx < len(phase_order):
            buckets[day] = phase_order[idx]
        else:
            buckets[day] = "other"

    df["bucket"] = df["day"].map(buckets)
    logger.debug(f"buckets: {df[['day','bucket']].values.tolist()}")

    return df


def add_relative_to_baseline(df):
    """Add pct_vir_rel and pct_cel_rel columns relative to a baseline sample.

    Baseline preference: prefer 'pre-9w' then 'day0'. If none present, set the
    relative columns to NA.
    """
    subj = df["subject"].iloc[0]

    baseline_candidates = df[df["bucket"].isin(["pre-9w", "day0"])].copy()

    if baseline_candidates.empty:
        logger.debug(f"Subject {subj}: no baseline (pre-9w/day0), setting rel=NaN")
        df["pct_vir_rel"] = pd.NA
        df["pct_cel_rel"] = pd.NA
        return df

    baseline_candidates["baseline_order"] = pd.Categorical(
        baseline_candidates["bucket"],
        categories=["pre-9w", "day0"],
        ordered=True,
    )

    baseline_row = baseline_candidates.sort_values("baseline_order").iloc[0]

    b_vir = baseline_row["pct_vir"]
    b_cel = baseline_row["pct_cel"]

    logger.debug(
        f"Subject {subj}: baseline bucket={baseline_row['bucket']}, "
        f"pct_vir={b_vir}, pct_cel={b_cel}"
    )

    df["pct_vir_rel"] = df["pct_vir"] / b_vir
    df["pct_cel_rel"] = df["pct_cel"] / b_cel

    return df


def load_and_prepare_data(base_dir: str = None, vir_cel_csv: str = "sample_to_virus_and_cellular_org_pct.csv", mapfile: str = "Subject To Sample.xlsx", sheet_name: str = "Supp. Table 1"):
    """Load CSV/Excel files, pivot to wide and merge as in original script.

    Returns the merged DataFrame (unsampled) after cleaning.
    """
    if base_dir is None:
        base_dir = os.getcwd()
    base_dir = str(Path(base_dir))

    logger.debug("Loading datasets...")

    vir_cel_path = os.path.join(base_dir, vir_cel_csv)
    map_path = os.path.join(base_dir, mapfile)

    vir_cel = pd.read_csv(vir_cel_path)
    mapdf = pd.read_excel(map_path, sheet_name=sheet_name)

    # pivot viruses / cellular organisms to wide format
    wide = (
        vir_cel
        .pivot_table(index=["acc", "sample_name"], columns="name", values="pct")
        .reset_index()
    )

    wide = wide.rename(columns={"Viruses": "pct_vir", "cellular organisms": "pct_cel"})

    merged = wide.merge(mapdf, left_on="sample_name", right_on="library", how="inner")

    merged["day"] = pd.to_numeric(merged["day"], errors="coerce")
    merged = merged.sort_values(["subject", "day"])  # stable ordering

    logger.debug(f"merged shape: {merged.shape}")
    logger.debug(merged.head())

    return merged


def filter_controls(merged, controls=CONTROL_SUBJECTS_TO_DELETE):
    logger.debug(f"Filtering {controls}")
    out = merged[~merged["subject"].isin(controls)].copy()
    logger.debug(f"After removing controls {controls}, shape: {out.shape}")
    logger.debug(f"Remaining subjects: {sorted(out['subject'].unique())}")
    return out


def compute_summary_tables(merged, phase_order=PHASE_ORDER):
    """Compute `summary` (absolute) and `summary_rel` (relative) tables.

    Very close to original script behavior: exclude 'other' bucket, compute mean,
    std, se and reindex by phase_order.
    """
    # assign buckets
    merged = (
        merged.groupby("subject", group_keys=False).apply(assign_buckets)
    )

    # add rel to baseline
    merged = (
        merged.groupby("subject", group_keys=False).apply(add_relative_to_baseline)
    )

    logger.debug("Bucket distribution:")
    logger.debug(merged["bucket"].value_counts())

    # absolute summary
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

    summary = (
        summary.set_index("bucket").reindex(phase_order).dropna(subset=["mean_vir"]).reset_index()
    )

    logger.debug("\nFinal summary table (absolute):")
    logger.debug(summary)

    # relative summary
    summary_rel = (
        merged[
            (merged["bucket"] != "other")
            & (merged["pct_vir_rel"].notna())
            & (merged["pct_cel_rel"].notna())
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
        summary_rel.set_index("bucket").reindex(phase_order).dropna(subset=["mean_vir_rel"]).reset_index()
    )

    logger.debug("\nFinal summary table (relative):")
    logger.debug(summary_rel)

    return merged, summary, summary_rel


def get_subjects(merged):
    return sorted(merged["subject"].unique())
