"""python3 -I clean_sheet.py <dir with master.png A.png B.png C.png> <out.png>
Top row: master + A (same height). Bottom row: B + C (same height). No text."""
import sys
from PIL import Image
d, out = sys.argv[1], sys.argv[2]
L = lambda n: Image.open(f'{d}/{n}').convert('RGB')
M, A, B, C = L('master.png'), L('A.png'), L('B.png'), L('C.png')
pad, bg = 40, (255, 255, 255)
H1 = 2400
rs = lambda im, h: im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
M, A = rs(M, H1), rs(A, H1)
W = M.width + pad + A.width
# bottom row height chosen so B + C fill the same width
h2 = round((W - pad) / (B.width / B.height + C.width / C.height))
B, C = rs(B, h2), rs(C, h2)
img = Image.new('RGB', (W + 2 * pad, H1 + h2 + 3 * pad), bg)
img.paste(M, (pad, pad)); img.paste(A, (pad + M.width + pad, pad))
img.paste(B, (pad, 2 * pad + H1)); img.paste(C, (pad + B.width + pad, 2 * pad + H1))
img.save(out); print(img.size)
