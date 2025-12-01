# ciprofloxacin_study (refactored)

This package contains a split-up version of the previous monolithic `Trend_Graph.py`.

- Modules:
- `config.py` — constants and defaults (PHASE_ORDER, DEFAULT_PDF_PATH)
- `logger.py` — small logging helper writing to `trend_debug.log`
- `processing.py` — data loading and aggregation utilities (assign_buckets, add_relative_to_baseline, compute_summary_tables)
- `plotting.py` — functions to render the PDF report with matplotlib
- `cli.py` — small entrypoint that ties everything together

New: the package also ingests `sample_to_num_of_virus_species.csv` when present and
will include additional summary and per-subject plots showing the number of
viral species per sample (absolute and relative to baseline). The PDF now uses
"fold change (relative to baseline)" wording for relative plots (these are
ratios rather than deltas).

Run the report from the repository root (recommended) or the package folder:

```bash
# repository root — this script will run from the root and find the datafiles
python Trend_Graph.py

# or, from inside the package folder (has same behaviour but requires quoting path to parent)
python "../Trend_Graph.py"
```

Or import and call the package programmatically:

```py
from ciprofloxacin_study.cli import main
main(base_dir='path/to/data', pdf_out='output.pdf')
```
