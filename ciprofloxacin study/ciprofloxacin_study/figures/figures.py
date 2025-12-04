"""
Reusable plotting functions for ciprofloxacin study report figures.
"""
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def plot_superkingdom_abs(ax, summary_sk, kingdom, COLORS):
    mean_col = f'mean_{kingdom}'
    se_col = f'se_{kingdom}'
    if mean_col in summary_sk.columns:
        means = summary_sk[mean_col].astype(float)
        ses = summary_sk[se_col].astype(float) if se_col in summary_sk.columns else np.zeros(len(summary_sk))
        x_sk = range(len(summary_sk))
        ax.plot(x_sk, means, marker='o', color=COLORS['abs'], linewidth=2)
        lower = np.maximum(means - ses, 1.0)
        ax.fill_between(x_sk, lower, means + ses, alpha=0.2, color=COLORS['abs'])
        ax.set_yscale('log')
        ax.set_xticks(x_sk)
        ax.set_xticklabels(summary_sk['bucket'], rotation=45, ha='right')
    else:
        ax.text(0.5, 0.5, f'No absolute read summary for {kingdom}', ha='center', va='center')
    ax.set_ylabel('Total Reads (log scale)', fontsize=10, weight='bold')
    ax.set_xlabel('Time Bucket', fontsize=10, weight='bold')
    ax.grid(alpha=0.3)

def plot_superkingdom_frac(ax, summary_sk, kingdom, COLORS):
    mean_frac_col = f'mean_{kingdom}_frac'
    se_frac_col = f'se_{kingdom}_frac'
    if mean_frac_col in summary_sk.columns:
        means = summary_sk[mean_frac_col].astype(float)
        ses = summary_sk[se_frac_col].astype(float) if se_frac_col in summary_sk.columns else np.zeros(len(summary_sk))
        x_sk = range(len(summary_sk))
        ax.plot(x_sk, means, marker='o', color=COLORS['frac'], linewidth=2)
        lower = np.maximum(means - ses, 0.0)
        ax.fill_between(x_sk, lower, means + ses, alpha=0.2, color=COLORS['frac'])
        ax.set_xticks(x_sk)
        ax.set_xticklabels(summary_sk['bucket'], rotation=45, ha='right')
    else:
        ax.text(0.5, 0.5, f'No fraction summary for {kingdom}', ha='center', va='center')
    ax.set_ylabel('Fraction of Total Reads', fontsize=10, weight='bold')
    ax.set_xlabel('Time Bucket', fontsize=10, weight='bold')
    ax.grid(alpha=0.3)

def plot_superkingdom_frac_rel(ax, summary_sk_rel, kingdom, COLORS):
    mean_frac_rel_col = f'mean_{kingdom}_frac_rel'
    se_frac_rel_col = f'se_{kingdom}_frac_rel'
    if mean_frac_rel_col in summary_sk_rel.columns:
        means = summary_sk_rel[mean_frac_rel_col].astype(float)
        ses = summary_sk_rel[se_frac_rel_col].astype(float) if se_frac_rel_col in summary_sk_rel.columns else np.zeros(len(summary_sk_rel))
        x_sk_rel = range(len(summary_sk_rel))
        ax.plot(x_sk_rel, means, marker='o', color=COLORS['rel'], linewidth=2)
        lower = np.maximum(means - ses, 0.0)
        ax.fill_between(x_sk_rel, lower, means + ses, alpha=0.2, color=COLORS['rel'])
        ax.axhline(1.0, linestyle='--', color='gray', alpha=0.6)
        ax.set_xticks(x_sk_rel)
        ax.set_xticklabels(summary_sk_rel['bucket'], rotation=45, ha='right')
    else:
        ax.text(0.5, 0.5, f'No fraction relative summary for {kingdom}', ha='center', va='center')
    ax.set_ylabel('Fold Change (fraction)', fontsize=10, weight='bold')
    ax.set_xlabel('Time Bucket', fontsize=10, weight='bold')
    ax.grid(alpha=0.3)
