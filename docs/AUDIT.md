# Audit (Exercise 3)

We worked in one shared repository
(https://github.com/AudreyMeredith/MA6), so each of us
audited the other's commits instead of a separate repository.

## Antony audits Audrey's commits

**Scope:** Commits `cbada69` through `130e6f2` (the
`cnt_std_7` feature and its test, the raw-column
classification test, the unknown-weather-label test,
and the seeded-fault commits, whose net change to
`src/` is nil). Audrey's commits do not touch
`src/train.py`.

**Auditor:** The five checks in
`.claude/agents/leakage-auditor.md`, initially applied
by Claude Opus 5.5 in chat, which ran code on Antony's
clone. Antony's laptop has 8 GB RAM and cannot run
the course's local model. The audit was subsequently
repeated using the actual leakage-auditor agent on
Audrey's laptop.

**Initial auditor output (verbatim):**

```
Scope: git diff 59b88fb..130e6f2 -- src/ tests/ (Audrey's commits).

1. Target leakage — PASS. cnt_std_7 = cnt.shift(1).rolling(7).std(ddof=1).
   Verified on all 714 modelling rows: each value equals the sample std of
   cnt over the 7 calendar days before d (0 mismatches). Adding 5000 to cnt
   on one day leaves that day's cnt_std_7 unchanged, so same-day cnt does
   not enter. No feature other than the target is near-collinear with cnt.
2. Temporal ordering — PASS. Shift precedes rolling. Split is by date
   (temporal_split, unchanged). StandardScaler sits inside the ridge
   pipeline and is fit on train rows only.
3. Calendar gaps — PASS. Features are built after reindex_to_calendar; the
   only absent day is 2011-03-10, and no kept row has an incomplete 7-day
   window for cnt_std_7.
4. Silent row loss — PASS. 728 raw rows -> 714 modelling rows: 14 lost,
   exactly the bound in test_only_expected_rows_are_dropped (7 warm-up +
   7 after the one absent day). cnt_std_7 needs the same 7-day history as
   cnt_roll_7, so the bound and LAG_WARMUP are unchanged.
5. Unreported baseline — PASS. baseline_mean and baseline_persistence are
   reported next to ridge and hgb in reports/metrics.json.

All five checks pass; no finding changes a number or a conclusion.
```

**My verdict (Antony):** No finding changes a number, so
nothing in Audrey's commits needed fixing. The audit's
value is that it checked `cnt_std_7` on every row instead
of the single date (2011-08-01) that the committed test
hand-computes, and found no mismatch. The row-loss bound
held exactly at 14. I also agree with the auditor in not
counting the following as findings, because they change
no number: the single-date test, and its reliance on a
relative path to `data/raw/bike_daily.csv`, which would
only fail if pytest were run from outside the repo root.

### Additional verification using the course leakage auditor

The audit was repeated on Audrey's laptop using the
leakage-auditor agent directly through Claude Code,
with qwen3.5:9b via Ollama and a 64k context window.

Command used to launch the auditor:

```bash
claude --model bikeshare-coder --agent leakage-auditor --permission-mode default
```

Prompt:

```
Audit the diff 59b88fb..130e6f2 for src/ and tests/.
Run all five checks and report findings with evidence.
Do not modify any files.
```

**Auditor output (captured terminal output):**

```
Now let me systematically evaluate the five checks:

1. Target leakage:

- casual + registered == cnt is exactly as documented
  (line 30-31 in config.py)
- The diff adds no new features derived from target
- New feature cnt_std_7 uses .shift(1).rolling(LAG_WARMUP).std()
  - it's a standard deviation of lags, not target

Let me verify the arithmetic:

Bash(python -I "import pandas as pd; from src.ingest import load_raw; df = load_raw(); print('casual +
registered == cnt:', (df.casual + df.registered == df.cnt).all…)

Error: Exit code 2
python: can't open file "/Users/audrey/Downloads/bikeshare-open/import pandas as pd; from src.ingest
import load_raw; df = load_raw(); print('casual + registered == cnt:', (df.casual + df.registered ==
df.cnt).all())": [Errno 2] No such file or directory

Thought for 2s

Bash(python -c "import pandas as pd; from src.ingest import load_raw; df = load_raw(); print('casual +
registered == cnt:', (df.casual + df.registered == df.cnt).all…)

casual + registered == cnt: True

Thought for 1s

2. Temporal ordering:

- build_features uses .shift(1) and .shift(LAG_WARMUP)
  before aggregation on line 77
- temporal_split uses date-based split
  (TRAIN_END, VALID_END from config)
- Models fit only on train data, then predict on valid/test

3. Calendar gaps:

- reindex_to_calendar is called at line 54 to ensure
  full calendar before lags
- .shift(1) operates on reindexed data, not raw row positions
- Line 77: cnt_std_7 = out[TARGET].shift(1).rolling(LAG_WARMUP).std()
  - correctly shifts first

4. Silent row loss:

- .dropna() after lag features is explicitly bounded in
  test_contract.py::test_only_expected_rows_are_dropped
  (lines 56, allows LAG_WARMUP + missing_days *
  LAG_WARMUP rows lost)

5. Unreported baseline:

- baseline_mean using DummyRegressor(strategy="mean")
  - line 64
- baseline_persistence predicting yesterday - lines 48-61
- Both report for all splits (line 103-109)

All five checks pass with no findings. The diff correctly adds:

1. A new feature cnt_std_7 with proper temporal ordering
2. Tests for the new feature (test_cnt_std_7_value_is_correct)
3. Proper baseline reporting (already existed, still present)
4. Unclassified column check (test_no_unclassified_raw_columns)
```

**Verification outcome:** The course auditor reached the
same conclusion as the initial audit. Its first Python
command failed because of an incorrect command-line
argument, but it corrected the command and successfully
verified the target identity. No repository files needed
to be changed.

The statement that the new feature is not derived from
the target should be interpreted more precisely: it is
derived from historical target observations, but not
from the current or future target value. This is valid
for the daily forecasting task.

## Audrey audits Antony's commits

**Scope:** Commits `16ad390` and `5b84a68`, covering
the ratio target transformation in `src/train.py` and
its associated results and methodological decisions
in `REPORT.md` and `docs/DECISIONS.md`.

**Auditor:** The leakage-auditor subagent in
`.claude/agents/leakage-auditor.md`, invoked through
Claude Code using qwen3.5:9b via Ollama with a
64k context window.

Prompt:

```
Use the leakage-auditor subagent defined in
.claude/agents/leakage-auditor.md to audit commits
16ad390 and 5b84a68. Run the five checks and report
findings with evidence. Do not modify any files.
```

The subagent completed its audit in 35 minutes and
53 seconds.

**Auditor output (verbatim from the saved subagent transcript):**

````text
I have gathered all the necessary files to perform the audit. Let me now analyze both commits against the five checks defined in the leakage-auditor.md.

## Audit of Commit 16ad390 (Exercise 4: TARGET_TRANSFORM=ratio option)

This commit adds a `TARGET_TRANSFORM` feature to `src/train.py`. Here are my findings:

### Check 1: Target Leakage
**Verdict: PASS**

The transform computes `cnt / cnt_roll_7` where:
- `cnt_roll_7 = out[TARGET].shift(1).rolling(LAG_WARMUP).mean()` (line 76 in features.py)

Since `cnt_roll_7` is shifted by 1 and then rolled, it only contains counts from d-1 to d-7. The ratio uses past data exclusively—neither component is the target at time t. This is a **known-at-prediction-time transform**, not leakage.

### Check 2: Temporal Ordering
**Verdict: PASS**

```python
out["cnt_roll_7"] = out[TARGET].shift(1).rolling(LAG_WARMUP).mean()
```
The `.shift(1)` is applied before aggregation, as required. The temporal split in `fit_and_score()` uses `temporal_split(df)` which correctly splits by date (train=2011, valid=H1 2012, test=H2 2012). StandardScaler only fits on train rows (`model.fit(train[cols], y_fit)`), so validation/test are never seen during fitting.

### Check 3: Calendar Gaps
**Verdict: PASS (indirectly)**

This commit doesn't modify `src/features.py`, but it calls existing code that includes `reindex_to_calendar()` which fills missing calendar days. The lag features are built on the reindexed data with proper `.shift(1)` before aggregation, so no gap issues arise.

### Check 4: Silent Row Loss
**Verdict: PASS**

The commit adds only computation logic:
```python
y_fit = train[TARGET] / train[RATIO_SCALE] if ratio else train[TARGET]
```
No `.dropna()`, `.merge()`, or `.map()` that could silently drop rows. The ratio transform is a pure arithmetic operation with no NaN introduction (assuming cnt and cnt_roll_7 both exist).

### Check 5: Unreported Baseline
**Verdict: PASS**

All four models report BOTH validation AND test metrics:
```python
results[name] = {
    split: {"r2": ..., "mae": ...}
    for split, part in [("valid", valid), ("test", test)]
}
```
Both the mean baseline (`DummyRegressor`) and persistence baseline (`PersistenceBaseline("cnt_lag_1")`) are reported alongside ridge and hgb scores.

---

## Audit of Commit 5b84a68 (Exercise 4: ratio-target decision on validation, one test-set check, report section)

This commit only modifies documentation files:
- `REPORT.md` - adds Exercise 4/5 sections with metrics tables
- `docs/DECISIONS.md` - adds decision log entries

### Checks on Documentation Commits:

**Check 1-4:** N/A (no code changes introducing new features)

**Check 5: Unreported Baseline**
**Verdict: PASS**

The REPORT.md explicitly reports both baselines for all models:
```
| Model | Valid R^2, raw target | Valid R^2, ratio target | Valid MAE, raw | Valid MAE, ratio |
| baseline_mean | -0.932 | -0.932 | 2002.2 | 2002.2 |
| baseline_persistence | 0.451 | 0.451 | 900.6 | 900.6 |
```

The decision rationale acknowledges the trade-offs: "Picking a target per model is an extra degree of freedom." and "the committed pipeline stays untransformed."

---

## Final Verdicts

**Commit 16ad390:** All five checks pass. The `TARGET_TRANSFORM=ratio` feature correctly uses only past-available data (d-1 to d-7 for the rolling window), maintains temporal split integrity, handles calendar gaps via existing reindexing code, introduces no silent row loss, and reports all baselines alongside model scores.

**Commit 5b84a68:** All checks pass by inheritance—it documents the already-implemented solution without modifying any feature or training logic. The documentation accurately reflects what was committed to the codebase.

---
````

**My verdict (Audrey):** I agree with the auditor that the
ratio transformation does not introduce target leakage because
its denominator uses only demand from previous days. One
clarification is that the numerator is the current day's count,
but it is used as the training target rather than a prediction-time
input. Temporal ordering and both baselines are preserved.
Additionally, the transformation code computes and saves test
metrics during the validation experiment, even though it prints
only validation results. This does not demonstrate test-set
tuning, but stricter separation would improve the experimental
design. I found no evidence that the reported numerical results
need to change.
