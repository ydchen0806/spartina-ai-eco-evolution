"""Retrieve NASA POWER climate context at the recovered image-bounds centre."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--no-download', action='store_true')
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    bounds = json.loads((ROOT / 'data/derived/recovery_20261007/raster_audit.json').read_text())['bounds_wgs84']
    lon, lat = (bounds[0]+bounds[2])/2, (bounds[1]+bounds[3])/2
    query = dict(parameters='T2M,PRECTOTCORR,RH2M,WS2M', community='AG', longitude=lon, latitude=lat,
                 start='20140101', end='20211231', format='JSON')
    raw = args.output / 'nasa_power_image_center_daily.json'
    if not args.no_download:
        session = requests.Session()
        session.trust_env = False
        response = session.get('https://power.larc.nasa.gov/api/temporal/daily/point', params=query, timeout=45)
        response.raise_for_status()
        raw.write_text(json.dumps(response.json(), indent=2)+'\n')
    data = json.loads(raw.read_text())
    frame = pd.DataFrame(data['properties']['parameter']).sort_index()
    fill = data.get('header', {}).get('fill_value', -999)
    frame = frame.replace(fill, np.nan)
    frame.index = pd.to_datetime(frame.index, format='%Y%m%d')
    frame.index.name = 'date'
    frame.to_csv(args.output / 'image_center_climate_daily.csv')
    annual = frame.groupby(frame.index.year).agg(
        temperature_mean_C=('T2M', 'mean'), precipitation_sum_mm=('PRECTOTCORR', lambda x: x.sum(min_count=1)),
        humidity_mean_percent=('RH2M', 'mean'), wind_mean_m_s=('WS2M', 'mean'))
    for col in frame:
        annual[col+'_valid_days'] = frame[col].groupby(frame.index.year).count()
    annual.to_csv(args.output / 'image_center_climate_annual.csv')
    metadata = dict(query=query, retrieval_date='2026-10-07', returned_geometry=data.get('geometry'),
        units=data.get('parameters'), raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
        days=len(frame), missing_by_parameter=frame.isna().sum().to_dict(),
        interpretation='Gridded meteorological context at image-bounds centre, not on-site measurements. '
        'Does not supply tides, exact flight weather, inundation or causal tests. '
        'Yearly summaries are not independent patch-level environmental replicates.')
    (args.output / 'climate_context_provenance.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
