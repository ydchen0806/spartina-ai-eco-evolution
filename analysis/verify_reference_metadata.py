"""Verify manuscript reference metadata and available abstracts using Crossref."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import requests

DOIS = ['10.2307/1941255', '10.1111/ecog.02881', '10.1890/03-4027',
        '10.1126/science.1242121', '10.1016/j.ecoleng.2008.05.013',
        '10.1016/j.rse.2020.111745', '10.1016/j.jag.2021.102456',
        '10.1890/0012-9658(2002)083[2248:ESORWD]2.0.CO;2']


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--no-download', action='store_true')
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    def retrieve(doi):
        path = args.output / (doi.replace('/', '_').replace(':', '_')+'.json')
        if not args.no_download:
            session = requests.Session()
            session.trust_env = False
            response = session.get('https://api.crossref.org/works/'+requests.utils.quote(doi, safe=''), timeout=25)
            response.raise_for_status()
            path.write_text(json.dumps(response.json(), ensure_ascii=False, indent=2)+'\n')
        item = json.loads(path.read_text())['message']
        assert item['DOI'].lower() == doi.lower()
        return dict(doi=doi, title=item.get('title'), authors=item.get('author'),
                    journal=item.get('container-title'), volume=item.get('volume'), pages=item.get('page'),
                    year=item.get('published', {}).get('date-parts'), abstract=item.get('abstract'),
                    license=item.get('license'), verification_scope='Crossref metadata and supplied abstract; not full-text review')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(retrieve, DOIS))
    (args.output / 'verified_metadata.json').write_text(json.dumps(results, indent=2, ensure_ascii=False)+'\n')
    print('Verified DOI records:', len(results))


if __name__ == '__main__':
    main()
