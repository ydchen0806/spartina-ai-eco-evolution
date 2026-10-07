"""Design-aware descriptive reanalysis of the Xiamen common garden, GCE BOT-GCED-1912.

Keep outputs local until source-specific redistribution terms are reconciled.
No local adaptation or causal invasion effect is estimated.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
TRAITS=['Plant_height','Seed_set'];YEARS=[2015,2016,2017]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    tables={t:pd.read_csv(args.source/f'BOT-GCED-1912_{t}_1_0.CSV',skiprows=[0,1,3,4]) for t in ['Geographic','Greenhouse']};g=tables['Greenhouse'];field=tables['Geographic']
    assert len(g)==720 and len(field)==240
    assert not g.duplicated(['Year','Range','Location','Block_design']).any()
    assert g.groupby(['Range','Location','Block_design']).Year.nunique().eq(3).all()
    duplicate=g[g.duplicated(['Year','Range','Location','Subsite_family','Plot_number'],keep=False)]
    duplicate.to_csv(out/'ambiguous_plot_identifiers.csv',index=False)
    g['block']=g.Block_design.str.extract(r'(\d+)').astype(int)
    assert set(g.block)==set(range(1,11))
    missing=g.groupby(['Range','Year'])[TRAITS].agg(['size','count']);missing.to_csv(out/'missingness.csv')
    means=g.groupby(['Range','Location','Latitude','Year'])[TRAITS].mean().reset_index();means.to_csv(out/'location_year_means.csv',index=False)
    heights=g.pivot(index=['Range','Location','Block_design'],columns='Year',values='Plant_height')
    reappear=heights.loc[heights[2016].isna() & heights[2017].notna()];reappear.to_csv(out/'records_observed_after_missing_year.csv')
    # Explicit range-stratified location resampling and a shared block resample,
    # preserving the same locations and pools across years and both traits.
    location_info=g[['Range','Location','Latitude']].drop_duplicates().sort_values(['Range','Location'])
    arrays={}
    for region in ['China','USA']:
        locs=location_info[location_info.Range==region].Location.tolist()
        arrays[region]=np.array([[[g[(g.Location==loc)&(g.Year==yr)&(g.block==b)][TRAITS].iloc[0].to_numpy(float) for yr in YEARS] for b in range(1,11)] for loc in locs])
    rng=np.random.default_rng(20261007);draws=[]
    for draw in range(5000):
        blocks=rng.integers(0,10,10);values={}
        for region,arr in arrays.items():
            selected=arr[rng.integers(0,len(arr),len(arr))][:,blocks]
            count=np.isfinite(selected).sum(axis=1);sums=np.nansum(selected,axis=1)
            m=np.divide(sums,count,out=np.full_like(sums,np.nan),where=count>0)
            values[region]=np.nanmean(m,axis=0)
        delta=values['China']-values['USA']
        for yi,year in enumerate(YEARS):
            for ti,trait in enumerate(TRAITS):draws.append(dict(draw=draw,year=year,trait=trait,china_minus_usa=delta[yi,ti]))
    boot=pd.DataFrame(draws);boot.to_csv(out/'bootstrap_draws.csv.gz',index=False,compression='gzip')
    contrasts=[]
    for year in YEARS:
        m=means[means.Year==year]
        for trait in TRAITS:
            delta=m.groupby('Range')[trait].mean();b=boot[(boot.year==year)&(boot.trait==trait)].china_minus_usa
            contrasts.append(dict(year=year,trait=trait,china_minus_usa=delta.China-delta.USA,lower=b.quantile(.025),upper=b.quantile(.975),china_locations=int(m[m.Range=='China'][trait].count()),usa_locations=int(m[m.Range=='USA'][trait].count())))
    contrasts=pd.DataFrame(contrasts);contrasts.to_csv(out/'range_contrasts.csv',index=False)
    sens=[]
    for trait in TRAITS:
        complete=g.groupby(['Range','Location','Block_design'])[trait].transform('count').eq(3)
        for name,keep in [('all_observed',pd.Series(True,index=g.index)),('complete_three_year_records',complete),('shared_latitude_range',g.Latitude.between(27.7,39.05)),('exclude_ambiguous_plot_location',g.Location!='Luoyuan')]:
            sub=g[keep];m=sub.groupby(['Range','Location','Year'])[trait].mean().reset_index();vals=m.groupby(['Range','Year'])[trait].mean().unstack(0)
            for yr,row in vals.iterrows():sens.append(dict(trait=trait,scenario=name,year=yr,china_minus_usa=row.China-row.USA,china_locations=int(m[(m.Range=='China')&(m.Year==yr)][trait].count()),usa_locations=int(m[(m.Range=='USA')&(m.Year==yr)][trait].count())))
    pd.DataFrame(sens).to_csv(out/'sensitivity_contrasts.csv',index=False)
    # Associations use location means; years are not independent replication.
    repeat=[]
    for trait in TRAITS:
        for region in ['China','USA']:
            m=means[means.Range==region].pivot(index='Location',columns='Year',values=trait)
            for y1,y2 in [(2015,2016),(2015,2017),(2016,2017)]:
                sub=m[[y1,y2]].dropna();repeat.append(dict(trait=trait,range=region,year1=y1,year2=y2,n_locations=len(sub),spearman=sub.corr(method='spearman').iloc[0,1]))
    pd.DataFrame(repeat).to_csv(out/'location_rank_persistence.csv',index=False)
    # Fixed leave-location-out benchmark: every year of a source stays together.
    from sklearn.ensemble import ExtraTreesRegressor
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    predictions=[]
    for trait in TRAITS:
        m=means.dropna(subset=[trait]).reset_index(drop=True)
        def design(frame):
            r=(frame.Range=='China').to_numpy(float);lat=frame.Latitude.to_numpy(float)-32
            return np.column_stack([r,frame.Year==2016,frame.Year==2017,r*(frame.Year==2016),r*(frame.Year==2017),lat,r*lat])
        for location in sorted(m.Location.unique()):
            train=m[m.Location!=location];test=m[m.Location==location]
            assert set(train.Location).isdisjoint(test.Location)
            baseline=train.groupby(['Range','Year'])[trait].mean()
            models={'ridge':make_pipeline(StandardScaler(),Ridge(alpha=10)),
                    'extra_trees':ExtraTreesRegressor(n_estimators=200,min_samples_leaf=2,random_state=20261007,n_jobs=1)}
            values={'range_year_mean':np.array([baseline.loc[(r.Range,r.Year)] for _,r in test.iterrows()])}
            for name,model in models.items():model.fit(design(train),train[trait]);values[name]=model.predict(design(test))
            for name,pred in values.items():
                for (_,row),value in zip(test.iterrows(),pred):predictions.append(dict(trait=trait,heldout_location=location,range=row.Range,year=row.Year,model=name,observed=row[trait],predicted=value,n_training_locations=train.Location.nunique(),n_train=len(train)))
    pred=pd.DataFrame(predictions);pred.to_csv(out/'leave_location_out_predictions.csv',index=False)
    metrics=[]
    for (trait,model),sub in pred.groupby(['trait','model']):
        base=pred[(pred.trait==trait)&(pred.model=='range_year_mean')]
        mse=mean_squared_error(sub.observed,sub.predicted);bmse=mean_squared_error(base.observed,base.predicted)
        metrics.append(dict(trait=trait,model=model,n=len(sub),n_locations=sub.heldout_location.nunique(),rmse=mse**.5,mae=mean_absolute_error(sub.observed,sub.predicted),r2=r2_score(sub.observed,sub.predicted),skill_vs_range_year_mean=1-mse/bmse))
    pd.DataFrame(metrics).to_csv(out/'leave_location_out_metrics.csv',index=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7,'lines.linewidth':1.0,'axes.titlesize':7,'xtick.labelsize':7,'ytick.labelsize':7,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(2,2,figsize=(183/25.4,135/25.4),layout='constrained')
    for ti,(trait,label) in enumerate(zip(TRAITS,['Plant height (cm)','Seed set (%)'])):
        ax=axs[0,ti]
        for region,color in [('China','#D55E00'),('USA','#0072B2')]:
            sub=means[means.Range==region]
            for _,m in sub.groupby('Location'):ax.plot(m.Year,m[trait],color=color,alpha=.22,lw=.7)
            avg=sub.groupby('Year')[trait].mean();ax.plot(avg.index,avg.values,'o-',color=color,label=region,lw=1,ms=4)
        ax.set(xticks=YEARS,xlabel='Common-garden year',ylabel=label);ax.set_title(f'{"ab"[ti]}   Equal-weight location means',loc='left',fontweight='bold');ax.legend(frameon=False)
        ax=axs[1,ti];sub=contrasts[contrasts.trait==trait];ax.errorbar(sub.year,sub.china_minus_usa,yerr=[sub.china_minus_usa-sub.lower,sub.upper-sub.china_minus_usa],fmt='o',capsize=3,color='#333333');ax.axhline(0,color='#999999',ls='--',lw=.8);ax.set(xticks=YEARS,xlabel='Common-garden year',ylabel='China − USA ('+('cm' if ti==0 else 'percentage points')+')');ax.set_title(f'{"cd"[ti]}   Location × block bootstrap',loc='left',fontweight='bold')
    for ax in fig.axes:
        title=ax.get_title(loc='left')
        ax.set_title(title[1:].strip(),loc='left',fontsize=7)
        ax.text(-.10,1.05,title[0],transform=ax.transAxes,fontsize=8,fontweight='bold')
    for ext in ['pdf','svg','png']:fig.savefig(out/f'xmu_common_garden.{ext}',dpi=300)
    plt.close(fig)
    audit={'field_rows':len(field),'greenhouse_rows':len(g),'candidate_clone_keys':len(heights),'range_locations':location_info.groupby('Range').size().to_dict(),'repeated_years':YEARS,'duplicate_plot_key_rows':len(duplicate),'missing_2016_observed_2017':len(reappear),'independent_gardens':1,'garden':'Xiamen University Xiang’an campus, 24.62 N, 118.31 E','bootstrap':'5000 stratified-location and shared-block draws; year trajectories retained; pointwise exploratory percentile intervals. No random range assignment.','limits':['Candidate clone keys use location and pool; two Luoyuan plot identifiers duplicate.','Missingness is not mortality; later observations follow some missing records.','Subsite_family labels are subsites, not verified maternal families.','Shoot-density column omitted: name suggests per-square-metre units but garden methods describe pot counts.','One garden cannot demonstrate home-site advantage or local adaptation.','Common ancestry and overlap with other Chinese common-garden publications unresolved; do not pool as independent studies.'],'source_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in args.source.glob('*.CSV')}}
    (out/'audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2));print(contrasts.to_string(index=False))
if __name__=='__main__':main()
