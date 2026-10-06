"""Rebuild 8-connected components and screen adjacent mask overlaps.

Links are image-index overlap candidates, not validated biological events.
No registration correction is estimated or applied by this script.
"""
import argparse
import gc
import json
from pathlib import Path
import warnings

import cv2
import numpy as np
import pandas as pd
import rasterio
from rasterio.errors import NotGeoreferencedWarning
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[1]
ROI = Window(10000, 4000, 15000, 18000)


def extract(source, image, size, pos):
    with rasterio.open(source / 'mask' / image) as ds:
        mask = ds.read(1, window=ROI)
    n, labels, stats, centers = cv2.connectedComponentsWithStats(mask, connectivity=8)
    del mask
    comp = pd.DataFrame(stats[1:], columns=['col', 'row', 'width', 'height', 'area_pixels'])
    comp['component_id'] = np.arange(1, n)
    comp['centroid_col'] = centers[1:, 0] + ROI.col_off
    comp['centroid_row'] = centers[1:, 1] + ROI.row_off
    comp['touches_roi_edge'] = ((comp.col == 0) | (comp.row == 0) |
        (comp.col + comp.width == ROI.width) | (comp.row + comp.height == ROI.height))
    comp['image'] = image
    col = './mask/' + image
    obs = pd.DataFrame({'source_row': size.index, 'row': pos[col+'x'], 'col': pos[col+'y'], 'archived_area': size[col]})
    obs = obs[obs.archived_area > 0]
    unique = comp.loc[~comp.duplicated(['row', 'col'], keep=False)]
    obs = obs.merge(unique[['row', 'col', 'component_id', 'area_pixels']], on=['row', 'col'],
                    how='left', validate='many_to_one')
    obs['image'] = image
    return labels, comp, obs


def overlap_edges(previous, current, prev_comp, comp, min_area):
    indices = np.flatnonzero(previous)
    left, right = previous.ravel()[indices], current.ravel()[indices]
    positive = right > 0
    codes = left[positive].astype(np.int64) * (len(comp)+1) + right[positive]
    unique, counts = np.unique(codes, return_counts=True)
    edges = pd.DataFrame({'source_component': unique // (len(comp)+1),
                          'target_component': unique % (len(comp)+1), 'intersection_pixels': counts})
    pa = prev_comp.set_index('component_id').area_pixels
    ca = comp.set_index('component_id').area_pixels
    edges['source_area'] = edges.source_component.map(pa)
    edges['target_area'] = edges.target_component.map(ca)
    edges['overlap_over_min_area'] = edges.intersection_pixels / edges[['source_area', 'target_area']].min(axis=1)
    edges['iou'] = edges.intersection_pixels / (edges.source_area + edges.target_area - edges.intersection_pixels)
    edges = edges[(edges.source_area >= min_area) & (edges.target_area >= min_area)]
    return edges, indices, left


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--min-area', type=int, default=100)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cv2.setNumThreads(2)
    warnings.filterwarnings('ignore', category=NotGeoreferencedWarning)
    size = pd.read_csv(ROOT / 'data/source/original_pipeline/result_size.csv', index_col=0)
    pos = pd.read_csv(ROOT / 'data/source/original_pipeline/result_pos.csv', index_col=0)
    names = [Path(c).name for c in size]
    components, archives, all_edges, summaries, events = [], [], [], [], []
    previous = prev_comp = prev_obs = prev_image = None
    for image in names:
        labels, comp, obs = extract(args.source, image, size, pos)
        components.append(comp)
        archives.append(obs)
        print(image, 'components', len(comp), 'archived bbox matches', obs.component_id.notna().sum(), flush=True)
        if previous is not None:
            edges, indices, left = overlap_edges(previous, labels, prev_comp, comp, args.min_area)
            edges['source_image'], edges['target_image'] = prev_image, image
            all_edges.append(edges)
            # Exact black / white screen on destination RGB at source foreground pixels.
            # It is a diagnostic for fill, not an authoritative valid-footprint classification.
            with rasterio.open(args.source / 'imagery_georeferenced' / image) as ds:
                rgb = ds.read([1, 2, 3], window=ROI).reshape(3, -1)[:, indices]
            extreme = (rgb == 0).all(axis=0) | (rgb == 255).all(axis=0)
            fill_count = np.bincount(left, weights=extreme, minlength=len(prev_comp)+1)
            fill_fraction = fill_count[1:] / prev_comp.area_pixels.to_numpy()
            fill_map = dict(zip(prev_comp.component_id, fill_fraction))
            del rgb, indices, left, extreme
            for threshold in [.1, .25, .5]:
                kept = edges[(edges.intersection_pixels >= 10) & (edges.overlap_over_min_area >= threshold)]
                outdegree = kept.groupby('source_component').size()
                indegree = kept.groupby('target_component').size()
                source_ids = prev_comp.loc[prev_comp.area_pixels >= args.min_area, 'component_id']
                target_ids = comp.loc[comp.area_pixels >= args.min_area, 'component_id']
                summaries.append(dict(source_image=prev_image, target_image=image, min_overlap_fraction=threshold,
                    source_components=len(source_ids), target_components=len(target_ids), edges=len(kept),
                    source_without_overlap=int((~source_ids.isin(outdegree.index)).sum()),
                    target_without_overlap=int((~target_ids.isin(indegree.index)).sum()),
                    source_multiple_targets=int((outdegree > 1).sum()), target_multiple_sources=int((indegree > 1).sum())))
                if threshold != .25:
                    continue
                successors = kept.groupby('source_component').target_component.agg(list).to_dict()
                next_records = obs.set_index('source_row')
                prev_details = prev_comp.set_index('component_id')
                for rec in prev_obs.to_dict('records'):
                    source_id = rec['component_id']
                    present = rec['source_row'] in next_records.index
                    target_id = next_records.loc[rec['source_row'], 'component_id'] if present else np.nan
                    targets = successors.get(source_id, [])
                    if pd.isna(source_id):
                        category = 'source_bbox_unresolved'
                    elif present:
                        category = 'continued_row_with_overlap' if target_id in targets else 'continued_row_without_overlap'
                    else:
                        category = 'row_absent_but_mask_overlap' if targets else 'row_absent_no_mask_overlap'
                    event = dict(source_image=prev_image, target_image=image, source_row=rec['source_row'],
                        source_component=source_id, archived_next_row_present=present,
                        archived_target_component=target_id, candidate_target_components=';'.join(map(str, targets)),
                        candidate_successors=len(targets), category=category,
                        target_rgb_extreme_fraction_at_source=fill_map.get(source_id, np.nan),
                        source_col=rec['col']+ROI.col_off, source_top=rec['row']+ROI.row_off)
                    if pd.notna(source_id):
                        details = prev_details.loc[source_id]
                        event.update(width=details.width, height=details.height, source_area=details.area_pixels)
                    events.append(event)
            del previous
        previous, prev_comp, prev_obs, prev_image = labels, comp, obs, image
        gc.collect()
    pd.concat(components).to_csv(args.output / 'connected_components.csv', index=False)
    archive = pd.concat(archives)
    archive.to_csv(args.output / 'archived_component_links.csv', index=False)
    pd.concat(all_edges).to_csv(args.output / 'adjacent_mask_overlap_edges.csv', index=False)
    pd.DataFrame(summaries).to_csv(args.output / 'overlap_threshold_sensitivity.csv', index=False)
    ev = pd.DataFrame(events)
    ev.to_csv(args.output / 'archived_transition_screen.csv', index=False)
    ev.groupby(['source_image', 'target_image', 'category']).size().rename('n').reset_index().to_csv(
        args.output / 'archived_transition_summary.csv', index=False)
    audit = dict(connectivity=8, roi_col_row_width_height=[10000, 4000, 15000, 18000],
        min_area_pixels=args.min_area, min_intersection_pixels=10, overlap_fraction_for_event_screen=.25,
        component_total=sum(map(len, components)), archive_observations=len(archive),
        exact_component_bbox_matches=int(archive.component_id.notna().sum()),
        transition_categories=ev.category.value_counts().to_dict(),
        high_fill_screen_n=int((ev.target_rgb_extreme_fraction_at_source >= .95).sum()),
        interpretation='Unregistered pixel-overlap candidates, conditional on existing masks and area threshold. '
        'Multiple links are not proven mergers or splits; absent rows are not deaths. '
        'Exact black/white RGB is a fill heuristic, not an independently validated coverage mask.')
    (args.output / 'mask_transition_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps(audit, indent=2), flush=True)


if __name__ == '__main__':
    main()
