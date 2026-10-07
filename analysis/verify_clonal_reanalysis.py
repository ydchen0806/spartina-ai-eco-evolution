"""Independent integrity, design and regression checks for the clonal reanalysis."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression

ROOT=Path(__file__).resolve().parents[1]

def main():
    source=ROOT/'external_data/clonal_common_garden_20261007'
    out=ROOT/'data/derived/clonal_common_garden_20261007'
    manifest=json.loads((source/'download_manifest.json').read_text())
    payload=(source/manifest['file']).read_bytes()
    assert hashlib.sha256(payload).hexdigest()==manifest['sha256']
    assert hashlib.md5(payload).hexdigest()==manifest['md5']
    d=pd.read_csv(source/manifest['file']);d.columns=d.columns.str.strip()
    assert len(d)==400 and not d.duplicated(['Common_garden','Block','Provenance']).any()
    traits={'ramets':'Peak number of ramet','emergence':'Ramet emergence day'}
    c=pd.read_csv(out/'garden_origin_trait_summary.csv')
    assert len(c)==48 and c.groupby('trait')['observed'].sum().to_dict()=={'emergence':338,'ramets':344}
    adjustment=pd.read_csv(out/'block_sensitivity_origin_means.csv').query("scenario == 'block_adjusted_additive'")
    max_error=0.
    # Independent parameterization: full one-hot encoding + sklearn's intercept,
    # rather than a reference category and direct numpy least squares.
    for trait,col in traits.items():
        for garden,g in d.groupby('Common_garden'):
            obs=g.dropna(subset=[col]);cols=['Provenance','Block']
            X=pd.get_dummies(obs[cols].astype(str),drop_first=False,dtype=float)
            model=LinearRegression().fit(X,obs[col])
            query=g[cols].copy();Z=pd.get_dummies(query.astype(str),drop_first=False,dtype=float).reindex(columns=X.columns,fill_value=0.)
            query['prediction']=model.predict(Z)
            expected=query.groupby('Provenance').prediction.mean().sort_index()
            actual=adjustment[(adjustment.trait==trait)&(adjustment.garden==garden)].set_index('origin').estimate.sort_index()
            err=float(np.max(np.abs(expected.to_numpy()-actual.to_numpy())));max_error=max(max_error,err)
            assert err<1e-8
    clines=pd.read_csv(out/'latitude_clines_exact_permutation.csv')
    for row in clines.itertuples():
        sub=c[(c.trait==row.trait)&(c.garden==row.garden)]
        assert abs(spearmanr(sub.latitude,sub['mean']).statistic-row.spearman_rho)<1e-12
        assert row.maxT_adjusted_p+1e-12>=row.exact_two_sided_p
        assert abs(row.exact_two_sided_p*40320-round(row.exact_two_sided_p*40320))<1e-8
    draws=pd.read_csv(out/'garden_contrast_bootstrap_draws.csv.gz')
    assert draws.groupby(['trait','scheme','contrast']).size().eq(5000).all()
    assert draws.groupby(['trait','scheme','contrast']).ngroups==12
    preds=pd.read_csv(out/'leave_origin_out_predictions.csv')
    assert len(preds)==144 and not preds.duplicated(['trait','model','held_out_origin','garden']).any()
    for row in preds[preds.model=='garden_mean'].itertuples():
        train=c[(c.trait==row.trait)&(c.garden==row.garden)&(c.origin!=row.held_out_origin)]
        assert len(train)==7 and abs(train['mean'].mean()-row.prediction)<1e-10
    folds=pd.read_csv(out/'fold_manifest.csv')
    assert len(folds)==8
    for row in folds.itertuples():
        assert len(row.training_origins.split(';'))==7 and row.held_out_origin not in row.training_origins.split(';')
    reference=pd.read_csv(out/'block_adjusted_latitude_clines.csv')
    z=reference[(reference.trait=='emergence')&(reference.garden=='Zhanjiang')].iloc[0]
    assert np.isclose(z.linear_slope_per_latitude_degree,-.04261836847818077,atol=1e-8)
    result={'source_digest_verified':True,'unique_record_keys':400,'source_populations':8,'trait_cells':48,
        'independent_block_regression_max_abs_difference':max_error,'exact_permutation_quantization_checked':True,
        'bootstrap_groups':12,'draws_per_group':5000,'whole_origin_folds':8,'prediction_rows':144,
        'interpretation':'Checks verify numerical implementation and data bookkeeping, not unknown design metadata or biological causality.'}
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    packages=['numpy','pandas','scipy','matplotlib','scikit-learn','requests','huggingface_hub']
    (out/'software_versions.json').write_text(json.dumps({'python':platform.python_version(),'packages':{p:importlib.metadata.version(p) for p in packages}},indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
