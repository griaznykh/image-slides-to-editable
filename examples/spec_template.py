# Slide spec for gen.py.  One list of blocks per slide (1-based, SL[0] unused).
# Block: (x0, y0, x1, y1, text, style) - coordinates in slide points, read from dump_ocr.py:
#   x0, y0 = left/top of the block's first OCR line, x1 = right edge of its widest line,
#   y1 = bottom of the last line.  For centred blocks pass cx= the centre of the card/column.
# Text is TYPED BY YOU from the slide image (OCR text is only a hint - it has errors and
# drops quotes, dashes and «»).  '|' = line break as in the original, '\n' = new paragraph.
#
# Style keys:
#   f   'sans' | 'serif'          font family key (see FAMILIES)
#   b/i 1                         bold / italic
#   c   '#RRGGBB'                 colour (sample it from the image)
#   a   'left'|'center'|'right'   alignment;  cx = centre x for 'center'
#   g   'name'                    blocks of one group share the smallest fitted size
#                                 (use for card headers 'h' and card bodies 'b')
#   w   pt                        wrap width (inner width of the card) for flowing text
#   br  1                         keep '|' breaks (titles, poems, text inside circles)
#   s / ls                        force font size / line spacing
#   sb  pt                        space after each paragraph
#   bullets 1                     real bullet list, one paragraph per item
#   runs [(para, c0, c1, {'bold': True})]   partial formatting, e.g. bold "Правило:" prefix
FAMILIES = {'sans': 'Noto Sans', 'serif': 'Noto Serif'}

D = '#1B2233'   # dark title colour
T = '#26303F'   # body text colour
SL = [None] * 16

SL[2] = [
    (93, 31, 1187, 104, 'Заголовок слайда', dict(b=1, c=D, a='center')),
    (153, 344, 490, 386, 'Заголовок карточки', dict(b=1, c=D, a='center', g='h', cx=321)),
    (81, 416, 359, 638, 'Первая строка|вторая строка абзаца.\nВторой абзац.', dict(c=T, g='b', w=318, sb=6)),
    (140, 599, 1148, 661, 'Правило: текст строки|вторая строка', dict(c=T, a='center', br=1,
                                                                    runs=[(0, 0, 8, {'bold': True})])),
]
