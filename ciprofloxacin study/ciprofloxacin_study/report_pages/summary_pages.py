"""Summary and superkingdom pages."""

from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ..figures.figures import plot_superkingdom_abs, plot_superkingdom_frac, plot_superkingdom_frac_rel
from ..figures.layout import plot_graphs_on_page
from .style import A4_SIZE, COLORS


def superkingdom_kingdoms(summary_sk, merged_sk) -> List[str]:
    if summary_sk is None and merged_sk is None:
        return []
    possible_kingdoms = ["Bacteria", "Viruses", "Archaea", "Eukaryota"]
    return [
        k
        for k in possible_kingdoms
        if (summary_sk is not None and f"mean_{k}" in summary_sk.columns)
        or (merged_sk is not None and k in merged_sk.columns)
    ]


def add_superkingdom_pages(pdf, summary_sk, summary_sk_rel, merged_sk):
    kingdoms = superkingdom_kingdoms(summary_sk, merged_sk)
    if not kingdoms:
        return False

    for kingdom in kingdoms:
        graph_fns = [
            (lambda k: (lambda ax: plot_superkingdom_abs(ax, summary_sk, k, COLORS)))(kingdom),
            (lambda k: (lambda ax: plot_superkingdom_frac(ax, summary_sk, k, COLORS)))(kingdom),
        ]
        titles = [
            f"{kingdom} Reads — Absolute (mean ± SE)",
            f"{kingdom} Fraction of Total Reads — Absolute (mean ± SE)",
        ]

        if summary_sk_rel is not None and len(summary_sk_rel) > 0:
            graph_fns.append((lambda k: (lambda ax: plot_superkingdom_frac_rel(ax, summary_sk_rel, k, COLORS)))(kingdom))
            titles.append(f"{kingdom} Fraction Fold-Change Relative to Baseline")

        plot_graphs_on_page(pdf, graph_fns, titles=titles, page_title=None)

    return True


def add_summary_abs_page(pdf, summary):
    x_abs = range(len(summary))
    fig_abs, axes_abs = plt.subplots(2, 1, figsize=A4_SIZE, sharex=False)

    sns.lineplot(x=list(x_abs), y=summary["mean_vir"], marker="o", ax=axes_abs[0])
    if "se_vir" in summary.columns and summary["se_vir"].notna().any():
        axes_abs[0].fill_between(list(x_abs), summary["mean_vir"] - summary["se_vir"], summary["mean_vir"] + summary["se_vir"], alpha=0.2)
    for xi, (_, row) in enumerate(summary.iterrows()):
        se = row["se_vir"] if row.get("se_vir") is not None else 0
        axes_abs[0].text(xi, row["mean_vir"] + se + 0.05, str(int(row["n_subjects"])), fontsize=8, ha="center", va="bottom", clip_on=True)
    axes_abs[0].set_ylabel("% Viruses")
    axes_abs[0].set_title("Mean VIRUS % per bucket (absolute)", fontweight="bold")
    axes_abs[0].grid(alpha=0.3)

    sns.lineplot(x=list(x_abs), y=summary["mean_cel"], marker="s", ax=axes_abs[1])
    if "se_cel" in summary.columns and summary["se_cel"].notna().any():
        axes_abs[1].fill_between(list(x_abs), summary["mean_cel"] - summary["se_cel"], summary["mean_cel"] + summary["se_cel"], alpha=0.2)
    for xi, (_, row) in enumerate(summary.iterrows()):
        se = row["se_cel"] if row["se_cel"] is not None else 0
        axes_abs[1].text(xi, row["mean_cel"] + se + 0.05, str(int(row["n_subjects"])), fontsize=8, ha="center", va="bottom", clip_on=True)

    axes_abs[1].set_ylabel("% cellular organisms")
    axes_abs[1].set_title("Mean cellular organisms % per bucket (absolute)", fontweight="bold")
    axes_abs[1].grid(alpha=0.3)

    for ax in axes_abs:
        ax.set_xticks(x_abs)
        ax.set_xticklabels(summary["bucket"], rotation=45)

    plt.tight_layout(rect=[0.08, 0.06, 0.97, 0.96])
    pdf.savefig(fig_abs)
    plt.close(fig_abs)


def add_summary_rel_page(pdf, summary_rel):
    summary_rel_plot = collapse_baseline_summary_rel(summary_rel)
    x_rel_plot = range(len(summary_rel_plot))

    fig_rel, axes_rel = plt.subplots(2, 1, figsize=A4_SIZE, sharex=False)

    sns.lineplot(x=list(x_rel_plot), y=summary_rel_plot["mean_vir_rel"], marker="o", ax=axes_rel[0])
    if "se_vir_rel" in summary_rel_plot.columns and summary_rel_plot["se_vir_rel"].notna().any():
        axes_rel[0].fill_between(list(x_rel_plot), summary_rel_plot["mean_vir_rel"] - summary_rel_plot["se_vir_rel"], summary_rel_plot["mean_vir_rel"] + summary_rel_plot["se_vir_rel"], alpha=0.2)
    axes_rel[0].axhline(1.0 if summary_rel_plot["mean_vir_rel"].notna().any() else 0, linestyle="--", linewidth=0.8)
    axes_rel[0].set_ylabel("Fold change (relative to baseline)")
    axes_rel[0].set_title("Mean VIRUS % per bucket (relative to baseline — fold change)", fontweight="bold")
    axes_rel[0].grid(alpha=0.3)

    sns.lineplot(x=list(x_rel_plot), y=summary_rel_plot["mean_cel_rel"], marker="s", ax=axes_rel[1])
    if "se_cel_rel" in summary_rel_plot.columns and summary_rel_plot["se_cel_rel"].notna().any():
        axes_rel[1].fill_between(list(x_rel_plot), summary_rel_plot["mean_cel_rel"] - summary_rel_plot["se_cel_rel"], summary_rel_plot["mean_cel_rel"] + summary_rel_plot["se_cel_rel"], alpha=0.2)
    axes_rel[1].axhline(1.0 if summary_rel_plot["mean_cel_rel"].notna().any() else 0, linestyle="--", linewidth=0.8)
    axes_rel[1].set_ylabel("Fold change (relative to baseline)")
    axes_rel[1].set_title("Mean cellular organisms % per bucket (relative to baseline — fold change)", fontweight="bold")
    axes_rel[1].grid(alpha=0.3)

    for ax in axes_rel:
        ax.set_xticks(x_rel_plot)
        ax.set_xticklabels(summary_rel_plot["bucket"], rotation=45)

    explanation = (
        "Baseline for fold-change = per-subject mean of 'pre-2d', 'pre-1d', and 'day0' samples "
        "(use available). If none present, fallback to 'pre-9w' or 'day0'."
    )
    fig_rel.text(0.5, 0.02, explanation, ha="center", fontsize=8)

    plt.tight_layout(rect=[0.08, 0.06, 0.97, 0.96])
    pdf.savefig(fig_rel)
    plt.close(fig_rel)
    return summary_rel_plot


def add_species_summary_page(pdf, summary, summary_rel_plot):
    sp_has_abs = "mean_num_virus_species" in summary.columns
    sp_has_rel = summary_rel_plot is not None and "mean_num_virus_species_rel" in summary_rel_plot.columns

    if not (sp_has_abs or sp_has_rel):
        return sp_has_abs, sp_has_rel

    x_abs = range(len(summary))
    x_rel_plot = range(len(summary_rel_plot))
    fig_sp, axes_sp = plt.subplots(2, 1, figsize=A4_SIZE, sharex=False)

    if sp_has_abs:
        sns.lineplot(x=list(x_abs), y=summary["mean_num_virus_species"], marker="o", ax=axes_sp[0])
        if "se_num_virus_species" in summary.columns and pd.notna(summary.get("se_num_virus_species")).any():
            axes_sp[0].fill_between(list(x_abs), summary["mean_num_virus_species"] - summary.get("se_num_virus_species", 0), summary["mean_num_virus_species"] + summary.get("se_num_virus_species", 0), alpha=0.2)
        for xi, (_, row) in enumerate(summary.iterrows()):
            val = row.get("mean_num_virus_species")
            if pd.notna(val):
                n_sub = int(row.get("n_subjects", 0))
                se = row.get("se_num_virus_species", 0) if pd.notna(row.get("se_num_virus_species")) else 0
                axes_sp[0].text(xi, val + se + 0.5, str(n_sub), fontsize=8, ha="center", va="bottom", clip_on=True)
        axes_sp[0].set_ylabel("# virus species")
        axes_sp[0].set_title("Mean # virus species per bucket (absolute)", fontweight="bold")
        axes_sp[0].grid(alpha=0.3)
        axes_sp[0].set_xticks(x_abs)
        axes_sp[0].set_xticklabels(summary["bucket"], rotation=45)
    else:
        axes_sp[0].text(0.5, 0.5, "No species absolute data available", ha="center", va="center")
        axes_sp[0].axis("off")

    if sp_has_rel:
        sns.lineplot(x=list(x_rel_plot), y=summary_rel_plot["mean_num_virus_species_rel"], marker="o", ax=axes_sp[1])
        if "se_num_virus_species_rel" in summary_rel_plot.columns and pd.notna(summary_rel_plot.get("se_num_virus_species_rel")).any():
            axes_sp[1].fill_between(list(x_rel_plot), summary_rel_plot["mean_num_virus_species_rel"] - summary_rel_plot.get("se_num_virus_species_rel", 0), summary_rel_plot["mean_num_virus_species_rel"] + summary_rel_plot.get("se_num_virus_species_rel", 0), alpha=0.2)
        axes_sp[1].axhline(1.0, linestyle="--", linewidth=0.8)
        axes_sp[1].set_ylabel("Fold change (relative to baseline)")
        axes_sp[1].set_title("Mean # virus species per bucket (relative to baseline — fold change)", fontweight="bold")
        axes_sp[1].grid(alpha=0.3)
        axes_sp[1].set_xticks(x_rel_plot)
        axes_sp[1].set_xticklabels(summary_rel_plot["bucket"], rotation=45)
    else:
        axes_sp[1].text(0.5, 0.5, "No species relative data available", ha="center", va="center")
        axes_sp[1].axis("off")

    plt.tight_layout(rect=[0.08, 0.06, 0.97, 0.96])
    pdf.savefig(fig_sp)
    plt.close(fig_sp)

    return sp_has_abs, sp_has_rel


def collapse_baseline_summary_rel(summary_rel: pd.DataFrame):
    """Collapse baseline buckets ('pre-2d', 'pre-1d', 'day0') into a single row for plotting."""
    df = summary_rel.copy()
    baseline_buckets = ["pre-2d", "pre-1d", "day0"]

    baseline_rows = df[df["bucket"].isin(baseline_buckets)]
    if baseline_rows.empty:
        return df

    numeric_cols = [
        "mean_vir_rel",
        "mean_cel_rel",
        "mean_num_virus_species_rel",
        "se_vir_rel",
        "se_cel_rel",
        "se_num_virus_species_rel",
        "n_rows",
        "n_subjects",
    ]

    combined = {"bucket": "baseline"}
    for col in numeric_cols:
        if col not in baseline_rows.columns:
            continue
        vals = baseline_rows[col].dropna()
        if vals.empty:
            combined[col] = pd.NA
            continue

        if col in ("mean_vir_rel", "mean_cel_rel", "mean_num_virus_species_rel") and "n_rows" in baseline_rows.columns:
            weights = baseline_rows.loc[vals.index, "n_rows"].fillna(1)
            combined[col] = (vals * weights).sum() / weights.sum()
        elif col in ("se_vir_rel", "se_cel_rel", "se_num_virus_species_rel") and "n_rows" in baseline_rows.columns:
            weights = baseline_rows.loc[vals.index, "n_rows"].fillna(1)
            combined[col] = (vals * weights).sum() / weights.sum()
        elif col in ("n_rows", "n_subjects"):
            combined[col] = baseline_rows[col].sum()
        else:
            combined[col] = vals.mean()

    rest = df[~df["bucket"].isin(baseline_buckets)].copy()
    try:
        idx = list(rest["bucket"]).index("pre-9w") + 1
    except ValueError:
        idx = 0

    top = rest.iloc[:idx]
    bottom = rest.iloc[idx:]

    combined_df = pd.DataFrame([combined])
    out = pd.concat([top, combined_df, bottom], ignore_index=True, axis=0, sort=False)
    return out.reset_index(drop=True)
