from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse,hashlib,json,time
from datetime import datetime,timezone
parser=argparse.ArgumentParser(description='Verify every recovered file against the transfer manifest.')
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
root=args.source
out=args.output
out.mkdir(parents=True,exist_ok=True)
manifest=json.loads((root/'recovery_manifest.json').read_text())
def verify(rec):
 p=root/rec['relative_path']; h=hashlib.sha256()
 try:
  with p.open('rb') as f:
   while b:=f.read(8*1024*1024): h.update(b)
  return {'path':rec['relative_path'],'bytes':p.stat().st_size,'sha256':h.hexdigest(),'matches':p.stat().st_size==rec['bytes'] and h.hexdigest()==rec['sha256']}
 except Exception as e:return {'path':rec['relative_path'],'matches':False,'error':str(e)}
t=time.monotonic();results=[]
with ThreadPoolExecutor(max_workers=4) as pool:
 for i,res in enumerate(pool.map(verify,manifest['files']),1):
  results.append(res)
  if i%100==0:print('verified',i,flush=True)
a={'verified_at':datetime.now(timezone.utc).isoformat(),'files':len(results),'bytes':sum(r.get('bytes',0) for r in results),'failures':[r for r in results if not r['matches']], 'elapsed_seconds':round(time.monotonic()-t,1),'results':results}
(out/'fresh_hash_verification.json').write_text(json.dumps(a,indent=2))
print({k:v for k,v in a.items() if k!='results'},flush=True)

if a["failures"]: raise SystemExit(1)
