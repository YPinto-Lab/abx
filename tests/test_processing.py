import pandas as pd

from ciprofloxacin_study.processing import assign_buckets, add_relative_to_baseline


def test_assign_buckets_simple():
    df = pd.DataFrame({
        "subject": ["S1", "S1", "S1", "S1"],
        "day": [-63, -2, -1, 0],
        "pct_vir": [1.0, 2.0, 3.0, 4.0],
        "pct_cel": [10.0, 20.0, 30.0, 40.0],
    })

    out = assign_buckets(df)
    assert out.loc[out['day'] == -63, 'bucket'].iloc[0] == 'pre-9w'
    assert out.loc[out['day'] == -2, 'bucket'].iloc[0] == 'pre-2d'
    assert out.loc[out['day'] == -1, 'bucket'].iloc[0] == 'pre-1d'
    assert out.loc[out['day'] == 0, 'bucket'].iloc[0] == 'day0'


def test_add_relative_to_baseline_uses_pre_samples_average():
    # when pre-2d, pre-1d and day0 exist, baseline should be the mean across them
    df = pd.DataFrame({
        "subject": ["S2", "S2", "S2", "S2"],
        "day": [-2, -1, 0, 1],
        "bucket": ['pre-2d', 'pre-1d', 'day0', 'day1'],
        "pct_vir": [3.0, 6.0, 9.0, 12.0],
        "pct_cel": [30.0, 60.0, 90.0, 120.0],
    })

    out = add_relative_to_baseline(df)
    # baseline mean for pct_vir = mean(3,6,9) = 6.0
    assert out.loc[out['day'] == -2, 'pct_vir_rel'].iloc[0] == 0.5
    assert out.loc[out['day'] == -1, 'pct_vir_rel'].iloc[0] == 1.0
    assert out.loc[out['day'] == 0, 'pct_vir_rel'].iloc[0] == 1.5
    assert out.loc[out['day'] == 1, 'pct_cel_rel'].iloc[0] == 120.0 / 60.0


def test_add_relative_to_baseline_fallback_to_pre9w_when_no_pre_samples():
    # when pre-2d/pre-1d/day0 are missing, fallback to pre-9w
    df = pd.DataFrame({
        "subject": ["S3", "S3"],
        "day": [-63, 1],
        "bucket": ['pre-9w', 'day1'],
        "pct_vir": [2.0, 6.0],
        "pct_cel": [10.0, 30.0],
    })

    out = add_relative_to_baseline(df)
    assert out.loc[out['day'] == -63, 'pct_vir_rel'].iloc[0] == 1.0
    assert out.loc[out['day'] == 1, 'pct_vir_rel'].iloc[0] == 3.0


def test_add_relative_to_baseline_with_species():
    df = pd.DataFrame({
        "subject": ["S3", "S3", "S3"],
        "day": [-63, 0, 1],
        "bucket": ['pre-9w', 'day0', 'day1'],
        "pct_vir": [2.0, 4.0, 6.0],
        "pct_cel": [10.0, 20.0, 30.0],
        "num_virus_species": [20, 40, 60],
    })

    out = add_relative_to_baseline(df)
    # baseline now uses any pre-samples (pre-2d/pre-1d/day0); here day0 is present
    # baseline num_virus_species = 40 -> pre-9w relative = 20/40=0.5
    assert out.loc[out['day'] == -63, 'num_virus_species_rel'].iloc[0] == 0.5
    assert out.loc[out['day'] == 0, 'num_virus_species_rel'].iloc[0] == 1.0
