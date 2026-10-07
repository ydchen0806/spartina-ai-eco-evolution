"""Download the public Xiamen Zhangjiang UAV archive, pinned V4, with provider MD5.

Raw and adapted data retain CC-BY-NC-SA-4.0; code licence does not replace it.
"""
import argparse,concurrent.futures,hashlib,json
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
def digest(p,algorithm):
 h=hashlib.new(algorithm)
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def download(rec,out):
 sub='DOM' if 'DOM' in rec['fileName'] else 'classified';folder=out/sub;folder.mkdir(exist_ok=True);p=folder/rec['fileName'];url='https://china.scidb.cn/download?fileId='+rec['id']
 if not (p.exists() and p.stat().st_size==rec['size'] and digest(p,'md5')==rec['md5']):
  for attempt in range(3):
   s=requests.Session();s.trust_env=False;part=p.with_suffix('.part')
   try:
    with s.get(url,stream=True,timeout=(30,90)) as r:
     r.raise_for_status()
     with part.open('wb') as f:
      for chunk in r.iter_content(4*1024*1024):f.write(chunk)
    assert part.stat().st_size==rec['size'] and digest(part,'md5')==rec['md5']
    part.replace(p);break
   except Exception:
    if attempt==2:raise
   finally:s.close()
 row={'file':str(p.relative_to(out)),'bytes':p.stat().st_size,'provider_md5':rec['md5'],'provider_md5_verified':True,'sha256':digest(p,'sha256'),'url':url};print('Verified',row['file'],flush=True);return row
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 m=json.loads((ROOT/'external_data/zhangjiang_uav_20261007/public_file_listing.json').read_text());assert len(m['files'])==20
 # Small maps first, then newest original imagery before historical imagery.
 ordered=sorted(m['files'],key=lambda r:('DOM' in r['fileName'],-int(r['fileName'][:6])))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(lambda r:download(r,a.output),ordered))
 result={'doi':m['doi'],'version':m['version'],'license':m['license'],'files':rows,'total_bytes':sum(r['bytes'] for r in rows),'all_provider_md5_verified':True}
 assert result['total_bytes']==1844072803
 (a.output/'download_manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Complete',len(rows),result['total_bytes'],flush=True)
if __name__=='__main__':main()
