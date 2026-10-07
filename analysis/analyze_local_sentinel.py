"""Same-season local spectral extension on fixed spatial support, not species validation."""
import argparse,hashlib,json,warnings
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import reproject,Resampling
from scipy.ndimage import binary_erosion
from pyproj import Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from download_local_sentinel import FULL
ROOT=Path(__file__).resolve().parents[1]
ROI=(FULL[0]+10000*1.08e-6,FULL[3]-22000*9.8e-7,FULL[0]+25000*1.08e-6,FULL[3]-4000*9.8e-7)

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=True)
 selected=pd.read_csv(a.source/'selected_scenes.csv');items={f['id']:f for p in a.source.glob('stac_september_*.json') for f in json.loads(p.read_text())['features']}
 manifest=json.loads((a.source/'download_manifest.json').read_text())
 verification=json.loads((a.source/'radiometry_verification.json').read_text());assert verification['selected_scenes']==len(selected)
 assert all(r['all_five_stac_band_conversions_match_xml'] and r['provider_sha256_verified'] for r in verification['records'])
 for rec in manifest['records']:
  p=a.source/'clips'/rec['item']/(rec['asset']+'.tif');assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['sha256']
 with rasterio.open(a.source/'clips'/selected.item.iloc[0]/'red.tif') as src:profile=src.profile.copy();shape=src.shape;tr=src.transform;crs=src.crs
 assert crs.to_epsg()==32650 and tr.a==10 and tr.e==-10
 yy,xx=np.indices(shape);east=tr.c+(xx+.5)*10;north=tr.f-(yy+.5)*10
 lon,lat=Transformer.from_crs(crs,4326,always_xy=True).transform(east,north)
 def box(bounds):return (lon>=bounds[0])&(lon<bounds[2])&(lat>=bounds[1])&(lat<bounds[3])
 inside=box(FULL);roi=box(ROI);sitecell=box((117.425,23.925,117.435,23.935))&inside
 def read(path,resample=False):
  with rasterio.open(path) as src:
   if src.shape==shape and src.transform==tr and src.crs==crs:return src.read(1)
   if not resample:raise AssertionError('10 m grids are not identical: '+str(path))
   d=np.zeros(shape,dtype=src.dtypes[0]);reproject(src.read(1),d,src_transform=src.transform,src_crs=src.crs,dst_transform=tr,dst_crs=crs,src_nodata=src.nodata,dst_nodata=0,resampling=Resampling.nearest);return d
 classes=read(ROOT/'data/derived/ccav_20261007/ccav_full_image_2019.tif',True)
 zones={'full_image':inside,'historical_roi':roi,'baseline_2019_spartina_class':inside&(classes==1),'baseline_2019_mangrove_class':inside&(classes==6),'site10_rounding_cell_intersection':sitecell}
 def save(name,data,dtype='float32',nodata=-9999):
  p=profile.copy();p.update(count=1,dtype=dtype,nodata=nodata,compress='deflate');v=np.where(np.isfinite(data),data,nodata).astype(dtype)
  with rasterio.open(out/name,'w',**p) as dst:dst.write(v,1);dst.update_tags(attribution='Contains modified Copernicus Sentinel data (2019–2025)',interpretation='Spectral context; not verified species cover')
 dates=[];ndvis=[];water=[];clear_masks=[];rgb=[];quality=[]
 for r in selected.itertuples():
  item=items[r.item];folder=a.source/'clips'/r.item;dn={key:read(folder/(key+'.tif'),key=='swir16') for key in ['blue','green','red','nir','swir16']}
  physical={}
  for key,values in dn.items():
   metadata=item['assets'][key]['raster:bands'][0];assert metadata['scale']==.0001 and metadata['offset']==-.1
   physical[key]=values.astype('float64')*metadata['scale']+metadata['offset']
  scl=read(folder/'scl.tif',True);clear=np.isin(scl,[4,5,6])&inside
  red,nir=physical['red'],physical['nir'];green,swir=physical['green'],physical['swir16']
  valid=(dn['red']>0)&(dn['nir']>0)&(red>=0)&(nir>=0)&((red+nir)>0)
  wetvalid=(dn['green']>0)&(dn['swir16']>0)&(green>=0)&(swir>=0)&((green+swir)>0)
  ndvi=np.divide(nir-red,nir+red,out=np.full(shape,np.nan),where=valid)
  mndwi=np.divide(green-swir,green+swir,out=np.full(shape,np.nan),where=wetvalid)
  assert np.all(np.abs(ndvi[np.isfinite(ndvi)])<=1+1e-10)
  dates.append(r.date);ndvis.append(ndvi);water.append(mndwi);clear_masks.append(clear)
  rgb.append(np.stack([physical[k] for k in ['red','green','blue']],axis=-1))
  quality.append(dict(item=r.item,date=r.date,year=r.year,local_clear_fraction=float(clear[inside].mean()),negative_red_or_nir_fraction_among_clear=float(((red<0)|(nir<0))[clear].mean()),ndvi_valid_fraction=float((clear&valid)[inside].mean()),scl_water_fraction_among_clear=float((scl[clear]==6).mean()),processing_baseline=item['properties']['s2:processing_baseline'],reflectance_scale=.0001,reflectance_offset=-.1))
 pd.DataFrame(quality).to_csv(out/'scene_radiometry_quality.csv',index=False)
 ndvis=np.array(ndvis);water=np.array(water);clear_masks=np.array(clear_masks);dates=np.array(dates);years=sorted(selected.year.unique());scene_year=np.array([int(d[:4]) for d in dates]);rgb=np.array(rgb)
 rows=[];scene_rows=[];comparisons=[];composites={};supports={};counts={};water_composites={}
 disk=np.indices((5,5));disk=((disk[0]-2)**2+(disk[1]-2)**2)<=4
 for buffer in [20,0]:
  masks=np.array([binary_erosion(m,structure=disk,border_value=0) for m in clear_masks]) if buffer else clear_masks.copy()
  values=np.where(masks,ndvis,np.nan);wet=np.where(masks,water,np.nan)
  annual=[];annual_water=[];annual_count=[]
  for year in years:
   subset=scene_year==year
   with warnings.catch_warnings():
    warnings.simplefilter('ignore',RuntimeWarning);annual.append(np.nanmedian(values[subset],axis=0));annual_water.append(np.nanmedian(wet[subset],axis=0))
   annual_count.append(np.isfinite(values[subset]).sum(axis=0))
  annual=np.array(annual);annual_count=np.array(annual_count);annual_water=np.array(annual_water)
  for minobs,year_scope in [(1,'all_available'),(2,'all_available'),(2,'years_with_two_dates')]:
   eligible=np.array([True if year_scope=='all_available' else (scene_year==y).sum()>=2 for y in years])
   support=inside&np.all(annual_count[eligible]>=minobs,axis=0)
   if year_scope=='all_available':supports[(buffer,minobs)]=support
   else:supports[(buffer,minobs,'multi')]=support
   for zone,area in zones.items():
    use=area&support;n=int(use.sum())
    for yi,year in enumerate(years):
     if not eligible[yi]:continue
     v=annual[yi][use];wetv=annual_water[yi][use];wetv=wetv[np.isfinite(wetv)]
     per_date=[]
     for si in np.where(scene_year==year)[0]:
      sample=values[si][use];fraction=float(np.isfinite(sample).mean()) if n else np.nan
      # Date summaries require >=80% of this fixed zone's common support.
      med=float(np.nanmedian(sample)) if n and fraction>=.8 else np.nan
      per_date.append(med);scene_rows.append(dict(buffer_m=buffer,min_observations_per_year=minobs,year_scope=year_scope,zone=zone,date=dates[si],fixed_support_pixels=n,date_valid_fraction=fraction,median_ndvi=med))
     finite=np.array(per_date)[np.isfinite(per_date)]
     rows.append(dict(buffer_m=buffer,min_observations_per_year=minobs,year_scope=year_scope,zone=zone,year=int(year),selected_dates=int((scene_year==year).sum()),original_zone_pixels=int(area.sum()),fixed_support_pixels=n,fixed_support_ha=n*.01,retained_fraction=n/area.sum() if area.sum() else np.nan,median_ndvi=float(np.median(v)) if n else np.nan,q25_ndvi=float(np.quantile(v,.25)) if n else np.nan,q75_ndvi=float(np.quantile(v,.75)) if n else np.nan,date_median_min=float(finite.min()) if len(finite) else np.nan,date_median_max=float(finite.max()) if len(finite) else np.nan,mndwi_valid_pixels=len(wetv),median_mndwi=float(np.median(wetv)) if len(wetv) else np.nan,positive_mndwi_fraction=float((wetv>0).mean()) if len(wetv) else np.nan))
    if n:
     delta=annual[-1][use]-annual[0][use]
     comparisons.append(dict(buffer_m=buffer,min_observations_per_year=minobs,year_scope=year_scope,zone=zone,year0=int(years[0]),year1=int(years[-1]),pixels=n,median_paired_pixel_delta=float(np.median(delta)),difference_of_spatial_medians=float(np.median(annual[-1][use])-np.median(annual[0][use]))))
  composites[buffer]=annual;counts[buffer]=annual_count;water_composites[buffer]=annual_water
  if buffer==20:
   for i,year in enumerate(years):
    save(f'ndvi_september_{year}.tif',annual[i]);save(f'mndwi_september_{year}.tif',annual_water[i]);save(f'valid_observation_count_{year}.tif',annual_count[i],'uint8',255)
   save('common_support_1_observation.tif',supports[(20,1)].astype('uint8'),'uint8',255)
 pd.DataFrame(rows).to_csv(out/'fixed_support_summary.csv',index=False);pd.DataFrame(scene_rows).to_csv(out/'date_variability.csv',index=False);pd.DataFrame(comparisons).to_csv(out/'endpoint_sensitivity.csv',index=False)
 # All endpoint date pairs share exactly the same pixels, including across pairs.
 endpoint0=np.where(scene_year==years[0])[0];endpoint1=np.where(scene_year==years[-1])[0]
 endpoint_ids=np.r_[endpoint0,endpoint1]
 buffered=np.array([binary_erosion(m,structure=disk,border_value=0) for m in clear_masks])
 pair_support=supports[(20,1)]&np.all(buffered[endpoint_ids]&np.isfinite(ndvis[endpoint_ids]),axis=0)
 pairs=[]
 for zone,area in zones.items():
  use=pair_support&area
  if not use.any():continue
  for i in endpoint0:
   for j in endpoint1:
    pairs.append(dict(zone=zone,date0=dates[i],date1=dates[j],fixed_support_pixels=int(use.sum()),median_paired_pixel_delta=float(np.median(ndvis[j][use]-ndvis[i][use])),difference_of_spatial_medians=float(np.median(ndvis[j][use])-np.median(ndvis[i][use]))))
 pd.DataFrame(pairs).to_csv(out/'endpoint_date_pairs.csv',index=False)
 audit={'collection':'sentinel-2-c1-l2a','candidate_items':manifest['candidate_count'],'selected_dates':len(selected),'years':list(map(int,years)),'missing_years':sorted(set(range(2019,2026))-set(map(int,years))),'selection_rule':manifest['selection'],'full_image_pixels':int(inside.sum()),'primary_common_support_pixels':int(supports[(20,1)].sum()),'primary_common_support_ha':float(supports[(20,1)].sum()*.01),'two_observation_support_pixels':int(supports[(20,2)].sum()),'multi_observation_years':[int(y) for y in years if (scene_year==y).sum()>=2],'multi_observation_common_support_ha':float(supports[(20,2,'multi')].sum()*.01),'source_window_hashes_verified':len(manifest['records']),'radiometry':'Collection 1 DN * 0.0001 - 0.1; source product metadata checked separately. Negative red/NIR reflectances excluded and counted; not clipped.','limitations':['Cloud-screened September observations, not annual means.','September 2022 absent from queried Collection 1 catalog; retained as a gap without legacy-product substitution.','Fixed 2019 CCAV strata are unvalidated map classes, not species truth.','No independent field labels, tide normalization, registration control points or intervention timing.','SCL is a model-based mask, not independent cloud truth.','Site10 rounding cell is not the original sampling footprint.','Pixels are spatially dependent; date ranges and spatial quartiles are not confidence intervals.']}
 (out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7,'axes.titlesize':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
 fig=plt.figure(figsize=(183/25.4,165/25.4),layout='constrained');gs=fig.add_gridspec(3,3,height_ratios=[1,1,.95])
 extent=[tr.c/1000,(tr.c+shape[1]*10)/1000,(tr.f-shape[0]*10)/1000,tr.f/1000]
 for i,year in enumerate(years):
  ax=fig.add_subplot(gs[i//3,i%3]);im=ax.imshow(np.where(inside,composites[20][i],np.nan),extent=extent,vmin=-.5,vmax=.9,cmap='YlGn');ax.set_title(f'{year} · {int((scene_year==year).sum())} '+('date' if (scene_year==year).sum()==1 else 'dates'),loc='left');ax.set_xticks([]);ax.set_yticks([])
  pts=Transformer.from_crs(4326,crs,always_xy=True).transform([117.425,117.435],[23.925,23.935]);ax.add_patch(Rectangle((pts[0][0]/1000,pts[1][0]/1000),(pts[0][1]-pts[0][0])/1000,(pts[1][1]-pts[1][0])/1000,fill=False,ec='#cc79a7',lw=.8))
  x=extent[0]+.15;y=extent[2]+.15;ax.plot([x,x+.5],[y,y],color='black',lw=1.4);ax.text(x,y+.05,'500 m',fontsize=6)
  ax.set_xlim(extent[:2]);ax.set_ylim(extent[2:]);ax.set_axis_off()
  ax.text(-.08,1.07,chr(97+i),transform=ax.transAxes,fontweight='bold',fontsize=9)
 fig.colorbar(im,ax=fig.axes[:len(years)],location='right',shrink=.65,label='September median NDVI',extend='both')
 ax=fig.add_subplot(gs[2,:2]);d=pd.DataFrame(rows);primary=d[(d.buffer_m==20)&(d.min_observations_per_year==1)&(d.year_scope=='all_available')]
 for zone,label,color in [('historical_roi','Historical ROI','#555555'),('baseline_2019_spartina_class','2019 Spartina map class','#0072B2'),('baseline_2019_mangrove_class','2019 mangrove map class','#D55E00')]:
  z=primary[primary.zone==zone].set_index('year').reindex(range(2019,2026));ax.plot(z.index,z.median_ndvi,'o-',ms=3,lw=1,color=color,label=label);ax.fill_between(z.index,z.date_median_min,z.date_median_max,color=color,alpha=.13)
 ax.axvspan(2021.8,2022.2,color='#dddddd',alpha=.5);ax.set(xlabel='Year (September only)',ylabel='Median NDVI',xticks=range(2019,2026));ax.legend(frameon=False,fontsize=6,loc='lower left');ax.text(-.04,1.04,'g',transform=ax.transAxes,fontweight='bold',fontsize=9)
 ax=fig.add_subplot(gs[2,2]);z=primary[primary.zone=='baseline_2019_spartina_class'].set_index('year').reindex(range(2019,2026));ax.plot(z.index,z.positive_mndwi_fraction*100,'o-',color='#56B4E9',ms=3);ax.set(xlabel='Year',ylabel='MNDWI > 0 (% of valid pixels)',xticks=[2019,2021,2023,2025]);ax.text(-.12,1.04,'h',transform=ax.transAxes,fontweight='bold',fontsize=9)
 fig.suptitle('Local spectral extension · fixed footprint, common season\n2022 unavailable in Collection 1; pink outline: Site10 coordinate rounding cell',fontsize=9)
 for ext in ['png','pdf','svg']:fig.savefig(out/f'local_sentinel_extension.{ext}',dpi=300)
 plt.close(fig)
 fig,axs=plt.subplots(2,3,figsize=(183/25.4,128/25.4),layout='constrained')
 for ax,year in zip(axs.flat,years):
  values=np.where(buffered[scene_year==year,:,:,None],rgb[scene_year==year],np.nan)
  with warnings.catch_warnings():
   warnings.simplefilter('ignore',RuntimeWarning);color=np.nanmedian(values,axis=0)
  missing=~np.isfinite(color).all(axis=2);color=np.clip(color/.3,0,1)**(1/1.6);color[missing]=1
  ax.imshow(color,extent=extent);ax.set_title(str(year),loc='left');ax.axis('off')
  x=extent[0]+.15;y=extent[2]+.15;ax.plot([x,x+.5],[y,y],color='black',lw=1.4);ax.text(x,y+.06,'500 m',fontsize=6)
 fig.suptitle('Surface-reflectance RGB · fixed stretch in every year\nSeptember composites; white: no accepted observation; 2022 unavailable',fontsize=9)
 for ext in ['png','pdf','svg']:fig.savefig(out/f'local_sentinel_rgb.{ext}',dpi=300)
 plt.close(fig);print(json.dumps(audit,indent=2));print(pd.DataFrame(comparisons).to_string(index=False))
if __name__=='__main__':main()
