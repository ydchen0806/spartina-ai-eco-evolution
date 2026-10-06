"""Screen cross-survey alignment with feature matches and spatially held-out tiles.

Features are not independently surveyed ground control; outputs are diagnostics.
No source raster or mask is transformed.
"""
import argparse
import json
from pathlib import Path

import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cv2.setNumThreads(2)
    cv2.setRNGSeed(20261007)
    sift = cv2.SIFT_create(nfeatures=500)
    matcher = cv2.BFMatcher()
    size = pd.read_csv(ROOT / 'data/source/original_pipeline/result_size.csv', index_col=0)
    names = [Path(c).name for c in size]
    # Same fixed grid for all images; fold assignment is spatial, not feature-random.
    tiles = [(ix+4*iy, x-1024, y-1024, (ix+iy) % 2)
             for iy, y in enumerate([3000, 9000, 15000, 21000])
             for ix, x in enumerate([3000, 9000, 15000, 21000])]
    previous = None
    diagnostics, matches = [], []
    for name in names:
        features = {}
        with rasterio.open(args.source / 'imagery_georeferenced' / name) as ds:
            for tile, col, row, fold in tiles:
                rgb = ds.read([1, 2, 3], window=Window(col, row, 2048, 2048),
                              out_shape=(3, 1024, 1024)).transpose(1, 2, 0)
                gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
                kps, desc = sift.detectAndCompute(gray, None)
                xy = np.asarray([kp.pt for kp in kps], dtype=np.float32).reshape(-1, 2)*2 + [col, row]
                features[tile] = (xy, desc, fold)
        print(name, 'features', sum(len(f[0]) for f in features.values()), flush=True)
        if previous is not None:
            observations = []
            for tile, _, _, fold in tiles:
                a, da, _ = previous[tile]
                b, db, _ = features[tile]
                if da is None or db is None or min(len(da), len(db)) < 2:
                    continue
                forward = matcher.knnMatch(da, db, k=2)
                reverse = {m.queryIdx: m.trainIdx for m in matcher.match(db, da)}
                for first, second in forward:
                    if first.distance < .65*second.distance and reverse.get(first.trainIdx) == first.queryIdx:
                        observations.append(dict(tile=tile, fold=fold,
                            source_col=a[first.queryIdx, 0], source_row=a[first.queryIdx, 1],
                            target_col=b[first.trainIdx, 0], target_row=b[first.trainIdx, 1]))
            obs = pd.DataFrame(observations)
            summary = dict(source_image=previous_name, target_image=name, mutual_ratio_matches=len(obs))
            if len(obs):
                train = obs.fold == 0
                summary.update(train_tiles=int(obs.loc[train].tile.nunique()),
                               test_tiles=int(obs.loc[~train].tile.nunique()))
                if train.sum() >= 20 and (~train).sum() >= 10 and summary['train_tiles'] >= 3 and summary['test_tiles'] >= 2:
                    x = obs[['source_col', 'source_row']].to_numpy()
                    y = obs[['target_col', 'target_row']].to_numpy()
                    affine, inliers = cv2.estimateAffinePartial2D(x[train], y[train], method=cv2.RANSAC,
                        ransacReprojThreshold=5, maxIters=5000, confidence=.999, refineIters=20)
                    if affine is not None:
                        pred = np.column_stack([x, np.ones(len(x))]) @ affine.T
                        residual = np.linalg.norm(pred-y, axis=1)
                        obs['uncorrected_distance_pixels'] = np.linalg.norm(x-y, axis=1)
                        obs['train_fitted_residual_pixels'] = residual
                        obs['training_ransac_inlier'] = False
                        obs.loc[train, 'training_ransac_inlier'] = inliers.ravel().astype(bool)
                        dx, dy = affine @ [17500, 13000, 1] - [17500, 13000]
                        summary.update(train_matches=int(train.sum()), test_matches=int((~train).sum()),
                            train_inliers=int(inliers.sum()), train_inlier_tiles=int(obs.loc[obs.training_ransac_inlier].tile.nunique()),
                            heldout_raw_median_pixels=float(obs.loc[~train, 'uncorrected_distance_pixels'].median()),
                            heldout_fitted_median_pixels=float(np.median(residual[~train])),
                            heldout_fraction_within_5px=float((residual[~train] <= 5).mean()),
                            roi_center_shift_col_pixels=float(dx), roi_center_shift_row_pixels=float(dy),
                            affine_00=float(affine[0, 0]), affine_01=float(affine[0, 1]), affine_02=float(affine[0, 2]),
                            affine_10=float(affine[1, 0]), affine_11=float(affine[1, 1]), affine_12=float(affine[1, 2]))
                obs['source_image'], obs['target_image'] = previous_name, name
                matches.append(obs)
            diagnostics.append(summary)
        previous, previous_name = features, name
    result = pd.DataFrame(diagnostics)
    result.to_csv(args.output / 'image_alignment_diagnostics.csv', index=False)
    pd.concat(matches).to_csv(args.output / 'image_alignment_feature_matches.csv', index=False)
    (args.output / 'image_alignment_method.json').write_text(json.dumps(dict(
        feature='SIFT', max_features_per_tile=500, tile_side_original_pixels=2048, downsample_factor=2,
        tiles=tiles, ratio_threshold=.65, mutual_nearest=True, seed=20261007,
        model='partial affine RANSAC fitted on checkerboard fold 0; evaluated on fold 1',
        ransac_threshold_original_pixels=5,
        interpretation='Appearance-feature alignment diagnostic. Features may include moving vegetation, '
        'water or matching errors. No independently surveyed control points; no corrected biological inference.'), indent=2)+'\n')
    fig, axes = plt.subplots(2, 1, figsize=(11, 6), layout='constrained', sharex=True)
    x = np.arange(len(result))
    axes[0].plot(x, result.heldout_raw_median_pixels, 'o-', label='Raw pixel coordinates', color='#D55E00')
    axes[0].plot(x, result.heldout_fitted_median_pixels, 's-', label='After diagnostic affine fit', color='#0072B2')
    axes[0].set(ylabel='Held-out feature median residual (px)')
    axes[0].legend(fontsize=8)
    axes[1].plot(x, result.heldout_fraction_within_5px, 'o-', color='#009E73')
    axes[1].set(ylabel='Held-out matches within 5 px', ylim=(0, 1.05))
    axes[1].set_xticks(x, result.target_image.str.replace('.tif', '', regex=False), rotation=60, ha='right')
    fig.suptitle('Adjacent-survey alignment diagnostic; image features are not ground control')
    fig.savefig(args.output / 'image_alignment_diagnostic.pdf')
    fig.savefig(args.output / 'image_alignment_diagnostic.png', dpi=180)
    plt.close(fig)
    print(result.to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
