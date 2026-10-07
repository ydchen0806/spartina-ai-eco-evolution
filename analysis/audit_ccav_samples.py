"""Audit official CCAV V4 sample provenance and eligibility for local validation.

No model accuracy is estimated: sample train/test membership is unavailable.
"""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

BOUNDS = (117.404195622047, 23.9134768474132, 117.432930102047, 23.9374309174132)
LABELS = ['S. alterniflora', 'Suaeda spp.', 'P. australis', 'T. chinensis', 'S. mariqueter', 'mangroves']
COLORS = ['#c44e52','#ddad39','#4c956c','#927653','#8172b3','#178a9b']


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--listing',type=Path,required=True)
    ap.add_argument('--legacy',type=Path)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    payload=args.source.read_bytes(); md5=hashlib.md5(payload).hexdigest()
    records=json.loads(args.listing.read_text())['data']
    official=next(x for x in records if x['fileName']==args.source.name)
    assert md5==official['md5'] and len(payload)==official['size']
    d=pd.read_excel(args.source)
    assert d.columns.tolist()==['ID','Name','Time','Longitude','Latitude']
    assert d[['Longitude','Latitude','Time','Name']].notna().all().all()
    d['class']=d.Name.str.strip()
    assert set(d['class'])==set(LABELS)
    assert d.ID.is_unique
    key=['Longitude','Latitude','Time','class']
    unique=d.drop_duplicates(key).copy()
    unique['source_multiplicity']=unique.set_index(key).index.map(d.groupby(key).size())
    x0,y0,x1,y1=BOUNDS
    d['inside_image']=d.Longitude.between(x0,x1)&d.Latitude.between(y0,y1)
    unique['inside_image']=unique.Longitude.between(x0,x1)&unique.Latitude.between(y0,y1)
    groups=d.groupby(['Longitude','Latitude','Time'])['class'].nunique()
    counts=pd.DataFrame({'raw_rows':d.groupby('class').size(),
        'unique_coordinate_year_class':unique.groupby('class').size()}).reindex(LABELS)
    counts['excess_duplicate_rows']=counts.raw_rows-counts.unique_coordinate_year_class
    counts.to_csv(args.output/'sample_class_counts.csv')
    d.groupby(['Time','class']).size().rename('rows').to_csv(args.output/'sample_year_class_counts.csv')
    local=unique.loc[unique.inside_image].copy()
    transform=Transformer.from_crs(4326,32650,always_xy=True)
    if len(local)>1:
        xy=np.column_stack(transform.transform(local.Longitude.to_numpy(),local.Latitude.to_numpy()))
        nn=cKDTree(xy).query(xy,k=2)[0][:,1]
        local['nearest_distinct_record_m']=nn
    local.to_csv(args.output/'local_unique_samples.csv',index=False)
    unique.to_csv(args.output/'samples_unique_coordinate_year_class.csv',index=False)
    report={'dataset_doi':'10.57760/sciencedb.31077','version':'V4','license':'CC-BY-4.0',
      'attribution':'Yuying Li et al., CCAV-10m (Science Data Bank, V4, 2026)',
      'provider_md5_verified':True,'md5':md5,'sha256':hashlib.sha256(payload).hexdigest(),
      'bytes':len(payload),'raw_rows':len(d),'unique_coordinate_year_class':len(unique),
      'excess_duplicate_rows':len(d)-len(unique),'unique_coordinates':len(d.drop_duplicates(['Longitude','Latitude'])),
      'conflicting_class_coordinate_year_groups':int((groups>1).sum()),
      'image_bounds_wgs84':BOUNDS,'local_raw_rows':int(d.inside_image.sum()),
      'local_unique_coordinate_year_class':len(local),
      'local_unique_coordinates':len(local.drop_duplicates(['Longitude','Latitude'])),
      'local_classes_raw':d.loc[d.inside_image,'class'].value_counts().to_dict(),
      'local_classes_unique':local['class'].value_counts().to_dict(),
      'local_nearest_distinct_record_m_median':float(np.median(nn)) if len(local)>1 else None,
      'legacy_byte_identical':args.legacy.read_bytes()==payload if args.legacy else None,
      'limitations':['Coordinates have no explicit CRS field; WGS84 assumed for overlay.',
       'Exact duplicate records collapsed for audit, not proof of independent plots.',
       'Year-repeat coordinates remain dependent; nearest-distance is diagnostic.',
       'Published 15558 total includes nonpublic samples; public sheet has no split membership.',
       'No independent accuracy metric can be computed from these records.']}
    (args.output/'sample_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    fig,axs=plt.subplots(1,3,figsize=(12,4),layout='constrained')
    for lab,col in zip(LABELS,COLORS):
        sel=unique[unique['class']==lab]
        axs[0].scatter(sel.Longitude,sel.Latitude,s=3,c=col,label=lab,alpha=.55,rasterized=True)
    axs[0].scatter([(x0+x1)/2],[(y0+y1)/2],marker='*',s=90,facecolor='none',edgecolor='black')
    axs[0].set(xlabel='Longitude (°E)',ylabel='Latitude (°N)',title='a  Public sample coordinates')
    axs[0].legend(fontsize=6,markerscale=2,frameon=False)
    ypos=np.arange(6)
    # Counts shown explicitly because most exact duplicate differences are small.
    axs[1].barh(ypos,counts.unique_coordinate_year_class,color=COLORS,label='Unique coordinate–year–class')
    axs[1].set(yticks=ypos,yticklabels=LABELS,xlabel='Records',title='b  Exact duplication audit')
    axs[1].set_xlim(0,3800)
    for i,row in enumerate(counts.itertuples()):
        axs[1].text(row.unique_coordinate_year_class+35,i,f'{row.unique_coordinate_year_class} (−{row.excess_duplicate_rows})',va='center',fontsize=7)
    axs[1].set_xlabel('Unique records (excess duplicates removed)')
    axs[2].scatter(local.Longitude,local.Latitude,s=25,c=COLORS[-1],alpha=.7)
    axs[2].set(xlim=(x0,x1),ylim=(y0,y1),xlabel='Longitude (°E)',ylabel='Latitude (°N)',title='c  Image footprint: mangrove labels only')
    axs[2].ticklabel_format(useOffset=False,axis='both');axs[2].tick_params(axis='x',rotation=30)
    axs[2].text(.03,.97,f'{len(local)} coordinate–year records\n{int(d.inside_image.sum())} original rows\n0 Spartina labels',transform=axs[2].transAxes,va='top',fontsize=8)
    for ext in ['png','pdf','svg']:fig.savefig(args.output/f'ccav_sample_audit.{ext}',dpi=220)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
