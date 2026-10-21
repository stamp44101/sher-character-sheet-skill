"""Labelled comparison board with face scores (pick board / blend board).
python3 -I board.py <out.jpg> --ref <src1.png> [--ref <src2.png> ...] <cand1.png> [<cand2.png> ...] [--labels "M1,M2,..."]
Top row: references. Bottom row: candidates, each labelled with its score vs every reference."""
import argparse, os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from face import emb, sim
a = argparse.ArgumentParser(); a.add_argument('out'); a.add_argument('cands', nargs='+')
a.add_argument('--ref', action='append', required=True); a.add_argument('--labels', default='')
o = a.parse_args()
labels = o.labels.split(',') if o.labels else [f'#{i+1}' for i in range(len(o.cands))]
R = [emb(p) for p in o.ref]
try: F = lambda z: ImageFont.truetype('DejaVuSans.ttf', z); F(10)
except OSError: F = lambda z: ImageFont.load_default()
H, pad = 700, 20
ld = lambda p: (lambda i: i.resize((int(i.width * H / i.height), H)))(Image.open(p).convert('RGB'))
top = [ld(p) for p in o.ref]; bot = [ld(p) for p in o.cands]
W = max(sum(i.width + pad for i in top), sum(i.width + pad for i in bot)) + pad
img = Image.new('RGB', (W, 2 * (H + 80) + pad), (245, 243, 240)); d = ImageDraw.Draw(img)
x = pad
for k, im in enumerate(top):
    img.paste(im, (x, pad)); d.text((x, pad + H + 10), f'source {k+1}', fill=(20, 20, 20), font=F(30)); x += im.width + pad
x = pad; y = H + 80 + pad
for lab, p, im in zip(labels, o.cands, bot):
    e = emb(p); sc = ' / '.join('-' if sim(r, e) is None else f'{sim(r, e):.2f}' for r in R)
    img.paste(im, (x, y)); d.text((x, y + H + 10), f'{lab}  {sc}', fill=(20, 20, 20), font=F(30)); x += im.width + pad
    print(lab, sc)
img.save(o.out, quality=88); print('board', img.size)
