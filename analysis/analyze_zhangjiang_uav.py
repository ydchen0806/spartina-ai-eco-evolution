"""Audit overlapping 20 cm UAV maps; count mapped positives, never infer death from zero.

Outputs adapt Huang et al., ScienceDB V4, CC-BY-NC-SA-4.0. Background in
classified rasters is tagged NoData=0; it is not a verified absence class.
"""
import argparse,json,hashlib,math
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.warp import reproject,transform_bounds
from rasterio.transform import from_origin
from rasterio.windows import Window
from pyproj import Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from download_local_sentinel import FULL
from download_zhangjiang_uav import digest
ROI=(FULL[0]+10000*1.08e-6,FULL[3]-22000*9.8e-7,FULL[0]+25000*1.08e-6,FULL[3]-4000*9.8e-7)
ROOT=Path(__file__).resolve().parents[1]

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((a.source/'download_manifest.json').read_text());assert len(manifest['files'])==20
 for r in manifest['files']:assert digest(a.source/r['file'],'md5')==r['provider_md5'] and digest(a.source/r['file'],'sha256')==r['sha256']
 sources=sorted((a.source/'classified').glob('*.tif'));dates=[p.name[:6] for p in sources]
 with rasterio.open(next((a.source/'DOM').glob('202206*'))) as ref:bounds=ref.bounds
 left=math.floor(bounds.left);top=math.ceil(bounds.top);width=math.ceil(bounds.right-left);height=math.ceil(top-bounds.bottom);tr=from_origin(left,top,1,1);shape=(height,width)
 yy,xx=np.indices(shape);lon,lat=Transformer.from_crs(32650,4326,always_xy=True).transform(left+xx+.5,top-yy-.5)
 def box(b):return (lon>=b[0])&(lon<b[2])&(lat>=b[1])&(lat<b[3])
 zones={'full_image':box(FULL),'historical_roi':box(ROI),'site10_rounding_cell':box((117.425,23.925,117.435,23.935))&box(FULL)}
 arrays={};masks={};rgbs={};rows=[];inventory=[];support=zones['full_image'].copy()
 def write(name,data,nodata,dtype):
  with rasterio.open(out/name,'w',driver='GTiff',height=height,width=width,count=1,dtype=dtype,crs=32650,transform=tr,nodata=nodata,compress='deflate') as r:
   r.write(data.astype(dtype),1);r.update_tags(attribution='Huang, Zhang, Zhou and Zhu, ScienceDB V4, DOI:10.57760/sciencedb.o00119.00069',license='CC-BY-NC-SA-4.0',interpretation='Mapped-positive fraction, zero not verified absence; spatial adaptation')
 for path,date in zip(sources,dates):
  dom=next((a.source/'DOM').glob(date+'*.tif'))
  with rasterio.open(path) as c,rasterio.open(dom) as r:
   cb=transform_bounds(c.crs,4326,*c.bounds);rb=transform_bounds(r.crs,4326,*r.bounds)
   inventory.append({'date':date,'classified_file':path.name,'dom_file':dom.name,'class_crs':str(c.crs),'dom_crs':str(r.crs),'class_resolution_m':c.res,'dom_resolution_m':r.res,'class_nodata':c.nodata,'dom_nodata':r.nodata,'classified_bounds_wgs84':cb,'dom_bounds_wgs84':rb,'class_rect_within_local_full_image':cb[0]>=FULL[0] and cb[1]>=FULL[1] and cb[2]<=FULL[2] and cb[3]<=FULL[3]})
   raw=c.read(1);codes,nums=np.unique(raw,return_counts=True);assert set(codes).issubset({0,1});native=float((raw==1).sum()*abs(c.transform.a*c.transform.e))
   fraction=np.zeros(shape,dtype='float32');rectangle=np.zeros(shape,dtype='uint8')
   # Use explicit ndarray and src_nodata=None: tagged zero is NOT discarded
   # during averaging. Fraction measures frequency of positive source labels.
   reproject(raw,fraction,src_transform=c.transform,src_crs=c.crs,src_nodata=None,dst_transform=tr,dst_crs=32650,dst_nodata=0,resampling=Resampling.average)
   reproject(np.ones(raw.shape,dtype='uint8'),rectangle,src_transform=c.transform,src_crs=c.crs,src_nodata=None,dst_transform=tr,dst_crs=32650,dst_nodata=0,resampling=Resampling.nearest)
   del raw
   with WarpedVRT(r,crs=32650,transform=tr,width=width,height=height,resampling=Resampling.nearest) as v:
    rgb=v.read([1,2,3]);observed=np.all(v.read_masks([1,2,3])>0,axis=0)
   assert np.all((fraction>=0)&(fraction<=1+1e-6))
   valid=observed&(rectangle==1)&zones['full_image'];support&=valid
   arrays[date]=fraction;masks[date]=valid
   if date in ['201408','202112','202206']:
    color=np.moveaxis(np.clip(rgb,0,255).astype('uint8'),0,-1);color[~observed]=255;rgbs[date]=color
   rows.append({'date':date,'native_mapped_positive_area_ha':native/10000,'one_m_grid_positive_area_ha':float(fraction.sum()/10000),'one_m_minus_native_area_ha':float((fraction.sum()-native)/10000),'dom_observed_in_full_image_ha':float((observed&zones['full_image']).sum()/10000),'observed_class_rectangle_ha':float(valid.sum()/10000),'source_0_interpretation':'NoData/unlabelled, not verified absence'})
   write(f'positive_fraction_{date}_1m.tif',fraction,-9999,'float32')
   print('Audited',date,'native positive ha',round(native/10000,3),flush=True)
 pd.DataFrame(rows).to_csv(out/'native_positive_inventory.csv',index=False)
 # Fixed intersection of RGB observation footprints AND class rectangles.
 summaries=[]
 for zone,z in zones.items():
  use=z&support
  for date in dates:summaries.append({'date':date,'zone':zone,'common_support_ha':float(use.sum()/10000),'mapped_positive_area_ha':float(arrays[date][use].sum()/10000),'mapped_positive_fraction':float(arrays[date][use].mean()) if use.any() else np.nan})
 pd.DataFrame(summaries).to_csv(out/'common_footprint_positive_area.csv',index=False);write('all_dates_common_support_1m.tif',support,255,'uint8')
 # Native-pixel endpoint accounting. Check header origins at submillimetre tolerance.
 p0=a.source/'classified/202112-classified.tif';p1=a.source/'classified/202206-classified.tif'
 changes=np.zeros((2,2),dtype='int64');validpixels=0;sourcepositive=[0,0];candidates=[]
 with rasterio.open(p0) as c0,rasterio.open(p1) as c1:
  assert c0.shape==c1.shape and c0.crs==c1.crs and c0.res==c1.res
  header_origin_offset_m=float(np.hypot(c0.transform.c-c1.transform.c,c0.transform.f-c1.transform.f));assert header_origin_offset_m<.001
  dr0=rasterio.open(next((a.source/'DOM').glob('202112*')));dr1=rasterio.open(next((a.source/'DOM').glob('202206*')))
  with dr0,dr1,WarpedVRT(dr0,crs=c0.crs,transform=c0.transform,width=c0.width,height=c0.height,resampling=Resampling.nearest) as v0,WarpedVRT(dr1,crs=c1.crs,transform=c1.transform,width=c1.width,height=c1.height,resampling=Resampling.nearest) as v1:
   for ro in range(0,c0.height,512):
    for co in range(0,c0.width,512):
     w=Window(co,ro,min(512,c0.width-co),min(512,c0.height-ro));b0=c0.read(1,window=w);b1=c1.read(1,window=w)
     mask=np.all(v0.read_masks([1,2,3],window=w)>0,axis=0)&np.all(v1.read_masks([1,2,3],window=w)>0,axis=0)
     changes+=np.bincount((b0[mask]*2+b1[mask]),minlength=4).reshape(2,2);validpixels+=int(mask.sum())
     if mask.sum():
      cx,cy=c0.xy(ro+w.height/2,co+w.width/2);candidates.append({'row':ro,'col':co,'width':int(w.width),'height':int(w.height),'easting':cx,'northing':cy,'valid_pixels':int(mask.sum()),'positive_removed':int((mask&(b0==1)&(b1==0)).sum()),'positive_added':int((mask&(b0==0)&(b1==1)).sum())})
  pixel_area=abs(c0.transform.a*c0.transform.e)
 assert changes.sum()==validpixels
 pd.DataFrame([{'label_202112':i,'label_202206':j,'pixels':int(changes[i,j]),'area_ha':float(changes[i,j]*pixel_area/10000),'interpretation':('positive retained' if i==j==1 else 'positive removed; later unlabelled' if i==1 else 'positive added; earlier unlabelled' if j==1 else 'unlabelled both')} for i in range(2) for j in range(2)]).to_csv(out/'endpoint_label_transitions.csv',index=False)
 pd.DataFrame(candidates).to_csv(out/'endpoint_review_tiles.csv',index=False)
 audit={'source_doi':manifest['doi'],'license':'CC-BY-NC-SA-4.0','files_verified':20,'total_bytes':manifest['total_bytes'],'dates':dates,'native_resolution_m':.2,'source_map_rectangles_within_local_image':all(r['class_rect_within_local_full_image'] for r in inventory),'all_dates_common_support_ha':float(support.sum()/10000),'endpoint_header_origin_offset_m':header_origin_offset_m,'endpoint_observed_overlap_ha':validpixels*pixel_area/10000,'endpoint_retained_positive_ha':float(changes[1,1]*pixel_area/10000),'endpoint_removed_positive_ha':float(changes[1,0]*pixel_area/10000),'endpoint_added_positive_ha':float(changes[0,1]*pixel_area/10000),'grid_approximation_max_abs_area_difference_ha':float(pd.DataFrame(rows).one_m_minus_native_area_ha.abs().max()),'limits':['Binary maps have foreground1 and NoData0; zero cannot establish absence, bare substrate or death.','2021 December versus 2022 June compares different seasons.','RTK filenames do not independently establish local coregistration error.','2014 August and 2015 August overlap acquisition months in recovered archive; historical-source independence unestablished.','2013–2022 maps represent reported distribution, not independent field-labelled validation.','Mapped-positive area inventories and label transitions are not demographic rates.','Common support uses nearest-neighbour RGB observation masks and source map rectangles on a 1m grid; native endpoint transitions pair original 20cm classified array cells after checking header-origin difference <1mm; this does not verify physical registration.']}
 (out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n');(out/'raster_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7,'axes.titlesize':8,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
 fig,axs=plt.subplots(2,2,figsize=(183/25.4,155/25.4),layout='constrained');extent=[left/1000,(left+width)/1000,(top-height)/1000,top/1000]
 for ax,date in zip(axs[0],['202112','202206']):
  ax.imshow(rgbs[date],extent=extent);overlay=np.zeros((*shape,4),dtype='float32');overlay[:,:,0]=1;overlay[:,:,1]=.35;overlay[:,:,2]=.05;overlay[:,:,3]=arrays[date]*.48;ax.imshow(overlay,extent=extent);ax.set_title(date[:4]+'-'+date[4:]+' · source positive labels',loc='left');ax.set_axis_off();x=extent[0]+.15;y=extent[2]+.15;ax.plot([x,x+.3],[y,y],color='black',lw=1.5);ax.text(x,y+.05,'300 m',fontsize=6)
 d=pd.DataFrame(summaries);colors={'full_image':'#0072B2','historical_roi':'#D55E00'}
 for zone,label in [('full_image','Shared observation footprint'),('historical_roi','Historical ROI intersection')]:
  z=d[d.zone==zone];axs[1,0].plot(pd.to_datetime(z.date,format='%Y%m'),z.mapped_positive_area_ha,'o-',ms=3,color=colors[zone],label=label)
 axs[1,0].set(ylabel='Mapped-positive area (ha)',xlabel='Acquisition month');axs[1,0].legend(frameon=False,fontsize=6);axs[1,0].tick_params(axis='x',rotation=30)
 values=[audit['endpoint_retained_positive_ha'],audit['endpoint_removed_positive_ha'],audit['endpoint_added_positive_ha']]
 axs[1,1].bar(['Retained\npositive','Removed\npositive','Added\npositive'],values,color=['#777777','#D55E00','#0072B2']);axs[1,1].set(ylabel='Label-transition area (ha)',title='2021-12 → 2022-06 · common RGB coverage')
 for i,value in enumerate(values):axs[1,1].text(i,value+.8,f'{value:.2f}',ha='center',fontsize=7)
 for letter,ax in zip('abcd',axs.flat):ax.text(-.06,1.05,letter,transform=ax.transAxes,fontweight='bold',fontsize=9)
 fig.suptitle('Recovered public UAV archive · 20 cm · same estuary footprint\nZeros are unlabelled/NoData; changes are not verified ecological events',fontsize=9)
 for ext in ['png','pdf','svg']:fig.savefig(out/f'zhangjiang_uav_extension.{ext}',dpi=300)
 plt.close(fig);print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
