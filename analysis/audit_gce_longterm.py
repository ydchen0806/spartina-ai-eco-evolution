"""Audit GCE long-term observations and exact soil joins; keep results local.

Biomass is calculated from height and is excluded from response modelling.
Density-size associations are descriptive, not a demonstrated self-thinning law.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.io import loadmat
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def fit_slope(d,environment=False):
    frame=d[['Year','Site','Zone']].astype(str)
    groups=pd.get_dummies(frame.Site+'_'+frame.Zone,drop_first=True,dtype=float)
    years=pd.get_dummies(frame.Year,drop_first=True,dtype=float)
    x=np.column_stack([np.ones(len(d)),np.log(d.density),groups,years])
    if environment:x=np.column_stack([x,d.Soil_Salinity_Porewater])
    coef=np.linalg.lstsq(x,np.log(d.mean_height),rcond=None)[0]
    return float(coef[1]),float(coef[-1]) if environment else None

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((a.source/'download_manifest.json').read_text())
    for file in manifest['files']:
        assert hashlib.sha256((a.source/file['name']).read_bytes()).hexdigest()==file['sha256']
        if file['name'].endswith('.CSV'):
            assert len(pd.read_csv(a.source/file['name'],skiprows=[0,1,3,4]))==file['expected_records']
    raw=loadmat(a.source/'PLT-GCES-1609_Observations_7_0_VARS.MAT',simplify_cells=True)
    def scalar(v):return None if isinstance(v,np.ndarray) and v.size==0 else v
    data={k:[scalar(v) for v in values] for k,values in raw.items() if not k.startswith('__') and k!='metadata'}
    assert {len(v) for v in data.values()}=={75236}
    allobs=pd.DataFrame(data);allobs.to_csv(out/'observations_decoded.csv.gz',index=False,compression='gzip')
    allobs.groupby(['Year','Species'],dropna=False).size().rename('records').to_csv(out/'year_species_inventory.csv')
    d=allobs[allobs.Species_Code=='A1'].copy();keys=['Year','Site','Zone','Plot']
    assert d.groupby(keys).Quadrat_Area.nunique().eq(1).all()
    assert d.groupby(keys).Location.nunique().eq(1).all()
    group=d.groupby(keys).agg(record_n=('Shoot_Height','size'),height_n=('Shoot_Height','count'),mean_height=('Shoot_Height','mean'),max_height=('Shoot_Height','max'),area=('Quadrat_Area','first'),Location=('Location','first'),disturbed=('Plot_Disturbance','max'),plot_flag=('Flag_Plot','max'),location_flag=('Flag_Location','max'),flowering_n=('Flowering_Status','sum'),flower_scored_n=('Flowering_Status','count')).reset_index()
    group['density']=group.height_n/group.area
    table=pd.read_csv(a.source/'PLT-GCES-1609_Shoots_Flowering_7_0.CSV',skiprows=[0,1,3,4]);table=table[table.Species_Code=='A1']
    joined=group.merge(table,on=keys,validate='one_to_one');assert len(joined)==len(group)==len(table)==3093
    density_error=float(np.max(np.abs(joined.density-joined.Num_Shoots_m2)));assert density_error==0
    # Flower counts require their own valid-scoring denominator; do not call NaN nonflowering.
    group['flowering_fraction']=group.flowering_n/group.flower_scored_n.replace(0,np.nan)
    group.to_csv(out/'spartina_plot_years.csv',index=False)
    env=pd.read_csv(a.source/'POR-GCES-2106_4_0.CSV',skiprows=[0,1,3,4]);assert len(env)==1308
    assert not env.duplicated(['Year','Location']).any()
    keep=['Year','Location','Soil_Salinity_Porewater','Flag_Soil_Salinity_Porewater','Flag_Location']
    ambiguous=group.duplicated(['Year','Location'],keep=False)
    group[ambiguous].to_csv(out/'ambiguous_year_location_keys.csv',index=False)
    merged=group[~ambiguous].merge(env[keep],on=['Year','Location'],how='left',validate='one_to_one',indicator=True)
    merged.to_csv(out/'spartina_soil_exact_join.csv',index=False)
    valid=group[(group.mean_height>0)&(group.density>0)&(group.Zone>0)].copy()
    fitted=[]
    for name,sub in [('all_observed',valid),('undisturbed',valid[valid.disturbed==0]),('plot_and_location_unflagged',valid[(valid.plot_flag==0)&(valid.location_flag==0)])]:
        slope,_=fit_slope(sub);fitted.append(dict(scenario=name,n_plot_years=len(sub),n_sites=sub.Site.nunique(),density_slope=slope,salinity_slope=np.nan))
    for site in sorted(valid.Site.unique()):
        sub=valid[valid.Site!=site];slope,_=fit_slope(sub);fitted.append(dict(scenario=f'leave_site_{site}_out',n_plot_years=len(sub),n_sites=sub.Site.nunique(),density_slope=slope,salinity_slope=np.nan))
    environmental=merged[(merged.mean_height>0)&(merged.density>0)&(merged.Zone>0)&merged.Soil_Salinity_Porewater.notna()&merged.Flag_Soil_Salinity_Porewater.isna()].copy()
    slope,salt=fit_slope(environmental,True);fitted.append(dict(scenario='exact_soil_join_unflagged_salinity',n_plot_years=len(environmental),n_sites=environmental.Site.nunique(),density_slope=slope,salinity_slope=salt));pd.DataFrame(fitted).to_csv(out/'descriptive_density_size_associations.csv',index=False)
    # A conservative temporal table: positive observed plots only, no fabricated absences.
    yearly=valid.groupby(['Year','Site']).agg(mean_height=('mean_height','mean'),mean_density=('density','mean'),n_plots=('Plot','size')).reset_index();yearly.to_csv(out/'site_year_means.csv',index=False)
    audit={'source_rows':len(allobs),'years':[int(allobs.Year.min()),int(allobs.Year.max())],'source_sites':int(allobs.Site.nunique()),'spartina_rows':len(d),'spartina_nonmissing_height':int(d.Shoot_Height.notna().sum()),'spartina_plot_years':len(group),'positive_height_density_plot_years':len(valid),'spartina_sites':int(d.Site.nunique()),'density_table_max_error':density_error,'soil_rows':len(env),'soil_years':[int(env.Year.min()),int(env.Year.max())],'ambiguous_location_plot_years_excluded_from_soil_join':int(ambiguous.sum()),'exact_soil_join_rows':int((merged._merge=='both').sum()),'usable_unflagged_soil_join_rows':len(environmental),'recorded_heights_at_or_below_10_cm':int(d.Shoot_Height.le(10).sum()),'limitations':['Native-range monitoring, not an invasive-range replication.','Stem observations are repeated cross-sectional samples, not individually tracked genets.','Number of stems with observed height divided by quadrat area reproduces all 3093 published density summaries; missing height rows must not be counted as live stems.','Locations may be estimated from replacement plots; supplied flags retained and unflagged sensitivity reported.','Protocol states live shoots above 10 cm, but some recorded heights are at or below 10 cm. Raw values retained, discrepancy recorded.','Density-size coefficients adjust for site-by-zone and year categories; no causal thinning rate, genetic effect, P value or confidence interval is claimed.','Biomass is allometrically derived from shoot height/flowering; excluded to avoid circular validation.','Soil links exclude all ambiguous Year+Location keys before matching; no spatial imputation. Nonpositive zone codes are excluded from descriptive regressions.','Original source is CC-BY in EML but legacy portal terms differ; raw and derived numbers remain local.']}
    (out/'audit.json').write_text(json.dumps(audit,indent=2))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7,'axes.titlesize':7,'axes.labelsize':7,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none','lines.linewidth':1})
    fig,axs=plt.subplots(2,2,figsize=(183/25.4,135/25.4),layout='constrained')
    matrix=group.groupby(['Site','Year']).size().unstack(fill_value=0);im=axs[0,0].imshow(matrix,aspect='auto',cmap='Blues');axs[0,0].set(yticks=range(len(matrix)),yticklabels=matrix.index,xticks=[0,5,10,15,20,23],xticklabels=[2000,2005,2010,2015,2020,2023],ylabel='Site',xlabel='Year');axs[0,0].set_title('Observed Spartina plot-years',loc='left');fig.colorbar(im,ax=axs[0,0],label='Plot count')
    axs[0,1].scatter(valid.density,valid.mean_height,s=3,alpha=.25,color='#0072B2');axs[0,1].set(xscale='log',yscale='log',xlabel='Recorded stem density (m⁻²)',ylabel='Mean shoot height (cm)');axs[0,1].set_title('Size–density observations',loc='left')
    for site,g in yearly.groupby('Site'):axs[1,0].plot(g.Year,g.mean_height,lw=.7,alpha=.7,label=str(site))
    axs[1,0].set(xlabel='Year',ylabel='Mean plot height (cm)');axs[1,0].set_title('Within-site annual summaries',loc='left')
    axs[1,0].legend(title='Site',fontsize=5,title_fontsize=5,ncol=3,loc='upper left',framealpha=.85)
    axs[1,1].scatter(environmental.Soil_Salinity_Porewater,environmental.mean_height,s=5,alpha=.35,color='#009E73');axs[1,1].set(xlabel='Soil porewater salinity (dimensionless)',ylabel='Mean shoot height (cm)');axs[1,1].set_title('Exact plot-year soil matches',loc='left')
    for letter,ax in zip('abcd',axs.flat):ax.text(-.1,1.04,letter,transform=ax.transAxes,fontweight='bold',fontsize=8)
    for ext in ['png','pdf','svg']:fig.savefig(out/f'gce_longterm_inventory.{ext}',dpi=300)
    plt.close(fig);print(json.dumps(audit,indent=2));print(pd.DataFrame(fitted).to_string(index=False))
if __name__=='__main__':main()
