"""Data loading utilities for the ciprofloxacin study package.

This module contains functions that read CSV/XLSX inputs and return cleaned
DataFrames suitable for downstream processing.
"""
from pathlib import Path
import os
import pandas as pd
from .logger import get_logger
from .config import CONTROL_SUBJECTS_TO_DELETE

logger = get_logger(__name__)


def _resolve_data_path(base_dir: str, filename: str, data_dirname: str = "data") -> Path:
    """Return a Path for filename preferring <base_dir>/data/<filename> when present."""
    base = Path(base_dir)
    data_path = base / data_dirname / filename
    if data_path.exists():
        return data_path
    return base / filename


def load_and_prepare_data(base_dir: str = None,
                          vir_cel_csv: str = "sample_to_virus_and_cellular_org_pct.csv",
                          mapfile: str = "Subject To Sample.xlsx",
                          sheet_name: str = "Supp. Table 1",
                          species_csv: str = "sample_to_num_of_virus_species.csv") -> pd.DataFrame:
    """Load CSV/Excel files, pivot to wide and merge as in original script.

    Returns the merged DataFrame (unsampled) after cleaning.
    """
    if base_dir is None:
        base_dir = os.getcwd()
    base_dir = str(Path(base_dir))

    logger.debug("Loading datasets...")

    vir_cel_path = _resolve_data_path(base_dir, vir_cel_csv)
    map_path = _resolve_data_path(base_dir, mapfile)

    vir_cel = pd.read_csv(vir_cel_path)
    mapdf = pd.read_excel(map_path, sheet_name=sheet_name)

    # pivot viruses / cellular organisms to wide format
    wide = (
        vir_cel
        .pivot_table(index=["acc", "sample_name"], columns="name", values="pct")
        .reset_index()
    )

    wide = wide.rename(columns={"Viruses": "pct_vir", "cellular organisms": "pct_cel"})

    merged = wide.merge(mapdf, left_on="sample_name", right_on="library", how="inner")

    # If a species-per-sample CSV is present, merge normalized class-level count into merged.
    species_path = _resolve_data_path(base_dir, species_csv)
    if species_path.exists():
        logger.debug(f"Loading species counts from {species_path}")
        species_df = pd.read_csv(species_path)
        species_col = None
        if "tax_id_normalized_to_class_level_count" in species_df.columns:
            species_col = "tax_id_normalized_to_class_level_count"
        elif "num_virus_species" in species_df.columns:
            species_col = "num_virus_species"

        if "sample_name" in species_df.columns and species_col:
            species_df = species_df.rename(columns={species_col: "num_virus_species"})
            merged = merged.merge(species_df[["sample_name", "num_virus_species"]], on="sample_name", how="left")
            logger.debug(f"Merged species data using column: {species_col}")
        else:
            logger.debug("species CSV missing expected columns; skipping")
    else:
        logger.debug("no species CSV found; proceeding without num_virus_species")

    merged["day"] = pd.to_numeric(merged["day"], errors="coerce")
    merged = merged.sort_values(["subject", "day"])  # stable ordering

    logger.debug(f"merged shape: {merged.shape}")
    logger.debug(merged.head())

    return merged


def load_virus_taxa_ranks(base_dir: str = None, taxa_csv: str = "virus_taxa_count_by_rank.csv") -> pd.DataFrame:
    """Load and process virus taxonomic rank distribution (count of distinct taxa per rank)."""
    if base_dir is None:
        base_dir = os.getcwd()
    base_dir = str(Path(base_dir))

    taxa_path = _resolve_data_path(base_dir, taxa_csv)
    if not taxa_path.exists():
        logger.debug(f"Virus taxa CSV not found at {taxa_path}")
        return None

    logger.debug(f"Loading virus taxa ranks from {taxa_path}")
    taxa_df = pd.read_csv(taxa_path)
    taxa_df = taxa_df[taxa_df['rank'].notna() & (taxa_df['rank'] != '')]
    taxa_df = taxa_df.sort_values('num_taxa', ascending=False).reset_index(drop=True)
    logger.debug(f"Loaded {len(taxa_df)} taxonomic ranks")
    logger.debug(taxa_df.head(10))
    return taxa_df


def load_virus_taxa_reads(base_dir: str = None, reads_csv: str = "self_count_per_taxa_rank.csv") -> pd.DataFrame:
    """Load and process read distribution per taxonomic rank (self_count)."""
    if base_dir is None:
        base_dir = os.getcwd()
    base_dir = str(Path(base_dir))

    reads_path = _resolve_data_path(base_dir, reads_csv)
    if not reads_path.exists():
        logger.debug(f"Virus taxa reads CSV not found at {reads_path}")
        return None

    logger.debug(f"Loading virus taxa read distribution from {reads_path}")
    reads_df = pd.read_csv(reads_path)
    if 'reads_at_rank' in reads_df.columns:
        reads_df['reads_at_rank'] = pd.to_numeric(reads_df['reads_at_rank'], errors='coerce')
    reads_df = reads_df.sort_values('reads_at_rank', ascending=False).reset_index(drop=True)
    logger.debug(f"Loaded {len(reads_df)} taxonomic ranks with read counts")
    logger.debug(reads_df.head(10))
    return reads_df


def load_superkingdom_reads(base_dir: str = None, sk_csv: str = "reads_total_count_per_superkingdom.csv") -> pd.DataFrame:
    """Load superkingdom read distribution per sample."""
    if base_dir is None:
        base_dir = os.getcwd()
    base_dir = str(Path(base_dir))

    sk_path = _resolve_data_path(base_dir, sk_csv)
    if not sk_path.exists():
        logger.debug(f"Superkingdom reads CSV not found at {sk_path}")
        return None

    logger.debug(f"Loading superkingdom read distribution from {sk_path}")
    sk_df = pd.read_csv(sk_path)
    sk_df['total_count'] = pd.to_numeric(sk_df['total_count'], errors='coerce')
    logger.debug(f"Loaded superkingdom data for {len(sk_df)} records")
    logger.debug(sk_df.head(10))
    return sk_df


def filter_controls(merged, controls=CONTROL_SUBJECTS_TO_DELETE):
    """Remove control subjects from the merged DataFrame.

    Defaults to `CONTROL_SUBJECTS_TO_DELETE` from config to preserve
    original behavior.
    """
    logger.debug(f"Filtering {controls}")
    out = merged[~merged["subject"].isin(controls)].copy()
    logger.debug(f"After removing controls {controls}, shape: {out.shape}")
    logger.debug(f"Remaining subjects: {sorted(out['subject'].unique())}")
    return out
