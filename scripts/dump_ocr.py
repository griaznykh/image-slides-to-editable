"""Print OCR lines in slide points: x0 y0 x1 y1 h conf text.  usage: dump_ocr.py WORKDIR [slide ...]"""
import sys, json
work = sys.argv[1]; only = set(sys.argv[2:])
meta = json.load(open(f'{work}/meta.json')); d = json.load(open(f'{work}/ocr.json'))
for k, v in d.items():
    if only and k not in only: continue
    bx = meta['slides'][k]['pic_box_pt']
    sx, sy = bx[2] / v['W'], bx[3] / v['H']
    print('=== slide', k)
    for l in v['lines']:
        b = l['box']
        x0, y0, x1, y1 = bx[0] + b[0]*sx, bx[1] + b[1]*sy, bx[0] + b[2]*sx, bx[1] + b[3]*sy
        print(f"{x0:5.0f}{y0:5.0f}{x1:5.0f}{y1:5.0f} h{y1-y0:3.0f} {l['conf']:.2f} {l['text']}")
