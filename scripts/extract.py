"""Extract the main (largest) picture of every slide of a .pptx.
usage: extract.py input.pptx WORKDIR
Writes WORKDIR/src/slideN.png and WORKDIR/meta.json:
  {slide_w, slide_h (pt), slides: {N: {image, pic_box_pt, texts: [...]}}}
`texts` lists text already present on the slide as editable shapes (e.g. a title the
author typed over the picture) - reproduce it in the spec instead of the baked-in text.
"""
import sys, os, json
from pptx import Presentation
from pptx.util import Emu
from PIL import Image
import io

src, work = sys.argv[1], sys.argv[2]
os.makedirs(f'{work}/src', exist_ok=True)
prs = Presentation(src)
EMU_PT = 12700
meta = {'slide_w': prs.slide_width / EMU_PT, 'slide_h': prs.slide_height / EMU_PT, 'slides': {}}
for n, slide in enumerate(prs.slides, 1):
    best, texts = None, []
    for sh in slide.shapes:
        if sh.shape_type == 13:  # picture
            area = sh.width * sh.height
            if best is None or area > best[0]:
                best = (area, sh)
        if sh.has_text_frame and sh.text_frame.text.strip():
            texts.append({'text': sh.text_frame.text,
                          'box_pt': [round(v / EMU_PT, 1) for v in (sh.left, sh.top, sh.width, sh.height)]})
    info = {'texts': texts}
    if best is None:
        # maybe the picture is the slide background
        bg = slide._element.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
        if bg is not None:
            rid = bg.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            blob = slide.part.related_part(rid).blob
            info['pic_box_pt'] = [0, 0, meta['slide_w'], meta['slide_h']]
        else:
            print(f'slide {n}: no picture found, skipped'); meta['slides'][n] = info; continue
    else:
        sh = best[1]; blob = sh.image.blob
        info['pic_box_pt'] = [round(v / EMU_PT, 1) for v in (sh.left, sh.top, sh.width, sh.height)]
    im = Image.open(io.BytesIO(blob)).convert('RGB')
    p = f'{work}/src/slide{n}.png'; im.save(p)
    info['image'] = p; info['px'] = im.size
    meta['slides'][n] = info
    print(f'slide {n}: {im.size[0]}x{im.size[1]} px, {len(texts)} existing text shape(s)')
json.dump(meta, open(f'{work}/meta.json', 'w'), ensure_ascii=False, indent=1)
print(f"slide size {meta['slide_w']}x{meta['slide_h']} pt")
