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

## Exercise 2: Fault 1 - Forbidden column

**Date:** 2026-11-25  
**Command:** `/seed-fault Temporarily modify feature_columns in src/features.py to include casual, a forbidden target-leakage column. Capture the real hook stderr and failing pytest output before repairing the fault. Restore the original implementation and confirm all 16 tests pass. Document the results in docs/SEEDED_FAULTS.md. Do not commit.`

---

## Fault Introduced

**File:** `src/features.py:82-85`  
**Change:** Modified `feature_columns()` to explicitly include `"casual"` despite it being in `FORBIDDEN`:

```python
def feature_columns(df: pd.DataFrame) -> list[str]:
    """Numeric columns that are safe to feed the model."""
    numeric = df.select_dtypes(include="number").columns
    return [c for c in numeric if c not in FORBIDDEN] + ["casual"]  # FAULT ADDED
```

---

## Hook Detection

**Hook:** `check_leakage.sh` (PostToolUse hook)  
**Result:** ✅ **FAULT DETECTED** - The PostToolUse hook caught the fault before it could be committed.

### Hook stderr:
```
[.../.claude/hooks/check_leakage.sh]: Leakage tests failed after editing /Users/audrey/Downloads/bikeshare-open/src/features.py:
feats =         dteday  instant  season      yr  ... cnt_lag_1 cnt_lag_7   cnt_roll_7    cnt_std_7
0   2011-01-10     10.0  WI...316
713 2012-12-31    731.0  WINTER  2012.0  ...    1796.0     920.0  1531.428571   887.135250

[714 rows x 29 columns]

def test_no_forbidden_features(feats):
    """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
    construction, so this cannot discover a *new* leaky column. What it
    catches is someone editing feature_columns() or FORBIDDEN -- which is
    exactly the fault the Step 7 hook demonstrates."""
    cols = set(feature_columns(feats))
>   assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E   AssertionError: forbidden columns in feature set: {'casual'}
E   assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_7', 'cnt_std_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:32: AssertionError
```

---

## Test Analysis

**Test that detected the fault:** `test_no_forbidden_features` (Line 26-32 in tests/test_leakage.py)

**Why it detected it:** This test computes the intersection of feature columns with FORBIDDEN and asserts it's empty. Since `"casual"` is both:
1. A numeric column (passes `select_dtypes(include="number")`)
2. In the FORBIDDEN set (`{"casual", "registered", "cnt", ...}`)

The test correctly identified the violation.

**Why this matters:** As documented in `src/config.py`:
> casual + registered == cnt exactly, on every row. A model handed these scores R^2 ~ 1.0 and has learned addition. At prediction time you would not know either input: they are components of the thing being predicted.

---

## Repair Applied

**File:** `src/features.py:85`  
**Change:** Reverted to original implementation (removed `+ ["casual"]`):

```python
def feature_columns(df: pd.DataFrame) -> list[str]:
    """Numeric columns that are safe to feed the model."""
    numeric = df.select_dtypes(include="number").columns
    return [c for c in numeric if c not in FORBIDDEN]  # REPAIRED
```

---

## Verification After Repair

**Command:** `make test`  
**Result:** ✅ **All 16 tests passed**

```
python -m pytest tests/ -q
................                                                         [100%]
16 passed in 1.60s
```

---

## Conclusion

The `check_leakage.sh` PostToolUse hook successfully demonstrated its value as a defensive layer: it detected target leakage after the edit was applied and returned the test failure to the agent. The test suite (`test_no_forbidden_features`) caught the exact violation pattern when executed.

**Status:** Fault detected → Hook reported failure → Repair applied → All tests pass
**Repair:** One corrective Edit tool call. The fault was repaired within the same agent task without an additional user repair prompt.


## Exercise 2: Fault 2 - Rolling mean leakage

Removed shift(1) from cnt_roll_7, allowing current-day demand into the rolling mean.

Claude introduced and repaired the fault using Edit in one task, with one corrective Edit call.

The following output was captured by reproducing the same fault and invoking the hook directly after the original agent run.

Hook exit code: 2

### Hook stderr

```text
Leakage tests failed after editing /Users/audrey/Downloads/bikeshare-open/src/features.py:
[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:58: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 7 passed in 0.59s

```

### Failing tests

```text
....F...                                                                 [100%]
=================================== FAILURES ===================================
_______________________ test_rolling_mean_excludes_today _______________________

feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7    cnt_std_7
0   2011-01-10     10.0  WINTER  ...     134....428571   886.694316
713 2012-12-31    731.0  WINTER  ...      920.0  1789.857143   887.135250

[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:58: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 7 passed in 0.28s

```

### Verification after restoration

```text
python -m pytest tests/ -q
................                                                         [100%]
16 passed in 1.35s

```

## Exercise 2: Fault 3 - Weather encoder

Removed the if unknown: raise ValueError block from encode_weather.

Initially, all 16 tests passed despite the fault.
Added test_unknown_weather_label_raises to address this
missing verification coverage.

After adding the test, the hook returned exit code 2.
Claude restored the original guard using one corrective
Edit call after one additional user repair prompt.


### Failing test output

```text
........F                                                                [100%]
=================================== FAILURES ===================================
______________________ test_unknown_weather_label_raises _______________________

    def test_unknown_weather_label_raises():
        """Unexpected weather labels must raise rather than silently become NaN."""
        from src.features import encode_weather
    
        weather = pd.Series(["GOOD", "UNKNOWN", "BAD"])
    
>       with pytest.raises(ValueError, match="unmapped weather labels"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:95: Failed
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_unknown_weather_label_raises - Failed: DID...
1 failed, 8 passed in 0.26s

```

### Hook stderr (direct invocation)

```text
Leakage tests failed after editing src/features.py:
........F                                                                [100%]
=================================== FAILURES ===================================
______________________ test_unknown_weather_label_raises _______________________

    def test_unknown_weather_label_raises():
        """Unexpected weather labels must raise rather than silently become NaN."""
        from src.features import encode_weather
    
        weather = pd.Series(["GOOD", "UNKNOWN", "BAD"])
    
>       with pytest.raises(ValueError, match="unmapped weather labels"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:95: Failed
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_unknown_weather_label_raises - Failed: DID...
1 failed, 8 passed in 0.25s

```

### Verification after repair

```text
python -m pytest tests/ -q
.................                                                        [100%]
17 passed in 1.47s

```

## Exercise 2: Fault 4 - Bash file operations

Claude Code initially denied the attempted Bash write
into data/raw/. Therefore, the agent's attempted write
did not succeed.

A separate researcher-controlled terminal experiment
demonstrated that a normal shell cp operation can write
into data/raw/ without invoking the PostToolUse hook.

The hook matches Edit and Write tools, not Bash commands
or external terminal operations.

Filesystem write protection would prevent unauthorized
changes to raw data. A SHA-256 integrity check in make
data would detect modifications to the original CSV.
A PreToolUse hook for Bash could provide additional
protection against agent-initiated writes.

The demonstration file was removed, and the original
dataset was not modified.

### Terminal experiment output

```text
Dataset hash before demonstration:
a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc  data/raw/bike_daily.csv
Copied demonstration file:
-rw-r--r--  1 audrey  staff  28 Nov 25 18:12 data/raw/fault4_demo.txt
Harmless demonstration file
Dataset hash after demonstration:
a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc  data/raw/bike_daily.csv

```
