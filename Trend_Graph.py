#!/usr/bin/env python3
"""Top-level runner for the ciprofloxacin study report.

This file mirrors the previous behaviour so you can run the report from the
repository root (for example by pressing Run in an editor) without worrying
about paths or wrappers.

It simply delegates to the package `ciprofloxacin_study.cli.main()` and exits.
"""

import sys
from pathlib import Path

# Try to ensure the package directory is importable when the repo has a
# parent folder with a space (`ciprofloxacin study/ciprofloxacin_study`). If the
# package isn't found on sys.path, add the nested folder so imports work when
# running from the project root.
ROOT = Path(__file__).resolve().parent
pkg_parent = ROOT / "ciprofloxacin study"
if (pkg_parent / "ciprofloxacin_study").exists():
    sys.path.insert(0, str(pkg_parent))

from ciprofloxacin_study.cli import main


def _pick_base_dir():
    """Prefer a directory that contains the data/ folder when available."""
    data_file = "sample_to_virus_and_cellular_org_pct.csv"
    candidates = [ROOT, ROOT / "ciprofloxacin study"]
    for cand in candidates:
        if (cand / "data" / data_file).exists() or (cand / data_file).exists():
            return str(cand)
    return str(ROOT)


if __name__ == "__main__":
    main(base_dir=_pick_base_dir())
