"""Download the public GCE BOT-GCED-1912 archive through its normal registration form.

Requires user-supplied registration details. Original files remain local because
GCE's dataset-specific EML and legacy download terms differ on redistribution.
"""
import argparse, hashlib, json, os
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
BASE='https://gce-lter.marsci.uga.edu/public/'

def form_values(form):
    values={e['name']:e.get('value','') for e in form.select('input[name]') if e.get('type')!='checkbox'}
    for e in form.select('select[name]'):
        selected=e.select_one('option[selected]') or e.select_one('option')
        values[e['name']]=selected.get('value','')
    return values

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--registration-name',default=os.environ.get('GCE_REGISTRATION_NAME'))
    ap.add_argument('--registration-email',default=os.environ.get('GCE_REGISTRATION_EMAIL'))
    args=ap.parse_args()
    if not args.registration_name or not args.registration_email:ap.error('Provide registration name and email explicitly or through GCE_REGISTRATION_* environment variables.')
    args.output.mkdir(parents=True,exist_ok=True);s=requests.Session();s.trust_env=False;rows=[]
    def save(name,url,content):
        (args.output/name).write_bytes(content)
        rows.append(dict(name=name,url=url,bytes=len(content),sha256=hashlib.sha256(content).hexdigest()))
    for table in ['Geographic','Greenhouse']:
        name=f'BOT-GCED-1912_{table}_1_0.CSV';url=BASE+'app/send_file.asp?accession=BOT-GCED-1912&filename='+name
        r=s.get(url,timeout=60);r.raise_for_status()
        # Registration and the subsequent download confirmation are separate forms.
        for _ in range(3):
            if 'html' not in r.headers.get('Content-Type',''):break
            soup=BeautifulSoup(r.text,'html.parser');form=soup.find('form')
            if form is None:raise RuntimeError('No data or registration form returned')
            values=form_values(form)
            values.update(username=args.registration_name,email=args.registration_email,affiliation='Academic',notify='0',notify2='0')
            r=s.post(urljoin(r.url,form['action']),data=values,timeout=60);r.raise_for_status()
        if 'html' in r.headers.get('Content-Type','') or b'"Year"' not in r.content[:1500]:raise RuntimeError('Response is not the expected CSV; not saved as data')
        save(name,url,r.content)
        name=f'BOT-GCED-1912_{table}_1_0-META.TXT';url=BASE+'datasets/metadata/'+name
        r=s.get(url,timeout=60);r.raise_for_status();save(name,url,r.content)
    url=BASE+'app/send_eml.asp?accession=BOT-GCED-1912';r=s.get(url,timeout=60);r.raise_for_status();save('metadata.xml',url,r.content)
    (args.output/'download_manifest.json').write_text(json.dumps({'files':rows,'source_accession':'BOT-GCED-1912','licence_note':'EML says CC BY 4.0; legacy portal restricts raw redistribution and requests notice before distributing derived products. Retain locally until reconciled.','provider_checksums_available':False},indent=2))
    print('Saved original tables and metadata; SHA-256 recorded, provider digests unavailable.')
if __name__=='__main__':main()
