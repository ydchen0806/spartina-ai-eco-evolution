"""Extract published ten-site summaries and screen geographic overlap, not sample independence."""
import argparse,json,hashlib
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from docx import Document

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((a.source/'manifest.json').read_text());raw=(a.source/'supplement.docx').read_bytes();assert hashlib.md5(raw).hexdigest()==manifest['file']['computed_md5']
 doc=Document(a.source/'supplement.docx');table=doc.tables[0];rows=[[c.text.strip() for c in r.cells] for r in table.rows];assert len(rows)==11 and len(rows[0])==9
 names=['region','site','longitude','latitude','resolution_m','low_patch_count','low_cover_fraction','high_patch_count','high_cover_fraction'];d=pd.DataFrame(rows[1:],columns=names)
 for col in names[2:]:d[col]=pd.to_numeric(d[col])
 assert d.site.is_unique and d[['low_cover_fraction','high_cover_fraction']].ge(0).all().all() and d[['low_cover_fraction','high_cover_fraction']].le(1).all().all()
 methods=json.loads((a.source/'methods_verified.json').read_text())
 assert hashlib.sha256((a.source/'article.xml').read_bytes()).hexdigest()==methods['sha256']
 d['campaign_month']=d.region.map(methods['campaign_month_by_region']);assert d.campaign_month.notna().all()
 d['window_area_m2']=methods['uav_window_width_m']*methods['uav_window_height_m']
 for tide in ['low','high']:
  d[tide+'_patch_density_per_1000_m2']=d[tide+'_patch_count']/d.window_area_m2*1000
  d[tide+'_covered_area_m2_approx']=d[tide+'_cover_fraction']*d.window_area_m2
 west,south,east,north=117.404195622047,23.9134768474132,117.432930102047,23.9374309174132
 d['nominal_point_in_local_image']=d.longitude.between(west,east)&d.latitude.between(south,north)
 # Coordinates printed to 0.01 degrees. This interval is a rounding screen,
 # not a confidence region or proof of shared imagery/material.
 d['rounded_coordinate_cell_intersects_local_image']=(d.longitude+.005>=west)&(d.longitude-.005<=east)&(d.latitude+.005>=south)&(d.latitude-.005<=north)
 d.to_csv(a.output/'published_sites_and_overlap_screen.csv',index=False)
 audit={'source_doi':manifest['doi'],'paper_doi':manifest['article_doi'],'published_sites':len(d),'site_tidal_cells':2*len(d),'window_area_m2':2500,'raw_images_acquired':False,'individual_trait_records_acquired':False,'nominal_overlapping_sites':d.loc[d.nominal_point_in_local_image,'site'].tolist(),'coordinate_resolution_degrees':.01,'interpretation':'Site10 nominal coordinates fall within the local aerial footprint. Its September 2025 campaign is later than our 2014–2021 imagery. Coordinate rounding does not establish shared plots or image footprints. Treat as a potential temporal extension, not independent spatial validation. Densities use the 50 by 50 m windows documented in Methods. Covered areas inherit rounding of published cover fractions.','raw_data_availability':'Author request; no openly linked raw-data repository identified in full-text availability statement. No authors contacted.','confounding':'Province, campaign season and year are confounded; this table cannot identify latitude effects independently of sampling season/year.','table_scope':'Supplement Table S1 site-level aggregates; no individual trait data or new trait-effect estimation.'}
 (a.output/'audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2))
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
 fig,axes=plt.subplots(1,2,figsize=(7.2,4.5),sharey=True)
 y=np.arange(len(d));labels=[f"{r.site} · {r.region} ({r.campaign_month})" for r in d.itertuples()]
 for ax,metric,title in zip(axes,['patch_density_per_1000_m2','cover_fraction'],['Patch density (per 1,000 m²)','Vegetation cover (%)']):
  scale=100 if metric=='cover_fraction' else 1
  low=d['low_'+metric]*scale;high=d['high_'+metric]*scale
  ax.hlines(y,low,high,color='#b8b8b8',lw=1,zorder=1)
  ax.scatter(low,y,c='#0072B2',s=22,label='Low tidal position',zorder=2)
  ax.scatter(high,y,c='#D55E00',marker='s',s=20,label='High tidal position',zorder=2)
  ax.set_xlabel(title);ax.set_xlim(left=0);ax.grid(axis='x',alpha=.15)
 axes[0].set_yticks(y,labels);axes[0].invert_yaxis()
 axes[0].get_yticklabels()[-1].set_fontweight('bold')
 axes[1].legend(loc='lower right',frameon=False,fontsize=7)
 for label,ax in zip('ab',axes):ax.text(-.04,1.04,label,transform=ax.transAxes,fontweight='bold',fontsize=11)
 fig.suptitle('Published site summaries · one 50 × 50 m window per tidal position',fontsize=9)
 fig.text(.02,.02,'Site10: nominal geographic overlap with local imagery; later campaign. Lines pair tidal positions, not trajectories.',fontsize=7)
 fig.tight_layout(rect=(0,.065,1,.96))
 for ext in ['png','pdf','svg']:fig.savefig(a.output/f'published_site_context.{ext}',dpi=300)
 plt.close(fig)
if __name__=='__main__':main()
