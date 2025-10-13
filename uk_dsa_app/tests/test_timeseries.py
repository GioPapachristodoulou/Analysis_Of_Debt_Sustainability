import pandas as pd
from dsa.timeseries import SeriesContainer

def test_add_and_resample_yearly_to_quarterly():
    sc = SeriesContainer()
    s = pd.Series([100, 105, 110], index=[2019, 2020, 2021], dtype=float)
    sc.add("gdp", s, "bn_gbp", "yearly")
    q = sc.resample("gdp", "quarterly")
    assert len(q) >= 12