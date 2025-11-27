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


if __name__ == "__main__":
    # Choose the correct data-containing folder as base_dir. Data files live
    # in the repo but inside the "ciprofloxacin study" folder in this tree,
    # so prefer that folder when it exists — this makes the runner work when
    # pressing Run from the repo root.
    candidate1 = ROOT
    candidate2 = ROOT / "ciprofloxacin study"

    if (candidate1 / "sample_to_virus_and_cellular_org_pct.csv").exists():
        base_dir = str(candidate1)
    elif (candidate2 / "sample_to_virus_and_cellular_org_pct.csv").exists():
        base_dir = str(candidate2)
    else:
        # fallback — use repo root
        base_dir = str(ROOT)

    main(base_dir=base_dir)
