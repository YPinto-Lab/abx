import tempfile
import os

import matplotlib
matplotlib.use("Agg")

import pandas as pd
from ciprofloxacin_study.plotting import generate_pdf


def test_generate_pdf_creates_outlines():
    merged = pd.DataFrame({
        "subject": ["TS1", "TS1", "TS1"],
        "bucket": ["pre-9w", "day0", "day1"],
        "pct_vir": [1.0, 2.0, 3.0],
        "pct_cel": [99.0, 98.0, 97.0],
        "num_virus_species": [5.0, 6.0, 7.0],
        "library": ["libA", "libB", "libC"],
        "acc": ["SRR000010", "SRR000011", "SRR000012"],
    })

    # summary/relative summary minimal frames
    buckets = ["pre-9w", "day0", "day1"]
    summary = pd.DataFrame({
        "bucket": buckets,
        "mean_vir": [1.0, 2.0, 3.0],
        "se_vir": [0.1, 0.1, 0.1],
        "mean_cel": [99.0, 98.0, 97.0],
        "se_cel": [0.1, 0.1, 0.1],
        "n_subjects": [1, 1, 1],
    })

    # construct a proper relative summary with expected column names
    summary_rel = pd.DataFrame({
        "bucket": buckets,
        "mean_vir_rel": [1.0, 1.5, 2.0],
        "se_vir_rel": [0.01, 0.02, 0.02],
        "mean_cel_rel": [1.0, 0.99, 0.98],
        "se_cel_rel": [0.01, 0.01, 0.01],
        "n_subjects": [1, 1, 1],
    })

    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        generate_pdf(merged, summary, summary_rel, pdf_path=path)

        # read outlines and assert entries exist
        from pypdf import PdfReader

        reader = PdfReader(path)
        outline = reader.outline
        # convert outline tree to list of titles
        def gather_titles(nodes):
            out = []
            for n in nodes:
                if isinstance(n, list):
                    out.extend(gather_titles(n))
                else:
                    title = getattr(n, 'title', None) or getattr(n, 'label', None)
                    if title:
                        out.append(title)
                    # if item has children, they may be accessible via 'children'
                    if hasattr(n, 'children') and n.children:
                        children = n.children() if callable(n.children) else n.children
                        if children:
                            out.extend(gather_titles(children))
            return out

        titles = gather_titles(outline)
        # basic expectations
        assert "Cover" in titles
        assert "Summary — absolute" in titles
        assert "Summary — relative" in titles
        assert "Per-subject pages" in titles
        assert "TS1" in titles

        # also confirm explanation text for baseline is present on the relative-summary page
        page2_text = reader.pages[2].extract_text()
        assert page2_text is not None
        assert "Baseline for fold-change" in page2_text
        # ensure the collapsed 'baseline' bucket label appears on the relative page
        assert "baseline" in page2_text.lower()
    finally:
        try:
            os.remove(path)
        except Exception:
            pass
