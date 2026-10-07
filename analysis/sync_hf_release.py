"""Synchronize tracked research files to Hugging Face in small additive commits.

Authentication: HF_TOKEN, --token-file, or the normal Hugging Face credential
store. Optional MICAO_DOWNLOAD_PROXY affects this process only. No deletions are
made, and untracked inputs, .git contents and credentials are never selected.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',default='cyd0806/spartina-ai-eco-evolution-data')
    ap.add_argument('--token-file',type=Path)
    ap.add_argument('--dry-run',action='store_true')
    ap.add_argument('--report',type=Path,default=Path('../briefing/HF_SYNC_LATEST.json'))
    args=ap.parse_args()
    proxy=os.getenv('MICAO_DOWNLOAD_PROXY')
    if proxy:
        for k in ['HTTP_PROXY','HTTPS_PROXY','http_proxy','https_proxy']:os.environ[k]=proxy
    os.environ['HF_ENDPOINT']='https://huggingface.co'
    os.environ['HF_HUB_DISABLE_XET']='1'
    os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1'
    from huggingface_hub import HfApi,CommitOperationAdd,get_token
    root=Path(__file__).resolve().parents[1]
    token=args.token_file.read_text().strip() if args.token_file else get_token()
    api=HfApi(endpoint='https://huggingface.co',token=token)
    paths=subprocess.check_output(['git','ls-files'],cwd=root,text=True).splitlines()
    remote={x.path:x for x in api.list_repo_tree(args.repo,repo_type='dataset',recursive=True) if hasattr(x,'blob_id')}
    changed=[]
    for path in paths:
        payload=(root/path).read_bytes();r=remote.get(path)
        if r:
            if r.lfs and hashlib.sha256(payload).hexdigest()==r.lfs.sha256:continue
            if not r.lfs and hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()==r.blob_id:continue
        changed.append(path)
    print('Changed tracked files:',len(changed),flush=True)
    if args.dry_run:return
    batches=[];batch=[];size=0
    for path in changed:
        n=(root/path).stat().st_size
        cost=200 if Path(path).suffix.lower() in ['.png','.jpg','.pdf','.docx','.xlsx','.tif','.gz'] else n
        if batch and (len(batch)>=12 or size+cost>700_000):batches.append(batch);batch=[];size=0
        batch.append(path);size+=cost
    if batch:batches.append(batch)
    commits=[]
    for i,batch in enumerate(batches):
        result=api.create_commit(repo_id=args.repo,repo_type='dataset',
            operations=[CommitOperationAdd(path_in_repo=p,path_or_fileobj=str(root/p)) for p in batch],
            commit_message=f'Sync reproducible research release, batch {i+1}/{len(batches)}')
        commits.append(result.oid);print('Synced batch',i+1,'files',len(batch),'commit',result.oid,flush=True)
    report={'status':'uploaded','repo':args.repo,'github_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        'changed_file_count':len(changed),'commits':commits,'verification':'Run --dry-run; zero changed files confirms remote Git/LFS digest agreement.'}
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
