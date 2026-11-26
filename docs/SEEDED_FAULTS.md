# Seeded Faults

## Exercise 1: Failing feature test

```text
============================= test session starts ==============================
platform darwin -- Python 3.14.6, pytest-9.1.1, pluggy-1.7.0 -- /Users/audrey/Downloads/bikeshare-open/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/audrey/Downloads/bikeshare-open
plugins: anyio-4.16.0
collecting ... collected 1 item

tests/test_leakage.py::test_cnt_std_7_value_is_correct FAILED            [100%]

=================================== FAILURES ===================================
_______________________ test_cnt_std_7_value_is_correct ________________________

feats =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857
713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571

[714 rows x 28 columns]

    def test_cnt_std_7_value_is_correct(feats):
        """Hand-compute the std of the previous seven calendar days and compare."""
        raw = pd.read_csv("data/raw/bike_daily.csv", parse_dates=["dteday"])
        target_date = pd.Timestamp("2011-08-01")
        # Get the previous seven calendar days
        window = [target_date - pd.Timedelta(days=k) for k in range(1, 8)]
    
        # Assert all seven dates exist in raw data
        missing = [d for d in window if d not in raw["dteday"].values]
        assert not missing, f"Missing dates: {missing}"
    
        # Get cnt values for those dates
        expected_std = np.std(raw.loc[raw.dteday.isin(window), TARGET], ddof=1)
    
>       actual_std = feats.set_index("dteday").cnt_std_7[target_date]
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_leakage.py:75: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self =             instant  season      yr  ... cnt_lag_1 cnt_lag_7   cnt_roll_7
dteday                               ...    ... 1787.0  1530.142857
2012-12-31    731.0  WINTER  2012.0  ...    1796.0     920.0  1531.428571

[714 rows x 27 columns]
name = 'cnt_std_7'

    @final
    def __getattr__(self, name: str):
        """
        After regular attribute access, try looking up the name
        This allows simpler access to columns for interactive use.
        """
        # Note: obj.x will always call obj.__getattribute__('x') prior to
        # calling obj.__getattr__('x').
        if (
            name not in self._internal_names_set
            and name not in self._metadata
            and name not in self._accessors
            and self._info_axis._can_hold_identifiers_and_holds_name(name)
        ):
            return self[name]
>       return object.__getattribute__(self, name)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'DataFrame' object has no attribute 'cnt_std_7'. Did you mean: 'cnt_lag_7'?

.venv/lib/python3.14/site-packages/pandas/core/generic.py:6194: AttributeError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_cnt_std_7_value_is_correct - AttributeErro...
============================== 1 failed in 0.30s ===============================

```
