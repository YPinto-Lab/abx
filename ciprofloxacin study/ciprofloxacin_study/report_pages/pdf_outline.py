"""PDF outline/bookmark helpers."""

from typing import List


def add_pdf_outlines(pdf_path: str, subjects: List[str], has_species_page: bool, has_taxa_page: bool = False, has_reads_page: bool = False, has_sk_page: bool = False):
    """Add PDF outline entries for the generated report using pypdf."""
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for p in reader.pages:
        writer.add_page(p)

    page_idx = 0
    writer.add_outline_item("Cover", page_idx)
    page_idx += 1

    writer.add_outline_item("Methodology", page_idx)
    page_idx += 1

    writer.add_outline_item("Taxonomy Normalization", page_idx)
    page_idx += 1

    if has_taxa_page:
        writer.add_outline_item("Taxonomy Distribution", page_idx)
        page_idx += 1

    if has_reads_page:
        writer.add_outline_item("Read Distribution by Rank", page_idx)
        page_idx += 1

    if has_sk_page:
        writer.add_outline_item("Superkingdom Read Abundance", page_idx)
        page_idx += 1
        writer.add_outline_item("Superkingdom Read Abundance (Fold-Change)", page_idx)
        page_idx += 1

    writer.add_outline_item("Summary — absolute", page_idx)
    page_idx += 1

    writer.add_outline_item("Summary — relative", page_idx)
    page_idx += 1

    if has_species_page:
        writer.add_outline_item("Summary — species", page_idx)
        page_idx += 1

    subj_start = page_idx
    if len(subjects) > 0:
        first_subj_page = subj_start if subj_start < len(reader.pages) else (len(reader.pages) - 1)
        parent = writer.add_outline_item("Per-subject pages", first_subj_page)
        pages_per_subject = 1 + (4 if has_sk_page else 0)
        for idx, subj in enumerate(subjects):
            page_index = subj_start + (idx * pages_per_subject)
            if page_index >= len(reader.pages):
                break
            writer.add_outline_item(subj, page_index, parent=parent, color=(0, 0, 1), bold=True)

    with open(pdf_path, "wb") as f:
        writer.write(f)
