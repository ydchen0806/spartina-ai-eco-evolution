"""Retrieve the pinned, CC-BY-4.0 genetic supplement and verify provider MD5."""
import hashlib,json,os
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]

def main():
    folder=ROOT/'external_data/xmu_literature_20261007';out=folder/'genet_ramet';out.mkdir(parents=True,exist_ok=True)
    session=requests.Session();session.trust_env=False
    proxy=os.environ.get('MICAO_DOWNLOAD_PROXY');proxies={'https':proxy,'http':proxy} if proxy else {}
    response=session.get('https://api.figshare.com/v2/articles/32141245/versions/1',proxies=proxies,timeout=60);response.raise_for_status();meta=response.json()
    assert meta['version']==1
    file=next(f for f in meta['files'] if f['id']==64150624)
    response=session.get(file['download_url'],proxies=proxies,timeout=120);response.raise_for_status();raw=response.content
    assert len(raw)==file['size'] and hashlib.md5(raw).hexdigest()==file['computed_md5']
    (out/'source.zip').write_bytes(raw);(folder/'figshare_32141245.json').write_text(json.dumps(meta,indent=2))
    (out/'manifest.json').write_text(json.dumps({'article':32141245,'version':1,'doi':meta['doi'],'paper_doi':meta['resource_doi'],'file':file,'sha256':hashlib.sha256(raw).hexdigest(),'license':meta['license']},indent=2))
    print('Downloaded and verified',len(raw),'bytes')
if __name__=='__main__':main()
