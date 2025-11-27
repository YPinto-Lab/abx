"""Configuration and constants for the ciprofloxacin study plotting package."""

# Desired ordering of buckets (PHASE_ORDER) when plotting on the X axis
PHASE_ORDER = [
    "pre-9w",
    "pre-2d",
    "pre-1d",
    "day0",
    "day1",
    "day2",
    "day3",
    "day4",
    "day5",
    "day6",
    "day7",
    "day8",
    "day10",
    "day18",
    "day28",
    "day77",
]

# Default control subjects to filter out
CONTROL_SUBJECTS_TO_DELETE = ["CAN", "CAC", "CAM", "CAK", "CAA"]

# Default output PDF path
DEFAULT_PDF_PATH = "per_subject_trends.pdf"

# toggles (can be overridden by client scripts)
DEBUG = True
