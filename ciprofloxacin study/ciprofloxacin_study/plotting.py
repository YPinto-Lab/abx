import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from .config import DEFAULT_PDF_PATH, PHASE_ORDER
from .logger import get_logger

logger = get_logger(__name__)


def generate_pdf(merged, summary, summary_rel, pdf_path: str = None, phase_order=PHASE_ORDER):
    """Generate a multi-page PDF with summary plots and per-subject plots.

    This mirrors the original Trend_Graph.py PDF generation logic.
    """
    if pdf_path is None:
        pdf_path = DEFAULT_PDF_PATH

    subjects = sorted(merged["subject"].unique())
    x_abs = range(len(summary))
    x_rel = range(len(summary_rel))

    with PdfPages(pdf_path) as pdf:

        # Page 1 — cover
        cover = plt.figure(figsize=(8.27, 11.69))
        cover.text(
            0.5, 0.9,
            "Brief antibiotic use drives human gut bacteria\n towards low-cost resistance",
            ha="center", fontsize=16, weight="bold"
        )

        cover.text(0.5, 0.84, "Ciprofloxacin study\nVirus + Cellular organism trajectories", ha="center", fontsize=11)

        cover.text(0.1, 0.78, "Subjects included:", fontsize=11, va="top")
        cover.text(0.12, 0.745, "\n".join(subjects), fontsize=9, va="top")

        pdf.savefig(cover)
        plt.close(cover)

        # Page 2 — SUMMARY absolute
        fig_abs, axes_abs = plt.subplots(2, 1, figsize=(8.27, 11.69), sharex=False)

        axes_abs[0].errorbar(x_abs, summary["mean_vir"], yerr=summary["se_vir"], marker="o", linestyle="-", capsize=3)
        for xi, (_, row) in enumerate(summary.iterrows()):
            se = row["se_vir"] if row["se_vir"] is not None else 0
            axes_abs[0].text(xi, row["mean_vir"] + se + 0.05, str(int(row["n_subjects"])), fontsize=8, ha="center", va="bottom", clip_on=True)
        axes_abs[0].set_ylabel("% Viruses")
        axes_abs[0].set_title("Mean VIRUS % per bucket (absolute)")
        axes_abs[0].grid(alpha=0.3)

        axes_abs[1].errorbar(x_abs, summary["mean_cel"], yerr=summary["se_cel"], marker="s", linestyle="-", capsize=3)
        for xi, (_, row) in enumerate(summary.iterrows()):
            se = row["se_cel"] if row["se_cel"] is not None else 0
            axes_abs[1].text(xi, row["mean_cel"] + se + 0.05, str(int(row["n_subjects"])), fontsize=8, ha="center", va="bottom", clip_on=True)

        axes_abs[1].set_ylabel("% cellular organisms")
        axes_abs[1].set_title("Mean cellular organisms % per bucket (absolute)")
        axes_abs[1].grid(alpha=0.3)

        for ax in axes_abs:
            ax.set_xticks(x_abs)
            ax.set_xticklabels(summary["bucket"], rotation=45)

        plt.tight_layout(rect=[0.08, 0.06, 0.97, 0.96])
        pdf.savefig(fig_abs)
        plt.close(fig_abs)

        # Page 3 — SUMMARY relative
        fig_rel, axes_rel = plt.subplots(2, 1, figsize=(8.27, 11.69), sharex=False)

        axes_rel[0].errorbar(x_rel, summary_rel["mean_vir_rel"], yerr=summary_rel["se_vir_rel"], marker="o", linestyle="-", capsize=3)
        axes_rel[0].axhline(1.0 if pd.notna(summary_rel.get("mean_vir_rel").iloc[0]) else 0, linestyle="--", linewidth=0.8)
        axes_rel[0].set_ylabel("Fold change (relative to baseline)")
        axes_rel[0].set_title("Mean VIRUS % per bucket (relative to baseline — fold change)")
        axes_rel[0].grid(alpha=0.3)

        axes_rel[1].errorbar(x_rel, summary_rel["mean_cel_rel"], yerr=summary_rel["se_cel_rel"], marker="s", linestyle="-", capsize=3)
        axes_rel[1].axhline(1.0 if pd.notna(summary_rel.get("mean_cel_rel").iloc[0]) else 0, linestyle="--", linewidth=0.8)
        axes_rel[1].set_ylabel("Fold change (relative to baseline)")
        axes_rel[1].set_title("Mean cellular organisms % per bucket (relative to baseline — fold change)")
        axes_rel[1].grid(alpha=0.3)

        for ax in axes_rel:
            ax.set_xticks(x_rel)
            ax.set_xticklabels(summary_rel["bucket"], rotation=45)

        plt.tight_layout(rect=[0.08, 0.06, 0.97, 0.96])
        pdf.savefig(fig_rel)
        plt.close(fig_rel)

        # PAGE 4 — SUMMARY species (absolute + relative) on the same page
        # Draw the absolute species means on the top subplot and the relative
        # (fold-change) on the bottom subplot so both views are side-by-side in
        # the output file.
        sp_has_abs = "mean_num_virus_species" in summary.columns
        sp_has_rel = "mean_num_virus_species_rel" in summary_rel.columns

        if sp_has_abs or sp_has_rel:
            fig_sp, axes_sp = plt.subplots(2, 1, figsize=(8.27, 11.69), sharex=False)

            # Top: absolute
            if sp_has_abs:
                axes_sp[0].errorbar(x_abs, summary["mean_num_virus_species"], yerr=summary.get("se_num_virus_species", None), marker="o", linestyle='-', capsize=3)
                for xi, (_, row) in enumerate(summary.iterrows()):
                    val = row.get("mean_num_virus_species")
                    if pd.notna(val):
                        n_sub = int(row.get("n_subjects", 0))
                        se = row.get("se_num_virus_species", 0) if pd.notna(row.get("se_num_virus_species")) else 0
                        axes_sp[0].text(xi, val + se + 0.5, str(n_sub), fontsize=8, ha='center', va='bottom', clip_on=True)
                axes_sp[0].set_ylabel("# virus species")
                axes_sp[0].set_title("Mean # virus species per bucket (absolute)")
                axes_sp[0].grid(alpha=0.3)
                axes_sp[0].set_xticks(x_abs)
                axes_sp[0].set_xticklabels(summary["bucket"], rotation=45)
            else:
                axes_sp[0].text(0.5, 0.5, "No species absolute data available", ha='center', va='center')
                axes_sp[0].axis('off')

            # Bottom: relative (fold-change)
            if sp_has_rel:
                axes_sp[1].errorbar(x_rel, summary_rel["mean_num_virus_species_rel"], yerr=summary_rel.get("se_num_virus_species_rel", None), marker="o", linestyle='-', capsize=3)
                axes_sp[1].axhline(1.0, linestyle='--', linewidth=0.8)
                axes_sp[1].set_ylabel("Fold change (relative to baseline)")
                axes_sp[1].set_title("Mean # virus species per bucket (relative to baseline — fold change)")
                axes_sp[1].grid(alpha=0.3)
                axes_sp[1].set_xticks(x_rel)
                axes_sp[1].set_xticklabels(summary_rel["bucket"], rotation=45)
            else:
                axes_sp[1].text(0.5, 0.5, "No species relative data available", ha='center', va='center')
                axes_sp[1].axis('off')

            plt.tight_layout(rect=[0.08, 0.06, 0.97, 0.96])
            pdf.savefig(fig_sp)
            plt.close(fig_sp)

        # Per-subject pages
        for subj in subjects:
            logger.debug(f"\nBuilding per-subject page for {subj}")

            subj_grp = merged[merged["subject"] == subj].copy()
            subj_grp = subj_grp[subj_grp["bucket"] != "other"]

            if subj_grp.empty:
                logger.debug(f"Subject {subj} has no non-'other' buckets, skipping.")
                continue

            subj_grp["bucket"] = pd.Categorical(subj_grp["bucket"], categories=phase_order, ordered=True)
            subj_grp = subj_grp.sort_values("bucket")

            # collect per-bucket means and also the first library and acc for each
            # bucket so we can display clickable library names on the x-axis.
            subj_summary_abs = (
                subj_grp
                .groupby("bucket", observed=True)
                .agg(
                    mean_vir=("pct_vir", "mean"),
                    mean_cel=("pct_cel", "mean"),
                    mean_num_virus_species=("num_virus_species", "mean"),
                    library=("library", "first"),
                    acc=("acc", "first"),
                )
                .reset_index()
            )

            # render the figure for a subject using a helper so tests can exercise it
            fig_s_abs = draw_subject_figure(subj_summary_abs, subj)
            pdf.savefig(fig_s_abs)
            plt.close(fig_s_abs)

        # finished generating pages in the PdfPages context
    logger.debug(f"\n\nPDF written to {pdf_path}\n")


def draw_subject_figure(subj_summary_abs: pd.DataFrame, subj: str):
    """Create and return a matplotlib Figure for a single subject's absolute page.

    The function returns the Figure object so unit tests can inspect tick label
    text and URL annotations without having to parse a generated PDF.
    """
    xs_abs = range(len(subj_summary_abs))

    # create 3 panels: viruses, cellular, and species (species may be NaN)
    fig_s_abs, axes_s_abs = plt.subplots(3, 1, figsize=(8.27, 11.69), sharex=False)
    fig_s_abs.suptitle(f"Subject {subj} – absolute", fontsize=14)

    axes_s_abs[0].plot(xs_abs, subj_summary_abs["mean_vir"], marker="o")
    axes_s_abs[0].grid(alpha=0.3)
    axes_s_abs[0].set_ylabel("% Viruses")
    axes_s_abs[0].set_title("VIRUSES trend (per phase, absolute)")
    axes_s_abs[0].set_xlabel("Bucket")
    # format tick labels as 'bucket\nlibrary' and attach a clickable URL
    xt_labels = [f"{b}\n{lib}" if pd.notna(lib) else str(b) for b, lib in zip(subj_summary_abs["bucket"], subj_summary_abs["library"])]
    axes_s_abs[0].set_xticks(xs_abs)
    axes_s_abs[0].set_xticklabels(xt_labels, rotation=45)

    # Attach URLs to the tick label text objects (PDF output will make these clickable).
    for idx, tick in enumerate(axes_s_abs[0].get_xticklabels()):
        acc = subj_summary_abs.loc[idx, "acc"] if idx < len(subj_summary_abs) else None
        if pd.notna(acc):
            # construct the trace URL per requested pattern
            url = f"https://trace.ncbi.nlm.nih.gov/Traces/index.html?view=run_browser&acc={acc}&display=analysis"
            try:
                tick.set_url(url)
                # make link-like visually obvious in the PDF
                tick.set_color("blue")
                # bold-ish for visibility
                tick.set_fontweight("bold")
            except Exception:
                # some backends may not support set_url; ignore gracefully
                pass

    axes_s_abs[1].plot(xs_abs, subj_summary_abs["mean_cel"], marker="o")
    axes_s_abs[1].grid(alpha=0.3)
    axes_s_abs[1].set_ylabel("% cellular")
    axes_s_abs[1].set_title("CELLULAR ORGANISMS trend (per phase, absolute)")
    axes_s_abs[1].set_xlabel("Bucket")
    # Also set the same library label + URLs on the second subplot's ticks
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

    # species (if present)
    if "mean_num_virus_species" in subj_summary_abs.columns and subj_summary_abs["mean_num_virus_species"].notna().any():
        axes_s_abs[2].plot(xs_abs, subj_summary_abs["mean_num_virus_species"], marker="o")
        axes_s_abs[2].grid(alpha=0.3)
        axes_s_abs[2].set_ylabel("# virus species")
        axes_s_abs[2].set_title("# virus species trend (per phase, absolute)")
        axes_s_abs[2].set_xlabel("Bucket")
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
        # hide the third axis if there is no species data
        fig_s_abs.delaxes(axes_s_abs[2])

    plt.tight_layout(rect=[0, 0.04, 1, 0.94])
    return fig_s_abs
