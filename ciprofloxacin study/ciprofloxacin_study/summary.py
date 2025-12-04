"""Summary and aggregation logic for ciprofloxacin study.

This module exposes functions that compute the summary tables used in the
reporting pipeline.
"""
from .config import PHASE_ORDER
from .logger import get_logger
from .transform import assign_buckets, add_relative_to_baseline, _add_superkingdom_relative_to_baseline, _add_superkingdom_fraction_relative_to_baseline
import pandas as pd
import numpy as np

logger = get_logger(__name__)


def compute_summary_tables(merged: pd.DataFrame, phase_order=PHASE_ORDER):
    """Compute `summary` (absolute) and `summary_rel` (relative) tables.

    Returns (merged_with_rel, summary, summary_rel)
    """
    merged = merged.groupby("subject", group_keys=False).apply(assign_buckets)
    merged = merged.groupby("subject", group_keys=False).apply(add_relative_to_baseline)

    logger.debug("Bucket distribution:")
    logger.debug(merged["bucket"].value_counts())

    summary = (
        merged[merged["bucket"] != "other"]
        .groupby("bucket")
        .agg(
            mean_vir=("pct_vir", "mean"),
            std_vir=("pct_vir", "std"),
            mean_cel=("pct_cel", "mean"),
            std_cel=("pct_cel", "std"),
            mean_num_virus_species=("num_virus_species", "mean"),
            std_num_virus_species=("num_virus_species", "std"),
            n_rows=("pct_vir", "count"),
            n_subjects=("subject", "nunique"),
        )
        .reset_index()
    )

    summary["se_vir"] = summary["std_vir"] / summary["n_rows"] ** 0.5
    summary["se_cel"] = summary["std_cel"] / summary["n_rows"] ** 0.5
    if "std_num_virus_species" in summary.columns:
        summary["se_num_virus_species"] = summary["std_num_virus_species"] / summary["n_rows"] ** 0.5

    summary = (
        summary.set_index("bucket").reindex(phase_order).dropna(subset=["mean_vir"]).reset_index()
    )

    logger.debug("\nFinal summary table (absolute):")
    logger.debug(summary)

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
            mean_num_virus_species_rel=("num_virus_species_rel", "mean"),
            std_num_virus_species_rel=("num_virus_species_rel", "std"),
            n_rows=("pct_vir_rel", "count"),
            n_subjects=("subject", "nunique"),
        )
        .reset_index()
    )

    summary_rel["se_vir_rel"] = summary_rel["std_vir_rel"] / summary_rel["n_rows"] ** 0.5
    summary_rel["se_cel_rel"] = summary_rel["std_cel_rel"] / summary_rel["n_rows"] ** 0.5
    if "std_num_virus_species_rel" in summary_rel.columns:
        summary_rel["se_num_virus_species_rel"] = summary_rel["std_num_virus_species_rel"] / summary_rel["n_rows"] ** 0.5

    summary_rel = (
        summary_rel.set_index("bucket").reindex(phase_order).dropna(subset=["mean_vir_rel"]).reset_index()
    )

    logger.debug("\nFinal summary table (relative):")
    logger.debug(summary_rel)

    return merged, summary, summary_rel


def compute_superkingdom_summary(merged: pd.DataFrame, sk_df: pd.DataFrame, phase_order=PHASE_ORDER):
    """Merge superkingdom read data with merged dataframe and compute summaries.

    Returns (merged_with_sk, summary_sk, summary_sk_rel)
    """
    if sk_df is None or sk_df.empty:
        logger.debug("No superkingdom data; skipping")
        return merged, None, None

    sk_wide = sk_df.pivot_table(index='sample_name', columns='name', values='total_count', aggfunc='first').reset_index()
    merged_sk = merged.merge(sk_wide, on='sample_name', how='left')

    sk_kingdoms = [col for col in sk_wide.columns if col != 'sample_name']
    for kingdom in sk_kingdoms:
        if kingdom in merged_sk.columns:
            merged_sk[kingdom] = merged_sk[kingdom].fillna(0)

    merged_sk['total_reads_all_kingdoms'] = merged_sk[[k for k in sk_kingdoms if k in merged_sk.columns]].sum(axis=1)
    for kingdom in sk_kingdoms:
        frac_col = f"{kingdom}_frac"
        if kingdom in merged_sk.columns:
            merged_sk[frac_col] = merged_sk.apply(
                lambda r: (r[kingdom] / r['total_reads_all_kingdoms']) if pd.notna(r['total_reads_all_kingdoms']) and r['total_reads_all_kingdoms'] > 0 else pd.NA,
                axis=1,
            )

    for kingdom in sk_kingdoms:
        if kingdom in merged_sk.columns:
            merged_sk = merged_sk.groupby('subject', group_keys=False).apply(
                lambda x: _add_superkingdom_relative_to_baseline(x, kingdom),
                include_groups=True
            )

    for kingdom in sk_kingdoms:
        frac_col = f"{kingdom}_frac"
        if frac_col in merged_sk.columns:
            merged_sk = merged_sk.groupby('subject', group_keys=False).apply(
                lambda x: _add_superkingdom_fraction_relative_to_baseline(x, kingdom),
                include_groups=True
            )

    summary_sk_list = []
    for kingdom in sk_kingdoms:
        if kingdom in merged_sk.columns:
            kingdom_summary = (
                merged_sk[merged_sk['bucket'] != 'other']
                .groupby('bucket')
                .agg(
                    **{
                        f'mean_{kingdom}': (kingdom, 'mean'),
                        f'std_{kingdom}': (kingdom, 'std'),
                        'n_rows': ('subject', 'count'),
                        'n_subjects': ('subject', 'nunique'),
                    }
                )
                .reset_index()
            )
            kingdom_summary[f'se_{kingdom}'] = kingdom_summary[f'std_{kingdom}'] / kingdom_summary['n_rows'] ** 0.5
            summary_sk_list.append(kingdom_summary)
        frac_col = f"{kingdom}_frac"
        if frac_col in merged_sk.columns:
            frac_summary = (
                merged_sk[merged_sk['bucket'] != 'other']
                .groupby('bucket')
                .agg(
                    **{
                        f'mean_{frac_col}': (frac_col, 'mean'),
                        f'std_{frac_col}': (frac_col, 'std'),
                        'n_rows': ('subject', 'count'),
                        'n_subjects': ('subject', 'nunique'),
                    }
                )
                .reset_index()
            )
            frac_summary[f'se_{frac_col}'] = frac_summary[f'std_{frac_col}'] / frac_summary['n_rows'] ** 0.5
            summary_sk_list.append(frac_summary)

    summary_sk = summary_sk_list[0] if summary_sk_list else None
    for i in range(1, len(summary_sk_list)):
        summary_sk = summary_sk.merge(summary_sk_list[i], on=['bucket', 'n_rows', 'n_subjects'], how='outer')

    if summary_sk is not None:
        summary_sk = summary_sk.set_index('bucket').reindex(phase_order).reset_index()
        logger.debug(f"\nSuperkingdom absolute summary:\n{summary_sk}")

    summary_sk_rel_list = []
    for kingdom in sk_kingdoms:
        if kingdom in merged_sk.columns:
            rel_col = f'{kingdom}_rel'
            valid_rows = merged_sk[(merged_sk['bucket'] != 'other') & (merged_sk[rel_col].notna())]
            if not valid_rows.empty:
                kingdom_rel_summary = (
                    valid_rows
                    .groupby('bucket')
                    .agg(
                        **{
                            f'mean_{kingdom}_rel': (rel_col, 'mean'),
                            f'std_{kingdom}_rel': (rel_col, 'std'),
                            'n_rows': ('subject', 'count'),
                            'n_subjects': ('subject', 'nunique'),
                        }
                    )
                    .reset_index()
                )
                kingdom_rel_summary[f'se_{kingdom}_rel'] = kingdom_rel_summary[f'std_{kingdom}_rel'] / kingdom_rel_summary['n_rows'] ** 0.5
                summary_sk_rel_list.append(kingdom_rel_summary)
        frac_rel_col = f"{kingdom}_frac_rel"
        if frac_rel_col in merged_sk.columns:
            valid_rows = merged_sk[(merged_sk['bucket'] != 'other') & (merged_sk[frac_rel_col].notna())]
            if not valid_rows.empty:
                frac_rel_summary = (
                    valid_rows
                    .groupby('bucket')
                    .agg(
                        **{
                            f'mean_{frac_rel_col}': (frac_rel_col, 'mean'),
                            f'std_{frac_rel_col}': (frac_rel_col, 'std'),
                            'n_rows': ('subject', 'count'),
                            'n_subjects': ('subject', 'nunique'),
                        }
                    )
                    .reset_index()
                )
                frac_rel_summary[f'se_{frac_rel_col}'] = frac_rel_summary[f'std_{frac_rel_col}'] / frac_rel_summary['n_rows'] ** 0.5
                summary_sk_rel_list.append(frac_rel_summary)

    summary_sk_rel = summary_sk_rel_list[0] if summary_sk_rel_list else None
    for i in range(1, len(summary_sk_rel_list)):
        summary_sk_rel = summary_sk_rel.merge(summary_sk_rel_list[i], on=['bucket', 'n_rows', 'n_subjects'], how='outer')

    if summary_sk_rel is not None:
        summary_sk_rel = summary_sk_rel.set_index('bucket').reindex(phase_order).reset_index()
        logger.debug(f"\nSuperkingdom relative summary:\n{summary_sk_rel}")

    return merged_sk, summary_sk, summary_sk_rel
