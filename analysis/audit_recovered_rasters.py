#!/usr/bin/env python3
"""Read-only raster audit. No assigned CRS or registration is written to source masks."""
import argparse, json, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window
from rasterio.enums import Resampling
from rasterio.errors import NotGeoreferencedWarning
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();root=args.source;out=args.output;out.mkdir(parents=True,exist_ok=True)
    warnings.filterwarnings('ignore',category=NotGeoreferencedWarning)
    release=Path(__file__).resolve().parents[1]
    sizes=pd.read_csv(release/'data/source/original_pipeline/result_size.csv')
    positions=pd.read_csv(release/'data/source/original_pipeline/result_pos.csv')
    names=[Path(c).name for c in sizes.columns if '.tif' in c]
    rows=[];thumbs=[];maps=[]
    for name in names:
        with rasterio.open(root/'imagery_georeferenced'/name) as rgb, rasterio.open(root/'mask'/name) as mask:
            assert rgb.shape==mask.shape
            hist=np.zeros(256,dtype=np.int64)
            bounds=[mask.width,mask.height,0,0]
            for top in range(0,mask.height,512):
                a=mask.read(1,window=Window(0,top,mask.width,min(512,mask.height-top)))
                hist+=np.bincount(a.ravel(),minlength=256)
                yy,xx=np.where(a>0)
                if len(xx):bounds=[min(bounds[0],int(xx.min())),min(bounds[1],int(yy.min()+top)),max(bounds[2],int(xx.max()+1)),max(bounds[3],int(yy.max()+top+1))]
            small=rgb.read(out_shape=(3,736,800),resampling=Resampling.nearest).transpose(1,2,0)
            ms=mask.read(1,out_shape=(736,800),resampling=Resampling.nearest)>0
            valid=(small>0).any(axis=2) # heuristic only: raster has no nodata
            c='./mask/'+name
            pts=positions.loc[sizes[c]>0,[c+'x',c+'y']].to_numpy()
            # Probe the two natural interpretations; no alignment is imposed.
            hits={}
            for label,xy in [('x_as_column',pts),('x_as_row',pts[:,::-1])]:
                good=(xy[:,0]>=0)&(xy[:,0]<mask.width)&(xy[:,1]>=0)&(xy[:,1]<mask.height)
                # Read strips containing points once each (bounded memory).
                vals=[]
                for y in np.unique(xy[good,1].astype(int)):
                    xs=xy[good & (xy[:,1].astype(int)==y),0].astype(int)
                    strip=mask.read(1,window=Window(0,int(y),mask.width,1))[0]
                    vals.extend((strip[xs]>0).tolist())
                hits[label+'_foreground_fraction']=float(np.mean(vals)) if vals else None
                hits[label+'_in_bounds_n']=int(good.sum())
            row={'image':name,'width':rgb.width,'height':rgb.height,'image_crs':str(rgb.crs),'mask_crs':str(mask.crs),
                 'image_transform':str(tuple(rgb.transform)[:6]),'mask_transform':str(tuple(mask.transform)[:6]),
                 'pixel_width_degrees':rgb.transform.a,'pixel_height_degrees':abs(rgb.transform.e),
                 'foreground_pixels':int(hist[1:].sum()),'foreground_fraction':float(hist[1:].sum()/hist.sum()),
                 'mask_values':json.dumps(np.flatnonzero(hist).tolist()),'foreground_bbox_colrow':json.dumps(bounds),
                 'sampled_rgb_nonblack_fraction':float(valid.mean()),
                 'sampled_foreground_on_black_fraction':float((ms & ~valid).sum()/max(ms.sum(),1)),
                 'archived_patch_count':int((sizes[c]>0).sum()),**hits}
            rows.append(row);thumbs.append(small);maps.append(ms)
            print(name,'mask pixels',row['foreground_pixels'],'position hits',hits,flush=True)
    df=pd.DataFrame(rows);df.to_csv(out/'raster_inventory.csv',index=False)
    fig,axes=plt.subplots(3,5,figsize=(16,9.5),layout='constrained')
    for ax,r,im,ms in zip(axes.flat,rows,thumbs,maps):
        ax.imshow(im); overlay=np.zeros((*ms.shape,4));overlay[ms]=[1,.15,.05,.4];ax.imshow(overlay)
        ax.set_title(r['image'].replace('.tif',''),fontsize=9);ax.axis('off')
    fig.suptitle('Recovered RGB and mask overlays — shared array indices, registration not yet established',fontsize=13)
    fig.savefig(out/'recovered_rgb_mask_contact_sheet.png',dpi=180);fig.savefig(out/'recovered_rgb_mask_contact_sheet.pdf');plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4),layout='constrained')
    ax.plot(range(15),df.foreground_pixels/1e6,'o-',label='Mask foreground (million pixels)')
    ax.set_xticks(range(15),[n.replace('.tif','') for n in names],rotation=60,ha='right');ax.set_ylabel('Foreground pixels (millions)')
    ax.set_title('Full-frame mask totals; changing observation footprint is not corrected')
    fig.savefig(out/'full_frame_mask_totals.pdf');plt.close(fig)
    audit={'pairs':len(rows),'binary_mask_values_all_0_255':bool(all(r['mask_values']=='[0, 255]' for r in rows)),
           'identical_rgb_transforms':bool(df.image_transform.nunique()==1),'all_masks_lack_crs':bool((df.mask_crs=='None').all()),
           'bounds_wgs84':[rgb.bounds.left,rgb.bounds.bottom,rgb.bounds.right,rgb.bounds.top],
           'interpretation':'Array overlays are inspection views, not independent registration validation. Black RGB is a heuristic for absent coverage, not authoritative nodata. Full-frame mask totals are not corrected population or invasion-area estimates.'}
    (out/'raster_audit.json').write_text(json.dumps(audit,indent=2))
if __name__=='__main__':main()
