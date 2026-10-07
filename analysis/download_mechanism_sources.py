"""Download pinned Figshare mechanisms data or documented GCE long-term tables.

GSM: complete source archive, CC-BY-4.0, provider MD5 checked per file.
GCE: original files and derived analyses must stay local pending reconciliation
of the EML licence with the legacy download agreement. Registration details
are read from GCE_REGISTRATION_NAME and GCE_REGISTRATION_EMAIL, never saved.
"""
import argparse,hashlib,json,os
from pathlib import Path
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from download_xmu_common_garden import form_values

def digest(path,algorithm):
    h=hashlib.new(algorithm)
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def gsm(args):
    session=requests.Session();session.trust_env=False
    proxies={'https':args.proxy,'http':args.proxy} if args.proxy else {}
    r=session.get('https://api.figshare.com/v2/articles/30068944/versions/1',proxies=proxies,timeout=60);r.raise_for_status();meta=r.json();assert meta['version']==1
    (args.output/'figshare_metadata.json').write_text(json.dumps(meta,indent=2))
    rows=[]
    for f in meta['files']:
        target=args.output/f['name']
        if not (target.exists() and target.stat().st_size==f['size'] and digest(target,'md5')==f['computed_md5']):
            temp=target.with_suffix(target.suffix+'.part')
            with session.get(f['download_url'],proxies=proxies,timeout=(30,90),stream=True) as response:
                response.raise_for_status()
                with temp.open('wb') as output:
                    for chunk in response.iter_content(4*1024*1024):output.write(chunk)
            if temp.stat().st_size!=f['size'] or digest(temp,'md5')!=f['computed_md5']:raise RuntimeError('Provider checksum mismatch: '+f['name'])
            temp.replace(target)
        rows.append(dict(f,sha256=digest(target,'sha256')));print('Verified',f['name'],flush=True)
    (args.output/'all_files_manifest.json').write_text(json.dumps({'doi':meta['doi'],'paper_doi':'10.1016/j.envc.2026.101453','license':meta['license'],'files':rows,'total_bytes':sum(f['size'] for f in rows),'provider_md5_verified':True},indent=2))

def gce(args):
    name=os.environ.get('GCE_REGISTRATION_NAME');email=os.environ.get('GCE_REGISTRATION_EMAIL')
    if not name or not email:raise ValueError('Set GCE_REGISTRATION_NAME and GCE_REGISTRATION_EMAIL')
    session=requests.Session();session.trust_env=False;rows=[]
    base='https://gce-lter.marsci.uga.edu/public/app/'
    for accession in ['PLT-GCES-1609','POR-GCES-2106']:
        r=session.get(base+'send_eml.asp',params={'accession':accession},timeout=60);r.raise_for_status();(args.output/(accession+'.xml')).write_bytes(r.content);root=ET.fromstring(r.content)
        for table in root.findall('.//dataTable'):
            extension='.MAT' if 'Observations' in table.findtext('entityName') else '.CSV'
            url=next(e.text for e in table.findall('.//url') if extension in (e.text or ''))
            filename=url.split('filename=')[1];target=args.output/filename
            if not target.exists():
                response=session.get(url,timeout=60);response.raise_for_status()
                for _ in range(3):
                    if 'html' not in response.headers.get('Content-Type',''):break
                    form=BeautifulSoup(response.text,'html.parser').find('form')
                    if form is None:raise RuntimeError('Missing normal registration form')
                    values=form_values(form);values.update(username=name,email=email,affiliation='Academic',notify='0',notify2='0')
                    response=session.post(urljoin(response.url,form['action']),data=values,timeout=90);response.raise_for_status()
                if 'html' in response.headers.get('Content-Type',''):raise RuntimeError('HTML is not data; no file saved')
                target.write_bytes(response.content)
            rows.append(dict(accession=accession,name=filename,url=url,expected_records=int(table.findtext('numberOfRecords')),bytes=target.stat().st_size,sha256=digest(target,'sha256')));print('Saved',filename,flush=True)
    (args.output/'download_manifest.json').write_text(json.dumps({'files':rows,'licence_note':'EML CC-BY and legacy download terms differ; keep raw and derived numbers local.','provider_checksums_available':False},indent=2))

def china(args):
    # Immutable supplement plus the reviewed article snapshot. Expected digests
    # are pinned in the repository, not learnt from the newly downloaded file.
    pinned=Path(__file__).resolve().parents[1]/'external_data/china_patch_traits_20261007'
    manifest=json.loads((pinned/'manifest.json').read_text())
    methods=json.loads((pinned/'methods_verified.json').read_text())
    session=requests.Session();session.trust_env=False
    proxies={'https':args.proxy,'http':args.proxy} if args.proxy else {}
    for name,url,expected in [('supplement.docx',manifest['file']['download_url'],manifest['sha256']),('article.xml',methods['source_url'],methods['sha256'])]:
        target=args.output/name
        if not (target.exists() and digest(target,'sha256')==expected):
            response=session.get(url,proxies=proxies,timeout=(30,90));response.raise_for_status()
            if hashlib.sha256(response.content).hexdigest()!=expected:raise RuntimeError('Source differs from reviewed snapshot: '+name)
            target.write_bytes(response.content)
        print('Verified',name,flush=True)
    for name in ['manifest.json','methods_verified.json']:
        (args.output/name).write_bytes((pinned/name).read_bytes())

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--dataset',choices=['gsm','gce','china'],required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--proxy',default=os.environ.get('MICAO_DOWNLOAD_PROXY'));args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    {'gsm':gsm,'gce':gce,'china':china}[args.dataset](args)
if __name__=='__main__':main()
