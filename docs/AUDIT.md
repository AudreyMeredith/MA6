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

**Auditor results (Claude Code summary of the
completed subagent audit):**

```
Audit Results

Commit 16ad390 - "Exercise 4: TARGET_TRANSFORM=ratio option in train.py"

Verdict: CLEAN — All five checks passed.

- Check 1 (Target leakage): PASS — cnt / cnt_roll_7 uses
  only days d-1..d-7, which are known at prediction time
- Check 2 (Temporal ordering): PASS — .shift(1) before
  aggregation; temporal split by date; StandardScaler
  fits only on train
- Check 3 (Calendar gaps): PASS — inherits
  reindex_to_calendar() from features.py
- Check 4 (Silent row loss): PASS — ratio transform is
  pure arithmetic, no dropna/merge/map
- Check 5 (Unreported baseline): PASS — all models report
  both valid and test metrics; mean and persistence
  baselines included

Commit 5b84a68 - "Exercise 4: ratio-target decision on validation..."

Verdict: CLEAN — Documentation-only commit with no code changes.

- Check 5 (Unreported baseline): PASS — explicitly reports
  both baselines alongside all model scores in the
  decision table

Key Evidence

From src/train.py line 76:

out["cnt_roll_7"] = out[TARGET].shift(1).rolling(LAG_WARMUP).mean()

The rolling mean is built on shifted target values,
ensuring the denominator never includes time t's count.
This is a valid known-at-prediction-time transform.

Conclusion

No findings that change numbers or invalidate conclusions.
Both commits are methodologically sound per the five
checks defined in leakage-auditor.md.
```

**My verdict (Audrey):** I agree with the auditor that
the ratio transformation does not introduce target
leakage because its denominator uses only demand from
previous days. The current day's count is used as the
training target, not as a prediction-time input.
Temporal ordering and both baselines are preserved.
The auditor incorrectly references `src/train.py` for
the rolling mean calculation, which is actually in
`src/features.py`. Additionally, the transformation
code computes and saves test metrics during the
validation experiment, even though it prints only
validation results. This does not demonstrate test-set
tuning, but stricter separation would improve the
experimental design. I found no evidence that the
reported numerical results need to change.