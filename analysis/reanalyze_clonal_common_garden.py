"""Exploratory provenance-level reanalysis of Chen's public clonal-trait experiment.

CC-BY-4.0 source: 10.6084/m9.figshare.33329481.v1. Block independence and
calendar meaning of emergence day are not fully documented. No genotype or
fitness identifiers exist. Never infer local historical evolution from this table.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import r2_score,mean_absolute_error,mean_squared_error

GARDENS=['Dongying','Taizhou','Zhanjiang']
TRAITS={'ramets':'Peak number of ramet','emergence':'Ramet emergence day'}
SEED=20261007


def slope(x,y):
    x=np.asarray(x);y=np.asarray(y);xc=x-x.mean()
    return float(xc@(y-y.mean())/(xc@xc)) if xc@xc>1e-12 else np.nan


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--output',type=Path,default=Path('data/derived/clonal_common_garden_20261007'))
    ap.add_argument('--bootstrap',type=int,default=5000)
    args=ap.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    files=list(args.source.glob('*.csv'));assert len(files)==1
    raw=files[0].read_bytes();manifest=json.loads((args.source/'download_manifest.json').read_text())
    assert hashlib.sha256(raw).hexdigest()==manifest['sha256']
    d=pd.read_csv(files[0]);d.columns=d.columns.str.strip()
    assert not d.duplicated(['Common_garden','Block','Provenance']).any()
    assert set(d.Common_garden)==set(GARDENS) and len(d)==400
    origins=d.groupby('Provenance').Latitude.first().sort_values().index.tolist()
    latitude=d.groupby('Provenance').Latitude.first().reindex(origins).to_numpy()
    assert len(origins)==8 and d.groupby('Provenance').Latitude.nunique().eq(1).all()
    climates=['Latitude','MAT','MAP','Soil salinity','Soil water content','Tidal range','AGDD','TAR']
    assert d.groupby('Provenance')[climates].nunique().eq(1).all().all()
    env=d.groupby('Provenance')[climates].first().reindex(origins)
    env.to_csv(out/'origin_environment.csv');env.corr().to_csv(out/'origin_environment_correlations.csv')
    key=['Common_garden','Provenance'];cells=[]
    for (garden,origin),g in d.groupby(key):
        for trait,column in TRAITS.items():
            vals=g[column].dropna();assert (vals>0).all()
            if trait=='ramets':assert np.allclose(vals,np.round(vals))
            cells.append(dict(garden=garden,origin=origin,latitude=float(g.Latitude.iloc[0]),trait=trait,
                listed_rows=len(g),observed=len(vals),missing=int(g[column].isna().sum()),
                mean=float(vals.mean()),std=float(vals.std()),median=float(vals.median()),
                missing_fraction=float(g[column].isna().mean())))
    c=pd.DataFrame(cells);c.to_csv(out/'garden_origin_trait_summary.csv',index=False)
    d.rename(columns={v:k for k,v in TRAITS.items()}).to_csv(out/'audited_records.csv',index=False)
    means={trait:c[c.trait==trait].pivot(index='origin',columns='garden',values='mean').reindex(index=origins,columns=GARDENS).to_numpy() for trait in TRAITS}
    # Exact provenance-label permutations: same latitude permutation across gardens/traits.
    perms=np.asarray(list(itertools.permutations(range(8))),dtype=int)
    xr=rankdata(latitude);xr-=xr.mean();xp=xr[perms]
    yr=[];obs=[];labels=[]
    for trait in TRAITS:
        for j,garden in enumerate(GARDENS):
            y=rankdata(means[trait][:,j]);y-=y.mean();yr.append(y)
            obs.append(float(xr@y/np.sqrt((xr@xr)*(y@y))));labels.append((trait,garden))
    yr=np.asarray(yr);denom=np.sqrt((xr@xr)*(yr*yr).sum(axis=1))
    perm_r=xp@yr.T/denom
    maxstat=np.abs(perm_r).max(axis=1)
    clines=[]
    for k,(trait,garden) in enumerate(labels):
        j=GARDENS.index(garden);y=means[trait][:,j]
        loo=[slope(np.delete(latitude,i),np.delete(y,i)) for i in range(8)]
        clines.append(dict(trait=trait,garden=garden,origins=8,spearman_rho=obs[k],
            exact_two_sided_p=float(np.mean(np.abs(perm_r[:,k])>=abs(obs[k])-1e-12)),
            maxT_adjusted_p=float(np.mean(maxstat>=abs(obs[k])-1e-12)),
            linear_slope_per_latitude_degree=slope(latitude,y),
            leave_one_origin_out_slope_min=min(loo),leave_one_origin_out_slope_max=max(loo)))
    pd.DataFrame(clines).to_csv(out/'latitude_clines_exact_permutation.csv',index=False)
    # Provenance-only and crossed provenance + within-garden block bootstrap.
    rng=np.random.default_rng(SEED);boot=[];discarded=0
    arrays={}
    for trait,col in TRAITS.items():
        for garden in GARDENS:
            arrays[(trait,garden)]=d[d.Common_garden==garden].pivot(index='Provenance',columns='Block',values=col).reindex(origins).to_numpy()
    for b in range(args.bootstrap):
        oi=rng.integers(0,8,8)
        block_indices={g:rng.integers(0,arrays[('ramets',g)].shape[1],arrays[('ramets',g)].shape[1]) for g in GARDENS}
        for trait in TRAITS:
            src=means[trait][oi]
            vals=[]
            for garden in GARDENS:
                a=arrays[(trait,garden)][oi][:,block_indices[garden]]
                n=np.isfinite(a).sum(axis=1)
                vals.append(np.divide(np.nansum(a,axis=1),n,out=np.full(8,np.nan),where=n>0))
            crossed=np.column_stack(vals)
            for scheme,a in [('origin',src),('origin_and_block',crossed)]:
                if not np.isfinite(a).all():discarded+=1;continue
                for low,high in [('Zhanjiang','Dongying'),('Taizhou','Dongying'),('Zhanjiang','Taizhou')]:
                    value=float(np.mean(a[:,GARDENS.index(low)]-a[:,GARDENS.index(high)]))
                    boot.append(dict(draw=b,trait=trait,scheme=scheme,contrast=low+' minus '+high,value=value))
    boot=pd.DataFrame(boot);boot.to_csv(out/'garden_contrast_bootstrap_draws.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    contrasts=[]
    for trait in TRAITS:
        for low,high in [('Zhanjiang','Dongying'),('Taizhou','Dongying'),('Zhanjiang','Taizhou')]:
            delta=means[trait][:,GARDENS.index(low)]-means[trait][:,GARDENS.index(high)]
            for scheme in ['origin','origin_and_block']:
                b=boot[(boot.trait==trait)&(boot.scheme==scheme)&(boot.contrast==low+' minus '+high)].value
                contrasts.append(dict(trait=trait,contrast=low+' minus '+high,scheme=scheme,mean_difference=float(delta.mean()),
                    percentile_low=float(b.quantile(.025)),percentile_high=float(b.quantile(.975)),
                    bootstrap_draws=len(b),leave_one_origin_out_min=min(np.delete(delta,i).mean() for i in range(8)),
                    leave_one_origin_out_max=max(np.delete(delta,i).mean() for i in range(8))))
    pd.DataFrame(contrasts).to_csv(out/'garden_contrasts.csv',index=False)
    # Missingness is not coded as mortality. These are explicitly hypothetical scenarios.
    scenarios=[]
    for name,value in [('observed_only',None),('missing_as_zero',0.),('missing_as_observed_max',float(d[TRAITS['ramets']].max()))]:
        z=d.copy()
        if value is not None:z[TRAITS['ramets']]=z[TRAITS['ramets']].fillna(value)
        a=z.groupby(key)[TRAITS['ramets']].mean().unstack(0).reindex(index=origins,columns=GARDENS)
        for garden in GARDENS:
            scenarios.append(dict(scenario=name,garden=garden,origin_balanced_mean=float(a[garden].mean()),
                latitude_slope=slope(latitude,a[garden].to_numpy()),zhanjiang_minus_dongying=float((a.Zhanjiang-a.Dongying).mean())))
    pd.DataFrame(scenarios).to_csv(out/'ramet_missingness_scenarios.csv',index=False)
    # Sensitivity to unequal block counts and observed block composition.
    sensitivity=[]
    for trait,col in TRAITS.items():
        for garden in GARDENS:
            sub=d[d.Common_garden==garden].dropna(subset=[col]).copy()
            block_levels=sorted(d[d.Common_garden==garden].Block.unique())
            def design(frame):
                return np.column_stack([np.ones(len(frame))]+[(frame.Provenance==o).to_numpy(dtype=float) for o in origins[1:]]+[(frame.Block==b).to_numpy(dtype=float) for b in block_levels[1:]])
            X=design(sub);assert np.linalg.matrix_rank(X)==X.shape[1]
            beta=np.linalg.lstsq(X,sub[col].to_numpy(),rcond=None)[0]
            all_cells=pd.DataFrame(list(itertools.product(origins,block_levels)),columns=['Provenance','Block'])
            all_cells['prediction']=design(all_cells)@beta
            adjusted=all_cells.groupby('Provenance').prediction.mean().reindex(origins)
            first10=d[(d.Common_garden==garden)&(d.Block<=10)].groupby('Provenance')[col].mean().reindex(origins)
            for scenario,values in [('block_adjusted_additive',adjusted),('recorded_blocks_1_to_10',first10)]:
                if scenario=='block_adjusted_additive':assert values.notna().all()
                for origin,value in values.items():sensitivity.append(dict(trait=trait,garden=garden,scenario=scenario,origin=origin,estimate=float(value)))
    sensitivity=pd.DataFrame(sensitivity);sensitivity.to_csv(out/'block_sensitivity_origin_means.csv',index=False)
    block_summary=[]
    for (trait,scenario),g in sensitivity.groupby(['trait','scenario']):
        a=g.pivot(index='origin',columns='garden',values='estimate').reindex(index=origins,columns=GARDENS)
        common=a.dropna();positions=[origins.index(o) for o in common.index]
        for garden in GARDENS:block_summary.append(dict(trait=trait,scenario=scenario,garden=garden,
            shared_origins=len(common),excluded_origins=';'.join(o for o in origins if o not in common.index),
            origin_balanced_mean=float(common[garden].mean()),latitude_slope=slope(latitude[positions],common[garden]),
            zhanjiang_minus_dongying=float((common.Zhanjiang-common.Dongying).mean())))
    pd.DataFrame(block_summary).to_csv(out/'block_sensitivity_summary.csv',index=False)
    adjusted_clines=[];adjusted_ranks=[]
    for trait,garden in labels:
        a=sensitivity[(sensitivity.trait==trait)&(sensitivity.garden==garden)&(sensitivity.scenario=='block_adjusted_additive')].set_index('origin').estimate.reindex(origins)
        y=rankdata(a);y-=y.mean();adjusted_ranks.append(y)
        adjusted_clines.append(dict(trait=trait,garden=garden,linear_slope_per_latitude_degree=slope(latitude,a),
            spearman_rho=float(xr@y/np.sqrt((xr@xr)*(y@y)))))
    ar=np.asarray(adjusted_ranks);pr=xp@ar.T/np.sqrt((xr@xr)*(ar*ar).sum(axis=1));maximum=np.abs(pr).max(axis=1)
    for k,row in enumerate(adjusted_clines):
        row['exact_two_sided_p']=float(np.mean(np.abs(pr[:,k])>=abs(row['spearman_rho'])-1e-12))
        row['maxT_adjusted_p']=float(np.mean(maximum>=abs(row['spearman_rho'])-1e-12))
    pd.DataFrame(adjusted_clines).to_csv(out/'block_adjusted_latitude_clines.csv',index=False)
    block_records=[]
    for (garden,block),g in d.groupby(['Common_garden','Block']):
        for trait,col in TRAITS.items():block_records.append(dict(garden=garden,block=int(block),trait=trait,
            observed=int(g[col].notna().sum()),mean=float(g[col].mean())))
    pd.DataFrame(block_records).to_csv(out/'recorded_block_summary.csv',index=False)
    halves=d.copy();halves['recorded_block_range']=np.where(halves.Block<=10,'1-10','11-20')
    half_rows=[]
    for (garden,origin,half),g in halves.groupby(['Common_garden','Provenance','recorded_block_range']):
        for trait,col in TRAITS.items():half_rows.append(dict(garden=garden,origin=origin,block_range=half,trait=trait,
            rows=len(g),observed=int(g[col].notna().sum()),mean=float(g[col].mean())))
    pd.DataFrame(half_rows).to_csv(out/'block_range_missingness.csv',index=False)
    # Whole-provenance holdout; all 3 cells of the test origin are withheld together.
    predictions=[]
    for trait in TRAITS:
        a=c[c.trait==trait].copy().sort_values(['origin','garden']).reset_index(drop=True)
        enc=np.column_stack([(a.garden==g).astype(float).to_numpy() for g in GARDENS])
        X=np.column_stack([enc,a.latitude.to_numpy()]);y=a['mean'].to_numpy()
        for test_origin in origins:
            test=a.origin.eq(test_origin).to_numpy();train=~test
            assert set(a.loc[train,'origin']).isdisjoint(set(a.loc[test,'origin']))
            pred_mean=np.array([a.loc[train&a.garden.eq(g),'mean'].mean() for g in a.loc[test,'garden']])
            pred_linear=[]
            for g,x in zip(a.loc[test,'garden'],a.loc[test,'latitude']):
                sub=a[train&a.garden.eq(g)];x0=sub.latitude.mean();y0=sub['mean'].mean()
                pred_linear.append(y0+slope(sub.latitude,sub['mean'])*(x-x0))
            model=ExtraTreesRegressor(n_estimators=200,min_samples_leaf=2,max_features=1.,random_state=SEED,n_jobs=1)
            model.fit(X[train],y[train]);pred_tree=model.predict(X[test])
            for name,pred in [('garden_mean',pred_mean),('garden_linear_latitude',pred_linear),('extra_trees',pred_tree)]:
                for idx,val in zip(np.flatnonzero(test),pred):
                    predictions.append(dict(trait=trait,held_out_origin=test_origin,garden=a.garden.iloc[idx],
                        model=name,observed=y[idx],prediction=float(val),training_origins=7,training_cells=21,test_cells=3))
    pred=pd.DataFrame(predictions);pred.to_csv(out/'leave_origin_out_predictions.csv',index=False)
    pd.DataFrame([dict(held_out_origin=o,training_origins=';'.join(x for x in origins if x!=o),
        training_cells=21,test_cells=3,gardens=';'.join(GARDENS)) for o in origins]).to_csv(out/'fold_manifest.csv',index=False)
    metrics=[]
    for (trait,name),g in pred.groupby(['trait','model']):
        baseline=pred[(pred.trait==trait)&(pred.model=='garden_mean')]
        sse=float(np.square(g.observed-g.prediction).sum());ref=float(np.square(baseline.observed-baseline.prediction).sum())
        metrics.append(dict(trait=trait,model=name,n_cells=len(g),n_origins=8,
            rmse=float(np.sqrt(mean_squared_error(g.observed,g.prediction))),mae=float(mean_absolute_error(g.observed,g.prediction)),
            pooled_r2=float(r2_score(g.observed,g.prediction)),skill_vs_garden_mean=1-sse/ref))
    metrics=pd.DataFrame(metrics);metrics.to_csv(out/'leave_origin_out_metrics.csv',index=False)
    # Descriptive trait coupling at the provenance-mean level; not a genetic covariance.
    coupling=[]
    for j,garden in enumerate(GARDENS):
        x=means['emergence'][:,j];y=means['ramets'][:,j]
        coupling.append(dict(garden=garden,origins=8,pearson_r=float(np.corrcoef(x,y)[0,1]),spearman_rho=float(np.corrcoef(rankdata(x),rankdata(y))[0,1])))
    pd.DataFrame(coupling).to_csv(out/'descriptive_trait_coupling.csv',index=False)
    report={'dataset_doi':manifest['doi'],'source_sha256':manifest['sha256'],'source_rows':len(d),'origins':origins,
        'gardens':GARDENS,'blocks_by_garden':d.groupby('Common_garden').Block.nunique().to_dict(),
        'observed_by_trait':{k:int(d[v].notna().sum()) for k,v in TRAITS.items()},
        'missing_by_trait':{k:int(d[v].isna().sum()) for k,v in TRAITS.items()},
        'source_environment_independent_units':8,'seed':SEED,'bootstrap_requested':args.bootstrap,
        'bootstrap_empty_cell_scheme_draws_discarded':discarded,'exact_permutations':len(perms),
        'multiplicity_family':'6 latitude-cline tests, max absolute Spearman statistic; shared origin-label permutation',
        'limitations':['Exploratory reanalysis of public dataset, not a preregistered confirmatory experiment.',
          'No linked article, calendar, genotype IDs, seed-family IDs or missingness explanation supplied.',
          'Garden contrasts combine climate and all other location conditions; no causal temperature effect.',
          'Source-population effects may include genetics, maternal and carry-over effects; not proof of heritability.',
          'Block labels treated as within-garden blocks; independence not established by metadata.',
          'Only 8 origin units; 400 rows do not provide 400 independent climate replicates.',
          'Observed-only targets condition on availability; missing-as-zero and observed-max are scenarios, not biological bounds.',
          'Bootstrap CIs are pointwise exploratory intervals; permutation exchangeability is an assumption.',
          'No local temporal adaptation, fitness advantage or independent-site AI transfer is demonstrated.']}
    (out/'analysis_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    fig,axs=plt.subplots(2,2,figsize=(10,7),layout='constrained');cmap=plt.get_cmap('viridis');norm=plt.Normalize(latitude.min(),latitude.max())
    for j,trait in enumerate(['emergence','ramets']):
        ax=axs[0,j]
        for i,origin in enumerate(origins):ax.plot(range(3),means[trait][i],'-o',c=cmap(norm(latitude[i])),label=origin,ms=4)
        ax.set(xticks=range(3),xticklabels=GARDENS,ylabel='Recorded emergence day' if trait=='emergence' else 'Peak ramet number',
            title=('a  Emergence timing' if j==0 else 'b  Clonal production'))
        missing=c[c.trait==trait].pivot(index='origin',columns='garden',values='missing_fraction').reindex(index=origins,columns=GARDENS)
        ax=axs[1,j];ax.imshow(missing.to_numpy(),vmin=0,vmax=.6,cmap='Blues',aspect='auto')
        ax.set(xticks=range(3),xticklabels=GARDENS,yticks=range(8),yticklabels=[f'{o} ({lat:g}°N)' for o,lat in zip(origins,latitude)],title=('c  Missing emergence records' if j==0 else 'd  Missing ramet records'))
        for i in range(8):
            for k in range(3):ax.text(k,i,f'{missing.iloc[i,k]:.0%}',ha='center',va='center',color='white' if missing.iloc[i,k]>.35 else '#172a33',fontsize=8)
    cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=axs[0,:],shrink=.9);cb.set_label('Origin latitude (°N)')
    for ext in ['png','pdf','svg']:fig.savefig(out/f'clonal_reaction_norms.{ext}',dpi=240)
    plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(9,3.8),layout='constrained')
    order=['garden_mean','garden_linear_latitude','extra_trees']
    for ax,trait,title in zip(axs,['emergence','ramets'],['Emergence timing','Peak ramet number']):
        g=metrics[metrics.trait==trait].set_index('model').loc[order]
        ax.bar(range(3),g.skill_vs_garden_mean,color=['#9aa6ac','#178a9b','#c44e52']);ax.axhline(0,color='black',lw=.7)
        ax.set(xticks=range(3),xticklabels=['Garden mean','Garden + latitude','Extra Trees'],ylabel='Squared-error skill vs garden mean',title=title)
        ax.tick_params(axis='x',rotation=20)
        for i,v in enumerate(g.skill_vs_garden_mean):ax.annotate(f'{v:.2f}',(i,v),xytext=(0,4 if v>=0 else -12),textcoords='offset points',ha='center',fontsize=8)
    fig.supxlabel('All three cells of each source population withheld together; 8 folds, 24 cells',fontsize=8)
    for ext in ['png','pdf','svg']:fig.savefig(out/f'clonal_leave_origin_out.{ext}',dpi=240)
    fig,axs=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    raw_y=means['emergence'][:,2]
    adj=sensitivity[(sensitivity.trait=='emergence')&(sensitivity.garden=='Zhanjiang')&(sensitivity.scenario=='block_adjusted_additive')].set_index('origin').estimate.reindex(origins).to_numpy()
    for y,label,col in [(raw_y,'Observed cell mean','#c44e52'),(adj,'Additive block adjustment','#178a9b')]:
        axs[0].scatter(latitude,y,color=col,label=label)
        axs[0].plot(latitude,y.mean()+slope(latitude,y)*(latitude-latitude.mean()),color=col)
    axs[0].set(xlabel='Origin latitude (°N)',ylabel='Recorded emergence day',title='a  Zhanjiang: sensitivity to block composition')
    axs[0].legend(frameon=False,fontsize=8)
    z=d[d.Common_garden=='Zhanjiang']
    for origin,lat in zip(origins,latitude):
        g=z[z.Provenance==origin];axs[1].scatter(g.Block,g[TRAITS['emergence']],c=[cmap(norm(lat))],s=16,alpha=.7)
    axs[1].axvline(10.5,color='#7d858c',ls=':',lw=1)
    axs[1].set(xlabel='Recorded block identifier',ylabel='Recorded emergence day',title='b  Observed timing and missing records')
    fig.supxlabel('Block meaning and missingness causes are undocumented; adjustment is a sensitivity analysis',fontsize=8)
    for ext in ['png','pdf','svg']:fig.savefig(out/f'clonal_block_sensitivity.{ext}',dpi=240)
    print('AUDIT',json.dumps(report,indent=2))
    print('CLINES',pd.DataFrame(clines).to_string(index=False))
    print('CONTRASTS',pd.DataFrame(contrasts).to_string(index=False))
    print('PREDICTION',metrics.to_string(index=False))

if __name__=='__main__':main()
