import sys
from pathlib import Path


# Ensure the package directory (inside the 'ciprofloxacin study' folder) is
# on sys.path so tests can import ciprofloxacin_study regardless of the space
# in its parent directory.
ROOT = Path(__file__).resolve().parent.parent
pkg_dir = ROOT / "ciprofloxacin study" / "ciprofloxacin_study"
if pkg_dir.exists():
    sys.path.insert(0, str(pkg_dir.parent))  # add parent so "ciprofloxacin_study" is importable
