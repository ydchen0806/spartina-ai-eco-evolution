"""Audit published marsh imagery, stratified reference labels and clipping records.

Reference labels are the source authors' interpretation of the same NAIP imagery,
not independent field truth. Experimental plot assignment is not documented in
these files; plot contrasts are descriptive.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((a.source/'all_files_manifest.json').read_text())
 # Provider checksums were verified on download. Verify local inputs consumed here.
 used=['GSM_validation_points_150_AOI2015_minus_forest.xlsx','GSM_2023_RF_classified_AOI2015_minus_forest.tif','clipping_experiment.xlsx','Irridiance_for_statistics.xlsx']
 for name in used:
  f=next(f for f in manifest['files'] if f['name']==name);raw=(a.source/name).read_bytes();assert hashlib.md5(raw).hexdigest()==f['computed_md5']
 d=pd.read_excel(a.source/used[0]);assert len(d)==150 and d.point_id.is_unique
 assert set(d.correct_01)=={0,1}
 d['reference']=d.ref_class.fillna('').str.upper().str.strip();fill=(d.correct_01==1)&d.reference.eq('');d.loc[fill,'reference']=d.loc[fill,'map_class'];assert d.reference.isin(['PA','LM','HM','OTHER']).all()
 assert (d.reference==d.map_class).eq(d.correct_01.astype(bool)).all()
 counts=pd.crosstab(d.map_class,d.reference).reindex(index=['PA','LM','HM'],columns=['PA','LM','HM','OTHER'],fill_value=0);assert counts.sum(axis=1).eq(50).all();counts.to_csv(out/'reference_confusion_counts.csv')
 with rasterio.open(a.source/used[1]) as r:
  assert r.crs.to_epsg()==26919;image=r.read(1);area=abs(r.transform.a*r.transform.e-r.transform.b*r.transform.d)
  n=np.array([(image==i).sum() for i in [1,2,3]]);areas=n*area;weights=areas/areas.sum()
  codes,totals=np.unique(image,return_counts=True);inventory=pd.DataFrame({'code':codes,'pixels':totals,'area_m2':totals*area});inventory.to_csv(out/'all_raster_class_areas.csv',index=False)
  sampled_domain_fraction=float(n.sum()/(image!=0).sum())
  sampled=np.array([v[0] for v in r.sample(d[['x','y']].to_numpy())]);assert np.array_equal(sampled,d.map_class_id)
  yy,xx=rasterio.transform.rowcol(r.transform,d.x.to_numpy(),d.y.to_numpy());cx,cy=rasterio.transform.xy(r.transform,yy,xx);assert np.max(np.abs(np.array(cx)-d.x))<1e-6 and np.max(np.abs(np.array(cy)-d.y))<1e-6
  profile={'crs':str(r.crs),'width':r.width,'height':r.height,'resolution_m':r.res,'transform':tuple(r.transform),'nodata':r.nodata,'domain':'Only strata 1,2,3 sampled; codes 4-7 unsampled and their class names undocumented in supplied code; 0 nodata. No whole-map inference.'}
  small=r.read(1,out_shape=(700,316),resampling=Resampling.nearest);bounds=r.bounds
  with rasterio.open(a.source/'GSM_20230811.tif') as rgb:
   with WarpedVRT(rgb,crs=r.crs,transform=r.transform,width=r.width,height=r.height,resampling=Resampling.nearest) as v:rgbsmall=v.read([1,2,3],out_shape=(3,700,316),resampling=Resampling.bilinear).transpose(1,2,0)
 probs=counts.to_numpy()/50;adjusted=(areas[:,None]*probs).sum(axis=0);se=np.sqrt((areas[:,None]**2*probs*(1-probs)/49).sum(axis=0))
 result=pd.DataFrame({'class':['PA','LM','HM','OTHER'],'mapped_area_m2':[*areas,np.nan],'adjusted_area_m2':adjusted,'SE_m2':se,'CI95_low_m2':adjusted-1.96*se,'CI95_high_m2':adjusted+1.96*se});result.to_csv(out/'reference_adjusted_area.csv',index=False)
 provider=pd.read_csv(a.source/'GSM_validation_points_150_AOI2015_minus_forest_ADJUSTED_AREA_RESULTS.csv');maxerr=float(np.max(np.abs(provider.adjusted_area_m2-result.adjusted_area_m2)));assert maxerr<1e-6
 assert abs(result.adjusted_area_m2.sum()-areas.sum())<1e-6
 d.to_csv(out/'audited_reference_points.csv',index=False)
 # Parse only labelled original columns, avoiding adjacent duplicated plotting/helper cells.
 sheet=pd.read_excel(a.source/'clipping_experiment.xlsx',sheet_name=0,header=None)
 dates={1:'2023-05-17',3:'2023-06-30',7:'2023-07-18',11:'2023-08-01',15:'2023-08-16',19:'2023-09-09',23:'2023-09-22',27:'2023-10-13',31:'2024-05-14',35:'2024-09-12',39:'2025-07-08'}
 par=pd.read_excel(a.source/'Irridiance_for_statistics.xlsx');ex=par[par.plot_type=='experimental'];assert len(ex)==6;groups=ex.set_index('plot#').treatment_type.to_dict()
 records=[]
 for row in range(4,10):
  plot=int(sheet.iloc[row,0])
  for col,date in dates.items():records.append(dict(plot=plot,treatment=groups[plot],date=date,cover_pct=float(sheet.iloc[row,col]),source_excel_row=row+1,source_excel_column=col+1))
 cover=pd.DataFrame(records);assert cover.cover_pct.between(0,100).all();assert not cover.duplicated(['plot','date']).any();cover.to_csv(out/'clipping_plot_time.csv',index=False)
 means=cover.groupby(['date','treatment']).cover_pct.mean().unstack();means['clipped_minus_control']=means.clipped-means.control;means['difference_in_change_from_first_observation']=means.clipped_minus_control-means.clipped_minus_control.iloc[0];means.to_csv(out/'clipping_descriptive_contrasts.csv')
 for col in dates:
  assert abs(sheet.iloc[14,col]-cover[(cover.date==dates[col])&(cover.treatment=='clipped')].cover_pct.mean())<1e-8
  assert abs(sheet.iloc[15,col]-cover[(cover.date==dates[col])&(cover.treatment=='control')].cover_pct.mean())<1e-8
 par.to_csv(out/'irradiance_plot_means.csv',index=False)
 # Source scripts explicitly use within-polygon random pixels. Missing shapefile
 # sidecars prevent recovery of training class attributes/CRS from that file alone.
 missing_sidecars=[name for name in ['GSM_training_data_2023.dbf','GSM_training_data_2023.shx','GSM_training_data_2023.prj'] if not (a.source/name).exists()]
 audit={'dataset_doi':manifest['doi'],'paper_doi':manifest['paper_doi'],'source_files':len(manifest['files']),'source_bytes':manifest['total_bytes'],'provider_md5_verified_on_download':True,'sampled_domain_fraction_of_nonzero_map':sampled_domain_fraction,'reference_points':len(d),'reference_points_agree_with_raster':int((sampled==d.map_class_id).sum()),'unweighted_reference_agreement':float(d.correct_01.mean()),'area_weighted_reference_agreement':float(np.sum(weights*np.diag(probs[:,:3]))),'published_adjusted_area_max_error_m2':maxerr,'clipping_plots':6,'plots_per_treatment':3,'clipping_plot_dates':len(cover),'last_observed_cover_difference_pp':float(means.clipped_minus_control.iloc[-1]),'first_to_last_difference_in_change_pp':float(means.difference_in_change_from_first_observation.iloc[-1]),'missing_training_sidecars':missing_sidecars,'raster':profile,'limits':['Spartina is native here; Phragmites is the invader. This is not an independent Chinese Spartina invasion replicate.','LM/HM are community classes, not independent species segmentation masks.','Reference points were labelled using the source image, not independent field measurements; uncertainty intervals condition on those labels.','Stratified samples must be weighted by mapped area; classes 4-7 are nonzero but unsampled, so reference agreement cannot assess the whole map.','Three plots per clipping arm with repeated dates; assignment/randomization and pairing are not established from the archived metadata. No causal P value or treatment-effect confidence interval is asserted.','Original RF checkpoint and complete training shapefile components are unavailable; original training accuracy is not independently reproduced.']}
 (out/'audit.json').write_text(json.dumps(audit,indent=2))
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7,'axes.titlesize':7,'axes.labelsize':7,'axes.spines.top':False,'axes.spines.right':False,'lines.linewidth':1,'pdf.fonttype':42,'svg.fonttype':'none'})
 fig,axs=plt.subplots(2,2,figsize=(183/25.4,160/25.4),layout='constrained',gridspec_kw={'height_ratios':[1.2,1]})
 extent=[bounds.left,bounds.right,bounds.bottom,bounds.top]
 axs[0,0].imshow(rgbsmall,extent=extent);axs[0,0].scatter(d.x,d.y,c=d.correct_01.map({1:'#009E73',0:'#D55E00'}),s=4,linewidths=.15,edgecolors='white');axs[0,0].set_title('Source imagery and reference agreement',loc='left');axs[0,0].set_axis_off()
 axs[0,0].text(.02,.02,'Green: agrees; orange: disagrees',transform=axs[0,0].transAxes,fontsize=5.5,color='white',bbox=dict(facecolor='black',alpha=.6,pad=2))
 display=small.copy();display[display>3]=4
 axs[0,1].imshow(display,cmap=ListedColormap(['#ffffff','#CC79A7','#009E73','#E69F00','#b6b6b6']),vmin=0,vmax=4,extent=extent);axs[0,1].set_title('Published map and unsampled classes',loc='left');axs[0,1].set_axis_off()
 from matplotlib.patches import Patch
 axs[0,1].legend(handles=[Patch(color=c,label=l) for c,l in [('#CC79A7','PA'),('#009E73','LM'),('#E69F00','HM'),('#b6b6b6','Codes 4–7 (unsampled)')]],loc='lower left',bbox_to_anchor=(1.01,0),frameon=False,fontsize=5.5)
 for ax in axs[0]:
  x0=bounds.left+40;y0=bounds.bottom+180
  ax.plot([x0,x0+200],[y0,y0],color='black',lw=1)
  ax.text(x0+100,y0+25,'200 m',ha='center',fontsize=5.5,bbox=dict(facecolor='white',edgecolor='none',alpha=.8,pad=1))
 ax=axs[1,0];x=np.arange(4);ax.bar(x-.16,result.mapped_area_m2/10000,width=.32,color='#a9bcc9',label='Mapped');ax.bar(x+.16,result.adjusted_area_m2/10000,width=.32,color='#0072B2',label='Reference-adjusted');ax.errorbar(x+.16,result.adjusted_area_m2/10000,yerr=1.96*result.SE_m2/10000,fmt='none',ecolor='#333333',capsize=2,lw=.7);ax.set(xticks=x,xticklabels=result['class'],ylabel='Area within mapped domain (ha)');ax.legend(frameon=False,fontsize=6);ax.set_title('Stratified reference-based area estimates',loc='left')
 ax=axs[1,1]
 for group,color in [('clipped','#009E73'),('control','#D55E00')]:
  sub=cover[cover.treatment==group]
  for _,g in sub.groupby('plot'):ax.plot(pd.to_datetime(g.date),g.cover_pct,color=color,alpha=.35,lw=.6)
  ax.plot(pd.to_datetime(means.index),means[group],color=color,label=group,lw=1)
 ax.set(ylabel='S. alterniflora cover (%)',ylim=(0,105));ax.set_title('Repeated clipping observations: 3 plots/arm',loc='left');ax.legend(frameon=False,fontsize=6);ax.tick_params(axis='x',rotation=30,labelsize=6)
 for letter,ax in zip('abcd',axs.flat):ax.text(-.1,1.04,letter,transform=ax.transAxes,fontweight='bold',fontsize=8)
 for ext in ['png','pdf','svg']:fig.savefig(out/f'gsm_external_evidence.{ext}',dpi=300)
 plt.close(fig);print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
