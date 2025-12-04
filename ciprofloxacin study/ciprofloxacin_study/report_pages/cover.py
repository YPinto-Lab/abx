"""Cover and methodology pages."""

import textwrap

import matplotlib.pyplot as plt

from ..config import CONTROL_SUBJECTS_TO_DELETE
from .style import A4_SIZE


def add_cover_page(pdf, merged, subjects):
    cover = plt.figure(figsize=A4_SIZE)
    cover.patch.set_facecolor("white")

    y_pos = 0.95
    cover.text(
        0.5,
        y_pos,
        "Brief Antibiotic Use Drives Human Gut Bacteria\nTowards Low-Cost Resistance",
        ha="center",
        fontsize=16,
        weight="bold",
    )
    y_pos -= 0.08

    cover.text(
        0.5,
        y_pos,
        "Ciprofloxacin Study — Virome and Cellular Organism Analysis",
        ha="center",
        fontsize=11,
        style="italic",
        color="darkslategray",
    )
    y_pos -= 0.06

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

    cover.text(0.1, y_pos, "Subjects:", fontsize=11, weight="bold")
    y_pos -= 0.03

    subjects_text = ", ".join(subjects)
    wrapped_subjects = textwrap.fill(subjects_text, width=90)
    cover.text(0.1, y_pos, wrapped_subjects, ha="left", va="top", fontsize=9)

    n_subject_lines = wrapped_subjects.count("\n") + 1
    y_pos -= n_subject_lines * 0.025 + 0.02

    if CONTROL_SUBJECTS_TO_DELETE:
        controls_note = f"Note: Control subjects ({', '.join(CONTROL_SUBJECTS_TO_DELETE)}) were omitted from analysis."
        cover.text(0.1, y_pos, controls_note, fontsize=8, style="italic", color="gray")
    y_pos -= 0.05

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

    pdf.savefig(cover)
    plt.close(cover)


def add_methodology_page(pdf):
    methods_fig = plt.figure(figsize=A4_SIZE)
    methods_fig.patch.set_facecolor("white")

    methods_fig.text(0.5, 0.94, "Methodology & Data Analysis", ha="center", fontsize=14, weight="bold")

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
        0.08,
        0.88,
        methods_text,
        ha="left",
        va="top",
        fontsize=9,
        family=None,
        bbox=dict(boxstyle="round", facecolor="whitesmoke", alpha=0.4),
    )

    pdf.savefig(methods_fig)
    plt.close(methods_fig)


def add_taxonomy_normalization_page(pdf):
    norm_fig = plt.figure(figsize=A4_SIZE)
    norm_fig.patch.set_facecolor("white")

    norm_fig.text(0.5, 0.96, "Choosing the Taxonomy Level for Viral Diversity", ha="center", fontsize=13, weight="bold")

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

    norm_fig.text(
        0.08,
        0.90,
        explanation_text,
        ha="left",
        va="top",
        fontsize=8.5,
        bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.2),
    )

    pdf.savefig(norm_fig)
    plt.close(norm_fig)
