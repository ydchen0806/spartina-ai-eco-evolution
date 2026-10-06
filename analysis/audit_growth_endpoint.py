"""Trace the modelling endpoint to annual matrices without editing source data."""
import argparse
from collections import Counter, defaultdict, deque
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    src = ROOT / 'data/source/original_pipeline'
    size = pd.read_csv(src / 'result_size1229.csv', index_col=0)
    pos = pd.read_csv(src / 'result_pos1229.csv', index_col=0)
    model = pd.read_excel(src / 'mydata_0224.xlsx')
    rows = []
    for row_id, values in size.iterrows():
        observed = values[values > 0]
        for j in range(len(observed) - 1):
            a, b = str(observed.index[j]), str(observed.index[j + 1])
            start, end = int(observed.iloc[j]), int(observed.iloc[j + 1])
            rows.append(dict(annual_source_row=int(row_id), year=int(a), end_year=int(b),
                             size=start, end_size=end, growth=end-start,
                             relative_gain=(end-start)/start, size_ratio=end/start,
                             start_X=int(pos.loc[row_id, a+'y']), start_Y=int(pos.loc[row_id, a+'x']),
                             X=int(pos.loc[row_id, b+'y']), Y=int(pos.loc[row_id, b+'x']),
                             first_pair_in_row=j == 0))
    pairs = pd.DataFrame(rows)
    # Queue matching preserves multiplicity; repeated keys remain explicitly ambiguous.
    keys = ['year', 'size', 'growth', 'X', 'Y']
    queues = defaultdict(deque)
    for i, key in enumerate(map(tuple, pairs[keys].to_numpy())):
        queues[key].append(i)
    counts = {k: len(q) for k, q in queues.items()}
    model['model_row'] = np.arange(len(model))
    linked = []
    for rec in model.to_dict('records'):
        key = tuple(rec[k] for k in keys)
        item = dict(rec)
        item['candidate_pair_count'] = counts.get(key, 0)
        if queues[key]:
            i = queues[key].popleft()
            item.update({k: v for k, v in pairs.loc[i].to_dict().items() if k not in keys})
            item['pair_index'] = i
        linked.append(item)
    linked = pd.DataFrame(linked)
    linked['recomputed_relative_gain'] = linked.growth / linked['size']
    linked['endpoint_difference'] = linked.growth_rate - linked.recomputed_relative_gain
    linked['endpoint_disagrees'] = linked.endpoint_difference.abs() > 1e-8
    pairs['in_model_table'] = pairs.index.isin(linked.pair_index.dropna().astype(int))
    linked.to_csv(out / 'model_endpoint_trace.csv', index=False)
    pairs.to_csv(out / 'annual_transition_pairs.csv', index=False)
    summary = linked.groupby('year').agg(
        model_n=('year', 'size'), endpoint_disagreement_n=('endpoint_disagrees', 'sum'),
        stored_mean=('growth_rate', 'mean'), recomputed_model_mean=('recomputed_relative_gain', 'mean'),
        difference_min=('endpoint_difference', 'min'), difference_max=('endpoint_difference', 'max'))
    all_summary = pairs.groupby('year').agg(all_pair_n=('year', 'size'),
        all_pair_mean=('relative_gain', 'mean'), nonpositive_n=('growth', lambda x: int((x <= 0).sum())),
        included_nonpositive_n=('in_model_table', lambda x: 0))
    all_summary['included_nonpositive_n'] = pairs.loc[pairs.growth <= 0].groupby('year').in_model_table.sum()
    summary = summary.join(all_summary).fillna({'included_nonpositive_n': 0})
    summary.to_csv(out / 'endpoint_year_summary.csv')
    lifetime = (size > 0).sum(axis=1).value_counts().sort_index()
    lifetime.rename_axis('observed_surveys').rename('annual_table_rows').to_csv(out / 'annual_observation_lengths.csv')
    # Record which full survey supplies each annual matrix: match exact area and bbox coordinates.
    full_size = pd.read_csv(src / 'result_size.csv', index_col=0)
    full_pos = pd.read_csv(src / 'result_pos.csv', index_col=0)
    survey_rows = []
    for year in size:
        valid = size[year] > 0
        annual_keys = Counter(zip(size.loc[valid, year], pos.loc[valid, year+'x'], pos.loc[valid, year+'y']))
        for survey in full_size:
            if year not in survey:
                continue
            valid_full = full_size[survey] > 0
            full_keys = Counter(zip(full_size.loc[valid_full, survey],
                                   full_pos.loc[valid_full, survey+'x'], full_pos.loc[valid_full, survey+'y']))
            survey_rows.append(dict(year=int(year), image=Path(survey).name,
                annual_observations=sum(annual_keys.values()), exact_area_bbox_matches=sum((annual_keys & full_keys).values())))
    pd.DataFrame(survey_rows).to_csv(out / 'annual_to_survey_inventory.csv', index=False)
    trend = {}
    for col in ['stored_mean', 'recomputed_model_mean', 'all_pair_mean']:
        rho, p = spearmanr(summary.index, summary[col])
        trend[col] = dict(n_years=len(summary), spearman_rho=float(rho), p_two_sided=float(p))
    audit = dict(annual_matrix_rows=len(size), singleton_rows=int(lifetime.get(1, 0)),
        annual_transition_pairs=len(pairs), annual_gaps=pairs.eval('end_year-year').value_counts().to_dict(),
        model_records=len(linked), model_records_linked=int(linked.pair_index.notna().sum()),
        ambiguous_model_records=int((linked.candidate_pair_count > 1).sum()),
        endpoint_disagreement_n=int(linked.endpoint_disagrees.sum()),
        all_nonpositive_pairs=int((pairs.growth <= 0).sum()),
        excluded_gain_at_least_10=int(((pairs.relative_gain >= 10) & ~pairs.in_model_table).sum()),
        selection_exactly_matches_gain_between_0_and_10=bool((((pairs.relative_gain > 0) & (pairs.relative_gain < 10)) == pairs.in_model_table).all()),
        included_nonpositive_pairs=int(((pairs.growth <= 0) & pairs.in_model_table).sum()),
        start_coordinate_matches=int(((linked.X == linked.start_X) & (linked.Y == linked.start_Y)).sum()),
        end_coordinate_matches=int(linked.pair_index.notna().sum()), annual_mean_trends=trend,
        interpretation='Stored growth_rate differs from matrix-derived relative gain in selected years. '
        'The missing transformation is unresolved; recomputed endpoints are sensitivity analyses, not ground truth. '
        'Annual rows and overlap links are not independently validated biological identities.')
    (out / 'endpoint_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), layout='constrained')
    for col, label, color in [('stored_mean', 'Stored model endpoint', '#D55E00'),
                             ('recomputed_model_mean', 'Same records: area-derived gain', '#0072B2'),
                             ('all_pair_mean', 'All archived pairs: area-derived gain', '#009E73')]:
        axes[0].plot(summary.index, summary[col], 'o-', label=label, color=color)
    axes[0].set(xlabel='Starting year', ylabel='Mean dimensionless endpoint', title='Endpoint definition sensitivity')
    axes[0].legend(fontsize=7)
    axes[1].scatter(linked.recomputed_relative_gain, linked.growth_rate, s=9,
                    c=np.where(linked.endpoint_disagrees, '#D55E00', '#0072B2'), alpha=.6)
    low = min(linked.recomputed_relative_gain.min(), linked.growth_rate.min())
    high = max(linked.recomputed_relative_gain.max(), linked.growth_rate.max())
    axes[1].plot([low, high], [low, high], color='gray', lw=1)
    axes[1].set(xlabel='(End area − start area) / start area', ylabel='Stored growth_rate', title=f'{int(linked.endpoint_disagrees.sum())} records disagree')
    axes[2].bar(summary.index-.18, summary.all_pair_n, width=.36, label='All archived pairs', color='#0072B2')
    axes[2].bar(summary.index+.18, summary.model_n, width=.36, label='Model table', color='#D55E00')
    axes[2].set(xlabel='Starting year', ylabel='Pair count', title='Conditioned on observed continuity')
    axes[2].legend(fontsize=8)
    fig.savefig(out / 'growth_endpoint_sensitivity.pdf')
    fig.savefig(out / 'growth_endpoint_sensitivity.png', dpi=180)
    plt.close(fig)
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
