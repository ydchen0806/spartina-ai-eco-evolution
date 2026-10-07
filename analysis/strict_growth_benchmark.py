"""Fixed-specification growth baseline with forward and buffered spatial holdouts.

Uses starting geometry only. Labels are archived area changes, not verified
biological growth. Spatial blocking and shared-object purging do not repair
erroneous tracking or unknown image registration.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.base import clone
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]


def lineage_groups(size, pos):
    parent = {int(x): int(x) for x in size.index}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    seen = {}
    for row, vals in size.iterrows():
        for year, area in vals.items():
            if area <= 0:
                continue
            key = (year, pos.loc[row, year+'x'], pos.loc[row, year+'y'])
            if key in seen:
                a, b = find(int(row)), find(seen[key])
                parent[max(a, b)] = min(a, b)
            else:
                seen[key] = int(row)
    return {row: find(row) for row in parent}


def metrics(y, pred):
    return dict(n=len(y), rmse=float(np.sqrt(mean_squared_error(y, pred))),
                mae=float(mean_absolute_error(y, pred)), r2=float(r2_score(y, pred)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    audit_root = ROOT / 'data/derived/trajectory_audit_20261007'
    pairs = pd.read_csv(audit_root / 'annual_transition_pairs.csv')
    source = ROOT / 'data/source/original_pipeline'
    size = pd.read_csv(source / 'result_size1229.csv', index_col=0)
    pos = pd.read_csv(source / 'result_pos1229.csv', index_col=0)
    groups = lineage_groups(size, pos)
    pairs['dependency_group'] = pairs.annual_source_row.map(groups)
    # Identical observed transition rows are counted once; distinct branches stay grouped.
    key = ['year', 'end_year', 'size', 'end_size', 'start_X', 'start_Y', 'X', 'Y']
    before = len(pairs)
    pairs = pairs.drop_duplicates(key).reset_index(drop=True)
    pairs['sample_id'] = pairs.index
    pairs['log_start_area'] = np.log(pairs['size'])
    pairs['log_area_ratio'] = np.log(pairs.end_size / pairs['size'])
    pairs['quadrant'] = (pairs.start_X >= 7500).astype(int) + 2*(pairs.start_Y >= 9000).astype(int)
    features = ['log_start_area', 'start_X', 'start_Y']
    X = pairs[features].replace([np.inf, -np.inf], np.nan)
    specs = {
        'training_mean': DummyRegressor(),
        'ridge': make_pipeline(SimpleImputer(strategy='median'), StandardScaler(), Ridge(alpha=10)),
        'extra_trees': make_pipeline(SimpleImputer(strategy='median'),
            ExtraTreesRegressor(n_estimators=160, min_samples_leaf=10, max_features=1.0, random_state=20261007, n_jobs=4))}
    folds = []
    for year in sorted(pairs.year.unique())[2:]:
        test = np.flatnonzero(pairs.year == year)
        train0 = np.flatnonzero(pairs.year < year)
        held = set(pairs.loc[test, 'dependency_group'])
        train = np.array([i for i in train0 if pairs.loc[i, 'dependency_group'] not in held], dtype=int)
        folds.append(('forward_year', str(year), train0, train, test))
    for quadrant in sorted(pairs.quadrant.unique()):
        test = np.flatnonzero(pairs.quadrant == quadrant)
        train0 = np.flatnonzero(pairs.quadrant != quadrant)
        held = set(pairs.loc[test, 'dependency_group'])
        # Exclude training starts within 512 px of held-out starts in any year.
        dist, _ = cKDTree(pairs.loc[test, ['start_X', 'start_Y']]).query(pairs.loc[train0, ['start_X', 'start_Y']])
        train = np.array([i for i, distance in zip(train0, dist)
                          if distance >= 512 and pairs.loc[i, 'dependency_group'] not in held], dtype=int)
        folds.append(('buffered_quadrant', str(quadrant), train0, train, test))
    membership, predrows, foldmetrics = [], [], []
    for split, fold, train0, train, test in folds:
        assert not set(pairs.loc[train, 'dependency_group']) & set(pairs.loc[test, 'dependency_group'])
        if split == 'forward_year':
            assert pairs.loc[train, 'year'].max() < pairs.loc[test, 'year'].min()
        for role, indices in [('train', train), ('test', test)]:
            membership.extend(dict(split=split, fold=fold, role=role, sample_id=int(i)) for i in indices)
        if len(train) < 30 or len(test) < 5:
            raise ValueError(f'Insufficient observations in {split}/{fold}: {len(train)}, {len(test)}')
        for target in ['relative_gain', 'log_area_ratio']:
            for model, spec in specs.items():
                fitted = clone(spec).fit(X.iloc[train], pairs.loc[train, target])
                pred = fitted.predict(X.iloc[test])
                foldmetrics.append(dict(split=split, fold=fold, target=target, model=model,
                    train_n=len(train), excluded_train_n=len(train0)-len(train), **metrics(pairs.loc[test, target], pred)))
                predrows.extend(dict(split=split, fold=fold, target=target, model=model, sample_id=int(i),
                    observed=float(pairs.loc[i, target]), predicted=float(v)) for i, v in zip(test, pred))
        print(split, fold, 'train', len(train), 'test', len(test), 'purged', len(train0)-len(train), flush=True)
    predictions = pd.DataFrame(predrows)
    results = []
    for key, frame in predictions.groupby(['split', 'target', 'model']):
        assert not frame.sample_id.duplicated().any()
        results.append(dict(zip(['split', 'target', 'model'], key), **metrics(frame.observed, frame.predicted)))
    results = pd.DataFrame(results)
    pairs.to_csv(args.output / 'benchmark_samples.csv', index=False)
    pd.DataFrame(membership).to_csv(args.output / 'fold_membership.csv', index=False)
    pd.DataFrame(foldmetrics).to_csv(args.output / 'fold_metrics.csv', index=False)
    predictions.to_csv(args.output / 'heldout_predictions.csv', index=False)
    results.to_csv(args.output / 'pooled_metrics.csv', index=False)
    config = dict(input_pairs=before, unique_pairs=len(pairs), duplicate_pairs_removed=before-len(pairs),
        dependency_groups=int(pairs.dependency_group.nunique()), features=features,
        primary_target='log_area_ratio', secondary_target='relative_gain', spatial_buffer_pixels=512,
        random_seed=20261007, model_selection='Fixed settings; no tuning or best-model selection on these folds.',
        preprocessing='Imputer and scaling fitted within each training fold; no legacy PCA or next-survey features.',
        limitations=['Archived area and identity remain unvalidated.',
          'Dependency groups use shared bbox coordinates and may miss tracking errors.',
          'Year labels are not exact elapsed time; log area ratio is not an annualized rate.',
          'Initial area occurs in the response denominator; apparent size dependence need not imply a mechanism.',
          'Spatial folds are within one study site, not independent-site validation.',
          'No weather features used; benchmark does not test climate or causal mechanisms.'])
    (args.output / 'benchmark_config.json').write_text(json.dumps(config, indent=2)+'\n')
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout='constrained')
    for ax, target in zip(axes, ['log_area_ratio', 'relative_gain']):
        show = results[results.target == target]
        for j, split in enumerate(['forward_year', 'buffered_quadrant']):
            frame = show[show.split == split].set_index('model').loc[list(specs)]
            ax.bar(np.arange(3)+(.18 if j else -.18), frame.r2, width=.36,
                   color=['#0072B2', '#D55E00'][j], label=split.replace('_', ' '))
        ax.axhline(0, color='gray', lw=.7)
        ax.set_xticks(range(3), ['Training mean', 'Ridge', 'Extra trees'], rotation=15)
        ax.set(title=target.replace('_', ' '), ylabel='Pooled held-out R²')
    axes[0].legend(fontsize=8)
    fig.suptitle('Starting geometry only; archived labels, purged holdouts')
    fig.savefig(args.output / 'strict_benchmark.pdf')
    fig.savefig(args.output / 'strict_benchmark.png', dpi=180)
    plt.close(fig)
    print(results.to_string(index=False))


if __name__ == '__main__':
    main()
