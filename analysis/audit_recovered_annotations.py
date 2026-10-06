#!/usr/bin/env python3
"""Verify two annotation deliveries and polygon-to-PNG consistency; not model accuracy."""
import argparse,json
from pathlib import Path
from collections import defaultdict,Counter
import numpy as np
import pandas as pd
from PIL import Image,ImageDraw

def rings_signature(rings):
    canonical=[]
    for ring in rings:
        pts=[]
        for pt in ring:
            pt=tuple(float(v) for v in pt)
            if not pts or pt!=pts[-1]:pts.append(pt)
        if len(pts)>1 and pts[-1]==pts[0]:pts.pop()
        candidates=[]
        for sequence in [pts,pts[::-1]]:
            minimum=min(sequence)
            candidates.extend(tuple(sequence[i:]+sequence[:i]) for i,p in enumerate(sequence) if p==minimum)
        canonical.append(min(candidates))
    return tuple(sorted(canonical))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    root=args.source/'annotations';out=args.output;out.mkdir(parents=True,exist_ok=True)
    singles={}
    for p in (root/'batch_1207').rglob('*.json'):
        d=json.loads(p.read_text(encoding='utf-8-sig'));batch='batch_1129' if '第一期' in d['filePath'] else 'batch_1202'
        key=(batch,Path(d['filePath']).name);assert key not in singles
        singles[key]=d
    rows=[];errors=[]
    for batch in ['batch_1129','batch_1202']:
        p=next((root/batch).rglob('*.json'));coco=json.loads(p.read_text(encoding='utf-8-sig'));byid=defaultdict(list)
        image_ids={x['id'] for x in coco['images']}
        for ann in coco['annotations']:
            if ann['image_id'] not in image_ids: errors.append({'batch':batch,'orphan_annotation_id':ann['id']})
            byid[ann['image_id']].append(ann)
        pngs={p.name:p for p in (root/batch).rglob('*.png')}
        for im in coco['images']:
            key=(batch,im['file_name']);single=singles.get(key);anns=byid[im['id']]
            a=Counter(rings_signature([np.asarray(r).reshape(-1,2).tolist() for r in ann['segmentation']]) for ann in anns)
            b=Counter(rings_signature(obj['coordinates']) for obj in single['dataList']) if single else Counter()
            row={'batch':batch,'image':im['file_name'],'width':im['width'],'height':im['height'],'objects':len(anns),
                 'single_json_present':single is not None,'dimensions_match':bool(single and (single['info']['width'],single['info']['height'])==(im['width'],im['height'])),
                 'polygon_multiset_identical':a==b,'png_iou_with_pil_polygon':None,'out_of_bounds_vertices':0}
            for ann in anns:
                for ring in ann['segmentation']:
                    xy=np.array(ring).reshape(-1,2)
                    row['out_of_bounds_vertices']+=int(((xy[:,0]<0)|(xy[:,0]>im['width'])|(xy[:,1]<0)|(xy[:,1]>im['height'])).sum())
            png=pngs.get(Path(im['file_name']).stem+'.mask.png')
            if png:
                canvas=Image.new('1',(im['width'],im['height']));draw=ImageDraw.Draw(canvas)
                for ann in anns:
                    for ring in ann['segmentation']: draw.polygon(list(map(tuple,np.array(ring).reshape(-1,2))),fill=1)
                expected=np.asarray(canvas,dtype=bool)
                with Image.open(png) as pi: actual=np.asarray(pi.convert('RGB'))[:,:,1]>0
                row['png_iou_with_pil_polygon']=float((actual&expected).sum()/max((actual|expected).sum(),1))
            rows.append(row)
    df=pd.DataFrame(rows);df.to_csv(out/'annotation_encoding_audit.csv',index=False)
    audit={'images':len(df),'objects':int(df.objects.sum()),'polygon_geometry_matches_after_ring_canonicalization':int(df.polygon_multiset_identical.sum()),'dimension_matches':int(df.dimensions_match.sum()),'png_compared':int(df.png_iou_with_pil_polygon.notna().sum()),'png_encoding_iou_min':float(df.png_iou_with_pil_polygon.min()),'png_encoding_iou_median':float(df.png_iou_with_pil_polygon.median()),'out_of_bounds_vertices':int(df.out_of_bounds_vertices.sum()),'orphan_annotations':errors,'interpretation':'Polygon/PNG agreement checks delivery consistency. It is not segmentation model IoU and supplies no train/test independence.'}
    (out/'annotation_audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
