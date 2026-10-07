"""Acquire exact native-grid Sentinel-2 windows with validated HTTP byte ranges.

No credentials required. Original digital numbers and SCL are preserved. All
September candidates are screened by local SCL, never by the vegetation outcome.
Sparse temporary TIFFs contain only requested source tiles and are not retained.
"""
import argparse,concurrent.futures,hashlib,io,json,math,os,tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import requests
import rasterio
from rasterio.windows import Window,from_bounds
from rasterio.warp import transform_bounds
from pyproj import Transformer
import tifffile

FULL=(117.404195622047,23.9134768474132,117.432930102047,23.9374309174132)

def get_range(url,start,end,etag=None):
    for attempt in range(4):
        session=requests.Session();session.trust_env=False
        try:
            headers={'Range':f'bytes={start}-{end}'}
            if etag:headers['If-Match']=etag
            r=session.get(url,headers=headers,timeout=(15,45));r.raise_for_status()
            assert r.status_code==206 and r.headers['Content-Range'].startswith(f'bytes {start}-{end}/')
            assert len(r.content)==end-start+1
            if etag:assert r.headers.get('ETag')==etag
            return r.content,r.headers
        except Exception:
            if attempt==3:raise
        finally:session.close()

def clip_asset(item,key,out):
    folder=out/'clips'/item['id'];folder.mkdir(parents=True,exist_ok=True)
    target=folder/(key+'.tif');log=folder/(key+'.json')
    if target.exists() and log.exists():
        record=json.loads(log.read_text())
        assert hashlib.sha256(target.read_bytes()).hexdigest()==record['sha256']
        return record
    asset=item['assets'][key];url=asset['href']
    head,headers=get_range(url,0,65535);size=int(headers['Content-Range'].split('/')[-1]);etag=headers['ETag']
    with tifffile.TiffFile(io.BytesIO(head)) as t:
        page=t.pages[0];offsets=page.dataoffsets;counts=page.databytecounts;tw,th=page.tilewidth,page.tilelength;shape=page.shape
    with tempfile.NamedTemporaryFile(suffix='.tif') as tmp:
        tmp.truncate(size);tmp.write(head);tmp.flush()
        with rasterio.open(tmp.name) as src:
            assert tuple(shape)==(src.height,src.width)
            bounds=transform_bounds(4326,src.crs,*FULL,densify_pts=21)
            w=from_bounds(*bounds,transform=src.transform)
            c0,r0=math.floor(w.col_off)-1,math.floor(w.row_off)-1
            c1,r1=math.ceil(w.col_off+w.width)+1,math.ceil(w.row_off+w.height)+1
            win=Window(c0,r0,c1-c0,r1-r0);assert c0>=0 and r0>=0 and c1<=src.width and r1<=src.height
            profile=src.profile.copy();transform=src.window_transform(win)
            nx=math.ceil(src.width/tw)
            indexes=[rr*nx+cc for rr in range(r0//th,(r1-1)//th+1) for cc in range(c0//tw,(c1-1)//tw+1)]
        chunks=[]
        for index in indexes:
            start,stop=offsets[index],offsets[index]+counts[index]
            for pos in range(start,stop,262144):chunks.append((pos,min(pos+262144,stop)-1))
        def fetch(chunk):
            start,end=chunk;return start,get_range(url,start,end,etag)[0]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            for start,data in ex.map(fetch,chunks):tmp.seek(start);tmp.write(data)
        tmp.flush()
        with rasterio.open(tmp.name) as src:data=src.read(1,window=win)
    assert data.shape==(r1-r0,c1-c0)
    profile.update(width=data.shape[1],height=data.shape[0],count=1,transform=transform,compress='deflate',tiled=False)
    profile.pop('blockxsize',None);profile.pop('blockysize',None)
    with rasterio.open(target,'w',**profile) as dst:
        dst.write(data,1);dst.update_tags(source_item=item['id'],source_asset=url,source_etag=etag,attribution='Contains modified Copernicus Sentinel data; spatial subset only; original DN retained')
    record={'item':item['id'],'asset':key,'url':url,'source_etag':etag,'source_object_bytes':size,'source_window_col_row_width_height':list(win.flatten()),'downloaded_bytes':len(head)+sum(b-a+1 for a,b in chunks),'range_lengths_and_etag_verified':True,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'clip_bytes':target.stat().st_size,'raster_band_metadata':asset.get('raster:bands'),'source_boa_offset_applied':item['properties'].get('earthsearch:boa_offset_applied'),'transform':list(transform),'crs':str(profile['crs'])}
    log.write_text(json.dumps(record,indent=2)+'\n');return record

def screen(item,out):
    clip_asset(item,'scl',out)
    with rasterio.open(out/'clips'/item['id']/'scl.tif') as src:
        a=src.read(1);yy,xx=np.indices(a.shape);tr=src.transform
        lon,lat=Transformer.from_crs(src.crs,4326,always_xy=True).transform(tr.c+(xx+.5)*tr.a,tr.f+(yy+.5)*tr.e)
        inside=(lon>=FULL[0])&(lon<FULL[2])&(lat>=FULL[1])&(lat<FULL[3]);assert inside.sum()>0
        clear=np.isin(a,[4,5,6])
    return {'item':item['id'],'date':item['properties']['datetime'][:10],'year':int(item['properties']['datetime'][:4]),'scene_cloud_pct':item['properties']['eo:cloud_cover'],'local_clear_fraction':float(clear[inside].mean()),'local_valid_fraction':float((a[inside]>0).mean()),'local_scl_vegetation_fraction':float((a[inside]==4).mean()),'local_scl_water_fraction':float((a[inside]==6).mean())}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--workers',type=int,default=4);a=ap.parse_args();a.source.mkdir(parents=True,exist_ok=True)
    # Complete searches already archived; reruns can refresh missing years.
    for year in range(2019,2026):
        p=a.source/f'stac_september_{year}.json'
        if not p.exists():
            session=requests.Session();session.trust_env=False
            r=session.get('https://earth-search.aws.element84.com/v1/search',params={'collections':'sentinel-2-c1-l2a','bbox':','.join(map(str,FULL)),'datetime':f'{year}-09-01T00:00:00Z/{year}-09-30T23:59:59Z','limit':100},timeout=60);r.raise_for_status();p.write_text(json.dumps(r.json()))
    items=[]
    for p in sorted(a.source.glob('stac_september_*.json')):
        d=json.loads(p.read_text());assert len(d['features'])==d['context']['matched'],'Pagination required before analysis'
        assert all(f['collection']=='sentinel-2-c1-l2a' for f in d['features'])
        items.extend(d['features'])
    assert len({f['id'] for f in items})==len(items)
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
        tasks={ex.submit(screen,f,a.source):f for f in items}
        for task in concurrent.futures.as_completed(tasks):
            row=task.result();rows.append(row);print('Screened',row['item'],round(row['local_clear_fraction'],3),flush=True)
    table=pd.DataFrame(rows).sort_values(['year','date','item']);table.to_csv(a.source/'candidate_scene_screen.csv',index=False)
    # One granule per date: choose greatest AOI clear fraction, then stable ID.
    selected=table.sort_values(['local_clear_fraction','item'],ascending=[False,True]).drop_duplicates('date')
    selected=selected[selected.local_clear_fraction>=.8].groupby('year',group_keys=False).head(3).sort_values(['year','date'])
    selected.to_csv(a.source/'selected_scenes.csv',index=False)
    lookup={f['id']:f for f in items}
    tasks=[(lookup[i],key,a.source) for i in selected.item for key in ['blue','green','red','nir','swir16']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
        for record in ex.map(lambda t:clip_asset(*t),tasks):print('Downloaded',record['item'],record['asset'],flush=True)
    manifest={'bounds_wgs84':FULL,'candidate_count':len(items),'selected_count':len(selected),'selection':'September 2019–2025; local SCL in {4,5,6} >=80%; one best granule/date; top three dates/year by AOI clear fraction then ID, before spectral analysis.','assets':['blue','green','red','nir','swir16','scl'],'source':'Copernicus Sentinel-2 Collection 1 L2A through Element84 Earth Search / AWS e84-earth-search-sentinel-data','license_url':'https://sentinel.esa.int/documents/247904/690755/Sentinel_Data_Legal_Notice','records':[json.loads(p.read_text()) for p in sorted((a.source/'clips').glob('*/*.json'))]}
    (a.source/'download_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Complete:',len(items),'candidates;',len(selected),'selected scenes',flush=True)
if __name__=='__main__':main()
