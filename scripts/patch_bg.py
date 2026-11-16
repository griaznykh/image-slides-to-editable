"""Fix a slide background inside an already saved .pptx (no need to redo the text).
usage:
  patch_bg.py DECK.pptx SLIDE --white x0 y0 x1 y1 [x0 y0 x1 y1 ...]   # paint white, feathered (pt)
  patch_bg.py DECK.pptx SLIDE --fill  x0 y0 x1 y1 ...                  # inpaint rectangles (pt)
  patch_bg.py DECK.pptx SLIDE --image new.png                          # replace whole background
Re-open the deck in DeckCraft afterwards (open_presentation) to see the change.
"""
import sys, zipfile, shutil, re, io, os, tempfile
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

deck, n, mode = sys.argv[1], int(sys.argv[2]), sys.argv[3]
vals = sys.argv[4:]
z = zipfile.ZipFile(deck)
pres = z.read('ppt/presentation.xml').decode()
cx, cy = map(int, re.search(r'sldSz cx="(\d+)" cy="(\d+)"', pres).groups())
SW = cx / 12700
# slide order from presentation.xml -> rels
rels = z.read('ppt/_rels/presentation.xml.rels').decode()
ids = re.findall(r'<p:sldId [^>]*r:id="([^"]+)"', pres)
target = re.search(rf'Id="{ids[n-1]}"[^>]*Target="([^"]+)"|Target="([^"]+)"[^>]*Id="{ids[n-1]}"', rels)
sl = 'ppt/' + (target.group(1) or target.group(2)).lstrip('/').replace('ppt/', '')
sx = z.read(sl).decode()
bg = re.search(r'<p:bg>.*?r:embed="([^"]+)"', sx, re.S)
if not bg: sys.exit('slide has no picture background')
srels = z.read(sl.replace('slides/', 'slides/_rels/') + '.rels').decode()
t = re.search(rf'Id="{bg.group(1)}"[^>]*Target="([^"]+)"|Target="([^"]+)"[^>]*Id="{bg.group(1)}"', srels)
media = os.path.normpath(os.path.join(os.path.dirname(sl), t.group(1) or t.group(2)))
im = Image.open(io.BytesIO(z.read(media))).convert('RGB'); W, H = im.size; s = W / SW
if mode == '--image':
    im = Image.open(vals[0]).convert('RGB').resize((W, H), Image.LANCZOS)
else:
    rs = [[float(v) * s for v in vals[i:i + 4]] for i in range(0, len(vals), 4)]
    m = Image.new('L', im.size, 0); d = ImageDraw.Draw(m)
    for r in rs: d.rectangle([int(c) for c in r], fill=255)
    if mode == '--white':
        m = m.filter(ImageFilter.GaussianBlur(12 * s / 2))
        im = Image.composite(Image.new('RGB', im.size, (255, 255, 255)), im, m)
    else:
        import cv2
        a = cv2.inpaint(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR), np.array(m), 9, cv2.INPAINT_TELEA)
        im = Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB))
buf = io.BytesIO(); im.save(buf, 'JPEG' if media.lower().endswith(('jpg', 'jpeg')) else 'PNG', quality=92)
tmp = tempfile.mktemp(suffix='.pptx')
with zipfile.ZipFile(deck) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        zout.writestr(item, buf.getvalue() if item.filename == media else zin.read(item.filename))
shutil.copy(deck, deck + '.bak'); shutil.move(tmp, deck)
print(f'patched {media} of slide {n} (backup: {deck}.bak)')
