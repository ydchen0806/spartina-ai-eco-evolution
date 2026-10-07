"""Summarize CCAV V4 on fixed site footprints; map agreement is not validation."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds,Window
from rasterio.warp import reproject,Resampling,transform_bounds
from rasterio.transform import from_origin
from pyproj import Transformer

FULL=(117.404195622047,23.9134768474132,117.432930102047,23.9374309174132)
ROI=(FULL[0]+10000*1.08e-6,FULL[3]-22000*9.8e-7,FULL[0]+25000*1.08e-6,FULL[3]-4000*9.8e-7)
NAMES={0:'Undocumented zero',1:'S. alterniflora',2:'Suaeda spp.',3:'P. australis',4:'T. chinensis',5:'S. mariqueter',6:'Mangroves',255:'No data / unmapped'}
COLORS=['#c44e52','#ddad39','#4c956c','#927653','#8172b3','#178a9b']

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    inv=[];rows=[];maps={};grids={};transitions=[]
    to_geo=Transformer.from_crs(32650,4326,always_xy=True)
    # A common 10 m UTM grid. Four phases diagnose discretization, not classification error.
    for footprint,bounds in [('full_image',FULL),('historical_roi',ROI)]:
        west,south,east,north=transform_bounds(4326,32650,*bounds,densify_pts=21)
        for sx,sy in [(0,0),(5,0),(0,5),(5,5)]:
            left=np.floor(west/10)*10-10+sx;top=np.ceil(north/10)*10+10+sy
            width=int(np.ceil((east-left)/10))+1;height=int(np.ceil((top-south)/10))+1
            transform=from_origin(left,top,10,10)
            yy,xx=np.indices((height,width));lon,lat=to_geo.transform(left+(xx+.5)*10,top-(yy+.5)*10)
            inside=(lon>=bounds[0])&(lon<bounds[2])&(lat>=bounds[1])&(lat<bounds[3])
            for path in sorted(args.source.glob('CCAV-10m_*.tif')):
                year=int(path.stem.rsplit('_',1)[-1])
                with rasterio.open(path) as src:
                    sb=transform_bounds(4326,src.crs,*bounds,densify_pts=21)
                    win=from_bounds(*sb,transform=src.transform)
                    c0=int(np.floor(win.col_off))-3;r0=int(np.floor(win.row_off))-3
                    win=Window(c0,r0,int(np.ceil(win.width))+7,int(np.ceil(win.height))+7)
                    data=src.read(1,window=win,boundless=True,fill_value=255)
                    values=np.unique(data)
                    assert set(values).issubset(NAMES),values
                    target=np.full((height,width),255,dtype=np.uint8)
                    reproject(data,target,src_transform=src.window_transform(win),src_crs=src.crs,
                        src_nodata=src.nodata,dst_transform=transform,dst_crs='EPSG:32650',dst_nodata=255,
                        resampling=Resampling.nearest)
                    target[~inside]=255
                    if footprint=='full_image' and sx==sy==0:
                        inv.append(dict(year=year,source_file=path.name,width=src.width,height=src.height,
                            crs=str(src.crs),nodata=src.nodata,transform=list(src.transform),local_values=values.tolist()))
                for value in NAMES:
                    n=int(np.sum((target==value)&inside))
                    rows.append(dict(footprint=footprint,shift_x_m=sx,shift_y_m=sy,year=year,
                        code=value,label=NAMES[value],pixels=n,area_ha=n*.01,footprint_pixels=int(inside.sum())))
                if sx==sy==0:
                    maps[(footprint,year)]=target;grids[footprint]=(transform,inside)
                    with rasterio.open(out/f'ccav_{footprint}_{year}.tif','w',driver='GTiff',height=height,width=width,
                        count=1,dtype='uint8',crs='EPSG:32650',transform=transform,nodata=255,compress='deflate') as dst:
                        dst.write(target,1);dst.update_tags(source='CCAV-10m V4; DOI:10.57760/sciencedb.31077',license='CC-BY-4.0',attribution='Yuying Li et al. (2026)',resampling='nearest',interpretation='Classified context, not locally validated vegetation truth')
        inside=grids[footprint][1]
        for year in range(2016,2023):
            a=maps[(footprint,year)];b=maps[(footprint,year+1)]
            for av in NAMES:
                for bv in NAMES:
                    n=int(np.sum(inside&(a==av)&(b==bv)))
                    if n:transitions.append(dict(footprint=footprint,year0=year,year1=year+1,code0=av,code1=bv,pixels=n,area_ha=.01*n))
    d=pd.DataFrame(rows);d.to_csv(out/'annual_class_areas_grid_sensitivity.csv',index=False)
    base=d[(d.shift_x_m==0)&(d.shift_y_m==0)];base.to_csv(out/'annual_class_areas.csv',index=False)
    pd.DataFrame(transitions).to_csv(out/'annual_class_transitions.csv',index=False)
    (out/'raster_inventory.json').write_text(json.dumps(inv,indent=2)+'\n')
    check=[]
    for key,g in d.groupby(['footprint','shift_x_m','shift_y_m','year']):
        assert g.pixels.sum()==g.footprint_pixels.iloc[0],key
        check.append(True)
    for footprint in ['full_image','historical_roi']:
        # Each categorical transition table partitions exactly the same footprint.
        t=pd.DataFrame(transitions).query('footprint == @footprint')
        assert (t.groupby('year0').pixels.sum()==int(grids[footprint][1].sum())).all()
    report={'doi':'10.57760/sciencedb.31077','version':'V4','license':'CC-BY-4.0',
       'source_files':len(inv),'footprints_wgs84':{'full_image':FULL,'historical_roi':ROI},
       'output_crs':'EPSG:32650','resolution_m':10,'resampling':'nearest',
       'grid_phases_m':[[0,0],[5,0],[0,5],[5,5]],'partitions_checked':len(check),
       'area_interpretation':'Projected pixel area (0.01 ha); not error-adjusted ecological area.',
       'limits':['Source grids differ by year; nearest-neighbour reprojection used.',
         'Grid-phase range is not an accuracy confidence interval.',
         'Nodata 255 is unclassified; no inference of bare substrate or death.',
         'CCAV sample split unknown and includes training data; no independent validation.',
         'Satellite annual class change is not an individual demographic transition.',
         'UAV acquisition dates differ from annual satellite composites; no contemporaneous accuracy inference.']}
    (out/'raster_analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    fig,axs=plt.subplots(2,4,figsize=(12,7),layout='constrained')
    cmap=ListedColormap(['#d9dce0']+COLORS)
    for ax,year in zip(axs.flat,range(2016,2024)):
        a=maps[('full_image',year)].copy();a[a==255]=0
        ax.imshow(a,cmap=cmap,vmin=0,vmax=6,interpolation='nearest');ax.set_title(str(year));ax.axis('off')
    fig.legend(handles=[Patch(color=cmap(i),label=NAMES[i] if i else 'Unmapped / no data') for i in range(7)],loc='outside lower center',ncol=4,frameon=False)
    for ext in ['png','pdf','svg']:fig.savefig(out/f'ccav_annual_site_maps.{ext}',dpi=220)
    plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for ax,fp,title in zip(axs,['full_image','historical_roi'],['Full image footprint','Historical patch ROI']):
        for code,col in [(1,COLORS[0]),(6,COLORS[5])]:
            g=d[(d.footprint==fp)&(d.code==code)].groupby('year').area_ha.agg(['min','max'])
            b=base[(base.footprint==fp)&(base.code==code)].sort_values('year')
            ax.plot(b.year,b.area_ha,'o-',color=col,label=NAMES[code])
            ax.fill_between(g.index,g['min'],g['max'],color=col,alpha=.2)
        ax.set(title=title,xlabel='Map year',ylabel='Classified area (ha)');ax.legend(frameon=False)
    fig.supxlabel('Shading: four grid phases; classification uncertainty is not estimated',fontsize=8)
    for ext in ['png','pdf','svg']:fig.savefig(out/f'ccav_classified_area.{ext}',dpi=220)
    print(base[base.code.isin([1,6,255])].to_string(index=False))

if __name__=='__main__':main()
