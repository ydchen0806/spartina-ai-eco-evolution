"""Download two public CC0 Dryad experiments and verify provider SHA-256 digests."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import zipfile

import requests

DATASETS = {'plasticity': ('10.5061/dryad.j3tx95xsc', 359901),
            'allocation': ('10.5061/dryad.2rbnzs7q7', 166262)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--no-download', action='store_true')
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    def get(url):
        session = requests.Session()
        session.trust_env = False
        response = session.get(url, timeout=45)
        response.raise_for_status()
        return response
    manifest = []
    for name, (doi, version) in DATASETS.items():
        out = args.output / name
        out.mkdir(exist_ok=True)
        meta = out / 'dataset_metadata.json'
        listing = out / 'file_listing.json'
        if not args.no_download:
            meta.write_text(json.dumps(get('https://datadryad.org/api/v2/datasets/'+requests.utils.quote('doi:'+doi, safe='')).json(), indent=2)+'\n')
            listing.write_text(json.dumps(get(f'https://datadryad.org/api/v2/versions/{version}/files').json(), indent=2)+'\n')
        metadata = json.loads(meta.read_text())
        assert 'CC0' in metadata['license']
        info = json.loads(listing.read_text())
        files = info['_embedded']['stash:files']
        assert info['total'] == len(files), 'Pagination requires explicit handling'
        def download(rec):
            path = out / Path(rec['path']).name
            # Public landing pages expose file_stream; API downloads require login.
            file_id = rec['_links']['self']['href'].rsplit('/', 1)[-1]
            url = 'https://datadryad.org/downloads/file_stream/' + file_id
            try:
                if not args.no_download:
                    path.write_bytes(get(url).content)
                if not path.exists():
                    raise FileNotFoundError(path.name)
            except (requests.RequestException, FileNotFoundError) as exc:
                return dict(dataset=name, doi=doi, pinned_version=version, filename=path.name,
                            url=url, status='not_downloaded', error_type=type(exc).__name__,
                            http_status=getattr(getattr(exc, 'response', None), 'status_code', None),
                            license=metadata['license'])
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert rec['digestType'] == 'sha-256' and digest == rec['digest']
            assert path.stat().st_size == rec['size']
            return dict(dataset=name, doi=doi, pinned_version=version, filename=path.name,
                        bytes=rec['size'], sha256=digest, provider_digest_verified=True, status='verified',
                        url=url, license=metadata['license'])
        with ThreadPoolExecutor(max_workers=3) as pool:
            records = list(pool.map(download, files))
        manifest.extend(records)
        for rec in records:
            if rec.get('status') == 'verified' and rec['filename'].endswith('.zip'):
                with zipfile.ZipFile(out / rec['filename']) as archive:
                    dest = out / 'extracted'
                    dest.mkdir(exist_ok=True)
                    for member in archive.infolist():
                        target = (dest / member.filename).resolve()
                        assert target.is_relative_to(dest.resolve()), 'Unsafe archive path'
                        assert member.file_size < 50_000_000
                    archive.extractall(dest)
        print(name, sum(r['status']=='verified' for r in records), '/', len(records), 'files verified', flush=True)
    (args.output / 'download_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__':
    main()
