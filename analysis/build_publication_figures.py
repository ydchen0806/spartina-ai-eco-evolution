"""Rebuild core quantitative panels at 183 mm with vector exports and source tables."""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'figures/publication_20261007'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7,'axes.labelsize':7,'axes.titlesize':7,
 'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'axes.spines.top':False,'axes.spines.right':False,
 'axes.linewidth':.7,'lines.linewidth':1.0,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','savefig.dpi':300})
BLUE='#0072B2';ORANGE='#D55E00';GREEN='#009E73';GRAY='#777777'
manifest=[]
def source(rel,name):
 p=ROOT/rel;d=pd.read_csv(p);d.to_csv(OUT/(name+'.csv'),index=False)
 manifest.append({'path':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});return d

def save(fig,name):
    for ax in fig.axes:
        title=ax.get_title(loc='left')
        if title and title[0] in 'abcd':
            ax.set_title(title[1:].strip(),loc='left',fontsize=7)
            ax.text(-.10,1.05,title[0],transform=ax.transAxes,fontsize=8,fontweight='bold')
    for ext in ['pdf','svg','png']:fig.savefig(OUT/f'{name}.{ext}')
    plt.close(fig)

def main():
 OUT.mkdir(exist_ok=True,parents=True)
 d=source('data/derived/trajectory_audit_20261007/endpoint_year_summary.csv','figure2_source')
 fig,axs=plt.subplots(1,2,figsize=(183/25.4,82/25.4),layout='constrained',gridspec_kw={'width_ratios':[1.2,1]})
 ax=axs[0]
 for col,label,color,style in [('stored_mean','Stored: retained transitions',ORANGE,'-'),('recomputed_model_mean','Area-derived: same transitions',BLUE,'-'),('all_pair_mean','Area-derived: all transitions',GRAY,'--')]:
  ax.plot(d.year,d[col],marker='o',ms=3,color=color,ls=style,label=label)
 ax.set(xlabel='Starting survey year',ylabel='Mean endpoint (dimensionless)',xticks=[2014,2016,2018,2020]);ax.legend(frameon=False)
 ax.set_title('a   Response and sampling sensitivity',loc='left',fontweight='bold')
 ax=axs[1];ax.bar(d.year,d.all_pair_n,color='#DDE2E5',label='All archived transitions (957)');ax.bar(d.year,d.model_n,color=BLUE,label='Retained transitions (854)')
 for _,r in d.iterrows():ax.text(r.year,r.all_pair_n+7,str(int(r.model_n))+'/'+str(int(r.all_pair_n)),ha='center',fontsize=6.5)
 ax.set(xlabel='Starting survey year',ylabel='Transition records',ylim=(0,440),xticks=[2014,2016,2018,2020]);ax.legend(frameon=False,loc='upper right');ax.set_title('b   Positive-growth selection',loc='left',fontweight='bold')
 save(fig,'figure2_endpoint')
 d=source('data/derived/strict_benchmark_20261007/pooled_metrics.csv','figure3_source')
 d=d[d.target=='log_area_ratio'];fig,axs=plt.subplots(1,2,figsize=(183/25.4,78/25.4),layout='constrained')
 splits=list(d.split.unique());labels={'buffered_quadrant':'Spatial holdout\n954 predictions','forward_year':'Forward years\n455 predictions'}
 print('Benchmark splits:',splits)
 for ax,metric,title in zip(axs,['r2','mae'],['a   Squared-error performance','b   Absolute-error performance']):
  for j,(model,color,label) in enumerate([('training_mean',GRAY,'Training mean'),('ridge',BLUE,'Ridge'),('extra_trees',ORANGE,'Extremely randomized trees')]):
   g=d[d.model==model].set_index('split').loc[splits];x=np.arange(len(splits))+(j-1)*.2;ax.scatter(x,g[metric],s=24,c=color,label=label)
  ax.set(xticks=np.arange(len(splits)),xticklabels=[labels.get(s,s) for s in splits],xlim=(-.5,len(splits)-.5),ylabel='Pooled R²' if metric=='r2' else 'MAE of log area ratio')
  ax.set_title(title,loc='left',fontweight='bold')
  if metric=='r2':ax.axhline(0,color='#AAAAAA',lw=.7,ls='--');ax.legend(frameon=False,fontsize=6.5,loc='lower left')
 save(fig,'figure3_prediction')
 d=source('data/derived/ccav_20261007/annual_class_areas_grid_sensitivity.csv','figure4_source')
 fig,axs=plt.subplots(1,2,figsize=(183/25.4,80/25.4),layout='constrained',sharey=True)
 for ax,fp,letter,title in zip(axs,['full_image','historical_roi'],'ab',['Full aerial-image footprint','Historical patch ROI']):
  for code,color,label in [(1,ORANGE,'S. alterniflora'),(3,GREEN,'Mangrove'),(255,GRAY,'Unmapped')]:
   # Class labels are verified below, rather than assuming a mangrove code.
   actual=d.loc[d.label.str.contains('mangrove',case=False),'code'].unique()
   if code==3:assert len(actual)==1;code=int(actual[0])
   sub=d[(d.footprint==fp)&(d.code==code)];bounds=sub.groupby('year').area_ha.agg(['min','max']);base=sub[(sub.shift_x_m==0)&(sub.shift_y_m==0)]
   ax.fill_between(bounds.index,bounds['min'],bounds['max'],color=color,alpha=.18)
   ax.plot(base.year,base.area_ha,'o-',color=color,ms=3,label=label)
  ax.set(xlabel='Satellite map year',xticks=[2016,2018,2020,2022]);ax.set_title(f'{letter}   {title}',loc='left',fontweight='bold')
 axs[0].set_ylabel('Classified area (ha)');axs[1].legend(frameon=False)
 save(fig,'figure4_landscape')
 (OUT/'figure_manifest.json').write_text(json.dumps({'width_mm':183,'font':'DejaVu Sans','font_pt':7,'sources':manifest,'uncertainty':'Figure 4 shading is four grid phases, not classification uncertainty. Figure 2 annual means are descriptive. Figure 3 pooled holdout metrics are point estimates.'},indent=2))
if __name__=='__main__':main()
