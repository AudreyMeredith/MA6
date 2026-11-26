"""Stage 3: temporal split, fit, evaluate, write metrics.

Two baselines and two models, on purpose.

  baseline_mean         predict the 2011 average for every day
  baseline_persistence  predict yesterday's count (cnt_lag_1)
  ridge                 standardised linear model on the audited features
  hgb                   gradient-boosted trees on the same features

The mean baseline shows what "the distribution moved" costs. Persistence
is the baseline that actually matters: ridge's features are dominated by
lagged demand, so if it cannot beat "yesterday again" it has learned
nothing worth reporting. The booster is there because it fails, and the
reason it fails is the headline result.

Run: python -m src.train

Exercise 4 (off by default): TARGET_TRANSFORM=ratio fits ridge and hgb on
cnt / cnt_roll_7 -- today relative to the trailing week -- and multiplies
predictions back by cnt_roll_7 before scoring against cnt. cnt_roll_7 uses
only d-1..d-7, so the transform is known at prediction time. A ratio stays
in the range seen in 2011 even as 2012 demand grows, which is what a tree
needs. Results go to reports/metrics_ex4.json and only validation scores
are printed; reports/metrics.json is always the untransformed pipeline.
"""
import json
import os

import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.config import METRICS, PROCESSED, TARGET, TRAIN_END, VALID_END
from src.features import feature_columns

TARGET_TRANSFORM = os.environ.get("TARGET_TRANSFORM", "none")
if TARGET_TRANSFORM not in {"none", "ratio"}:
    raise ValueError(f"unknown TARGET_TRANSFORM: {TARGET_TRANSFORM!r}")
RATIO_SCALE = "cnt_roll_7"            # the denominator; past-only by construction
RATIO_MODELS = {"ridge", "hgb"}       # baselines are never transformed


class PersistenceBaseline(BaseEstimator, RegressorMixin):
    """Predict a single lagged column unchanged. Nothing is fit."""

    def __init__(self, column: str = "cnt_lag_1"):
        self.column = column

    def fit(self, X, y=None):
        if self.column not in X.columns:
            raise ValueError(f"persistence baseline needs column {self.column!r}")
        return self

    def predict(self, X):
        return X[self.column].to_numpy(dtype=float)


MODELS = {
    "baseline_mean": DummyRegressor(strategy="mean"),
    "baseline_persistence": PersistenceBaseline("cnt_lag_1"),
    "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
    "hgb": HistGradientBoostingRegressor(random_state=0, max_iter=300),
}


def temporal_split(df: pd.DataFrame):
    """Split by date, never at random. A random split on a time series
    puts tomorrow in train and today in test."""
    train = df[df.dteday <= TRAIN_END]
    valid = df[(df.dteday > TRAIN_END) & (df.dteday <= VALID_END)]
    test = df[df.dteday > VALID_END]
    return train, valid, test


def fit_and_score() -> dict:
    df = pd.read_parquet(PROCESSED)
    cols = feature_columns(df)
    train, valid, test = temporal_split(df)

    results = {
        "n_features": len(cols),
        "features": cols,
        "n_train": len(train),
        "n_valid": len(valid),
        "n_test": len(test),
    }
    if TARGET_TRANSFORM != "none":
        results["target_transform"] = TARGET_TRANSFORM
    for name, model in MODELS.items():
        ratio = TARGET_TRANSFORM == "ratio" and name in RATIO_MODELS
        y_fit = train[TARGET] / train[RATIO_SCALE] if ratio else train[TARGET]
        model.fit(train[cols], y_fit)

        def predict(part, model=model, ratio=ratio):
            pred = model.predict(part[cols])
            return pred * part[RATIO_SCALE].to_numpy() if ratio else pred

        results[name] = {
            split: {
                "r2": round(float(r2_score(part[TARGET], predict(part))), 4),
                "mae": round(float(mean_absolute_error(part[TARGET], predict(part))), 1),
            }
            for split, part in [("valid", valid), ("test", test)]
        }
    return results


if __name__ == "__main__":
    res = fit_and_score()
    out = METRICS if TARGET_TRANSFORM == "none" else METRICS.with_name("metrics_ex4.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2))
    if TARGET_TRANSFORM == "none":
        print(json.dumps({k: v for k, v in res.items() if k != "features"}, indent=2))
    else:
        # Exercise 4 is decided on validation only; the test set is opened once, later.
        print(f"TARGET_TRANSFORM={TARGET_TRANSFORM} -> {out.name} (validation only)")
        for name in MODELS:
            print(f"  {name:22s} valid R2 {res[name]['valid']['r2']:+.4f}  MAE {res[name]['valid']['mae']:.1f}")
