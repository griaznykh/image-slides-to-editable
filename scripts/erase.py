"""Erase baked-in text from slide images -> WORKDIR/bg/bgN.png
usage: erase.py WORKDIR [--extra extra.json] [--notebooklm] [--slides 1 2 ...]

How it works: inside every OCR box (words on one row are merged, boxes widened by
0.6*line height so dashes/bullets/quotes between words are caught) pixels that differ
from a local median background are masked, long straight lines (card borders, table
rules) are protected, then the mask is filled with cv2.inpaint (Telea).

extra.json (slide points): {"7": [[x0,y0,x1,y1], ...], "*": [...]} - rectangles that are
force-filled entirely (residue the OCR missed). "*" applies to all slides.
--notebooklm adds the "NotebookLM / Gemini Notebook" watermark corner on every slide.
"""
import sys, os, json, cv2, numpy as np
work = sys.argv[1]
args = sys.argv[2:]
extra = json.load(open(args[args.index('--extra') + 1])) if '--extra' in args else {}
only = set(args[args.index('--slides') + 1:]) if '--slides' in args else None
meta = json.load(open(f'{work}/meta.json')); d = json.load(open(f'{work}/ocr.json'))
os.makedirs(f'{work}/bg', exist_ok=True)
SW, SH = meta['slide_w'], meta['slide_h']
for k, v in d.items():
    if only and k not in only: continue
    img = cv2.imread(meta['slides'][k]['image'], cv2.IMREAD_COLOR)
    H, W = img.shape[:2]
    bx = meta['slides'][k]['pic_box_pt']
    sx, sy = W / bx[2], H / bx[3]
    pt2px = lambda r: [int((r[0]-bx[0])*sx), int((r[1]-bx[1])*sy), int((r[2]-bx[0])*sx), int((r[3]-bx[1])*sy)]
    rects = sorted([list(l['box']) for l in v['lines']], key=lambda r: r[0])
    merged = []
    for r in rects:
        for m in merged:
            h = min(r[3]-r[1], m[3]-m[1]); ov = min(r[3], m[3]) - max(r[1], m[1])
            if ov > 0.5*h and r[0] - m[2] < 2.5*h:
                m[:] = [min(m[0], r[0]), min(m[1], r[1]), max(m[2], r[2]), max(m[3], r[3])]; break
        else:
            merged.append(r)
    rects = []
    for x0, y0, x1, y1 in merged:
        e = int((y1-y0)*0.6); rects.append([max(0, x0-e), y0, min(W, x1+e), y1])
    if '--notebooklm' in args:
        rects.append(pt2px([SW*0.91, SH*0.964, SW-1, SH*0.996]))
    mask = np.zeros((H, W), np.uint8)
    for x0, y0, x1, y1 in rects:
        lh = max(4, y1 - y0); p = max(4, int(lh*0.25))
        X0, Y0, X1, Y1 = max(0, x0-p), max(0, y0-p), min(W, x1+p), min(H, y1+p)
        if X1 <= X0 or Y1 <= Y0: continue
        g = cv2.cvtColor(img[Y0:Y1, X0:X1], cv2.COLOR_BGR2GRAY)
        ks = max(7, min(int(lh*1.5) | 1, 255))
        diff = cv2.absdiff(g, cv2.medianBlur(g, ks))
        m = (diff > 28).astype(np.uint8)*255
        rh, rw = m.shape
        vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(3, int(rh*0.92))))
        hk = cv2.getStructuringElement(cv2.MORPH_RECT, (max(3, int(lh*4)), 1))
        lines = cv2.morphologyEx(m, cv2.MORPH_OPEN, vk) | cv2.morphologyEx(m, cv2.MORPH_OPEN, hk)
        lines = cv2.dilate(lines, np.ones((5, 5), np.uint8))
        m = m & ~lines
        m = cv2.dilate(m, np.ones((5, 5), np.uint8), iterations=max(1, lh//25))
        mask[Y0:Y1, X0:X1] |= m & ~lines
    for r in extra.get(k, []) + extra.get('*', []):
        x0, y0, x1, y1 = pt2px(r); mask[max(0, y0):y1, max(0, x0):x1] = 255
    out = cv2.inpaint(img, mask, 9, cv2.INPAINT_TELEA)
    cv2.imwrite(f'{work}/bg/bg{k}.png', out); print('bg', k, flush=True)
