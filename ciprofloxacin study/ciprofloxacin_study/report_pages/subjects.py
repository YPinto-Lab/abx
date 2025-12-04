"""Per-subject pages and figures."""

from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ..logger import get_logger
from .style import A4_SIZE, COLORS

logger = get_logger(__name__)


def add_per_subject_pages(pdf, merged, subjects: List[str], phase_order, merged_sk):
    for subj in subjects:
        logger.debug(f"\nBuilding per-subject page for {subj}")

        subj_grp = merged[merged["subject"] == subj].copy()
        subj_grp = subj_grp[subj_grp["bucket"] != "other"]

        if subj_grp.empty:
            logger.debug(f"Subject {subj} has no non-'other' buckets, skipping.")
            continue

        subj_grp["bucket"] = pd.Categorical(subj_grp["bucket"], categories=phase_order, ordered=True)
        subj_grp = subj_grp.sort_values("bucket")

        subj_summary_abs = (
            subj_grp.groupby("bucket", observed=True)
            .agg(
                mean_vir=("pct_vir", "mean"),
                mean_cel=("pct_cel", "mean"),
                mean_num_virus_species=("num_virus_species", "mean"),
                library=("library", "first"),
                acc=("acc", "first"),
            )
            .reset_index()
        )

        fig_s_abs = draw_subject_figure(subj_summary_abs, subj)
        pdf.savefig(fig_s_abs)
        plt.close(fig_s_abs)

        if merged_sk is None or subj not in merged_sk["subject"].unique():
            continue

        subj_sk_grp = merged_sk[merged_sk["subject"] == subj].copy()
        subj_sk_grp = subj_sk_grp[subj_sk_grp["bucket"] != "other"]
        if subj_sk_grp.empty:
            continue

        subj_sk_grp["bucket"] = pd.Categorical(subj_sk_grp["bucket"], categories=phase_order, ordered=True)
        subj_sk_grp = subj_sk_grp.sort_values("bucket")
        x_subj_sk = range(len(subj_sk_grp))

        for kingdom in [k for k in ["Bacteria", "Viruses", "Archaea", "Eukaryota"] if k in subj_sk_grp.columns]:
            fig_k_subj, axes_k_subj = plt.subplots(2, 1, figsize=A4_SIZE, sharex=True)
            fig_k_subj.suptitle(f"{kingdom} reads for subject {subj}", fontsize=14, weight="bold")

            axes_k_subj[0].plot(x_subj_sk, subj_sk_grp[kingdom], marker="o", color=COLORS["abs"])
            axes_k_subj[0].set_yscale("log")
            axes_k_subj[0].set_ylabel("Total Reads (log scale)", fontsize=10, weight="bold")
            axes_k_subj[0].grid(alpha=0.3)

            frac_col = f"{kingdom}_frac"
            if frac_col in subj_sk_grp.columns:
                axes_k_subj[1].plot(x_subj_sk, subj_sk_grp[frac_col], marker="o", color=COLORS["frac"])
                axes_k_subj[1].set_ylabel("Fraction of total reads", fontsize=10, weight="bold")
            else:
                axes_k_subj[1].text(0.5, 0.5, "No fraction data for this subject/kingdom", ha="center", va="center")
                axes_k_subj[1].axis("off")

            axes_k_subj[1].set_xticks(x_subj_sk)
            axes_k_subj[1].set_xticklabels(subj_sk_grp["bucket"], rotation=45, ha="right")
            axes_k_subj[1].set_xlabel("Time Bucket", fontsize=10, weight="bold")

            plt.tight_layout(rect=[0.05, 0.03, 0.98, 0.95])
            pdf.savefig(fig_k_subj)
            plt.close(fig_k_subj)


def draw_subject_figure(subj_summary_abs: pd.DataFrame, subj: str):
    """Create and return a matplotlib Figure for a single subject's absolute page."""
    xs_abs = range(len(subj_summary_abs))

    fig_s_abs, axes_s_abs = plt.subplots(3, 1, figsize=A4_SIZE, sharex=False)
    fig_s_abs.suptitle(subj, fontsize=14, fontweight="bold")

    sns.lineplot(x=list(xs_abs), y=subj_summary_abs["mean_vir"], marker="o", ax=axes_s_abs[0])
    axes_s_abs[0].grid(alpha=0.3)
    axes_s_abs[0].set_ylabel("% Viruses")
    axes_s_abs[0].set_title("Virues trend (absolute)", fontweight="bold")

    xt_labels = [
        f"{b}\n{lib}" if pd.notna(lib) else str(b)
        for b, lib in zip(subj_summary_abs["bucket"], subj_summary_abs["library"])
    ]
    axes_s_abs[0].set_xticks(xs_abs)
    axes_s_abs[0].set_xticklabels(xt_labels, rotation=45)

    for idx, tick in enumerate(axes_s_abs[0].get_xticklabels()):
        acc = subj_summary_abs.loc[idx, "acc"] if idx < len(subj_summary_abs) else None
        if pd.notna(acc):
            url = f"https://trace.ncbi.nlm.nih.gov/Traces/index.html?view=run_browser&acc={acc}&display=analysis"
            try:
                tick.set_url(url)
                tick.set_color("blue")
                tick.set_fontweight("bold")
            except Exception:
                pass

    sns.lineplot(x=list(xs_abs), y=subj_summary_abs["mean_cel"], marker="o", ax=axes_s_abs[1])
    axes_s_abs[1].grid(alpha=0.3)
    axes_s_abs[1].set_ylabel("% cellular")
    axes_s_abs[1].set_title("Cellular Organisms trend (Absolute)", fontweight="bold")
    axes_s_abs[1].set_xticks(xs_abs)
    axes_s_abs[1].set_xticklabels(xt_labels, rotation=45)
    for idx, tick in enumerate(axes_s_abs[1].get_xticklabels()):
        acc = subj_summary_abs.loc[idx, "acc"] if idx < len(subj_summary_abs) else None
        if pd.notna(acc):
            url = f"https://trace.ncbi.nlm.nih.gov/Traces/index.html?view=run_browser&acc={acc}&display=analysis"
            try:
                tick.set_url(url)
                tick.set_color("blue")
                tick.set_fontweight("bold")
            except Exception:
                pass

    if "mean_num_virus_species" in subj_summary_abs.columns and subj_summary_abs["mean_num_virus_species"].notna().any():
        sns.lineplot(x=list(xs_abs), y=subj_summary_abs["mean_num_virus_species"], marker="o", ax=axes_s_abs[2])
        axes_s_abs[2].grid(alpha=0.3)
        axes_s_abs[2].set_ylabel("# virus species")
        axes_s_abs[2].set_title("# virus species trend (absolute)", fontweight="bold")
        axes_s_abs[2].set_xticks(xs_abs)
        axes_s_abs[2].set_xticklabels(xt_labels, rotation=45)
        for idx, tick in enumerate(axes_s_abs[2].get_xticklabels()):
            acc = subj_summary_abs.loc[idx, "acc"] if idx < len(subj_summary_abs) else None
            if pd.notna(acc):
                url = f"https://trace.ncbi.nlm.nih.gov/Traces/index.html?view=run_browser&acc={acc}&display=analysis"
                try:
                    tick.set_url(url)
                    tick.set_color("blue")
                    tick.set_fontweight("bold")
                except Exception:
                    pass
    else:
        fig_s_abs.delaxes(axes_s_abs[2])

    plt.tight_layout(rect=[0, 0.04, 1, 0.94])
    return fig_s_abs
