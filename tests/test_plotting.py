import matplotlib
matplotlib.use("Agg")

import pandas as pd

from ciprofloxacin_study.plotting import draw_subject_figure
from ciprofloxacin_study.plotting import collapse_baseline_summary_rel


def test_draw_subject_tick_labels_and_urls():
    df = pd.DataFrame({
        "bucket": ["pre-9w", "day0", "day1"],
        "mean_vir": [1.0, 2.0, 3.0],
        "mean_cel": [99.0, 98.0, 97.0],
        "mean_num_virus_species": [10.0, 12.0, 13.0],
        "library": ["libA", "libB", "libC"],
        "acc": ["SRR000001", "SRR000002", "SRR000003"],
    })

    fig = draw_subject_figure(df, "TESTSUBJ")
    ax = fig.axes[0]

    texts = [t.get_text() for t in ax.get_xticklabels()]
    assert texts == ["pre-9w\nlibA", "day0\nlibB", "day1\nlibC"]

    urls = [t.get_url() for t in ax.get_xticklabels()]
    expected = [
        "https://trace.ncbi.nlm.nih.gov/Traces/index.html?view=run_browser&acc=SRR000001&display=analysis",
        "https://trace.ncbi.nlm.nih.gov/Traces/index.html?view=run_browser&acc=SRR000002&display=analysis",
        "https://trace.ncbi.nlm.nih.gov/Traces/index.html?view=run_browser&acc=SRR000003&display=analysis",
    ]
    assert urls == expected

    colors = [t.get_color() for t in ax.get_xticklabels()]
    assert all(c == "blue" for c in colors)


def test_collapse_baseline_summary_rel():
    df = pd.DataFrame({
        "bucket": ["pre-9w", "pre-2d", "pre-1d", "day0", "day1"],
        "mean_vir_rel": [1.5, 0.8, 1.0, 1.2, 1.4],
        "se_vir_rel": [0.1, 0.11, 0.09, 0.08, 0.12],
        "n_rows": [10, 5, 5, 10, 12],
        "n_subjects": [10, 5, 5, 10, 12],
    })

    out = collapse_baseline_summary_rel(df)
    # expect one baseline bucket present instead of three pre-* entries
    assert "baseline" in list(out["bucket"])
    # ensure only one baseline row
    assert sum(out["bucket"] == "baseline") == 1


def test_draw_subject_figure_single_bucket_label_when_species_present():
    df = pd.DataFrame({
        "bucket": ["pre-9w", "day0", "day1"],
        "mean_vir": [1.0, 2.0, 3.0],
        "mean_cel": [99.0, 98.0, 97.0],
        "mean_num_virus_species": [10, 12, 15],
        "library": ["L1", "L2", "L3"],
        "acc": ["A1", "A2", "A3"],
    })
    fig = draw_subject_figure(df, "S1")
    # ensure 'Bucket' label is not present at all
    bucket_labels = [ax.get_xlabel() for ax in fig.axes]
    assert 'Bucket' not in bucket_labels


def test_draw_subject_figure_single_bucket_label_when_no_species():
    df = pd.DataFrame({
        "bucket": ["pre-9w", "day0"],
        "mean_vir": [1.0, 2.0],
        "mean_cel": [99.0, 98.0],
        "library": ["L1", "L2"],
        "acc": ["A1", "A2"],
    })
    fig = draw_subject_figure(df, "S2")
    bucket_labels = [ax.get_xlabel() for ax in fig.axes]
    # There should be no 'Bucket' label
    assert 'Bucket' not in bucket_labels


def _is_bold_fontweight(weight):
    # matplotlib accepts either 'bold' or numeric weights (700+). Accept both.
    try:
        if isinstance(weight, str):
            return 'bold' in weight.lower()
        return float(weight) >= 700
    except Exception:
        return False


def test_draw_subject_titles_are_bold():
    df = pd.DataFrame({
        "bucket": ["pre-9w", "day0", "day1"],
        "mean_vir": [1.0, 2.0, 3.0],
        "mean_cel": [99.0, 98.0, 97.0],
        "mean_num_virus_species": [10, 12, 15],
        "library": ["L1", "L2", "L3"],
        "acc": ["A1", "A2", "A3"],
    })
    fig = draw_subject_figure(df, "S3")
    # assert every axis title text is bold
    for ax in fig.axes:
        weight = ax.title.get_fontweight()
        assert _is_bold_fontweight(weight), f"Axis title not bold: {ax.get_title()} (weight={weight})"

    # ensure suptitle uses the subject-only text and is bold
    supt = fig._suptitle
    assert supt.get_text() == "S3"
    assert _is_bold_fontweight(supt.get_fontweight())
