"""PDF reporting for the ciprofloxacin study."""

import traceback
from typing import Optional

from matplotlib.backends.backend_pdf import PdfPages

from .config import DEFAULT_PDF_PATH, PHASE_ORDER
from .logger import get_logger
from .report_pages.cover import add_cover_page, add_methodology_page, add_taxonomy_normalization_page
from .report_pages.pdf_outline import add_pdf_outlines
from .report_pages.style import configure_plot_style
from .report_pages.summary_pages import (
    add_species_summary_page,
    add_summary_abs_page,
    add_summary_rel_page,
    add_superkingdom_pages,
)
from .report_pages.summary_pages import collapse_baseline_summary_rel  # re-export
from .report_pages.taxonomy import add_reads_distribution_page, add_taxa_distribution_page
from .report_pages.subjects import add_per_subject_pages, draw_subject_figure  # re-export for tests

logger = get_logger(__name__)


def generate_pdf(
    merged,
    summary,
    summary_rel,
    pdf_path: Optional[str] = None,
    phase_order=PHASE_ORDER,
    taxa_df=None,
    taxa_reads_df=None,
    summary_sk=None,
    summary_sk_rel=None,
    merged_sk=None,
):
    """Generate a multi-page PDF with summary plots, methodology, taxonomy analysis, and per-subject plots."""
    if pdf_path is None:
        pdf_path = DEFAULT_PDF_PATH

    subjects = sorted(merged["subject"].unique())
    configure_plot_style()

    with PdfPages(pdf_path) as pdf:
        add_cover_page(pdf, merged, subjects)
        add_methodology_page(pdf)
        add_taxonomy_normalization_page(pdf)
        has_taxa = add_taxa_distribution_page(pdf, taxa_df)
        has_reads = add_reads_distribution_page(pdf, taxa_reads_df)
        has_sk = add_superkingdom_pages(pdf, summary_sk, summary_sk_rel, merged_sk)

        add_summary_abs_page(pdf, summary)
        summary_rel_plot = add_summary_rel_page(pdf, summary_rel)
        sp_has_abs, sp_has_rel = add_species_summary_page(pdf, summary, summary_rel_plot)
        add_per_subject_pages(pdf, merged, subjects, phase_order, merged_sk)

    has_species_page = sp_has_abs or sp_has_rel
    try:
        add_pdf_outlines(
            pdf_path,
            subjects,
            has_species_page,
            has_taxa_page=has_taxa,
            has_reads_page=has_reads,
            has_sk_page=has_sk,
        )
    except Exception as exc:
        logger.debug("Could not add outlines to PDF: %s", exc)
        logger.debug(traceback.format_exc())
