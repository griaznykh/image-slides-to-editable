"""Turn a slide spec into a DeckCraft `batch` command list (JSON on stdout).
usage: gen.py SPEC.py SLIDE [SLIDE ...] [--yoff 0.33]
Paste the printed JSON as `commands` of mcp__deckcraft__batch (3-4 slides per call is fine).

Spec format (see examples/spec_template.py):
  SL[n] = [(x0, y0, x1, y1, text, style), ...]   # coordinates in slide points from dump_ocr.py
  x0,y0 = top-left of the first line's OCR box, x1 = right edge of the widest line,
  y1 = bottom of the last line.
  text: '\n' = new paragraph, '|' = original line break (joined with a space so text
        re-wraps naturally; with br=1 kept as a soft line break)
  style: f sans|serif, b bold, i italic, c colour, a left|center|right, cx centre x,
         g group (same font size = min of the group), s force size, ls force line spacing,
         w box width (wrap width), sb space after paragraphs, br keep line breaks,
         bullets 1, runs [(para, c0, c1, {"bold": True} | {"color": "#..."})]
Font size is solved so that the widest line of the block matches its width in the
original image; line spacing comes from the original line pitch.
"""
import sys, json, re, runpy, subprocess
from PIL import ImageFont

args = sys.argv[1:]
yoff = 0.33
if '--yoff' in args:
    i = args.index('--yoff'); yoff = float(args[i + 1]); del args[i:i + 2]
spec = runpy.run_path(args[0])
SL = spec['SL']
FAM = spec.get('FAMILIES', {'sans': 'Noto Sans', 'serif': 'Noto Serif'})

_fc = {}
def font(f, b, i):
    k = (f, b, i)
    if k not in _fc:
        style = ':'.join(x for x in (['bold'] if b else []) + (['italic'] if i else []))
        q = FAM[f] + (':' + style if style else '')
        path = subprocess.check_output(['fc-match', '-f', '%{file}', q], text=True)
        _fc[k] = ImageFont.truetype(path, 100)
    return _fc[k]

def width1(st, line):
    return font(st.get('f', 'sans'), bool(st.get('b')), bool(st.get('i'))).getlength(line) / 100

out = []
for slide in map(int, args[1:]):
    blocks = SL[slide]
    info = []
    for (x0, y0, x1, y1, text, st) in blocks:
        lines = re.split(r'[|\n]', text)
        mw = max(width1(st, l) for l in lines)
        info.append((st.get('s') or (x1 - x0) / mw, mw, lines))
    groups = {}
    for blk, (s, _, _) in zip(blocks, info):
        g = blk[5].get('g')
        if g and not blk[5].get('s'):
            groups[g] = min(groups.get(g, 1e9), s)
    out.append({'command': 'slide.go', 'params': {'index': slide - 1}})
    for (x0, y0, x1, y1, text, st), (s, mw, lines) in zip(blocks, info):
        if st.get('g') in groups and not st.get('s'):
            s = groups[st['g']]
        s = round(s * 2) / 2
        n = len(lines)
        ls = st.get('ls')
        if ls is None:
            ls = 1.0 if n == 1 else ((y1 - y0) / n) / (1.2 * s)
            ls = max(0.9, min(1.05 if st.get('b') else 1.6, ls))
        ls = round(ls, 2)
        w = max(st.get('w', 0), mw * s + 8)
        a = st.get('a', 'left')
        if a == 'center':
            x = st.get('cx', (x0 + x1) / 2) - w / 2
        elif a == 'right':
            x = x1 - w
        else:
            x = x0 - 1
        if st.get('bullets'):
            x -= 24; w += 24
        t = text.replace('|', '\u000b' if st.get('br') else ' ')
        out.append({'command': 'insert.textBox', 'params': {'rect': [round(x, 1), round(y0 - yoff * s, 1), round(w, 1), 40], 'text': t}})
        fd = {'family': FAM[st.get('f', 'sans')], 'size': s, 'color': st['c']}
        if st.get('b'): fd['bold'] = True
        if st.get('i'): fd['italic'] = True
        out.append({'command': 'format.fontDialog', 'params': fd})
        out.append({'command': 'format.margins', 'params': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0}})
        para = {'align': a, 'lineSpacing': ls, 'spaceBefore': 0, 'spaceAfter': st.get('sb', 0)}
        if st.get('bullets'):
            out.append({'command': 'format.bullets', 'params': {'on': True, 'char': '•'}})
            pitch = (y1 - y0) / n
            para.update(lineSpacing=1.0, indentLeft=24, indentFirst=-24, spaceAfter=round(max(0, pitch - 1.2 * s), 1))
        out.append({'command': 'format.paragraph', 'params': para})
        for (p, c0, c1, fmt) in st.get('runs', []):
            out += [{'command': 'text.edit', 'params': {'at': [p, c0]}},
                    {'command': 'text.select', 'params': {'anchor': [p, c0], 'caret': [p, c1]}},
                    {'command': 'format.fontDialog', 'params': fmt},
                    {'command': 'text.exit', 'params': {}}]
    out.append({'command': 'edit.select', 'params': {'ids': []}})
print(json.dumps(out, ensure_ascii=False, separators=(',', ':')))
