"""Contact sheets (2x2 per PNG) for quick visual review.
usage: sheet.py PATTERN OUTPREFIX N   e.g. sheet.py 'work/bg/bg{}.png' work/bgsheet 15
"""
import sys
from PIL import Image
pat, out, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
ims = [Image.open(pat.format(i)).convert('RGB').resize((688, 387)) for i in range(1, n + 1)]
for k in range(0, n, 4):
    s = Image.new('RGB', (688 * 2, 387 * 2), 'white')
    for j, im in enumerate(ims[k:k + 4]):
        s.paste(im, ((j % 2) * 688, (j // 2) * 387))
    s.save(f'{out}{k // 4}.png'); print(f'{out}{k // 4}.png')
