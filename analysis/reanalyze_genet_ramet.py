"""Audit published genet/ramet identities; descriptive external comparator, not local validation."""
from pathlib import Path
import io, json, hashlib, zipfile
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT/'external_data/xmu_literature_20261007/genet_ramet'
OUT = ROOT/'data/derived/genet_ramet_20261007'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((SRC/'manifest.json').read_text())
    raw = (SRC/'source.zip').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == manifest['sha256']
    assert hashlib.md5(raw).hexdigest() == manifest['file']['computed_md5']
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        d = pd.read_excel(io.BytesIO(z.read('genotype data/Tomasula_SALT_MLL_pop_patch_x_y.xlsx')))
        (OUT/'source_metadata.txt').write_bytes(z.read('genotype data/0.metadata.txt'))
    assert d.notna().all().all()
    assert not d.duplicated(['Patch','x','y']).any()
    assert d.Individual.is_unique
    assert d.groupby('Population').Patch.nunique().eq(1).all()
    d.to_csv(OUT/'audited_samples.csv', index=False)
    counts = d.groupby(['Patch','clone']).size().rename('sampled_ramets').reset_index()
    counts.to_csv(OUT/'patch_lineage_counts.csv',index=False)
    rows=[]
    for patch,g in d.groupby('Patch',sort=True):
        c=g.clone.value_counts().to_numpy();n=len(g)
        rows.append(dict(patch=patch,sampled_stems=n,lineages=len(c),richness=(len(c)-1)/(n-1),
                         largest_lineage_fraction=c.max()/n,
                         same_lineage_random_pair_probability=sum(c*(c-1))/(n*(n-1))))
    summary=pd.DataFrame(rows)
    summary.to_csv(OUT/'patch_summary.csv',index=False)
    shared=d.groupby('clone').Patch.nunique(); shared=shared[shared>1]
    d[d.clone.isin(shared.index)].to_csv(OUT/'cross_patch_lineages.csv',index=False)
    audit=dict(source_doi=manifest['doi'], paper_doi=manifest['paper_doi'],
               sampled_stems=len(d),patches=d.Patch.nunique(),unique_lineages=d.clone.nunique(),
               patch_lineage_combinations=len(counts),shared_lineages=shared.index.tolist(),
               min_lineages_per_patch=int(summary.lineages.min()),max_lineages_per_patch=int(summary.lineages.max()),
               scope='Published threshold-8 multilocus lineage assignments; genotype calling and threshold choice not re-estimated. Native-range Georgetown study, not Xiamen University or local UAV validation.',
               interpretation='Field-defined patches and sampled stems are different units from inferred genetic lineages; no image-to-genotype correspondence or evolutionary rate is estimated.')
    (OUT/'audit.json').write_text(json.dumps(audit,indent=2))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7,'axes.labelsize':7,'axes.titlesize':7,
                         'xtick.labelsize':7,'ytick.labelsize':7,'pdf.fonttype':42,'ps.fonttype':42,
                         'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
    fig=plt.figure(figsize=(183/25.4,150/25.4),layout='constrained')
    gs=fig.add_gridspec(3,2,height_ratios=[1.2,.85,.85])
    ax=fig.add_subplot(gs[0,0]); y=np.arange(len(summary))
    ax.barh(y,summary.sampled_stems,color='#B9CED9',label='Sampled stems')
    ax.barh(y,summary.lineages,color='#0072B2',label='Inferred lineages')
    ax.set(yticks=y,yticklabels=summary.patch,xlabel='Count within field-defined patch')
    ax.legend(frameon=False,fontsize=7);ax.set_title('a   Stems and genetic lineages',loc='left',fontweight='bold')
    ax=fig.add_subplot(gs[0,1]);ax.scatter(summary.largest_lineage_fraction,summary.richness,color='#009E73',s=20)
    for _,r in summary[summary.patch.isin(['Black','Green','Pink'])].iterrows():ax.annotate(r.patch,(r.largest_lineage_fraction,r.richness),xytext=(3,3),textcoords='offset points',fontsize=6.5)
    ax.set(xlabel='Fraction in largest sampled lineage',ylabel='Genotypic richness, (G − 1)/(N − 1)',xlim=(0,1),ylim=(0,.65))
    ax.set_title('b   Variation among ten patches',loc='left',fontweight='bold')
    # All ten patches appear above. Two illustrative maps selected by extrema in lineage count.
    for row,patch,letter in [(1,summary.loc[summary.lineages.idxmin(),'patch'],'c'),(2,summary.loc[summary.lineages.idxmax(),'patch'],'d')]:
        ax=fig.add_subplot(gs[row,:]);g=d[d.Patch==patch];freq=g.clone.value_counts(); top=freq.index[0]
        for clone,t in g.groupby('clone'):
            color='#0072B2' if clone==top else '#D9DEE2'
            ax.scatter(t.y,t.x,c=color,s=165,marker='s',edgecolors='white',linewidths=.5)
            for _,r in t.iterrows():ax.text(r.y,r.x,str(r.clone),fontsize=6,ha='center',va='center',color='white' if clone==top else '#263238')
        ax.set(xlabel='Recorded y-coordinate (m)',ylabel='x (m)',yticks=[1,3,5],ylim=(.4,5.6),xlim=(.4,24))
        ax.set_title(f'{letter}   {patch} patch: {len(g)} stems, {g.clone.nunique()} lineages',loc='left',fontweight='bold')
    for ax in fig.axes:
        title=ax.get_title(loc='left')
        ax.set_title(title[1:].strip(),loc='left',fontsize=7)
        ax.text(-.10,1.05,title[0],transform=ax.transAxes,fontsize=8,fontweight='bold')
    for ext in ['png','pdf','svg']:fig.savefig(OUT/f'genet_ramet_units.{ext}',dpi=300)
    plt.close(fig)
    print(json.dumps(audit,indent=2))

if __name__=='__main__':main()
