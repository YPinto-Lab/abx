import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
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

    # apply a clean seaborn theme for nicer default styling
    sns.set_theme(style="whitegrid")

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

        sns.lineplot(x=list(x_abs), y=summary["mean_vir"], marker="o", ax=axes_abs[0])
        # add se band if present
        if "se_vir" in summary.columns and summary["se_vir"].notna().any():
            axes_abs[0].fill_between(list(x_abs), summary["mean_vir"] - summary["se_vir"], summary["mean_vir"] + summary["se_vir"], alpha=0.2)
        for xi, (_, row) in enumerate(summary.iterrows()):
            se = row["se_vir"] if pd.notna(row.get("se_vir")) else 0
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

        # Page 3 — SUMMARY relative
        fig_rel, axes_rel = plt.subplots(2, 1, figsize=(8.27, 11.69), sharex=False)

        # compute collapsed version (baseline fusion) and plot that instead
        summary_rel_plot = collapse_baseline_summary_rel(summary_rel)
        x_rel_plot = range(len(summary_rel_plot))

        sns.lineplot(x=list(x_rel_plot), y=summary_rel_plot["mean_vir_rel"], marker="o", ax=axes_rel[0])
        if "se_vir_rel" in summary_rel_plot.columns and summary_rel_plot["se_vir_rel"].notna().any():
            axes_rel[0].fill_between(list(x_rel_plot), summary_rel_plot["mean_vir_rel"] - summary_rel_plot["se_vir_rel"], summary_rel_plot["mean_vir_rel"] + summary_rel_plot["se_vir_rel"], alpha=0.2)
        axes_rel[0].axhline(1.0 if pd.notna(summary_rel.get("mean_vir_rel").iloc[0]) else 0, linestyle="--", linewidth=0.8)
        axes_rel[0].set_ylabel("Fold change (relative to baseline)")
        axes_rel[0].set_title("Mean VIRUS % per bucket (relative to baseline — fold change)", fontweight="bold")
        axes_rel[0].grid(alpha=0.3)

        sns.lineplot(x=list(x_rel_plot), y=summary_rel_plot["mean_cel_rel"], marker="s", ax=axes_rel[1])
        if "se_cel_rel" in summary_rel_plot.columns and summary_rel_plot["se_cel_rel"].notna().any():
            axes_rel[1].fill_between(list(x_rel_plot), summary_rel_plot["mean_cel_rel"] - summary_rel_plot["se_cel_rel"], summary_rel_plot["mean_cel_rel"] + summary_rel_plot["se_cel_rel"], alpha=0.2)
        axes_rel[1].axhline(1.0 if pd.notna(summary_rel.get("mean_cel_rel").iloc[0]) else 0, linestyle="--", linewidth=0.8)
        axes_rel[1].set_ylabel("Fold change (relative to baseline)")
        axes_rel[1].set_title("Mean cellular organisms % per bucket (relative to baseline — fold change)", fontweight="bold")
        axes_rel[1].grid(alpha=0.3)

        # For relative plots, collapse the pre-samples (pre-2d, pre-1d, day0)
        # into a single 'baseline' point because fold-change is defined as the
        # average across those samples per subject (see explanation below).
        summary_rel_plot = collapse_baseline_summary_rel(summary_rel)
        x_rel_plot = range(len(summary_rel_plot))

        for ax in axes_rel:
            ax.set_xticks(x_rel_plot)
            ax.set_xticklabels(summary_rel_plot["bucket"], rotation=45)

        # document baseline definition so readers understand the fold-change reference
        explanation = (
            "Baseline for fold-change = per-subject mean of 'pre-2d', 'pre-1d', and 'day0' samples "
            "(use available). If none present, fallback to 'pre-9w' or 'day0'."
        )
        fig_rel.text(0.5, 0.02, explanation, ha='center', fontsize=8)

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
                sns.lineplot(x=list(x_abs), y=summary["mean_num_virus_species"], marker="o", ax=axes_sp[0])
                if "se_num_virus_species" in summary.columns and pd.notna(summary.get("se_num_virus_species")).any():
                    axes_sp[0].fill_between(list(x_abs), summary["mean_num_virus_species"] - summary.get("se_num_virus_species", 0), summary["mean_num_virus_species"] + summary.get("se_num_virus_species", 0), alpha=0.2)
                for xi, (_, row) in enumerate(summary.iterrows()):
                    val = row.get("mean_num_virus_species")
                    if pd.notna(val):
                        n_sub = int(row.get("n_subjects", 0))
                        se = row.get("se_num_virus_species", 0) if pd.notna(row.get("se_num_virus_species")) else 0
                        axes_sp[0].text(xi, val + se + 0.5, str(n_sub), fontsize=8, ha='center', va='bottom', clip_on=True)
                axes_sp[0].set_ylabel("# virus species")
                axes_sp[0].set_title("Mean # virus species per bucket (absolute)", fontweight="bold")
                axes_sp[0].grid(alpha=0.3)
                axes_sp[0].set_xticks(x_abs)
                axes_sp[0].set_xticklabels(summary["bucket"], rotation=45)
            else:
                axes_sp[0].text(0.5, 0.5, "No species absolute data available", ha='center', va='center')
                axes_sp[0].axis('off')

            # Bottom: relative (fold-change)
            if sp_has_rel:
                # use the collapsed relative summary for the species relative plot too
                sns.lineplot(x=list(x_rel_plot), y=summary_rel_plot["mean_num_virus_species_rel"], marker="o", ax=axes_sp[1])
                if "se_num_virus_species_rel" in summary_rel_plot.columns and pd.notna(summary_rel_plot.get("se_num_virus_species_rel")).any():
                    axes_sp[1].fill_between(list(x_rel_plot), summary_rel_plot["mean_num_virus_species_rel"] - summary_rel_plot.get("se_num_virus_species_rel", 0), summary_rel_plot["mean_num_virus_species_rel"] + summary_rel_plot.get("se_num_virus_species_rel", 0), alpha=0.2)
                axes_sp[1].axhline(1.0, linestyle='--', linewidth=0.8)
                axes_sp[1].set_ylabel("Fold change (relative to baseline)")
                axes_sp[1].set_title("Mean # virus species per bucket (relative to baseline — fold change)", fontweight="bold")
                axes_sp[1].grid(alpha=0.3)
                axes_sp[1].set_xticks(x_rel_plot)
                axes_sp[1].set_xticklabels(summary_rel_plot["bucket"], rotation=45)
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

    # attempt to add PDF outlines (bookmarks) for easier navigation in viewers
    try:
        add_pdf_outlines(pdf_path, subjects, sp_has_abs)
    except Exception as exc:
        import traceback
        logger.debug("Could not add outlines to PDF: %s", exc)
        logger.debug(traceback.format_exc())


def add_pdf_outlines(pdf_path: str, subjects: list[str], has_species_page: bool):
    """Add PDF outline entries for the generated report using pypdf.

    Outline structure:
      - Cover
      - Summary — absolute
      - Summary — relative
      - Summary — species (optional)
      - Per-subject pages
          - Subject1
          - Subject2

    This function overwrites the existing PDF in place after adding bookmarks.
    """
    try:
        from pypdf import PdfReader, PdfWriter
    except Exception:  # fallback message if library is missing
        raise

    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    # copy pages to the writer
    for p in reader.pages:
        writer.add_page(p)

    # page indexes are zero-based. pages order in the PDF:
    # 0: cover, 1: summary abs, 2: summary rel, 3: species (if present), 3/4+: per-subject
    writer.add_outline_item("Cover", 0)
    writer.add_outline_item("Summary — absolute", 1)
    writer.add_outline_item("Summary — relative", 2)

    subj_start = 3
    if has_species_page:
        writer.add_outline_item("Summary — species", 3)
        subj_start = 4

    # top-level 'Per-subject pages' entry points to the first subject page
    if len(subjects) > 0:
        first_subj_page = subj_start if subj_start < len(reader.pages) else (len(reader.pages) - 1)
        parent = writer.add_outline_item("Per-subject pages", first_subj_page)
        # add each subject as a child under the parent
        for idx, subj in enumerate(subjects):
            page_index = subj_start + idx
            if page_index >= len(reader.pages):
                break
            # color must be a tuple (r,g,b) or hex string; use blue RGB tuple
            writer.add_outline_item(subj, page_index, parent=parent, color=(0, 0, 1), bold=True)

    # overwrite original PDF
    with open(pdf_path, "wb") as f:
        writer.write(f)


def collapse_baseline_summary_rel(summary_rel: pd.DataFrame):
    """Collapse 'pre-2d', 'pre-1d', 'day0' rows in a relative-summary dataframe
    into a single 'baseline' row for plotting.

    The function returns a new DataFrame with the baseline aggregated (weighted
    by n_rows where available) and the rest of the rows in the same order
    (pre-9w, baseline, then day1...).
    """
    df = summary_rel.copy()
    baseline_buckets = ["pre-2d", "pre-1d", "day0"]

    baseline_rows = df[df["bucket"].isin(baseline_buckets)]
    if baseline_rows.empty:
        return df

    # combine numeric columns using n_rows as weights when available
    # list numeric columns typically present in summary_rel
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
    total_n = baseline_rows.get("n_rows", pd.Series([0])).sum()

    for col in numeric_cols:
        if col not in baseline_rows.columns:
            continue
        vals = baseline_rows[col].dropna()
        if vals.empty:
            combined[col] = pd.NA
            continue

        if col in ("mean_vir_rel", "mean_cel_rel", "mean_num_virus_species_rel") and "n_rows" in baseline_rows.columns:
            # weighted mean by n_rows
            weights = baseline_rows.loc[vals.index, "n_rows"].fillna(1)
            combined[col] = (vals * weights).sum() / weights.sum()
        elif col in ("se_vir_rel", "se_cel_rel", "se_num_virus_species_rel") and "n_rows" in baseline_rows.columns:
            # crude weighted average of se (approximate)
            weights = baseline_rows.loc[vals.index, "n_rows"].fillna(1)
            combined[col] = (vals * weights).sum() / weights.sum()
        elif col in ("n_rows", "n_subjects"):
            combined[col] = baseline_rows[col].sum()
        else:
            combined[col] = vals.mean()

    # drop the baseline rows and insert combined row after pre-9w
    rest = df[~df["bucket"].isin(baseline_buckets)].copy()

    # find insert position after pre-9w
    try:
        idx = list(rest["bucket"]).index("pre-9w") + 1
    except ValueError:
        idx = 0

    top = rest.iloc[:idx]
    bottom = rest.iloc[idx:]

    combined_df = pd.DataFrame([combined])
    out = pd.concat([top, combined_df, bottom], ignore_index=True, axis=0, sort=False)
    return out.reset_index(drop=True)


def draw_subject_figure(subj_summary_abs: pd.DataFrame, subj: str):
    """Create and return a matplotlib Figure for a single subject's absolute page.

    The function returns the Figure object so unit tests can inspect tick label
    text and URL annotations without having to parse a generated PDF.
    """
    xs_abs = range(len(subj_summary_abs))

    # create 3 panels: viruses, cellular, and species (species may be NaN)
    fig_s_abs, axes_s_abs = plt.subplots(3, 1, figsize=(8.27, 11.69), sharex=False)
    # suptitle: show only the subject code (e.g. 'AAQ') — omit the words
    # 'Subject' and 'absolute' per UX request; keep it bold and prominent.
    fig_s_abs.suptitle(subj, fontsize=14, fontweight="bold")

    sns.lineplot(x=list(xs_abs), y=subj_summary_abs["mean_vir"], marker="o", ax=axes_s_abs[0])
    axes_s_abs[0].grid(alpha=0.3)
    axes_s_abs[0].set_ylabel("% Viruses")
    axes_s_abs[0].set_title("Virues trend (absolute)", fontweight="bold")
    # Only set the x-label on the figure's bottom-most visible axis so "Bucket"
    # does not repeat across subplots. We'll set the label on the lowest
    # axis that remains (species if present, otherwise the second one).
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

    sns.lineplot(x=list(xs_abs), y=subj_summary_abs["mean_cel"], marker="o", ax=axes_s_abs[1])
    axes_s_abs[1].grid(alpha=0.3)
    axes_s_abs[1].set_ylabel("% cellular")
    axes_s_abs[1].set_title("Cellular Organisms trend (Absolute)", fontweight="bold")
    # intentionally do not set xlabel here to avoid repeating 'Bucket'
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
        sns.lineplot(x=list(xs_abs), y=subj_summary_abs["mean_num_virus_species"], marker="o", ax=axes_s_abs[2])
        axes_s_abs[2].grid(alpha=0.3)
        axes_s_abs[2].set_ylabel("# virus species")
        axes_s_abs[2].set_title("# virus species trend (absolute)", fontweight="bold")
        # Do not show an x-axis label; tick labels are sufficient and 'Bucket'
        # is intentionally omitted per UX request.
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
        # hide the third axis if there is no species data and label the 2nd (bottom) axis
        fig_s_abs.delaxes(axes_s_abs[2])
        # intentionally do not add a repeated x-axis label; omit 'Bucket' entirely

    plt.tight_layout(rect=[0, 0.04, 1, 0.94])
    return fig_s_abs
