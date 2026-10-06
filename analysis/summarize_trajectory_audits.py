"""Summarize shared components and alignment limits from the saved audits."""
import argparse
import json
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--audit', type=Path, required=True)
    args = ap.parse_args()
    p = args.audit
    links = pd.read_csv(p / 'archived_component_links.csv').dropna(subset=['component_id'])
    counts = links.groupby(['image', 'component_id']).size().rename('archive_rows_per_component')
    shared = links.join(counts, on=['image', 'component_id'])
    shared = shared[shared.archive_rows_per_component > 1]
    shared.to_csv(p / 'shared_component_archive_records.csv', index=False)
    counts[counts > 1].reset_index().to_csv(p / 'shared_components.csv', index=False)
    align = pd.read_csv(p / 'image_alignment_diagnostics.csv')
    # Explicit descriptive diagnostic criterion, not a preregistered ground-truth test.
    sufficient = ((align.train_inlier_tiles >= 3) & (align.heldout_fraction_within_5px >= .8)
                  & (align.heldout_fitted_median_pixels <= 5))
    transitions = pd.read_csv(p / 'archived_transition_screen.csv')
    endpoint = pd.read_csv(p / 'model_endpoint_trace.csv')
    endpoint.loc[endpoint.candidate_pair_count > 1].to_csv(p / 'ambiguous_endpoint_links.csv', index=False)
    summary = dict(shared_component_dates=int((counts > 1).sum()),
        archive_records_on_shared_components=len(shared), excess_archive_rows_over_components=int((counts-1).sum()),
        same_component_records_are_not_independent=True,
        alignment_pairs=len(align), alignment_pairs_with_fits=int(align.train_inliers.notna().sum()),
        alignment_pairs_passing_diagnostic_gate=int(sufficient.sum()),
        diagnostic_gate='At least 3 training-inlier tiles, >=80% held-out matches within 5 px, held-out median <=5 px. '
                        'Descriptive gate applied to diagnostics; independently identified stable controls still required.',
        continued_records_without_expected_overlap_but_with_another_target=int(((transitions.category == 'continued_row_without_overlap') &
                                                                               (transitions.candidate_successors > 0)).sum()),
        ambiguous_model_records=int((endpoint.candidate_pair_count > 1).sum()),
        interpretation='Repeated archive rows can refer to the same raster component. Their cause is unresolved '
                       '(e.g. track branching or duplicate assignment); do not count them as independent individuals.')
    (p / 'trajectory_evidence_summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
