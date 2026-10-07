"""Download CCAV V4 through its public ScienceDB file links and verify MD5.

The frozen public_file_listing.json was retrieved from ScienceDB's public
childrenFileListByPath endpoint via the dataset landing page on 2026-10-07.
Full national rasters stay local; derived site clips can be version controlled.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
import requests

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--directory',type=Path,default=Path('external_data/ccav_20261007'))
    ap.add_argument('--verify-only',action='store_true')
    args=ap.parse_args();p=args.directory
    listing=json.loads((p/'public_file_listing.json').read_text())['data']
    assert len(listing)==3 and all(r['version']=='V4' for r in listing)
    session=requests.Session();session.trust_env=False;rows=[]
    for rec in listing:
        f=p/rec['fileName'];assert f.parent==p
        url='https://china.scidb.cn/download?fileId='+rec['id']
        if not f.exists() and not args.verify_only:
            temp=f.with_suffix(f.suffix+'.tmp')
            with session.get(url,timeout=(30,90),stream=True) as response:
                response.raise_for_status()
                with temp.open('wb') as out:
                    for block in response.iter_content(1024*1024):out.write(block)
            temp.rename(f)
        b=f.read_bytes()
        assert len(b)==rec['size'] and hashlib.md5(b).hexdigest()==rec['md5'],f.name
        rows.append(dict(filename=f.name,bytes=len(b),md5=rec['md5'],sha256=hashlib.sha256(b).hexdigest(),provider_md5_verified=True,url=url))
        print('Verified',f.name,flush=True)
    manifest={'doi':'10.57760/sciencedb.31077','version':'V4','license':'CC-BY-4.0',
        'attribution':'Yuying Li et al., CCAV-10m, Science Data Bank, V4 (2026)',
        'landing_page':'https://www.scidb.cn/detail?dataSetId=a085f16794464c869ad6511f1a887ffe',
        'files':rows}
    (p/'download_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(p/'CCAV-10mV4.zip') as z:
        dest=(p/'extracted').resolve()
        for info in z.infolist():
            target=(dest/info.filename).resolve()
            assert target.is_relative_to(dest) and info.file_size<1_000_000_000
            if not target.exists() or target.stat().st_size!=info.file_size:z.extract(info,dest)

if __name__=='__main__':main()
