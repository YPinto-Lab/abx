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


def test_add_relative_to_baseline_prefers_pre9w():
    df = pd.DataFrame({
        "subject": ["S2", "S2", "S2"],
        "day": [-63, 0, 1],
        "bucket": ['pre-9w', 'day0', 'day1'],
        "pct_vir": [2.0, 4.0, 6.0],
        "pct_cel": [10.0, 20.0, 30.0],
    })

    out = add_relative_to_baseline(df)
    assert out.loc[out['day'] == -63, 'pct_vir_rel'].iloc[0] == 1.0
    assert out.loc[out['day'] == 0, 'pct_vir_rel'].iloc[0] == 2.0
    assert out.loc[out['day'] == 1, 'pct_cel_rel'].iloc[0] == 3.0


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
    assert out.loc[out['day'] == -63, 'num_virus_species_rel'].iloc[0] == 1.0
    assert out.loc[out['day'] == 0, 'num_virus_species_rel'].iloc[0] == 2.0
