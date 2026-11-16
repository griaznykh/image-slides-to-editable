"""Build a .pptx with N blank slides whose *slide background* is the cleaned image.
usage: skeleton.py WORKDIR OUT.pptx [--width 2560]
Open OUT.pptx in DeckCraft (open_presentation) and add text boxes on top.
(DeckCraft's design.background only accepts base64, so the background is set here.)
"""
import sys, os, json
from pptx import Presentation
from pptx.util import Pt
from pptx.oxml.ns import qn
from lxml import etree
from PIL import Image
work, out = sys.argv[1], sys.argv[2]
width = int(sys.argv[sys.argv.index('--width') + 1]) if '--width' in sys.argv else 2560
meta = json.load(open(f'{work}/meta.json'))
SW, SH = meta['slide_w'], meta['slide_h']
os.makedirs(f'{work}/bgj', exist_ok=True)
prs = Presentation()
prs.slide_width, prs.slide_height = Pt(SW), Pt(SH)
NS = ('xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
for n in sorted(meta['slides'], key=int):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    p = f'{work}/bg/bg{n}.png'
    if not os.path.exists(p):
        print(f'slide {n}: no background, left blank'); continue
    # canvas = slide area; picture placed at its original box (usually the full slide)
    bx = meta['slides'][n]['pic_box_pt']; sc = width / SW
    canvas = Image.new('RGB', (width, round(SH*sc)), 'white')
    im = Image.open(p).convert('RGB').resize((max(1, round(bx[2]*sc)), max(1, round(bx[3]*sc))), Image.LANCZOS)
    canvas.paste(im, (round(bx[0]*sc), round(bx[1]*sc)))
    j = f'{work}/bgj/bg{n}.jpg'; canvas.save(j, quality=90)
    _, rId = s.part.get_or_add_image_part(j)
    bg = etree.fromstring(f'<p:bg {NS}><p:bgPr><a:blipFill dpi="0" rotWithShape="1"><a:blip r:embed="{rId}"/>'
                          f'<a:srcRect/><a:stretch><a:fillRect/></a:stretch></a:blipFill><a:effectLst/></p:bgPr></p:bg>')
    s._element.find(qn('p:cSld')).insert(0, bg)
prs.save(out); print('saved', out)
