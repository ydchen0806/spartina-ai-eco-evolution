"""Freeze a stratified random RGB annotation pilot independent of old masks.

Two tiles per geographic stratum, all 15 dates; no model-based resampling.
This is a pilot design, not a completed segmentation validation.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import rasterio
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--metadata-output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'images').mkdir(exist_ok=True)
    args.metadata_output.mkdir(parents=True, exist_ok=True)
    existing = args.output / 'sample_manifest.csv'
    if existing.exists():
        raise SystemExit('Frozen manifest already exists; use a new output directory for a revised protocol.')
    cells = []
    for row in range(0, 18000, 512):
        for col in range(0, 15000, 512):
            width, height = min(512, 15000-col), min(512, 18000-row)
            sx, sy = min(3, int((col+width/2)/3750)), min(3, int((row+height/2)/4500))
            role = {0: 'development', 1: 'validation', 2: 'development', 3: 'test'}[(sx+sy) % 4]
            cells.append(dict(tile_id=f'r{row:05d}_c{col:05d}', roi_col=col, roi_row=row,
                full_col=col+10000, full_row=row+4000, width=width, height=height,
                stratum=sy*4+sx, split=role))
    frame = pd.DataFrame(cells)
    rng = np.random.default_rng(20261008)
    selected = []
    for stratum, group in frame.groupby('stratum', sort=True):
        sample = group.loc[rng.choice(group.index, size=2, replace=False)].copy()
        sample['inclusion_probability'] = 2/len(group)
        sample['design_weight'] = len(group)/2
        selected.append(sample)
    sites = pd.concat(selected).sort_values(['stratum', 'tile_id']).reset_index(drop=True)
    # Split is attached to the entire geographic stratum across every date.
    # Delineate training exclusions using expanded bounding rectangles of held-out frame tiles.
    held_rects = []
    for _, g in frame[frame.split != 'development'].groupby('stratum'):
        held_rects.append((int(g.roi_col.min()), int(g.roi_row.min()),
            int((g.roi_col+g.width).max()), int((g.roi_row+g.height).max())))
    allowed = []
    for rec in sites.itertuples():
        yy, xx = np.mgrid[rec.roi_row:rec.roi_row+rec.height, rec.roi_col:rec.roi_col+rec.width]
        safe = np.ones(xx.shape, bool) if rec.split == 'development' else np.zeros(xx.shape, bool)
        for x0, y0, x1, y1 in held_rects:
            safe &= ~((xx >= x0-1024) & (xx < x1+1024) & (yy >= y0-1024) & (yy < y1+1024))
        allowed.append(float(safe.mean()))
    sites['development_fraction_outside_holdout_buffer'] = allowed
    source_cols = pd.read_csv(ROOT / 'data/source/original_pipeline/result_size.csv', nrows=0).columns[1:]
    names = [Path(c).name for c in source_cols]
    records = []
    for image in names:
        with rasterio.open(args.source / 'imagery_georeferenced' / image) as ds:
            for rec in sites.to_dict('records'):
                case_id = image.removesuffix('.tif') + '_' + rec['tile_id']
                arr = ds.read([1, 2, 3], window=Window(rec['full_col'], rec['full_row'], rec['width'], rec['height']))
                path = args.output / 'images' / (case_id+'.png')
                Image.fromarray(arr.transpose(1, 2, 0)).save(path)
                records.append(dict(rec, case_id=case_id, image=image, image_path='images/'+path.name,
                                    png_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        print(image, 'exported', len(sites), 'mask-independent sampled windows', flush=True)
    manifest = pd.DataFrame(records)
    frame.to_csv(args.output / 'sampling_frame.csv', index=False)
    sites.to_csv(args.output / 'sampled_sites.csv', index=False)
    manifest.to_csv(existing, index=False)
    for name in ['sampling_frame.csv', 'sampled_sites.csv', 'sample_manifest.csv']:
        (args.metadata_output / name).write_bytes((args.output / name).read_bytes())
    config = dict(seed=20261008, frame_tiles=len(frame), strata=16, sites_per_stratum=2,
        sampled_sites=len(sites), dates=len(names), sampled_tile_dates=len(manifest), tile_side_pixels=512,
        roi_col_row_width_height=[10000, 4000, 15000, 18000],
        split_site_counts=sites.split.value_counts().to_dict(), development_buffer_pixels=1024,
        holdout_rectangles_roi_colrow=held_rects,
        expert_labels_completed=0, historical_training_overlap='Unknown; missing original training RGB prevents verification.',
        units='Sampling units are tiles within this ROI, repeated across dates. Pixel masks are never read by this script.',
        inference='Known tile inclusion probabilities support future design-weighted totals within the frame; '
                  'do not claim unbiased precision/recall ratios, complete-site coverage, or validated ground truth.',
        test_use='Freeze for a new model. Expert test labels must be sequestered from training and model choice. '
                 'All dates of a spatial stratum stay in the same split. Exclude development pixels within 1024 px of held-out strata.',
        limitations='Pilot size, not powered confirmatory sample. Partial edge tiles retain native dimensions. '
                    'No filtering by vegetation visibility, old mask positivity, season or fill. '
                    'Spatial separation does not establish independence from historical segmenter training.')
    for dest in [args.output, args.metadata_output]:
        (dest / 'sampling_protocol.json').write_text(json.dumps(config, indent=2)+'\n')
    items = manifest[['case_id', 'image_path', 'width', 'height']].to_dict('records')
    template = (ROOT / 'templates/annotation_pilot.html').read_text()
    (args.output / 'index.html').write_text(template.replace('__SAMPLES_JSON__', json.dumps(items)))
    print(json.dumps(config, indent=2))


if __name__ == '__main__':
    main()
