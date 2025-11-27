"""Small orchestration CLI for the ciprofloxacin study package.

This provides a programmatic entrypoint equivalent to the original Trend_Graph.py
script and is kept intentionally simple (no heavy argument parsing required).
"""
from pathlib import Path
from .logger import get_logger
from .processing import load_and_prepare_data, filter_controls, compute_summary_tables
from .plotting import generate_pdf
from .config import DEFAULT_PDF_PATH

logger = get_logger(__name__)


def main(base_dir: str = None, pdf_out: str = None):
    if base_dir is None:
        base_dir = Path.cwd()
    logger.debug("=== RUN START ===")

    merged = load_and_prepare_data(base_dir=base_dir)
    merged = filter_controls(merged)

    merged, summary, summary_rel = compute_summary_tables(merged)

    if pdf_out is None:
        pdf_out = DEFAULT_PDF_PATH

    generate_pdf(merged, summary, summary_rel, pdf_path=pdf_out)

    logger.debug("Done — output written to %s" % pdf_out)


if __name__ == "__main__":
    # convenience epic: allow direct script execution
    main()
