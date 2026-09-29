"""Check the actual review frames, crops, hashes and fixed viewport margins."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops

def check(folder):
    manifest=json.loads((folder/'manifest.json').read_text())
    rows=[]
    for clip in manifest:
        digest=hashlib.sha256();failures=[];bytes_=0
        crop=(clip['x'],clip['y'],clip['x']+clip['width'],clip['y']+clip['height'])
        for index in range(clip['frames']):
            name=f'{index:03}.png'
            path=folder/'watch'/clip['id']/name
            data=path.read_bytes();digest.update(data);bytes_+=len(data)
            full=Image.open(folder/'frames'/clip['id']/name).convert('RGB')
            watch=Image.open(path).convert('RGB')
            if full.size!=(280,156) or watch.size!=(clip['width'],clip['height']):failures.append(f'{index}: dimensions')
            restored=Image.new('RGB',full.size);restored.paste(watch,(clip['x'],clip['y']))
            if ImageChops.difference(full,restored).getbbox():failures.append(f'{index}: crop loses pixels')
            if ImageChops.difference(full.crop(crop),watch).getbbox():failures.append(f'{index}: crop differs')
            bounds=full.getbbox()
            if not bounds or bounds[0]<2 or bounds[1]<2 or bounds[2]>278 or bounds[3]>154:failures.append(f'{index}: outer viewport margin')
        if digest.hexdigest()!=clip['sha256']:failures.append('sequence hash')
        if bytes_!=clip['png_bytes']:failures.append('byte count')
        if clip['width']*clip['height']*clip['fps']>320000:failures.append('per-clip pixel budget')
        for sub in ['frames','watch']:
            if len(list((folder/sub/clip['id']).glob('*.png')))!=clip['frames']:failures.append(f'{sub}: stale or missing frames')
        rows.append({'id':clip['id'],'frames':clip['frames'],'sha256':digest.hexdigest(),'failures':failures})
    return {'passed':all(not row['failures'] for row in rows),'exercises':rows,
            'frames':sum(c['frames'] for c in manifest),'png_bytes':sum(c['png_bytes'] for c in manifest),
            'scope':'Host export identity, crops and bounds. Not form, collision or device-performance approval.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path);args=parser.parse_args()
    report=check(args.folder)
    (args.folder/'export-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='exercises'}))
    for row in report['exercises']:
        if row['failures']:print(row['id'],row['failures'])
    raise SystemExit(0 if report['passed'] else 1)
