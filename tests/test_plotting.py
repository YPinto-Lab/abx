import matplotlib
matplotlib.use("Agg")

import pandas as pd

from ciprofloxacin_study.plotting import draw_subject_figure


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
