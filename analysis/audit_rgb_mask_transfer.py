#!/usr/bin/env python3
"""Audit temporal transfer of RGB-to-archived-mask relationships.

This is a label-transfer audit, not an accuracy estimate: the historical mask
is the target in every fold and no independent expert labels are available.
The experiment asks whether colour features learned from the other surveys
reproduce the archived positive/zero labels in a completely held-out survey.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
                             confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score, jaccard_score)


def feature_block(rgb: np.ndarray, rows: np.ndarray, cols: np.ndarray,
                  height: int, width: int) -> np.ndarray:
    x = rgb[:, rows, cols].astype(np.float32) / 255.0
    r, g, b = x
    den = r + g + b + 1e-6
    # Colour and chromaticity features; coordinates are excluded to avoid a
    # spatial shortcut that would inflate temporal transfer.
    return np.column_stack([r, g, b, 2*g-r-b, g-r, g-b,
                            r/den, g/den, b/den,
                            rows.astype(np.float32)/height,
                            cols.astype(np.float32)/width])[:, :9]


def sample_date(image: Path, mask: Path, n_each: int, seed: int,
                window: int = 512) -> tuple[np.ndarray, np.ndarray, dict]:
    rng = np.random.default_rng(seed)
    with rasterio.open(image) as src, rasterio.open(mask) as msk:
        assert (src.width, src.height) == (msk.width, msk.height)
        pos, neg = [], []
        # Keep a bounded, spatially spread candidate pool. Enumerating every
        # 0.2-m background pixel would require hundreds of millions of Python
        # objects for one orthomosaic.
        # Read tiled windows so the 30-GB recovered archive is never loaded in
        # memory. Candidate coordinates are retained only for this date.
        for row in range(0, src.height, window):
            for col in range(0, src.width, window):
                h, w = min(window, src.height-row), min(window, src.width-col)
                lab = msk.read(1, window=rasterio.windows.Window(col, row, w, h))
                for target, bucket in ((1, pos), (0, neg)):
                    rr, cc = np.where((lab > 0) if target == 1 else (lab == 0))
                    if len(rr):
                        take = rng.choice(len(rr), size=min(32, len(rr)), replace=False)
                        bucket.extend(((rr[take]+row)*src.width + cc[take]+col).tolist())
        if not pos or not neg:
            raise ValueError(f"Missing class in {mask}")
        pos = rng.choice(np.asarray(pos, dtype=np.int64), size=min(n_each, len(pos)), replace=False)
        neg = rng.choice(np.asarray(neg, dtype=np.int64), size=min(n_each, len(neg)), replace=False)
        ids = np.concatenate([pos, neg]); y = np.concatenate([np.ones(len(pos), dtype=np.uint8), np.zeros(len(neg), dtype=np.uint8)])
        rows, cols = np.divmod(ids, src.width)
        # Small point reads are slower than a full window. Group by source
        # windows and read each RGB window once.
        X = np.empty((len(ids), 9), dtype=np.float32)
        for wr in np.unique(rows // window):
            for wc in np.unique(cols // window):
                take = (rows//window == wr) & (cols//window == wc)
                if not take.any(): continue
                r0, c0 = int(wr*window), int(wc*window)
                h, w = min(window, src.height-r0), min(window, src.width-c0)
                rgb = src.read([1,2,3], window=rasterio.windows.Window(c0,r0,w,h))
                X[take] = feature_block(rgb, rows[take]-r0, cols[take]-c0, h, w)
        return X, y, {"n_positive_candidates": int(len(pos)), "n_negative_candidates": int(len(neg)),
                      "n_positive_sampled": int((y==1).sum()), "n_negative_sampled": int((y==0).sum())}


def uniform_sample(image: Path, mask: Path, n: int, seed: int,
                   window: int = 512) -> tuple[np.ndarray, np.ndarray]:
    """Sample pixels uniformly over the complete raster for prevalence bias."""
    rng = np.random.default_rng(seed)
    with rasterio.open(image) as src, rasterio.open(mask) as msk:
        ids = rng.integers(0, src.width * src.height, size=n, dtype=np.int64)
        rows, cols = np.divmod(ids, src.width)
        y = np.empty(n, dtype=np.uint8); X = np.empty((n, 9), dtype=np.float32)
        for wr in np.unique(rows // window):
            for wc in np.unique(cols // window):
                take = (rows//window == wr) & (cols//window == wc)
                if not take.any(): continue
                r0, c0 = int(wr*window), int(wc*window)
                h, w = min(window, src.height-r0), min(window, src.width-c0)
                win = rasterio.windows.Window(c0, r0, w, h)
                rgb = src.read([1,2,3], window=win)
                y[take] = (msk.read(1, window=win)[rows[take]-r0, cols[take]-c0] > 0).astype(np.uint8)
                X[take] = feature_block(rgb, rows[take]-r0, cols[take]-c0, h, w)
        return X, y


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--imagery", type=Path, required=True)
    ap.add_argument("--masks", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--n-each", type=int, default=3000)
    args = ap.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    pairs = [(p.stem, p, args.masks/p.name) for p in sorted(args.imagery.glob("*.tif")) if (args.masks/p.name).exists()]
    if len(pairs) < 10: raise RuntimeError("Expected at least ten paired RGB/mask surveys")
    data = {}
    for i,(date,img,msk) in enumerate(pairs):
        print("Sampling",date,flush=True)
        X, y, meta = sample_date(img,msk,args.n_each,20261010+i)
        uX, uy = uniform_sample(img,msk,4000,20262010+i)
        data[date] = (X, y, meta, uX, uy)
    rows=[];pred_rows=[]
    for held in data:
        train_dates=[d for d in data if d != held]
        Xtr=np.concatenate([data[d][0] for d in train_dates]); ytr=np.concatenate([data[d][1] for d in train_dates])
        Xte,yte,meta,uX,uy=data[held]
        model=ExtraTreesClassifier(n_estimators=300,min_samples_leaf=8,max_features="sqrt",class_weight="balanced",random_state=20261010,n_jobs=-1)
        model.fit(Xtr,ytr); score=model.predict_proba(Xte)[:,1]; pred=(score>=.5).astype(np.uint8)
        tn,fp,fn,tp=confusion_matrix(yte,pred,labels=[0,1]).ravel()
        uscore=model.predict_proba(uX)[:,1]; upred=(uscore>=.5).astype(np.uint8)
        rows.append({"held_out_date":held,"train_dates":";".join(train_dates),"train_n":len(ytr),"test_n":len(yte),
                     "observed_positive_fraction":float(yte.mean()),"predicted_positive_fraction":float(pred.mean()),
                     "uniform_archived_prevalence":float(uy.mean()),"uniform_predicted_prevalence":float(upred.mean()),
                     "uniform_prevalence_bias":float(upred.mean()-uy.mean()),"roc_auc":float(roc_auc_score(yte,score)),
                     "average_precision":float(average_precision_score(yte,score)),"f1":float(f1_score(yte,pred)),
                     "iou":float(jaccard_score(yte,pred)),"balanced_accuracy":float(balanced_accuracy_score(yte,pred)),
                     "precision":float(precision_score(yte,pred,zero_division=0)),"recall":float(recall_score(yte,pred)),
                     "tp":int(tp),"fp":int(fp),"fn":int(fn),"tn":int(tn),
                     "interpretation":"Held-out reproduction of archived labels, not independent biological truth."})
        for s,o,p in zip(score,yte,pred): pred_rows.append({"held_out_date":held,"observed_label":int(o),"predicted_label":int(p),"predicted_probability":float(s)})
    result=pd.DataFrame(rows); result.to_csv(args.output/"temporal_transfer_metrics.csv",index=False); pd.DataFrame(pred_rows).to_csv(args.output/"temporal_transfer_predictions.csv",index=False)
    summary={"paired_surveys":len(pairs),"dates":[x[0] for x in pairs],"n_each":args.n_each,
             "mean_roc_auc":float(result.roc_auc.mean()),"mean_iou":float(result.iou.mean()),"mean_f1":float(result.f1.mean()),
             "mean_abs_uniform_prevalence_bias":float(result.uniform_prevalence_bias.abs().mean()),
             "scope":"Temporal label-transfer audit. Archived masks are targets; no independent expert labels or segmentation accuracy are established."}
    (args.output/"temporal_transfer_audit.json").write_text(json.dumps(summary,indent=2)+"\n")
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8,"axes.spines.top":False,"axes.spines.right":False})
    x=np.arange(len(result)); fig,ax=plt.subplots(1,2,figsize=(7.2,3.1),layout="constrained")
    ax[0].bar(x,result.roc_auc,color="#0072B2");ax[0].axhline(.5,color="#888",lw=.8);ax[0].set(ylim=(.4,1),ylabel="ROC AUC",title="Temporal label transfer");ax[0].set_xticks(x,result.held_out_date,rotation=65,ha="right")
    ax[1].bar(x,result.uniform_prevalence_bias*100,color=np.where(result.uniform_prevalence_bias>=0,"#D55E00","#009E73"));ax[1].axhline(0,color="#333",lw=.8);ax[1].set(ylabel="Predicted − archived prevalence (%)",title="Uniform-raster prevalence bias");ax[1].set_xticks(x,result.held_out_date,rotation=65,ha="right")
    fig.suptitle("RGB-to-archived-mask transfer across surveys",fontsize=10,fontweight="bold")
    for ext in ("png","pdf","svg"): fig.savefig(args.output/f"temporal_transfer.{ext}",dpi=300)
    plt.close(fig); print(json.dumps(summary,indent=2))


if __name__ == "__main__": main()
