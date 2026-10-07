"""Independently verify source-cell means and every held-out baseline from raw CSVs."""
import argparse,csv,hashlib,json,math
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 audit=json.loads((a.output/'audit.json').read_text())
 for name,sha in audit['source_sha256'].items():assert hashlib.sha256((a.source/name).read_bytes()).hexdigest()==sha
 with (a.source/'BOT-GCED-1912_Greenhouse_1_0.CSV').open() as f:
  rows=list(csv.reader(f));names=rows[2];records=[dict(zip(names,row)) for row in rows[5:] if row]
 assert len(records)==720 and len({(r['Year'],r['Range'],r['Location'],r['Block_design']) for r in records})==720
 cells=defaultdict(list)
 for r in records:
  for trait in ['Plant_height','Seed_set']:
   if r[trait]:
    val=float(r[trait]);assert val>=0
    if trait=='Seed_set':assert val<=100
    cells[(trait,r['Range'],r['Location'],int(r['Year']))].append(val)
 means={k:sum(v)/len(v) for k,v in cells.items()}
 pred=pd.read_csv(a.output/'leave_location_out_predictions.csv');assert len(pred)==408
 maxerr=0
 for _,r in pred.iterrows():
  key=(r.trait,r['range'],r.heldout_location,int(r.year));assert abs(means[key]-r.observed)<1e-10
  if r.model=='range_year_mean':
   pool=[v for (t,region,loc,yr),v in means.items() if t==r.trait and region==r['range'] and yr==r.year and loc!=r.heldout_location]
   expected=sum(pool)/len(pool);maxerr=max(maxerr,abs(expected-r.predicted))
 assert maxerr<1e-10
 assert not pred.duplicated(['trait','heldout_location','year','model']).any()
 for _,sub in pred.groupby(['trait','model']):assert len(sub)==68 and sub.heldout_location.nunique()==24
 for _,r in pd.read_csv(a.output/'leave_location_out_metrics.csv').iterrows():
  sub=pred[(pred.trait==r.trait)&(pred.model==r.model)]
  assert abs(math.sqrt(np.mean((sub.observed-sub.predicted)**2))-r.rmse)<1e-10
 draw=pd.read_csv(a.output/'bootstrap_draws.csv.gz');assert len(draw)==30000 and not draw.duplicated(['draw','year','trait']).any()
 for _,r in pd.read_csv(a.output/'range_contrasts.csv').iterrows():
  values=draw[(draw.trait==r.trait)&(draw.year==r.year)].china_minus_usa
  assert len(values)==5000
  assert abs(np.quantile(values,.025)-r.lower)<1e-10 and abs(np.quantile(values,.975)-r.upper)<1e-10
 verification={'status':'passed','raw_rows':720,'raw_source_hashes_match':True,'heldout_predictions':408,'heldout_locations':24,'baseline_independent_max_abs_error':maxerr,'bootstrap_draws':30000,'limitations':'Numerical and split verification does not validate biological identity, missingness assumptions or causal inference.'}
 (a.output/'verification.json').write_text(json.dumps(verification,indent=2));print(json.dumps(verification,indent=2))
if __name__=='__main__':main()
