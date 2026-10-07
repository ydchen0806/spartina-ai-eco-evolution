"""Verify provider product XML hashes and radiometry against selected STAC assets."""
import argparse,concurrent.futures,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
import requests
BAND_IDS={'blue':'1','green':'2','red':'3','nir':'7','swir16':'11'}

def verify(item,out):
    asset=item['assets']['product_metadata'];path=out/'product_metadata'/f"{item['id']}.xml";path.parent.mkdir(exist_ok=True)
    if not path.exists():
        session=requests.Session();session.trust_env=False;r=session.get(asset['href'],timeout=60);r.raise_for_status();path.write_bytes(r.content)
    payload=path.read_bytes();assert asset['file:checksum']=='1220'+hashlib.sha256(payload).hexdigest();assert len(payload)==asset['file:size']
    root=ET.fromstring(payload)
    quant=[float(e.text) for e in root.iter() if e.tag.split('}')[-1]=='BOA_QUANTIFICATION_VALUE'];assert len(quant)==1
    offsets={e.attrib['band_id']:float(e.text) for e in root.iter() if e.tag.split('}')[-1]=='BOA_ADD_OFFSET'}
    for band,band_id in BAND_IDS.items():
        meta=item['assets'][band]['raster:bands'][0]
        assert meta['scale']==1/quant[0] and meta['offset']==offsets[band_id]/quant[0]
    return {'item':item['id'],'product_metadata_url':asset['href'],'provider_sha256_verified':True,'sha256':hashlib.sha256(payload).hexdigest(),'quantification':quant[0],'band_offsets_dn':{b:offsets[i] for b,i in BAND_IDS.items()},'all_five_stac_band_conversions_match_xml':True}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,required=True);a=ap.parse_args()
    ids=set(pd.read_csv(a.source/'selected_scenes.csv').item);items=[f for p in a.source.glob('stac_september_*.json') for f in json.loads(p.read_text())['features'] if f['id'] in ids]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(lambda f:verify(f,a.source),items))
    assert len(rows)==len(ids)
    (a.source/'radiometry_verification.json').write_text(json.dumps({'selected_scenes':len(rows),'scope':'Product metadata and STAC consistency. Not full-band checksum verification; raster windows have ETag/range-length validation and local SHA-256.','records':rows},indent=2)+'\n');print('Provider XML SHA-256 and five-band scale/offset verified:',len(rows),'scenes')
if __name__=='__main__':main()
