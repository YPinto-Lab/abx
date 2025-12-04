"""Data transformation helpers: bucketing and baseline-relative computations.

These functions are intentionally pure (operate on DataFrames and return DataFrames)
so they are easy to unit-test.
"""
from .config import PHASE_ORDER
from .logger import get_logger
import pandas as pd

logger = get_logger(__name__)


def assign_buckets(df: pd.DataFrame, phase_order=PHASE_ORDER) -> pd.DataFrame:
    """Assign bucket labels to a single subject's samples by ordering them in time."""
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


def add_relative_to_baseline(df: pd.DataFrame) -> pd.DataFrame:
    """Add pct_vir_rel and pct_cel_rel columns relative to a baseline sample."""
    subj = df["subject"].iloc[0]

    baseline_buckets = ["pre-2d", "pre-1d", "day0"]
    baseline_rows = df[df["bucket"].isin(baseline_buckets)].copy()

    if not baseline_rows.empty:
        b_vir = baseline_rows["pct_vir"].mean()
        b_cel = baseline_rows["pct_cel"].mean()
        b_species = baseline_rows["num_virus_species"].mean() if "num_virus_species" in baseline_rows.columns else None
        logger.debug(
            f"Subject {subj}: baseline from buckets {sorted(baseline_rows['bucket'].unique())} with mean pct_vir={b_vir}, pct_cel={b_cel}"
        )
    else:
        baseline_candidates = df[df["bucket"].isin(["pre-9w", "day0"])].copy()

        if baseline_candidates.empty:
            logger.debug(f"Subject {subj}: no baseline (pre-2d/pre-1d/day0 or pre-9w/day0), setting rel=NaN")
            df["pct_vir_rel"] = pd.NA
            df["pct_cel_rel"] = pd.NA
            df["num_virus_species_rel"] = pd.NA
            return df

        baseline_candidates["baseline_order"] = pd.Categorical(
            baseline_candidates["bucket"],
            categories=["pre-9w", "day0"],
            ordered=True,
        )

        baseline_row = baseline_candidates.sort_values("baseline_order").iloc[0]
        b_vir = baseline_row.get("pct_vir")
        b_cel = baseline_row.get("pct_cel")
        b_species = baseline_row.get("num_virus_species")

        logger.debug(
            f"Subject {subj}: baseline bucket={baseline_row['bucket']}, "
            f"pct_vir={b_vir}, pct_cel={b_cel}"
        )

    df["pct_vir_rel"] = df["pct_vir"] / b_vir if pd.notna(b_vir) else pd.NA
    df["pct_cel_rel"] = df["pct_cel"] / b_cel if pd.notna(b_cel) else pd.NA

    if "num_virus_species" in df.columns and pd.notna(b_species):
        df["num_virus_species_rel"] = df["num_virus_species"] / b_species
    else:
        df["num_virus_species_rel"] = pd.NA

    return df


def _add_superkingdom_relative_to_baseline(df: pd.DataFrame, kingdom: str) -> pd.DataFrame:
    """Compute fold-change for a superkingdom relative to baseline."""
    subj = df['subject'].iloc[0]
    baseline_buckets = ['pre-2d', 'pre-1d', 'day0']
    baseline_rows = df[df['bucket'].isin(baseline_buckets)].copy()
    rel_col = f'{kingdom}_rel'

    if not baseline_rows.empty:
        b_kingdom = baseline_rows[kingdom].mean()
        logger.debug(f"Subject {subj}: {kingdom} baseline from {sorted(baseline_rows['bucket'].unique())} = {b_kingdom}")
    else:
        baseline_candidates = df[df['bucket'].isin(['pre-9w', 'day0'])].copy()
        if baseline_candidates.empty:
            logger.debug(f"Subject {subj}: no baseline for {kingdom}, setting rel=NaN")
            df[rel_col] = pd.NA
            return df
        baseline_candidates['baseline_order'] = pd.Categorical(
            baseline_candidates['bucket'],
            categories=['pre-9w', 'day0'],
            ordered=True,
        )
        baseline_row = baseline_candidates.sort_values('baseline_order').iloc[0]
        b_kingdom = baseline_row.get(kingdom)
        logger.debug(f"Subject {subj}: {kingdom} baseline (fallback) = {b_kingdom}")

    df[rel_col] = df[kingdom] / b_kingdom if pd.notna(b_kingdom) and b_kingdom > 0 else pd.NA
    return df


def _add_superkingdom_fraction_relative_to_baseline(df: pd.DataFrame, kingdom: str) -> pd.DataFrame:
    """Compute fold-change for the kingdom fraction (kingdom_frac) relative to baseline."""
    subj = df['subject'].iloc[0]
    frac_col = f"{kingdom}_frac"
    rel_col = f"{frac_col}_rel"

    baseline_buckets = ['pre-2d', 'pre-1d', 'day0']
    baseline_rows = df[df['bucket'].isin(baseline_buckets)].copy()

    if not baseline_rows.empty:
        b_frac = baseline_rows[frac_col].mean()
        logger.debug(f"Subject {subj}: {frac_col} baseline from {sorted(baseline_rows['bucket'].unique())} = {b_frac}")
    else:
        baseline_candidates = df[df['bucket'].isin(['pre-9w', 'day0'])].copy()
        if baseline_candidates.empty:
            logger.debug(f"Subject {subj}: no baseline for {frac_col}, setting rel=NaN")
            df[rel_col] = pd.NA
            return df
        baseline_candidates['baseline_order'] = pd.Categorical(
            baseline_candidates['bucket'],
            categories=['pre-9w', 'day0'],
            ordered=True,
        )
        baseline_row = baseline_candidates.sort_values('baseline_order').iloc[0]
        b_frac = baseline_row.get(frac_col)
        logger.debug(f"Subject {subj}: {frac_col} baseline (fallback) = {b_frac}")

    df[rel_col] = df[frac_col] / b_frac if pd.notna(b_frac) and b_frac > 0 else pd.NA
    return df


def get_subjects(merged: pd.DataFrame):
    return sorted(merged["subject"].unique())
