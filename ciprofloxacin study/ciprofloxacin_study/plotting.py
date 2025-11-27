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
        axes_rel[0].axhline(0, linestyle="--", linewidth=0.8)
        axes_rel[0].set_ylabel("Δ% Viruses (relative to baseline)")
        axes_rel[0].set_title("Mean VIRUS % per bucket (relative to baseline)")
        axes_rel[0].grid(alpha=0.3)

        axes_rel[1].errorbar(x_rel, summary_rel["mean_cel_rel"], yerr=summary_rel["se_cel_rel"], marker="s", linestyle="-", capsize=3)
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

            subj_summary_abs = subj_grp.groupby("bucket", observed=True).agg(mean_vir=("pct_vir", "mean"), mean_cel=("pct_cel", "mean")).reset_index()

            xs_abs = range(len(subj_summary_abs))

            fig_s_abs, axes_s_abs = plt.subplots(2, 1, figsize=(8.27, 11.69), sharex=False)
            fig_s_abs.suptitle(f"Subject {subj} – absolute", fontsize=14)

            axes_s_abs[0].plot(xs_abs, subj_summary_abs["mean_vir"], marker="o")
            axes_s_abs[0].grid(alpha=0.3)
            axes_s_abs[0].set_ylabel("% Viruses")
            axes_s_abs[0].set_title("VIRUSES trend (per phase, absolute)")
            axes_s_abs[0].set_xlabel("Bucket")
            axes_s_abs[0].set_xticks(xs_abs)
            axes_s_abs[0].set_xticklabels(subj_summary_abs["bucket"], rotation=45)

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

    logger.debug(f"\n\nPDF written to {pdf_path}\n")
