"""OCR every extracted slide image (Russian + English) -> WORKDIR/ocr.json.
usage: ocr.py WORKDIR [--langs ru,en] [--slides 3 4]
Boxes are stored in image pixels; dump_ocr.py prints them in slide points.
"""
import sys, json
import easyocr
work = sys.argv[1]
langs = sys.argv[sys.argv.index('--langs') + 1].split(',') if '--langs' in sys.argv else ['ru', 'en']
meta = json.load(open(f'{work}/meta.json'))
only = set(sys.argv[sys.argv.index('--slides') + 1:]) if '--slides' in sys.argv else None
r = easyocr.Reader(langs, gpu=False)
res = {}
for n, s in meta['slides'].items():
    if 'image' not in s or (only and n not in only): continue
    lines = r.readtext(s['image'], paragraph=False, width_ths=0.7)
    res[n] = {'W': s['px'][0], 'H': s['px'][1], 'lines': [
        {'box': [int(min(x for x, y in b)), int(min(y for x, y in b)), int(max(x for x, y in b)), int(max(y for x, y in b))],
         'text': t, 'conf': round(float(c), 2)} for b, t, c in lines]}
    print(n, len(lines), 'lines', flush=True)
json.dump(res, open(f'{work}/ocr.json', 'w'), ensure_ascii=False, indent=1)
