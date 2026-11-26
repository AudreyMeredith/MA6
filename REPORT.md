# Report: daily bikeshare demand

## Results

_To fill in: table of validation and test R^2 and MAE for baseline_mean, baseline_persistence, ridge and hgb, before and after the new feature (`cnt_std_7`), matching `reports/metrics.json` exactly._

## Headline finding

_To fill in._

## Exercise 4: target transformation

Gradient boosting scores below the mean baseline on the H2 2012 test set (R^2 -0.696) because a tree cannot predict outside the range of targets it saw in training, and 2012 demand grew past the 2011 maximum. To let it compete, `TARGET_TRANSFORM=ratio` (in `src/train.py`, off by default) fits ridge and hgb on **cnt / cnt_roll_7**, today's demand relative to the trailing week, and multiplies predictions back by `cnt_roll_7` before scoring against `cnt`. Run it with `TARGET_TRANSFORM=ratio python -m src.train`; results go to `reports/metrics_ex4.json`. The committed `reports/metrics.json` is the untransformed pipeline.

The decision was made on validation (H1 2012) only:

| Model | Valid R^2, raw target | Valid R^2, ratio target | Valid MAE, raw | Valid MAE, ratio |
|---|---|---|---|---|
| baseline_mean | -0.932 | -0.932 | 2002.2 | 2002.2 |
| baseline_persistence | 0.451 | 0.451 | 900.6 | 900.6 |
| ridge | **0.722** | 0.613 | **700.4** | 857.3 |
| hgb | 0.098 | **0.748** | 1381.6 | **685.5** |

**Verdict: defensible, with limits.** In favour: `cnt_roll_7` uses only days d-1..d-7, so the transform is known at prediction time and adds no leakage; and a ratio matches how the data changed, since 2012 demand grew by a multiplier and the ratio removes that level while keeping the day-to-day pattern. Against: we chose it after seeing hgb fail, tried only one transform, and it makes ridge worse. Picking a target per model is an extra degree of freedom. So the fair comparison is each model's best validated version (ridge raw vs hgb ratio), not "hgb wins", and the transform does not replace the headline pipeline.

**Test set, opened once after the verdict above:** hgb with the ratio target scores R^2 0.628 (MAE 832.8) against ridge on the raw target at 0.636 (MAE 840.3), and persistence at 0.510 (MAE 840.1). Once the growth trend is divided out, the tree reaches parity with ridge, rather than failing below the mean baseline. Neither model clearly beats the other, and both are close to "yesterday again" on MAE. Ridge on the ratio target falls to 0.198 on test, which supports not applying the transform across the board.

## Exercise 5: ridge vs persistence

_To fill in._

## Attribution

_To fill in: model and size used by each teammate (Audrey: local model; Antony: Claude Opus 5.5 in chat for Exercise 4, because the hosted fallback qwen3.5:27b-cloud was retired and the replacement required payment, and his laptop has 8 GB RAM). Then two lists: what the agent generated, and the decisions that were ours._
