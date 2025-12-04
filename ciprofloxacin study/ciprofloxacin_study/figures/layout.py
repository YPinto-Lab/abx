"""
Layout helpers for consistent figure/page arrangement in ciprofloxacin study reports.
"""
import matplotlib.pyplot as plt
from matplotlib import gridspec

def plot_graphs_on_page(pdf, graph_fns, titles=None, page_title=None):
    """
    Plot 1-3 graphs on a single A4 page, enforcing layout rules.
    graph_fns: list of functions that accept (ax) and plot on it.
    titles: list of subplot titles.
    page_title: optional page-level title.
    """
    n_graphs = len(graph_fns)
    fig = plt.figure(figsize=(8.27, 11.69))  # A4 in inches
    if n_graphs == 1:
        # Place the single plot in the upper half so the title and suptitle
        # sit above the plot and are not clipped. Leave the lower half as
        # whitespace so the plot height is limited to ~50% of the page.
        gs = gridspec.GridSpec(2, 1, height_ratios=[1, 1], figure=fig)
        ax = fig.add_subplot(gs[0])  # upper half
        # Leave extra top room for a page-level title and prevent clipping
        fig.subplots_adjust(top=0.90, bottom=0.05, left=0.10, right=0.95)
        graph_fns[0](ax)
        if titles:
            # place subplot title just above the axes area
            ax.set_title(titles[0], fontsize=16, pad=12)
        # lower half remains blank (used as breathing room / for future packing)
        ax_empty = fig.add_subplot(gs[1])
        ax_empty.axis('off')
    elif n_graphs in [2,3]:
        gs = gridspec.GridSpec(n_graphs, 1, figure=fig)
        axes = [fig.add_subplot(gs[i]) for i in range(n_graphs)]
        fig.subplots_adjust(top=0.95, bottom=0.08, left=0.12, right=0.95, hspace=0.35)
        for i, ax in enumerate(axes):
            graph_fns[i](ax)
            if titles and i < len(titles):
                ax.set_title(titles[i], fontsize=14, pad=12)
    else:
        raise ValueError("Only 1-3 graphs per page are supported by layout rule.")
    if page_title:
        fig.suptitle(page_title, fontsize=18, y=0.99)
    pdf.savefig(fig, dpi=150)
    plt.close(fig)
