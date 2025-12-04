import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import traceback
import textwrap
from matplotlib.backends.backend_pdf import PdfPages
from .config import DEFAULT_PDF_PATH, PHASE_ORDER, CONTROL_SUBJECTS_TO_DELETE
from .logger import get_logger

logger = get_logger(__name__)


def generate_pdf(merged, summary, summary_rel, pdf_path: str = None, phase_order=PHASE_ORDER, taxa_df=None, taxa_reads_df=None):
    """Generate a multi-page professional PDF with summary plots, methodology, taxonomy analysis, and per-subject plots.
    
    Args:
        merged: Full merged dataframe with all samples
        summary: Absolute summary (mean/se per bucket)
        summary_rel: Relative summary (fold-change per bucket)
        pdf_path: Output PDF path
        phase_order: List of phase labels in order
        taxa_df: Optional dataframe with virus taxa ranks (from load_virus_taxa_ranks)
        taxa_reads_df: Optional dataframe with reads per taxa rank (from load_virus_taxa_reads)
    """
    if pdf_path is None:
        pdf_path = DEFAULT_PDF_PATH

    subjects = sorted(merged["subject"].unique())
    x_abs = range(len(summary))
    x_rel = range(len(summary_rel))

    # apply a clean seaborn theme for nicer default styling
    sns.set_theme(style="whitegrid")

    with PdfPages(pdf_path) as pdf:

        # Page 1 — PROFESSIONAL COVER (clean Word-document style)
        cover = plt.figure(figsize=(8.27, 11.69))
        cover.patch.set_facecolor('white')
        
        y_pos = 0.95  # Start near top
        
        # Title (centered, bold, large)
        cover.text(
            0.5, y_pos,
            "Brief Antibiotic Use Drives Human Gut Bacteria\nTowards Low-Cost Resistance",
            ha="center", fontsize=16, weight="bold"
        )
        y_pos -= 0.08
        
        # Subtitle (centered, italic, smaller)
        cover.text(
            0.5, y_pos,
            "Ciprofloxacin Study — Virome and Cellular Organism Analysis",
            ha="center", fontsize=11, style="italic", color="darkslategray"
        )
        y_pos -= 0.06
        
        # Study Overview section
        cover.text(0.1, y_pos, "Study Overview", fontsize=11, weight="bold")
        y_pos -= 0.03
        
        overview_text = (
            "This analysis tracks longitudinal changes in viral and cellular populations across "
            "multiple subjects during and after brief ciprofloxacin administration. Samples were "
            "characterized using metagenomic sequencing. Fold-changes are computed relative to each "
            "subject's pre-treatment baseline."
        )
        cover.text(0.1, y_pos, overview_text, ha="left", va="top", fontsize=9, wrap=True)
        y_pos -= 0.12
        
        # Subjects section (natural flowing list)
        cover.text(0.1, y_pos, "Subjects:", fontsize=11, weight="bold")
        y_pos -= 0.03
        
        # Write subjects as flowing text, line-wrapped naturally
        subjects_text = ", ".join(subjects)
        # Use textwrap to break into reasonable lines
        wrapped_subjects = textwrap.fill(subjects_text, width=90)
        cover.text(0.1, y_pos, wrapped_subjects, ha="left", va="top", fontsize=9)
        
        # Calculate how much space was used
        n_subject_lines = wrapped_subjects.count('\n') + 1
        y_pos -= (n_subject_lines * 0.025 + 0.02)
        
        # Controls note (small, at bottom of subjects)
        if CONTROL_SUBJECTS_TO_DELETE:
            controls_note = f"Note: Control subjects ({', '.join(CONTROL_SUBJECTS_TO_DELETE)}) were omitted from analysis."
            cover.text(0.1, y_pos, controls_note, fontsize=8, style="italic", color="gray")
        y_pos -= 0.05
        
        # Dataset Summary section
        cover.text(0.1, y_pos, "Dataset Summary", fontsize=11, weight="bold")
        y_pos -= 0.03
        
        n_samples = len(merged)
        n_rows = len(merged[merged["bucket"] != "other"])
        
        dataset_info = (
            f"Total samples collected: {n_samples}\n"
            f"Samples included in analysis: {n_rows}\n"
            f"Data source: Metagenomic sequencing (virus and cellular organism classification)\n"
            f"Method: Taxonomic abundance aggregated by time bucket per subject\n"
            f"Baseline: Per-subject mean of immediate pre-treatment samples (pre-2d, pre-1d, day0)\n"
            f"Visualization: Summary plots show mean ± SE across subjects; per-subject pages include\n"
            f"  sample metadata (library, accession) with links to NCBI Trace Run Browser"
        )
        cover.text(0.1, y_pos, dataset_info, ha="left", va="top", fontsize=8.5)
        
        pdf.savefig(cover, bbox_inches='tight')
        plt.close(cover)

        # Page 2 — METHODOLOGY EXPLANATION
        methods_fig = plt.figure(figsize=(8.27, 11.69))
        methods_fig.patch.set_facecolor('white')
        
        methods_fig.text(0.5, 0.94, "Methodology & Data Analysis", ha="center", fontsize=14, weight="bold")
        
        # Concise, non-redundant Methodology text
        methods_text = (
            "Baseline definition:\n"
            "- For each subject, baseline is the mean of available immediate pre-treatment samples (pre-2d, pre-1d, day0).\n"
            "- If none of these are available, the earlier pre-9w or day0 sample is used.\n\n"
            "Fold-change:\n"
            "- Fold-change = sample_value / baseline_value. Values >1 indicate an increase relative to baseline.\n\n"
            "Data aggregation and plotting:\n"
            "- Summary plots show mean ± standard error across subjects.\n"
            "- Relative plots collapse immediate pre-treatment samples into a single 'baseline' point for clarity.\n"
            "- Per-subject pages include library and accession information; tick labels link to NCBI Trace Run Browser.\n"
        )

        methods_fig.text(
            0.08, 0.88,
            methods_text,
            ha="left", va="top", fontsize=9, family=None,
            bbox=dict(boxstyle='round', facecolor='whitesmoke', alpha=0.4)
        )
        
        pdf.savefig(methods_fig, bbox_inches='tight')
        plt.close(methods_fig)
        
        # Page 3 — TAXONOMY NORMALIZATION EXPLANATION
        norm_fig = plt.figure(figsize=(8.27, 11.69))
        norm_fig.patch.set_facecolor('white')
        
        norm_fig.text(0.5, 0.96, "Choosing the Taxonomy Level for Viral Diversity", 
                     ha="center", fontsize=13, weight="bold")
        
        explanation_text = (
            "Challenge:\n"
            "Metagenomic classifiers (e.g., STAT) do not always classify reads to species level. Many reads\n"
            "are only classified to genus, family, or higher ranks. Using only species-level assignments loses\n"
            "information and introduces technical noise: apparent diversity changes may reflect classification\n"
            "uncertainty rather than true biological changes.\n\n"
            
            "Solution Strategy:\n"
            "We analyzed two complementary distributions:\n"
            "  1. Number of distinct taxa per rank: How many unique names exist at each level?\n"
            "  2. Read distribution per rank: Where is the biological material actually concentrated?\n\n"
            
            "Why This Matters:\n"
            "The two distributions often tell different stories. The taxa count table may suggest many species\n"
            "exist, but the read distribution reveals that most classified reads fall into genus or family level.\n"
            "This means species-level information is sparse and unstable, creating false impressions of\n"
            "diversity changes that are actually technical artifacts of the classifier.\n\n"
            
            "Key Decision:\n"
            "We chose genus or 'genus-like' level as the normalization standard because:\n"
            "  • It receives strong support from read assignments (most reads classify to this level)\n"
            "  • It is stable and resistant to classification errors\n"
            "  • It unites different species of the same genus into a reliable diversity metric\n"
            "  • Changes observed at this level reflect biological reality, not technical noise\n"
        )
        
        norm_fig.text(0.08, 0.90, explanation_text, ha="left", va="top", fontsize=8.5,
                     bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.2))
        
        pdf.savefig(norm_fig, bbox_inches='tight')
        plt.close(norm_fig)
        
        # Page 4 — TAXA COUNT DISTRIBUTION (if taxa data available)
        if taxa_df is not None and len(taxa_df) > 0:
            fig_taxa = plt.figure(figsize=(8.27, 6))
            
            # Title
            fig_taxa.text(0.5, 0.95, "Virus Taxonomy Tree Structure", ha="center", fontsize=14, weight="bold")
            
            # Explanation
            explanation = (
                "This chart shows the breadth of viral diversity detected across all subjects. "
                "Each bar represents the number of unique taxa (distinct viruses) identified at that taxonomic rank. "
                "For example, 120,825 unique viral species were detected, nested within 3,094 genera, "
                "which belong to 4,015 orders, and so on. This reflects the hierarchical nature of viral taxonomy."
            )
            fig_taxa.text(0.1, 0.90, explanation, ha="left", va="top", fontsize=9, wrap=True)
            
            # Create subplot for bar chart
            ax_taxa = fig_taxa.add_axes([0.15, 0.25, 0.75, 0.60])
            
            # Bar chart
            colors = sns.color_palette("husl", len(taxa_df))
            bars = ax_taxa.barh(taxa_df['rank'], taxa_df['num_taxa'], color=colors)
            
            # Add count labels on bars
            for i, (idx, row) in enumerate(taxa_df.iterrows()):
                ax_taxa.text(row['num_taxa'] + max(taxa_df['num_taxa'])*0.02, i, 
                           f"{int(row['num_taxa']):,}", 
                           va='center', fontsize=8)
            
            ax_taxa.set_xlabel('Number of Unique Taxa', fontsize=10, weight='bold')
            ax_taxa.set_title('')  # Remove default title, using fig title instead
            ax_taxa.grid(axis='x', alpha=0.2)
            ax_taxa.invert_yaxis()  # Most abundant at top
            
            # Add note at bottom
            note = "Note: Taxonomic ranks are hierarchical. Species are the most granular level; phylum/kingdom represent broader categories."
            fig_taxa.text(0.1, 0.08, note, ha="left", va="top", fontsize=8, style="italic", color="gray")
            
            pdf.savefig(fig_taxa, bbox_inches='tight')
            plt.close(fig_taxa)
        
        # Page 5 — READ DISTRIBUTION PER RANK (if reads data available)
        if taxa_reads_df is not None and len(taxa_reads_df) > 0:
            fig_reads = plt.figure(figsize=(8.27, 6))
            
            # Title
            fig_reads.text(0.5, 0.95, "Read Distribution by Taxonomic Rank", ha="center", fontsize=14, weight="bold")
            
            # Explanation with emphasis on self_count vs total_count
            explanation = (
                "This chart shows where the actual sequence data (reads) is distributed across taxonomic ranks. "
                "Each bar represents the number of reads DIRECTLY assigned to that rank (self_count). "
                "This is distinct from total_count, which includes reads assigned to the rank AND all its descendants. "
                "Using self_count reveals the true abundance at each level and avoids double-counting. "
                "Notice: many taxa exist at the species level (left chart), but few reads actually classify to species (this chart). "
                "Most reads concentrate in higher ranks (order, class), indicating classification uncertainty at fine resolution."
            )
            fig_reads.text(0.1, 0.90, explanation, ha="left", va="top", fontsize=8.5, wrap=True)
            
            # Create subplot for bar chart
            ax_reads = fig_reads.add_axes([0.15, 0.25, 0.75, 0.60])
            
            # Bar chart
            colors = sns.color_palette("viridis", len(taxa_reads_df))
            bars = ax_reads.barh(taxa_reads_df['rank'], taxa_reads_df['reads_at_rank'], color=colors)
            
            # Add count labels on bars
            for i, (idx, row) in enumerate(taxa_reads_df.iterrows()):
                reads_val = row['reads_at_rank']
                if pd.notna(reads_val) and reads_val > 0:
                    ax_reads.text(reads_val + max(taxa_reads_df['reads_at_rank'].fillna(0))*0.02, i,
                               f"{int(reads_val):,}",
                               va='center', fontsize=8)
            
            ax_reads.set_xlabel('Number of Reads (self_count)', fontsize=10, weight='bold')
            ax_reads.set_title('')  # Remove default title, using fig title instead
            ax_reads.grid(axis='x', alpha=0.2)
            ax_reads.invert_yaxis()  # Most abundant at top
            
            # Add note about self_count
            note = (
                "Note: self_count = reads directly assigned to this exact taxon only (not including descendants). "
                "This reveals the true abundance at each classification level."
            )
            fig_reads.text(0.1, 0.08, note, ha="left", va="top", fontsize=8, style="italic", color="gray")
            
            pdf.savefig(fig_reads, bbox_inches='tight')
            plt.close(fig_reads)

        # Page 4 (or 3) — SUMMARY absolute
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
        has_taxa = taxa_df is not None and len(taxa_df) > 0
        has_reads = taxa_reads_df is not None and len(taxa_reads_df) > 0
        add_pdf_outlines(pdf_path, subjects, sp_has_abs, has_taxa_page=has_taxa, has_reads_page=has_reads)
    except Exception as exc:
        logger.debug("Could not add outlines to PDF: %s", exc)
        logger.debug(traceback.format_exc())


def add_pdf_outlines(pdf_path: str, subjects: list[str], has_species_page: bool, has_taxa_page: bool = False, has_reads_page: bool = False):
    """Add PDF outline entries for the generated report using pypdf.

    Outline structure:
      - Cover
      - Methodology
      - Taxonomy Normalization Explanation
      - Taxonomy Distribution (optional)
      - Read Distribution by Rank (optional)
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
    # 0: cover, 1: methodology, 2: normalization explanation, 3: taxa count (if present), 
    # 4: reads dist (if present), 5: summary abs, 6: summary rel, 7: species (if present), rest: per-subject
    page_idx = 0
    writer.add_outline_item("Cover", page_idx)
    page_idx += 1
    
    writer.add_outline_item("Methodology", page_idx)
    page_idx += 1
    
    writer.add_outline_item("Taxonomy Normalization", page_idx)
    page_idx += 1
    
    if has_taxa_page:
        writer.add_outline_item("Taxonomy Distribution", page_idx)
        page_idx += 1
    
    if has_reads_page:
        writer.add_outline_item("Read Distribution by Rank", page_idx)
        page_idx += 1
    
    writer.add_outline_item("Summary — absolute", page_idx)
    page_idx += 1
    
    writer.add_outline_item("Summary — relative", page_idx)
    page_idx += 1

    if has_species_page:
        writer.add_outline_item("Summary — species", page_idx)
        page_idx += 1

    subj_start = page_idx

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
