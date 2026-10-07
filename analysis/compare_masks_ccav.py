"""Compare recovered isolated-patch foreground with annual CCAV map classes.

This is agreement between two unvalidated measurements at different scales,
not a species-accuracy assessment. No raw inputs are modified.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window
from pyproj import Transformer


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--masks',type=Path,required=True)
    ap.add_argument('--ccav',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    transform=Transformer.from_crs(4326,32650,always_xy=True)
    rows=[]
    for path in sorted(args.masks.glob('*.tif')):
        if not path.name[:4].isdigit():continue
        year=int(path.name[:4]);cp=args.ccav/f'ccav_historical_roi_{year}.tif'
        if not cp.exists():continue
        with rasterio.open(cp) as sat:
            a=sat.read(1);inv=~sat.transform
        counts={k:0 for k in [0,1,2,3,4,5,6,255]};unassigned=0;total=0
        with rasterio.open(path) as src:
            assert src.shape==(24443,26606)
            for start in range(4000,22000,1000):
                mask=src.read(1,window=Window(10000,start,15000,min(1000,22000-start)))
                rr,cc=np.nonzero(mask);total+=len(rr)
                lon=117.404195622047+(cc+10000+.5)*1.08e-6
                lat=23.9374309174132-(rr+start+.5)*9.8e-7
                x,y=transform.transform(lon,lat)
                col=np.floor(inv.a*x+inv.b*y+inv.c).astype(int)
                row=np.floor(inv.d*x+inv.e*y+inv.f).astype(int)
                valid=(col>=0)&(col<a.shape[1])&(row>=0)&(row<a.shape[0])
                unassigned+=int((~valid).sum())
                vals,n=np.unique(a[row[valid],col[valid]],return_counts=True)
                for v,k in zip(vals,n):counts[int(v)]+=int(k)
        assert sum(counts.values())+unassigned==total
        for code,n in counts.items():rows.append(dict(image=path.name,year=year,ccav_code=code,
            mask_foreground_pixels=n,total_mask_foreground_pixels=total,fraction=n/total if total else None,
            out_of_grid_foreground_pixels=unassigned))
        print(path.name,'foreground',total,'Spartina',round(counts[1]/total,3),'mangrove',round(counts[6]/total,3),flush=True)
    d=pd.DataFrame(rows);d.to_csv(args.output/'isolated_mask_ccav_agreement.csv',index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    pivot=d.pivot(index='image',columns='ccav_code',values='fraction')
    fig,ax=plt.subplots(figsize=(10,4),layout='constrained')
    bottom=np.zeros(len(pivot))
    for code,label,col in [(1,'Satellite: Spartina','#c44e52'),(6,'Satellite: mangroves','#178a9b'),(3,'Satellite: Phragmites','#4c956c'),(255,'Satellite: unmapped','#d9dce0')]:
        ax.bar(np.arange(len(pivot)),pivot[code],bottom=bottom,color=col,label=label)
        bottom+=pivot[code].to_numpy()
    assert np.allclose(bottom,1), 'Plot needs additional observed classes'
    ax.set(xticks=np.arange(len(pivot)),xticklabels=[x[:8] for x in pivot.index],
        ylabel='Fraction of isolated-mask foreground',ylim=(0,1),
        title='Agreement across observation scales; neither product is local ground truth')
    ax.tick_params(axis='x',rotation=45);ax.spines[['top','right']].set_visible(False)
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.24),ncol=4,frameon=False,fontsize=8)
    for ext in ['png','pdf','svg']:fig.savefig(args.output/f'isolated_mask_ccav_agreement.{ext}',dpi=220)
    # Independently extracted component areas must sum to the same ROI foreground.
    archive=Path(__file__).resolve().parents[1]/'data/derived/trajectory_audit_20261007/connected_components.csv'
    components=pd.read_csv(archive).groupby('image').area_pixels.sum()
    for image,g in d.groupby('image'):assert int(components.loc[image])==g.total_mask_foreground_pixels.iloc[0]
    (args.output/'mask_comparison.json').write_text(json.dumps({'dates':int(d.image.nunique()),
        'source':'recovered 15-date masks; historical ROI; foreground pixel centres projected to CCAV common grid',
        'count_conservation':True,'independent_component_area_totals_match':True,
        'limitations':['Both products unvalidated locally; agreement is not accuracy.',
            'Annual composites differ from individual UAV dates.',
            'Header coordinates assumed; absolute georeferencing not independently verified.',
            'Small patches below 10m support can occur within other satellite classes.',
            'No pixels from the frozen expert-validation pilot were labelled or used for tuning.']},indent=2)+'\n')

if __name__=='__main__':main()
