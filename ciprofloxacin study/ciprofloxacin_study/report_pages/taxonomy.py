"""Taxonomy distribution pages."""

import matplotlib.pyplot as plt
import seaborn as sns

from .style import A4_SIZE


def add_taxa_distribution_page(pdf, taxa_df):
    if taxa_df is None or len(taxa_df) == 0:
        return False

    fig_taxa = plt.figure(figsize=A4_SIZE)
    fig_taxa.text(0.5, 0.95, "Virus Taxonomy Tree Structure", ha="center", fontsize=14, weight="bold")

    explanation = (
        "This chart shows the breadth of viral diversity detected across all subjects. "
        "Each bar represents the number of unique taxa (distinct viruses) identified at that taxonomic rank. "
        "For example, 120,825 unique viral species were detected, nested within 3,094 genera, "
        "which belong to 4,015 orders, and so on. This reflects the hierarchical nature of viral taxonomy."
    )
    fig_taxa.text(0.1, 0.90, explanation, ha="left", va="top", fontsize=9, wrap=True)

    ax_taxa = fig_taxa.add_axes([0.15, 0.25, 0.75, 0.60])
    colors = sns.color_palette("husl", len(taxa_df))
    ax_taxa.barh(taxa_df["rank"], taxa_df["num_taxa"], color=colors)

    for i, (idx, row) in enumerate(taxa_df.iterrows()):
        ax_taxa.text(
            row["num_taxa"] + max(taxa_df["num_taxa"]) * 0.02,
            i,
            f"{int(row['num_taxa']):,}",
            va="center",
            fontsize=8,
        )

    ax_taxa.set_xlabel("Number of Unique Taxa", fontsize=10, weight="bold")
    ax_taxa.set_title("")
    ax_taxa.grid(axis="x", alpha=0.2)
    ax_taxa.invert_yaxis()

    note = "Note: Taxonomic ranks are hierarchical. Species are the most granular level; phylum/kingdom represent broader categories."
    fig_taxa.text(0.1, 0.08, note, ha="left", va="top", fontsize=8, style="italic", color="gray")

    pdf.savefig(fig_taxa)
    plt.close(fig_taxa)
    return True


def add_reads_distribution_page(pdf, taxa_reads_df):
    if taxa_reads_df is None or len(taxa_reads_df) == 0:
        return False

    fig_reads = plt.figure(figsize=A4_SIZE)
    fig_reads.text(0.5, 0.95, "Read Distribution by Taxonomic Rank", ha="center", fontsize=14, weight="bold")

    explanation = (
        "This chart shows where the actual sequence data (reads) is distributed across taxonomic ranks. "
        "Each bar represents the number of reads DIRECTLY assigned to that rank (self_count). "
        "This is distinct from total_count, which includes reads assigned to the rank AND all its descendants. "
        "Using self_count reveals the true abundance at each level and avoids double-counting. "
        "Notice: many taxa exist at the species level (left chart), but few reads actually classify to species (this chart). "
        "Most reads concentrate in higher ranks (order, class), indicating classification uncertainty at fine resolution."
    )
    fig_reads.text(0.1, 0.90, explanation, ha="left", va="top", fontsize=8.5, wrap=True)

    ax_reads = fig_reads.add_axes([0.15, 0.25, 0.75, 0.60])
    colors = sns.color_palette("viridis", len(taxa_reads_df))
    ax_reads.barh(taxa_reads_df["rank"], taxa_reads_df["reads_at_rank"], color=colors)

    for i, (idx, row) in enumerate(taxa_reads_df.iterrows()):
        reads_val = row["reads_at_rank"]
        if reads_val and reads_val > 0:
            ax_reads.text(
                reads_val + max(taxa_reads_df["reads_at_rank"].fillna(0)) * 0.02,
                i,
                f"{int(reads_val):,}",
                va="center",
                fontsize=8,
            )

    ax_reads.set_xlabel("Number of Reads (self_count)", fontsize=10, weight="bold")
    ax_reads.set_title("")
    ax_reads.grid(axis="x", alpha=0.2)
    ax_reads.invert_yaxis()

    note = "Note: self_count = reads directly assigned to this exact taxon only (not including descendants). This reveals the true abundance at each classification level."
    fig_reads.text(0.1, 0.08, note, ha="left", va="top", fontsize=8, style="italic", color="gray")

    pdf.savefig(fig_reads)
    plt.close(fig_reads)
    return True
