"""Split sheets A/B/C into panels, score each panel vs the master, write a QA board.

python3 -I sheet_qa.py <dir> <NAME> <out.jpg> [baseline images ...]
<dir> must contain master.png A.png B.png C.png. Panels are written to <dir>/panels/.
If a sheet comes back with a different grid, set LAYOUT, e.g.
  LAYOUT='{"B":[[5,5],["front","3qL","3qR","3qL2","3qR2","profile","front2","high","3q","low"]]}'
"""
import json, os, sys, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from face import emb, sim, THRESH

d, NAME, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
m = emb(f'{d}/master.png')
assert m is not None, 'no face found in master.png'
grid = {'A': [4], 'B': [3, 3], 'C': [3, 3]}
names = {'A': ['front', '3q', 'side', 'back'],
         'B': ['front', '3qL', '3qR', 'profile', 'high', 'low'],
         'C': ['neutral', 'smile', 'laugh', 'serious', 'surprised', 'signature']}
for k, v in json.loads(os.environ.get('LAYOUT', '{}')).items():
    grid[k], names[k] = v
os.makedirs(f'{d}/panels', exist_ok=True)
res, report = {}, []
for s, rows in grid.items():
    im = cv2.imread(f'{d}/{s}.png'); H, W = im.shape[:2]; i = 0
    for r, cols in enumerate(rows):
        for c in range(cols):
            p = im[r * H // len(rows):(r + 1) * H // len(rows), c * W // cols:(c + 1) * W // cols]
            fn = f'{d}/panels/{s}{i + 1}_{names[s][i]}.png'; cv2.imwrite(fn, p)
            sc = sim(m, emb(p, 1200)); res[f'{s}{i + 1}'] = (fn, names[s][i], sc)
            report.append(f'{s}{i + 1} {names[s][i]:<10} {sc}')
            i += 1
for f in sys.argv[4:]:
    report.append(f'baseline {os.path.basename(f)} {sim(m, emb(f))}')
print('\n'.join(report))
fails = [k for k, (_, n, sc) in res.items() if sc is not None and sc < THRESH and n not in ('side', 'profile', 'back')]
print('FAIL (redo these):', fails or 'none')

# board
try:
    font = lambda z: ImageFont.truetype('DejaVuSans.ttf', z)
    font(10)
except OSError:
    font = lambda z: ImageFont.load_default()
pad, H1, h2 = 16, 900, 330
load = lambda p, h: (lambda im: im.resize((int(im.width * h / im.height), h)))(Image.open(p).convert('RGB'))
master = load(f'{d}/master.png', H1)
rows = [[res[k] for k in res if k.startswith(s)] for s in 'ABC']
A = [load(x[0], H1) for x in rows[0]]; BC = [[load(x[0], h2) for x in r] for r in rows[1:]]
W = max(master.width + pad + sum(i.width + pad for i in A), *(sum(i.width + pad for i in r) for r in BC)) + pad
img = Image.new('RGB', (W, 70 + H1 + 44 + (h2 + 44) * 2 + pad), (245, 243, 240)); dr = ImageDraw.Draw(img)
dr.text((pad, 14), f'{NAME.upper()} - character sheet QA (face match vs master; same person > {THRESH})', fill=(20, 20, 20), font=font(30))
def lab(x, y, k, it):
    s = it[2]; col = (30, 120, 60) if s is None or s >= .6 else ((190, 120, 20) if s >= THRESH else (190, 40, 40))
    dr.text((x, y), f'{k} {it[1]} ' + ('-' if s is None else f'{s:.2f}'), fill=col, font=font(24))
x, y = pad, 70; img.paste(master, (x, y)); dr.text((x, y + H1 + 6), 'MASTER', fill=(20, 20, 20), font=font(24)); x += master.width + pad
for n, (it, im) in enumerate(zip(rows[0], A), 1):
    img.paste(im, (x, y)); lab(x, y + H1 + 6, f'A{n}', it); x += im.width + pad
for ri, (s, r, ims) in enumerate(zip('BC', rows[1:], BC)):
    y = 70 + H1 + 44 + ri * (h2 + 44); x = pad
    for n, (it, im) in enumerate(zip(r, ims), 1):
        img.paste(im, (x, y)); lab(x, y + h2 + 6, f'{s}{n}', it); x += im.width + pad
img.save(OUT, quality=88); print('board', img.size)
