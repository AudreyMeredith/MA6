# Audit (Exercise 3)

We worked in one shared repository (https://github.com/AudreyMeredith/MA6), so each of us audited the other's commits instead of a separate repository.

## Antony audits Audrey's commits

**Scope:** commits `cbada69` through `130e6f2` (the `cnt_std_7` feature and its test, the raw-column classification test, the unknown-weather-label test, and the seeded-fault commits, whose net change to `src/` is nil). Audrey's commits do not touch `src/train.py`.

**Auditor:** the five checks in `.claude/agents/leakage-auditor.md`, applied by Claude Opus 5.5 in chat, which ran code on Antony's clone. This is not the `/leakage-auditor` subagent: Antony's laptop (8 GB RAM) cannot run the course's local model. Using a different model from the one that wrote the code (qwen3.5:9b) is the point of an adversarial review, because it does not share the author's weights.

**Auditor output (verbatim):**

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

**My verdict:** No finding changes a number, so nothing in Audrey's commits needed fixing. The audit's value is that it checked `cnt_std_7` on every row instead of the single date (2011-08-01) that the committed test hand-computes, and found no mismatch. The row-loss bound held exactly at 14. I also agree with the auditor in not counting the following as findings, because they change no number: the single-date test, and its reliance on a relative path to `data/raw/bike_daily.csv`, which would only fail if pytest were run from outside the repo root.

## Audrey audits Antony's commits

_Audrey: scope `16ad390` (`TARGET_TRANSFORM` in `src/train.py`) and `5b84a68`. Paste the `/leakage-auditor` output verbatim, then your own one-paragraph verdict on which findings change a number._
