# Report: daily bikeshare demand

## Results

The original pipeline used 14 features. After adding
cnt_std_7, the pipeline uses 15 features and retains
714 observations: 348 training, 182 validation, and
184 test observations.

| Feature set | Model | Valid R² | Valid MAE | Test R² | Test MAE |
|---|---|---:|---:|---:|---:|
| Before | baseline_mean | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| Before | baseline_persistence | 0.4507 | 900.6 | 0.5099 | 840.1 |
| Before | ridge | 0.6475 | 832.9 | 0.5833 | 947.1 |
| Before | hgb | 0.2185 | 1296.6 | -0.4975 | 1972.6 |
| After | baseline_mean | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| After | baseline_persistence | 0.4507 | 900.6 | 0.5099 | 840.1 |
| After | ridge | 0.7224 | 700.4 | 0.6356 | 840.3 |
| After | hgb | 0.0977 | 1381.6 | -0.6959 | 2108.4 |

The before results were recorded from the unmodified starter.
The after results match reports/metrics.json and are
reproducible using make all.

## Headline finding

The original leaky evaluation achieves an R² of 1.000
because casual and registered sum exactly to total demand.
Under a valid temporal split, the mean baseline performs
poorly on test data (R² = -2.1441), reflecting the increase
in ridership between 2011 and 2012. With the new feature,
ridge achieves a test R² of 0.6356 compared with 0.5099 for
persistence, although their MAEs are nearly identical
(840.3 versus 840.1 rides). Gradient boosting achieves
a negative test R² of -0.6959 but still outperforms the
mean baseline.

We retained cnt_std_7 because it improved ridge validation
R² by 0.0749 and reduced validation MAE from 832.9 to 700.4,
despite decreasing gradient boosting validation R² by
0.1208. The feature decision was based on validation results.

## Exercise 4: target transformation

Gradient boosting has a negative R² on the H2 2012 test set (R^2 -0.696) because a tree cannot predict outside the range of targets it saw in training, and 2012 demand grew past the 2011 maximum. To let it compete, `TARGET_TRANSFORM=ratio` (in `src/train.py`, off by default) fits ridge and hgb on **cnt / cnt_roll_7**, today's demand relative to the trailing week, and multiplies predictions back by `cnt_roll_7` before scoring against `cnt`. Run it with `TARGET_TRANSFORM=ratio python -m src.train`; results go to `reports/metrics_ex4.json`. The committed `reports/metrics.json` is the untransformed pipeline.

The decision was made on validation (H1 2012) only:

| Model | Valid R^2, raw target | Valid R^2, ratio target | Valid MAE, raw | Valid MAE, ratio |
|---|---|---|---|---|
| baseline_mean | -0.932 | -0.932 | 2002.2 | 2002.2 |
| baseline_persistence | 0.451 | 0.451 | 900.6 | 900.6 |
| ridge | **0.722** | 0.613 | **700.4** | 857.3 |
| hgb | 0.098 | **0.748** | 1381.6 | **685.5** |

**Verdict: defensible, with limits.** In favour: `cnt_roll_7` uses only days d-1..d-7, so the transform is known at prediction time and adds no leakage; and a ratio matches how the data changed, since 2012 demand grew by a multiplier and the ratio removes that level while keeping the day-to-day pattern. Against: we chose it after seeing hgb fail, tried only one transform, and it makes ridge worse. Picking a target per model is an extra degree of freedom. So the fair comparison is each model's best validated version (ridge raw vs hgb ratio), not "hgb wins", and the transform does not replace the headline pipeline.

**Test set, opened once after the verdict above:** hgb with the ratio target scores R^2 0.628 (MAE 832.8) against ridge on the raw target at 0.636 (MAE 840.3), and persistence at 0.510 (MAE 840.1). Once the growth trend is divided out, the tree reaches parity with ridge, rather than producing a negative R². Neither model clearly beats the other, and both are close to "yesterday again" on MAE. Ridge on the ratio target falls to 0.198 on test, which supports not applying the transform across the board.

## Exercise 5: ridge vs persistence

**Ridge is not worth deploying over "yesterday again."** On the held-out H2 2012 test set, ridge's mean absolute error is 840.3 rides a day and persistence's is 840.1: a forecaster using either one is off by the same amount on a typical day, and persistence gets there with no parameters, no training and nothing to retrain. Ridge does score higher on R^2 (0.636 vs 0.510), but R^2 squares the errors, so the gap indicates lower squared prediction error despite nearly identical absolute error. This is consistent with fewer or smaller large misses, although we did not separately verify their causes. Its advantage also shrank between validation and test: on H1 2012 ridge led by 0.27 R^2 and 200 rides of MAE, and six months later the MAE lead was gone. That is the pattern you would expect from a model whose lagged-demand coefficients were fit on 2011 levels and are drifting as demand grows. The case for ridge is that big misses can be the expensive ones (empty or overflowing docks), and if an operator could show that, the R^2 gap would matter. Without that evidence, a model that only matches a zero-parameter rule on the metric that measures everyday error has not earned its complexity, so we would deploy persistence as the default and keep ridge as a candidate to re-test as more 2012 data arrives.

## Attribution

**Models used:** Audrey used **`qwen3.5:9b` via Ollama with a 64k context window**, running locally through Claude Code under the custom model name `bikeshare-coder`; she did not switch models. Antony used **Claude Opus 5.5** (Anthropic, in the claude.ai chat, with access to his copy of the repo), not the course's local agent. His laptop has 8 GB of RAM, too little for the local model; the hosted fallback `qwen3.5:27b-cloud` was no longer available, and Ollama's suggested replacement (`glm-5.3-flash:cloud`) required payment. Work from different models is labelled below and should not be compared as if it came from one setup.

**What the agents generated (code and text):**
- `cnt_std_7` in `src/features.py` and its hand-computed test in `tests/test_leakage.py` (Audrey's agent, via `/new-feature`)
- the raw-column classification and seeded fault experiments were completed using Audrey's local Claude Code agent with assistance from ChatGPT. ChatGPT also assisted with test corrections, the unknown-weather-label test, the seed-fault skill, documentation, and project configuration.
- the `TARGET_TRANSFORM=ratio` option in `src/train.py`, and first drafts of the Exercise 4 and Exercise 5 sections and their `DECISIONS.md` lines (Claude Opus 5.5)

**Decisions that were ours** (each has a line in `docs/DECISIONS.md`):
- **What to predict:** total daily rides (`cnt`) for day d, using only information available before d.
- **What counts as leakage:** `casual` and `registered` (they sum to `cnt`), time indexes (`instant`, `yr`, `days_since_2011`), and the unverified `cnt_2d_bfr`; every lag is shifted before it is aggregated.
- **How to split:** by date (train 2011, validate H1 2012, test H2 2012); feature and transform choices were based on validation results. The starter pipeline and verification tests also computed held-out test scores, and the transformation script saved test metrics even when only validation metrics were printed.
- **Which baselines:** the 2011 mean, and persistence ("yesterday again"), reported next to every model.
- **Whether to keep the feature:** kept `cnt_std_7` (ridge validation R^2 +0.075, above the 0.01 noise floor).
- **Whether the transform is defensible:** the ratio target is fair (past-only, matches multiplicative growth) but limited (chosen after seeing hgb fail, hurts ridge); the committed pipeline stays untransformed.
- **Whether the answer is believable:** ridge does not beat persistence on test MAE, so we recommend persistence and treat ridge's R^2 edge as unproven.
