"""Retrieve the versioned public clonal-trait dataset and verify the provider MD5.

Set MICAO_DOWNLOAD_PROXY to an existing HTTP proxy when direct access fails.
No credentials or proxy addresses are written to the provenance manifest.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import requests

DOI='10.6084/m9.figshare.33329481.v1'
API='https://api.figshare.com/v2/articles/33329481/versions/1'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=Path('external_data/clonal_common_garden_20261007'))
    ap.add_argument('--verify-only',action='store_true')
    args=ap.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    session=requests.Session();session.trust_env=False
    proxy=os.getenv('MICAO_DOWNLOAD_PROXY')
    if proxy:session.proxies={'http':proxy,'https':proxy}
    metadata_path=out/'article_metadata.json'
    if not args.verify_only:
        response=session.get(API,timeout=45);response.raise_for_status()
        metadata_path.write_text(json.dumps(response.json(),ensure_ascii=False,indent=2)+'\n')
    metadata=json.loads(metadata_path.read_text())
    assert metadata['version']==1 and metadata['doi']==DOI
    assert metadata['license']['name']=='CC BY 4.0' and len(metadata['files'])==1
    rec=metadata['files'][0];path=out/Path(rec['name']).name
    if not path.exists() and not args.verify_only:
        response=session.get(rec['download_url'],timeout=60);response.raise_for_status()
        assert len(response.content)==rec['size'] and hashlib.md5(response.content).hexdigest()==rec['computed_md5']
        path.write_bytes(response.content)
    payload=path.read_bytes()
    assert len(payload)==rec['size'] and hashlib.md5(payload).hexdigest()==rec['computed_md5']
    record=dict(doi=DOI,version=1,author='Xincong Chen',license=metadata['license'],file=rec['name'],
        bytes=len(payload),provider_md5_verified=True,md5=rec['computed_md5'],sha256=hashlib.sha256(payload).hexdigest(),source_url=rec['download_url'])
    (out/'download_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Verified',path.name,len(payload),'bytes')

if __name__=='__main__':main()
