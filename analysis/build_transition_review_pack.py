"""Export a seeded diagnostic review sample; this is not a prevalence sample."""
import argparse
import json
import html
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import rasterio
from rasterio.errors import NotGeoreferencedWarning
from rasterio.windows import Window


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--audit', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for sub in ['raw_pairs', 'overlay_pairs']:
        (args.output / sub).mkdir(exist_ok=True)
    warnings.filterwarnings('ignore', category=NotGeoreferencedWarning)
    df = pd.read_csv(args.audit / 'archived_transition_screen.csv')
    rng = np.random.default_rng(20261007)
    choices = []
    for _, group in df.groupby(['source_image', 'category'], sort=True):
        choices.append(int(rng.choice(group.index.to_numpy())))
    high_fill = df[df.target_rgb_extreme_fraction_at_source >= .95]
    if len(high_fill):
        choices.extend(rng.choice(high_fill.index, min(4, len(high_fill)), replace=False).tolist())
    selected = df.loc[sorted(set(choices))].copy().reset_index(drop=True)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    records = []
    for i, rec in selected.iterrows():
        case = f'case_{i+1:03d}'
        w = rec.width if pd.notna(rec.width) else 100
        h = rec.height if pd.notna(rec.height) else 100
        side = int(max(512, min(1024, max(w, h)+160)))
        col = int(np.clip(rec.source_col + w/2 - side/2, 0, 26606-side))
        row = int(np.clip(rec.source_top + h/2 - side/2, 0, 24443-side))
        window = Window(col, row, side, side)
        raw_panels, overlay_panels = [], []
        for name in [rec.source_image, rec.target_image]:
            with rasterio.open(args.source / 'imagery_georeferenced' / name) as ds:
                rgb = ds.read([1, 2, 3], window=window).transpose(1, 2, 0)
            with rasterio.open(args.source / 'mask' / name) as ds:
                mask = ds.read(1, window=window) > 0
            overlay = rgb.copy()
            overlay[mask] = (overlay[mask]*.55 + np.array([255, 0, 180])*.45).astype('uint8')
            for panels, array in [(raw_panels, rgb), (overlay_panels, overlay)]:
                im = Image.fromarray(array).resize((512, 512))
                canvas = Image.new('RGB', (512, 545), 'white')
                canvas.paste(im, (0, 33))
                ImageDraw.Draw(canvas).text((8, 8), f'{case} | {name}', fill='black', font=font)
                panels.append(canvas)
        for sub, panels in [('raw_pairs', raw_panels), ('overlay_pairs', overlay_panels)]:
            canvas = Image.new('RGB', (1024, 545), 'white')
            for j, panel in enumerate(panels):
                canvas.paste(panel, (j*512, 0))
            canvas.save(args.output / sub / (case+'.png'))
        item = rec.to_dict()
        item.update(case_id=case, window_col=col, window_row=row, window_side_pixels=side)
        records.append(item)
    manifest = pd.DataFrame(records)
    manifest.to_csv(args.output / 'diagnostic_sample_manifest.csv', index=False)
    form = manifest[['case_id', 'source_image', 'target_image']].copy()
    for col in ['reviewer', 'source_patch_visible', 'target_patch_visible', 'alignment_problem',
                'fill_or_coverage_problem', 'possible_merge', 'possible_split', 'identity_confidence', 'notes']:
        form[col] = ''
    form.to_csv(args.output / 'blank_review_form.csv', index=False)
    (args.output / 'README.md').write_text('''# Diagnostic transition review pack

Seed: 20261007. One random archived observation is sampled per source survey and
automated screening category, plus up to four high-fill cases. This deliberately
enriched sample is for discovering failure modes; it cannot estimate event
prevalence, segmentation accuracy or generalization performance.

Start with `raw_pairs/` and `blank_review_form.csv`. These pairs show the same
array-index window in successive original orthomosaics. They have not been
registered. Open `overlay_pairs/` only after an initial RGB review; pink marks
the archived binary mask. `diagnostic_sample_manifest.csv` contains the screening
categories and full-image window coordinates. The window is centred on the
source bounding box, not necessarily the next archived coordinate. Month-only
survey filenames do not establish a known acquisition day.

All forms are blank: no expert annotation or independent performance estimate
is implied. A subsequent probability sample including old-mask-negative regions
is required for formal validation. Preserve ambiguous and unobservable cases;
do not force death/merger labels from missing masks.
''')
    (args.output / 'sample_audit.json').write_text(json.dumps(dict(seed=20261007, cases=len(manifest),
        category_counts=manifest.category.value_counts().to_dict(), expert_labels_completed=0), indent=2)+'\n')
    cards = []
    for rec in manifest.to_dict('records'):
        case = rec['case_id']
        caption = html.escape(str(rec['source_image']) + ' → ' + str(rec['target_image']))
        cards.append(f'<article><h2>{case}</h2><p>{caption}</p><a href="raw_pairs/{case}.png"><img loading="lazy" src="raw_pairs/{case}.png" data-case="{case}" alt="{caption}"></a></article>')
    page = """<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>斑块连续影像复核</title>
+<style>body{font-family:system-ui,sans-serif;background:#f5f6f7;color:#172b3a;margin:24px;max-width:1400px}header{position:sticky;top:0;background:#f5f6f7;padding:12px 0;z-index:1}h1{font-size:25px}h2{font-size:17px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(480px,1fr));gap:20px}article{padding:15px;background:white;border:1px solid #dae0e5;border-radius:8px}img{width:100%;height:auto}a{color:#126683}p{line-height:1.6}@media(max-width:550px){main{grid-template-columns:1fr}body{margin:10px}}</style>
+<header><h1>斑块连续影像复核 · 诊断样本</h1><p>前后影像展示同一像素窗口，尚未配准。样本按异常类别抽取，不能用来估计事件发生率。请先查看原图并填写复核表，再打开 mask 叠加。</p><label><input type="checkbox" id="overlay"> 显示历史 mask（粉色）</label>　<a href="blank_review_form.csv">下载空白复核表</a>　<a href="README.md">抽样与解释说明</a></header><main>""".replace('\n+', '\n')
    page += ''.join(cards) + """</main><script>document.getElementById('overlay').addEventListener('change',e=>{document.querySelectorAll('img[data-case]').forEach(img=>{img.src=(e.target.checked?'overlay_pairs/':'raw_pairs/')+img.dataset.case+'.png';img.parentElement.href=img.src})})</script></html>"""
    (args.output / 'index.html').write_text(page)
    print('Exported diagnostic cases:', len(manifest), flush=True)


if __name__ == '__main__':
    main()
