"""Verify every compressed part and every unique file without extracting to disk."""
from pathlib import Path
import gzip, hashlib, io, json, tarfile
from restore_data import ROOT, Joined, digest

def main():
    manifest=json.loads((ROOT/'metadata/manifest.json').read_text('utf-8'))
    paths=[]
    for part in manifest['parts']:
        p=ROOT/part['path']
        assert p.stat().st_size==part['bytes'] and digest(p)==part['sha256'],p
        paths.append(p)
    unique={r['path']:r for r in manifest['files'] if 'duplicate_of' not in r}
    checked=set()
    with io.BufferedReader(Joined(paths)) as stream,gzip.GzipFile(fileobj=stream) as gz,tarfile.open(fileobj=gz,mode='r|') as tar:
        for member in tar:
            assert member.isfile() and member.name in unique and member.name not in checked,member.name
            r=unique[member.name];assert member.size==r['bytes'],member.name
            h=hashlib.sha256()
            with tar.extractfile(member) as f:
                for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
            assert h.hexdigest()==r['sha256'],member.name
            checked.add(member.name)
    assert checked==set(unique),'Missing files'
    for r in manifest['files']:
        if 'duplicate_of' in r:
            canonical=unique[r['duplicate_of']]
            assert r['sha256']==canonical['sha256'] and r['bytes']==canonical['bytes'],r['path']
    print(json.dumps({'archive_parts_verified':len(paths),'unique_files_verified':len(checked),'restorable_files':len(manifest['files']),'duplicate_paths_verified':len(manifest['files'])-len(checked)},indent=2))
if __name__=='__main__':main()
