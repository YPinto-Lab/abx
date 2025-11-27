"""Ciprofloxacin study utilities package.

This package mostly mirrors the original Trend_Graph.py script but split across
modules so individual responsibilities are clear and unit-testable.
"""

from .config import PHASE_ORDER, CONTROL_SUBJECTS_TO_DELETE, DEFAULT_PDF_PATH
from .logger import get_logger
from .processing import (
    assign_buckets,
    add_relative_to_baseline,
    load_and_prepare_data,
    compute_summary_tables,
)

__all__ = [
    "PHASE_ORDER",
    "CONTROL_SUBJECTS_TO_DELETE",
    "DEFAULT_PDF_PATH",
    "get_logger",
    "assign_buckets",
    "add_relative_to_baseline",
    "load_and_prepare_data",
    "compute_summary_tables",
    # plotting module imports matplotlib; keep that lazy so lightweight imports
    # such as `from ciprofloxacin_study import processing` don't require it.
]
