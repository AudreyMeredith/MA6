# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.

- 2026-11-25: Added cnt_std_7 to capture recent demand volatility. All seven inputs are known before the prediction date because demand is shifted before aggregation. Validation R2 increased from 0.6475 to 0.7224 for ridge (+0.0749) and decreased from 0.2185 to 0.0977 for HGB (-0.1208). Kept the feature because ridge is the stronger validation model and its improvement exceeds 0.01. Both baselines remained unchanged. No test-set metrics were used for this decision.
- 2026-11-25: Updated CLAUDE.md to document the volatility feature, explicit raw column classification, and reusable seed-fault skill.
- 2026-11-25: Added an unknown-weather-label test after discovering that the original verification suite did not detect removal of the weather encoder's error guard.
- 2026-11-25: Exercise 4. Added TARGET_TRANSFORM=ratio to src/train.py (off by default): ridge and hgb fit on cnt / cnt_roll_7 and predictions are multiplied back by cnt_roll_7. Past-only, because cnt_roll_7 uses d-1..d-7. Validation R2: hgb 0.098 -> 0.748, ridge 0.722 -> 0.613; baselines unchanged. Judged fair but limited: it matches multiplicative 2012 growth, but it was chosen after seeing hgb fail, only one transform was tried, and it hurts ridge. Test set opened once after this decision: hgb ratio 0.628 vs ridge raw 0.636. Committed reports/metrics.json stays the untransformed pipeline.
- 2026-11-25: Exercise 5. Recommend persistence over ridge for deployment: test MAE ties (840.1 vs 840.3) and ridge's MAE lead on validation (200 rides) disappeared on test; ridge's higher test R^2 (0.636 vs 0.510) reflects fewer large misses, which only matters with evidence that large misses are costlier.
