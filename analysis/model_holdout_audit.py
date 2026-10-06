#!/usr/bin/env python3
"""Audit generalisation of growth-rate models under time and spatial holdout.

This is an independent reanalysis of the recovered 854-row workbook. It is
deliberately conservative: model scores are reported on held-out records and
are not interpreted as causal environmental effects.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


HERE = Path(__file__).resolve()
RELEASE_ROOT = HERE.parents[1]
WORK_ROOT = HERE.parents[2]
SOURCE = WORK_ROOT / "nature_manuscript/external_data/legacy_simulation_archive/230214simulation/raw_data.xlsx"
if not SOURCE.exists():
    SOURCE = RELEASE_ROOT / "data/source/legacy_simulation_archive/230214simulation/raw_data.xlsx"
OUT = RELEASE_ROOT


def score_predictions(y, pred, split, feature_set, model):
    return {"split": split, "feature_set": feature_set, "model": model,
            "n": int(len(y)), "rmse": float(np.sqrt(mean_squared_error(y, pred))),
            "mae": float(mean_absolute_error(y, pred)), "r2": float(r2_score(y, pred))}


def main():
    d = pd.read_excel(SOURCE)
    d = d.rename(columns={"Unnamed: 0": "record_id"})
    target = d.growth_rate.astype(float)
    climate = [c for c in d.columns if c not in {"record_id", "year", "size", "X", "Y", "growth_rate", "pca1", "pca2", "pca3", "pca4", "growth_rate_simulation"}]
    feature_sets = {
        "pca+space": ["size", "X", "Y", "pca1", "pca2", "pca3", "pca4"],
        "climate+space": climate + ["size", "X", "Y"],
        "climate_only": climate + ["size"],
    }
    models = {
        "mean": DummyRegressor(strategy="mean"),
        "ridge": make_pipeline(StandardScaler(), Ridge(alpha=10.0)),
        "random_forest": RandomForestRegressor(n_estimators=300, min_samples_leaf=4, max_features=0.7, random_state=42, n_jobs=-1),
        "extra_trees": ExtraTreesRegressor(n_estimators=300, min_samples_leaf=4, max_features=0.7, random_state=42, n_jobs=-1),
    }
    results = []; pred_rows = []
    year_groups = d.year.to_numpy()
    # Four-by-four spatial blocks; blocks with few rows are retained as groups.
    bx = pd.qcut(d.X, 4, labels=False, duplicates="drop").to_numpy()
    by = pd.qcut(d.Y, 4, labels=False, duplicates="drop").to_numpy()
    spatial_groups = (bx * 10 + by).astype(int)
    for split_name, groups in [("leave_one_year_out", year_groups), ("spatial_blocks", spatial_groups)]:
        n_splits = len(np.unique(groups)) if split_name == "leave_one_year_out" else min(5, len(np.unique(groups)))
        cv = GroupKFold(n_splits=n_splits)
        for fs_name, cols in feature_sets.items():
            X = d[cols].replace([np.inf, -np.inf], np.nan).fillna(d[cols].median())
            for model_name, estimator in models.items():
                pred = np.full(len(d), np.nan)
                for train, test in cv.split(X, target, groups):
                    estimator.fit(X.iloc[train], target.iloc[train])
                    pred[test] = estimator.predict(X.iloc[test])
                results.append(score_predictions(target, pred, split_name, fs_name, model_name))
                if model_name in {"ridge", "random_forest", "extra_trees"}:
                    for i in range(len(d)):
                        pred_rows.append({"record_id": int(d.record_id.iloc[i]), "year": int(d.year.iloc[i]), "split": split_name,
                                          "feature_set": fs_name, "model": model_name, "observed_growth_rate": float(target.iloc[i]), "predicted_growth_rate": float(pred[i])})
    summary = pd.DataFrame(results)
    pred_df = pd.DataFrame(pred_rows)
    (OUT / "tables").mkdir(exist_ok=True)
    summary.to_csv(OUT / "tables/model_holdout_summary.csv", index=False)
    pred_df.to_csv(OUT / "tables/model_holdout_predictions.csv", index=False)
    best = summary.sort_values(["split", "rmse"]).groupby("split", as_index=False).first()
    audit = {"source": str(SOURCE), "n_rows": int(len(d)), "n_year_groups": int(len(np.unique(year_groups))),
             "n_spatial_blocks": int(len(np.unique(spatial_groups))), "best_by_split": best.to_dict(orient="records"),
             "interpretation": "Held-out predictive audit only; scores do not establish causal environmental effects or heritability."}
    (OUT / "tables/model_holdout_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False))

    # Compact figure: RMSE and R2 for non-baseline models.
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    show = summary[summary.model != "mean"].copy()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), constrained_layout=True)
    for split, color in [("leave_one_year_out", "#176B87"), ("spatial_blocks", "#D55E00")]:
        s = show[show.split == split]
        labels = s.feature_set + " / " + s.model
        axes[0].barh(labels, s.rmse, color=color, alpha=.78, label=split.replace("_", " "))
        axes[1].scatter(s.rmse, s.r2, color=color, s=46, label=split.replace("_", " "))
        for _, row in s.iterrows(): axes[1].annotate(row.model + "\n" + row.feature_set, (row.rmse, row.r2), fontsize=6, xytext=(3, 3), textcoords="offset points")
    axes[0].set(xlabel="Held-out RMSE", title="A  Out-of-sample error"); axes[0].legend(frameon=False, fontsize=8)
    axes[1].set(xlabel="Held-out RMSE", ylabel="Held-out R²", title="B  Accuracy–generalisation trade-off"); axes[1].axhline(0, color="#999", lw=.7); axes[1].grid(alpha=.2); axes[1].legend(frameon=False, fontsize=8)
    fig.suptitle("Growth-rate model audit under temporal and spatial holdout", fontsize=13, fontweight="bold")
    (OUT / "figures/generated_candidates").mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "figures/generated_candidates/fig_model_holdout_audit.pdf", bbox_inches="tight")
    fig.savefig(OUT / "figures/generated_candidates/fig_model_holdout_audit.png", dpi=320, bbox_inches="tight")
    plt.close(fig)
    print(json.dumps(audit, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
