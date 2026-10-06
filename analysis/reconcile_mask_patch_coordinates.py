#!/usr/bin/env python3
"""Test the crop/bounding-box convention inferred from 2014 on all mask dates.

The fixed hypothesis is row=archive_x+4000, col=archive_y+10000;
ROI rows [4000,22000), cols [10000,25000). No per-date fit is used.
Areas are independent foreground counts within external contours, not assumed
identical to the legacy extraction algorithm. This does not validate biological
parentage or temporal matching.
"""
import argparse,json,warnings
from pathlib import Path
import cv2,numpy as np,pandas as pd,rasterio
from rasterio.windows import Window
from rasterio.errors import NotGeoreferencedWarning
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 out=args.output;out.mkdir(parents=True,exist_ok=True);cv2.setNumThreads(2)
 warnings.filterwarnings('ignore',category=NotGeoreferencedWarning)
 release=Path(__file__).resolve().parents[1];src=release/'data/source/original_pipeline'
 sizes=pd.read_csv(src/'result_size.csv');pos=pd.read_csv(src/'result_pos.csv');summary=[];allrows=[]
 for col in [c for c in sizes.columns if '.tif' in c]:
  name=Path(col).name
  with rasterio.open(args.source/'mask'/name) as ds:a=ds.read(1,window=Window(10000,4000,15000,18000))
  cs,_=cv2.findContours(a,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);records=[]
  for c in cs:
   x,y,w,h=cv2.boundingRect(c)
   stencil=np.zeros((h,w),dtype=np.uint8);cv2.drawContours(stencil,[c-np.array([[[x,y]]])],-1,1,-1)
   component=(a[y:y+h,x:x+w]>0)&(stencil>0)
   pixels=int(component.sum())
   exclusive=int(component[:-1,:-1].sum())
   bbox_exclusive=int((a[y:y+h-1,x:x+w-1]>0).sum())
   records.append({'archive_y':x,'archive_x':y,'recovered_pixels':pixels,'exclusive_max_pixels':exclusive,'bbox_exclusive_max_pixels':bbox_exclusive,'width':w,'height':h,'touches_roi_edge':x==0 or y==0 or x+w==a.shape[1] or y+h==a.shape[0]})
  extracted=pd.DataFrame(records)
  archived=pd.DataFrame({'source_row':sizes.index,'archive_x':pos[col+'x'],'archive_y':pos[col+'y'],'archived_size':sizes[col]})
  archived=archived[archived.archived_size>0]
  ambiguous=extracted.duplicated(['archive_x','archive_y'],keep=False)
  ambiguous_keys=set(map(tuple,extracted.loc[ambiguous,['archive_x','archive_y']].to_numpy()))
  extracted=extracted.loc[~ambiguous]
  m=archived.merge(extracted,on=['archive_x','archive_y'],how='left',validate='many_to_one');m['image']=name
  m['ambiguous_bbox']=list(map(lambda xy:xy in ambiguous_keys,map(tuple,m[['archive_x','archive_y']].to_numpy())))
  m['absolute_pixel_difference']=m.recovered_pixels-m.archived_size
  m['relative_pixel_difference']=m.absolute_pixel_difference/m.archived_size
  m['full_image_row']=m.archive_x+4000;m['full_image_col']=m.archive_y+10000
  m['role']='coordinate_hypothesis_discovery' if name=='201408ddyw.tif' else 'fixed_coordinate_hypothesis_validation'
  allrows.append(m)
  matched=m.recovered_pixels.notna()
  row={'image':name,'role':m.role.iloc[0],'archived_n':len(m),'exact_bbox_matched_n':int(matched.sum()),'matched_fraction':float(matched.mean()),'exact_area_matched_n':int((m.absolute_pixel_difference==0).sum()),'exclusive_max_area_matched_n':int((m.exclusive_max_pixels==m.archived_size).sum()),'bbox_exclusive_max_area_matched_n':int((m.bbox_exclusive_max_pixels==m.archived_size).sum()),'ambiguous_bbox_n':int(m.ambiguous_bbox.sum()),'median_relative_area_difference':float(m.relative_pixel_difference.median()),'median_absolute_relative_area_difference':float(m.relative_pixel_difference.abs().median()),'roi_foreground_pixels':int((a>0).sum())}
  summary.append(row);print(row,flush=True)
 matches=pd.concat(allrows)
 matches.to_csv(out/'mask_patch_coordinate_matches.csv',index=False)
 matches.loc[matches.bbox_exclusive_max_pixels!=matches.archived_size].to_csv(out/'mask_patch_unresolved_records.csv',index=False)
 df=pd.DataFrame(summary);df.to_csv(out/'mask_patch_coordinate_summary.csv',index=False)
 audit={'fixed_roi_col_row_width_height':[10000,4000,15000,18000],'archive_coordinate_role':'bounding-box top-left; x is row, y is column','discovery_date':'201408ddyw.tif','validation_dates':14,'records':int(df.archived_n.sum()),'exact_bbox_matches':int(df.exact_bbox_matched_n.sum()),'exact_area_matches':int(df.exact_area_matched_n.sum()),'exclusive_max_area_matches':int(df.exclusive_max_area_matched_n.sum()),'bbox_exclusive_max_area_matches':int(df.bbox_exclusive_max_area_matched_n.sum()),'interpretation':'Tests raster-to-table coordinate provenance. Source pixel masks are not independent ground truth; area extraction differences and trajectory biological identity remain to be audited.'}
 (out/'mask_patch_coordinate_audit.json').write_text(json.dumps(audit,indent=2))
 fig,axes=plt.subplots(2,1,figsize=(10,6),layout='constrained',sharex=True)
 axes[0].bar(range(15),df.matched_fraction,color='#176B87');axes[0].set(ylabel='Exact bounding-box match fraction',ylim=(0,1.07));axes[0].axvspan(-.5,.5,color='gray',alpha=.15)
 axes[1].plot(range(15),100*df.median_relative_area_difference,'o-',color='#D55E00');axes[1].axhline(0,color='gray',lw=.6);axes[1].set_ylabel('Median area difference (%)')
 axes[1].set_xticks(range(15),df.image.str.replace('.tif','',regex=False),rotation=60,ha='right');fig.suptitle('Fixed crop convention links recovered masks to archived patch tables')
 fig.savefig(out/'mask_patch_coordinate_validation.pdf');fig.savefig(out/'mask_patch_coordinate_validation.png',dpi=180);plt.close(fig)
 print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
