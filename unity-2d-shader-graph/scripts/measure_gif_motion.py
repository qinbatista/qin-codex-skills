#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys
from collections import Counter
from pathlib import Path
from PIL import Image, ImageChops, ImageSequence
import numpy as np

def main() -> int:
    p=Path(argparse.ArgumentParser().parse_known_args()[1][0]) if False else None
    parser=argparse.ArgumentParser()
    parser.add_argument('gif', type=Path)
    parser.add_argument('--min-mean', type=float, default=0.0)
    parser.add_argument('--min-visible', type=float, default=0.0)
    parser.add_argument('--require-downward', action='store_true')
    parser.add_argument('--min-down-shift', type=float, default=0.25)
    parser.add_argument('--min-downward-frac', type=float, default=0.65)
    parser.add_argument('--max-direction-shift', type=int, default=32)
    a=parser.parse_args()
    rgb=[f.convert('RGB') for f in ImageSequence.Iterator(Image.open(a.gif))]
    if len(rgb)<2: raise ValueError('GIF must contain at least two frames')
    diffs=[]; visible=[]
    for x,y in zip(rgb, rgb[1:]+rgb[:1]):
        d=ImageChops.difference(x,y); hist=d.histogram(); total=x.size[0]*x.size[1]*3
        diffs.append(sum((i%256)*c for i,c in enumerate(hist))/total)
        vis=d.convert('L').point(lambda v:255 if v>8 else 0)
        visible.append(sum(vis.histogram()[1:])/(x.size[0]*x.size[1]))
    print(f'frames={len(rgb)}'); print(f'size={rgb[0].size[0]}x{rgb[0].size[1]}')
    print(f'mean_diff_loop={sum(diffs)/len(diffs):.3f}'); print(f'visible_frac_loop={sum(visible)/len(visible):.4f}')
    failed=sum(diffs)/len(diffs)<a.min_mean or sum(visible)/len(visible)<a.min_visible
    if a.require_downward:
        frames=[]
        for f in ImageSequence.Iterator(Image.open(a.gif)):
            rgba=np.asarray(f.convert('RGBA'), dtype=np.float32); alpha=rgba[...,3]/255.0
            gray=(0.299*rgba[...,0]+0.587*rgba[...,1]+0.114*rgba[...,2])/255.0
            mask=((alpha>0.08)&(gray>0.025)).astype(np.float32); frames.append((gray*mask, mask))
        shifts=[]
        for (g0,m0),(g1,m1) in zip(frames, frames[1:]):
            best=None
            for dy in range(-a.max_direction_shift, a.max_direction_shift+1):
                if dy>=0:
                    x=g0[:-dy or None,:]; y=g1[dy:,:]; valid=(m0[:-dy or None,:]*m1[dy:,:])>0.01
                else:
                    x=g0[-dy:,:]; y=g1[:dy,:]; valid=(m0[-dy:,:]*m1[:dy,:])>0.01
                if int(valid.sum())<200: continue
                xv=x[valid]; yv=y[valid]; xv=xv-xv.mean(); yv=yv-yv.mean()
                score=float((xv*yv).sum()/(np.sqrt((xv*xv).sum()*(yv*yv).sum())+1e-8))
                if best is None or score>best[1]: best=(dy,score)
            if best: shifts.append(best[0])
        avg=sum(shifts)/len(shifts) if shifts else 0.0; down=sum(s>0 for s in shifts)/len(shifts) if shifts else 0.0; up=sum(s<0 for s in shifts)/len(shifts) if shifts else 0.0
        print(f'avg_vertical_shift_px_per_frame={avg:.3f}'); print(f'downward_frame_frac={down:.4f}'); print(f'upward_frame_frac={up:.4f}'); print(f'dominant_shift_counts={dict(Counter(shifts).most_common(8))}')
        failed = failed or avg<a.min_down_shift or down<a.min_downward_frac
    return 1 if failed else 0
if __name__ == '__main__': raise SystemExit(main())
