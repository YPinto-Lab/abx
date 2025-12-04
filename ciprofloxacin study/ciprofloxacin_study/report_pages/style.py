"""Shared styling constants and helpers for report pages."""

import matplotlib.pyplot as plt
import seaborn as sns

A4_SIZE = (8.27, 11.69)
COLORS = {"abs": "C0", "frac": "C1", "rel": "C2"}


def configure_plot_style():
    """Apply consistent styling for A4 PDF output."""
    sns.set_theme(style="whitegrid")
    plt.rcParams.update(
        {
            "figure.figsize": A4_SIZE,
            "figure.dpi": 150,
            "axes.titlesize": 14,
            "axes.labelsize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "font.size": 10,
            "lines.linewidth": 2,
            # keep consistent margins across A4 pages
            "figure.subplot.left": 0.12,
            "figure.subplot.right": 0.95,
            "figure.subplot.top": 0.92,
            "figure.subplot.bottom": 0.08,
            "figure.subplot.hspace": 0.35,
            "figure.subplot.wspace": 0.2,
        }
    )
