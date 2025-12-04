"""Compatibility shim: re-export refactored processing functions.

This file preserves the original public API by importing implementations from
smaller modules (`data_io`, `transform`, `summary`). Callers that import from
`.processing` will continue to work while the implementation is split.
"""

from .data_io import (
    load_and_prepare_data,
    load_virus_taxa_ranks,
    load_virus_taxa_reads,
    load_superkingdom_reads,
    filter_controls,
)

from .transform import (
    assign_buckets,
    add_relative_to_baseline,
    _add_superkingdom_relative_to_baseline,
    _add_superkingdom_fraction_relative_to_baseline,
    get_subjects,
)

from .summary import (
    compute_summary_tables,
    compute_superkingdom_summary,
)

__all__ = [
    'load_and_prepare_data', 'load_virus_taxa_ranks', 'load_virus_taxa_reads', 'load_superkingdom_reads', 'filter_controls',
    'assign_buckets', 'add_relative_to_baseline', '_add_superkingdom_relative_to_baseline', '_add_superkingdom_fraction_relative_to_baseline', 'get_subjects',
    'compute_summary_tables', 'compute_superkingdom_summary',
]
