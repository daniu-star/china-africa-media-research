"""Restore the lossless research archive using Python's standard library."""
from pathlib import Path
import argparse, gzip, hashlib, io, json, shutil, tarfile

ROOT=Path(__file__).resolve().parents[1]
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
class Joined(io.RawIOBase):
    def __init__(self,paths):self.paths=iter(paths);self.f=None
    def readable(self):return True
    def readinto(self,buffer):
        while True:
            if self.f is None:
                try:self.f=next(self.paths).open('rb')
                except StopIteration:return 0
            n=self.f.readinto(buffer)
            if n:return n
            self.f.close();self.f=None
    def close(self):
        if self.f:self.f.close()
        super().close()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=ROOT/'restored'/'demo')
    ap.add_argument('--only',help='Restore a file or directory prefix, e.g. 清洗数据')
    ap.add_argument('--verify-only',action='store_true',help='Verify archive parts without extracting')
    args=ap.parse_args();manifest=json.loads((ROOT/'metadata/manifest.json').read_text('utf-8'))
    paths=[]
    for part in manifest['parts']:
        p=ROOT/part['path']
        if p.stat().st_size!=part['bytes'] or digest(p)!=part['sha256']:raise SystemExit('Archive integrity failure: '+str(p))
        paths.append(p)
    print('All archive parts verified.',flush=True)
    if args.verify_only:return
    selected=[r for r in manifest['files'] if not args.only or r['path']==args.only or r['path'].startswith(args.only.rstrip('/')+'/')]
    if not selected:raise SystemExit('No files match --only')
    required={r.get('duplicate_of',r['path']) for r in selected}
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    def target(name):
        p=(out/name).resolve()
        if not p.is_relative_to(out):raise ValueError('Unsafe archive path')
        return p
    for r in selected:
        p=target(r['path'])
        if p.exists() and (not p.is_file() or digest(p)!=r['sha256']):raise SystemExit('Refusing to overwrite a different file: '+str(p))
    extracted={}
    with io.BufferedReader(Joined(paths)) as stream, gzip.GzipFile(fileobj=stream) as gz, tarfile.open(fileobj=gz,mode='r|') as tar:
        for member in tar:
            if member.name not in required:continue
            if not member.isfile():raise ValueError('Unexpected archive entry')
            p=target(member.name)
            p.parent.mkdir(parents=True,exist_ok=True)
            if p.exists():
                expected=next(r['sha256'] for r in manifest['files'] if r['path']==member.name)
                if digest(p)!=expected:raise SystemExit('Refusing to overwrite: '+str(p))
            else:
                with tar.extractfile(member) as src,p.open('wb') as dst:shutil.copyfileobj(src,dst,4*1024*1024)
            extracted[member.name]=p
    for r in selected:
        p=target(r['path'])
        if 'duplicate_of' in r and not p.exists():
            p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(extracted[r['duplicate_of']],p)
        if not p.is_file() or p.stat().st_size!=r['bytes'] or digest(p)!=r['sha256']:raise SystemExit('Restored file integrity failure: '+str(p))
    print(f'Restored and SHA-256 verified {len(selected)} files to {out}',flush=True)
if __name__=='__main__':main()
