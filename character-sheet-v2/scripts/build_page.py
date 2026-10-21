"""Build the results page (like the Hanna / Nadia run pages): summary table, one section per TSV column,
face score per frame vs the master, click-to-enlarge lightbox (no outbound navigation).

python3 -I build_page.py <scenes.tsv> <run_dir> <master.png> --title "Nadia V2 x Sunburst" \
    --model-label "GPT Image 2.5 Sunburst (medium)" --char-name "Nadia - Character Sheet V2" \
    [--outfit-name "Nadia - Pink Clara Set"] [--spec "gpt_image_2_5 · sunburst · medium" --spec "2k · 3:4"]

<run_dir>/urls.txt: one line per job: "<index> <result_url>" or "<index> -" for blocked/failed.
<run_dir>/raw/<index>.png: downloaded results. Indices: 100+row = Prompt, 200+row = Prompt with References.
Writes <run_dir>/index.html, img/ (grid thumbs) and lg/ (lightbox size). Publish index.html with img/ and lg/ as files.
"""
import argparse, csv, re, html, os, json, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from face import emb, sim, THRESH
ap = argparse.ArgumentParser()
ap.add_argument('tsv'); ap.add_argument('run'); ap.add_argument('master')
ap.add_argument('--title', required=True); ap.add_argument('--model-label', required=True)
ap.add_argument('--char-name', required=True); ap.add_argument('--outfit-name', default='')
ap.add_argument('--spec', action='append', default=[])
a = ap.parse_args()
rows = {int(x['#']): x for x in csv.DictReader(open(a.tsv, encoding='utf-8'), delimiter='\t')}
N = len(rows)
os.chdir(a.run); os.makedirs('img', exist_ok=True); os.makedirs('lg', exist_ok=True)
urls = dict(l.split() for l in open('urls.txt') if l.strip())
m = emb(a.master)
scores = {}
for k, u in urls.items():
    k = int(k)
    if u == '-': continue
    p = f'raw/{k}.png'
    scores[k] = sim(m, emb(p))
    im = Image.open(p).convert('RGB')
    if not os.path.exists(f'img/{k}.webp'): im.resize((480, round(480 * im.height / im.width)), Image.LANCZOS).save(f'img/{k}.webp', quality=74, method=6)
    if not os.path.exists(f'lg/{k}.webp'): im.thumbnail((1000, 1340), Image.LANCZOS); im.save(f'lg/{k}.webp', quality=78, method=6)
json.dump(scores, open('scores.json', 'w'))
col = lambda r, *ks: next((r[k] for k in ks if r.get(k)), '')

def fig(i, off):
    r = rows[i]; loc = html.escape(re.sub(r'^\(\d+\)\s*', '', col(r, 'Location')))
    sub = html.escape(' · '.join(x for x in (col(r, 'Light'), col(r, 'Camera'), col(r, 'Pose')) if x))
    k = i + off; u = urls.get(str(k), '-')
    if u == '-':
        media = '<div class="blocked"><span>Blocked or failed</span></div>'; sc = ''
    else:
        s = scores[k]; sc = f'<small class="sc">face {s:.2f}</small>' if s is not None else '<small class="sc">face —</small>'
        media = f'<button type="button" class="lb" data-href="{html.escape(u)}" data-lg="lg/{k}.webp" data-cap="{i} · {loc}" aria-label="Enlarge row {i}"><img src="img/{k}.webp" alt="Row {i}, {loc}" loading="lazy" width="720" height="964"></button>'
    return f'<figure>{media}<div class="cap"><span class="no">{i}</span><div class="t"><b>{loc}</b><small>{sub}</small>{sc}</div></div></figure>'

def stats(off):
    gen = [i + off for i in rows if urls.get(str(i + off), '-') != '-']
    v = [scores[k] for k in gen if scores.get(k) is not None]
    return len(gen), (sum(v) / len(v) if v else 0), (min(v) if v else 0)

SECT = [('prompt', 'Prompt', 100, f'{a.model_label} · column “Prompt” · “a young woman” → <<<{a.char_name}>>>')]
if any(urls.get(str(200 + i)) for i in rows):
    SECT.append(('refs', 'Prompt with References', 200, f'{a.model_label} · column “Prompt with References” · <<<{a.char_name}>>>' + (f' wearing <<<{a.outfit_name}>>>' if a.outfit_name else '')))
intro = (f'All {N} rows of {os.path.basename(a.tsv)} on {a.model_label} using the {a.char_name} Element'
         + (f' and the {a.outfit_name} Element' if a.outfit_name else '') +
         f'. Face score is an automatic match against the master portrait; above {THRESH} reads as the same person. Tap a frame to enlarge; use arrows or swipe to browse.')
summary = ''.join(f'<tr><td><a href="#{sid}">{html.escape(t)}</a></td><td>Elements</td><td class="m">{n}/{N}</td><td class="m">{av:.2f}</td><td class="m">{lo:.2f}</td></tr>'
                  for sid, t, off, _ in SECT for n, av, lo in [stats(off)])
sections = ''.join(f'<section id="{sid}"><header class="sh"><h2>{html.escape(t)} <span class="tag">Elements</span></h2><p>{html.escape(d)} · <span class="ct">{n}/{N} generated · face avg {av:.2f}</span></p></header><div class="grid">{"".join(fig(i, off) for i in sorted(rows))}</div></section>'
                   for sid, t, off, d in SECT for n, av, lo in [stats(off)])

page = '''<title>''' + html.escape(a.title) + '''</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500&family=Figtree:wght@400;600&family=JetBrains+Mono:wght@500&display=swap">
<style>
:root{--bg:#f6f3f2;--card:#fffdfc;--fg:#231f20;--mute:#7a6f70;--line:#e4dcdb;--blush:#c98b93;--blk:#efe7e6;
--disp:"Fraunces",Georgia,serif;--body:"Figtree",system-ui,sans-serif;--mono:"JetBrains Mono",ui-monospace,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#181516;--card:#221e1f;--fg:#f1eaea;--mute:#a59a9b;--line:#352f30;--blush:#e0a9b0;--blk:#2b2526;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#181516;--card:#221e1f;--fg:#f1eaea;--mute:#a59a9b;--line:#352f30;--blush:#e0a9b0;--blk:#2b2526;color-scheme:dark}
body{background:var(--bg);color:var(--fg);font-family:var(--body);font-size:15px}
.wrap{max-width:1240px;margin:0 auto;padding-block:32px 64px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:48px}
.top h1{font-family:var(--disp);font-weight:500;font-size:clamp(28px,5vw,44px);margin:0 0 8px;text-wrap:balance}
.top p{margin:0;color:var(--mute);max-width:65ch;line-height:1.55}
.spec{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}
.spec span{font-family:var(--mono);font-size:12px;border:1px solid var(--line);padding:4px 10px;border-radius:999px}
.sum{margin-top:20px;overflow-x:auto}
.sum table{border-collapse:collapse;min-width:420px;font-size:14px}
.sum th,.sum td{text-align:left;padding:8px 14px 8px 0;border-bottom:1px solid var(--line)}
.sum th{color:var(--mute);font-weight:600;font-size:12px}
.sum td.m{font-family:var(--mono);font-variant-numeric:tabular-nums}
.sum tr.old td{color:var(--mute)}
.grp{font-family:var(--disp);font-weight:500;font-size:clamp(22px,3.5vw,30px);margin:0 0 -24px;padding-top:8px;border-top:2px solid var(--fg)}
.tag{font-family:var(--mono);font-size:11px;vertical-align:middle;border:1px solid var(--blush);color:var(--blush);padding:2px 8px;border-radius:999px;margin-left:6px}
.tag.o{border-color:var(--line);color:var(--mute)}
.sum a{color:var(--fg);font-weight:600;text-decoration:none;border-bottom:2px solid var(--blush)}
.sh{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:8px;border-bottom:1px solid var(--line);padding-bottom:12px;margin-bottom:20px}
.sh h2{font-family:var(--disp);font-weight:500;font-size:26px;margin:0}
.sh p{margin:0;color:var(--mute);font-size:13px}
.ct{font-family:var(--mono);color:var(--fg)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:20px}
figure{margin:0;display:grid;gap:8px;min-width:0}
figure img,.blocked{display:block;width:100%;height:auto;aspect-ratio:3/4;object-fit:cover;max-width:100%;background:var(--blk)}
figure a:focus-visible{outline:2px solid var(--blush);outline-offset:3px}
.blocked{display:grid;place-items:center;border:1px dashed var(--line)}
.blocked span{font-size:12px;color:var(--mute);letter-spacing:.04em;text-transform:uppercase}
.cap{display:flex;gap:10px;align-items:flex-start;min-width:0}
.no{font-family:var(--mono);font-size:12px;color:var(--blush);padding-top:2px;min-width:2ch;font-variant-numeric:tabular-nums}
.t{display:grid;gap:2px;min-width:0}
.t b{font-weight:600;font-size:13px;line-height:1.3}
.t small{color:var(--mute);font-size:12px}
.t .sc{font-family:var(--mono);font-size:11px}
@media (max-width:420px){.grid{grid-template-columns:1fr 1fr;gap:14px}}
button.lb{all:unset;display:block;cursor:zoom-in;overflow:hidden;width:100%}
button.lb:focus-visible{outline:2px solid var(--blush);outline-offset:3px}
#lbx{position:fixed;inset:0;z-index:50;background:rgba(10,8,9,.92);display:none;align-items:center;justify-content:center;padding:16px}
#lbx.on{display:flex}
#lbx img{max-width:100%;max-height:calc(100vh - 90px);object-fit:contain;box-shadow:0 10px 40px rgba(0,0,0,.5)}
#lbx .bar{position:absolute;left:0;right:0;bottom:0;display:flex;gap:12px;align-items:center;justify-content:center;padding:12px 16px;color:#f1eaea;font-size:13px}
#lbx .bar a{color:#e0a9b0}
#lbx button{position:absolute;top:50%;transform:translateY(-50%);background:rgba(255,255,255,.12);color:#fff;border:0;width:44px;height:64px;font-size:28px;cursor:pointer;border-radius:8px}
#lbx .pv{left:12px}#lbx .nx{right:12px}
#lbx .x{top:16px;right:16px;transform:none;width:44px;height:44px;font-size:22px}
@media (hover:hover){figure .lb img{transition:transform .25s ease}figure .lb:hover img{transform:scale(1.04)}}
</style>
<div class="wrap">
<div class="top"><h1>''' + html.escape(a.title) + '''</h1>
<p>''' + html.escape(intro) + '''</p>
<div class="spec">''' + ''.join(f'<span>{html.escape(x)}</span>' for x in a.spec) + '''</div>
<div class="sum"><table><thead><tr><th>Run</th><th>Method</th><th>Generated</th><th>Face avg</th><th>Face min</th></tr></thead><tbody>''' + summary + '''</tbody></table></div></div>
''' + sections + '''
</div>
<div id="lbx" role="dialog" aria-modal="true" aria-label="Image viewer"><button class="x" aria-label="Close">×</button><button class="pv" aria-label="Previous">‹</button><img alt=""><button class="nx" aria-label="Next">›</button><div class="bar"><span class="c"></span><a class="o" target="_blank" rel="noopener">Open full 2k ↗</a></div></div>
<script>
(()=>{const L=[...document.querySelectorAll('button.lb')],b=document.getElementById('lbx'),im=b.querySelector('img'),c=b.querySelector('.c'),o=b.querySelector('.o');let i=0;
const cache={};const pre=n=>{const a=L[(n+L.length)%L.length];if(!cache[a.dataset.lg]){const x=new Image();x.src=a.dataset.lg;cache[a.dataset.lg]=x}};
const show=n=>{i=(n+L.length)%L.length;const a=L[i],lg=a.dataset.lg;im.src=a.querySelector('img').src;const x=cache[lg]||new Image();cache[lg]=x;const swap=()=>{if(L[i]===a)im.src=lg};if(x.complete&&x.naturalWidth)swap();else{x.onload=swap;if(!x.src)x.src=lg}pre(i+1);pre(i-1);im.alt=a.dataset.cap;c.textContent=a.dataset.cap;o.href=a.dataset.href;b.classList.add('on')};
L.forEach((a,n)=>a.addEventListener('click',e=>{e.preventDefault();show(n)}));
const hide=()=>{b.classList.remove('on');im.src=''};
b.querySelector('.x').onclick=hide;b.querySelector('.pv').onclick=e=>{e.stopPropagation();show(i-1)};b.querySelector('.nx').onclick=e=>{e.stopPropagation();show(i+1)};
b.addEventListener('click',e=>{if(e.target===b)hide()});
addEventListener('keydown',e=>{if(!b.classList.contains('on'))return;if(e.key==='Escape')hide();if(e.key==='ArrowRight')show(i+1);if(e.key==='ArrowLeft')show(i-1)});
let x0=null;b.addEventListener('touchstart',e=>x0=e.touches[0].clientX,{passive:true});b.addEventListener('touchend',e=>{if(x0===null)return;const d=e.changedTouches[0].clientX-x0;if(Math.abs(d)>50)show(i+(d<0?1:-1));x0=null});})();
</script>'''
open('index.html', 'w').write(page)
for sid, t, off, d in SECT: print(t, stats(off))
print('frames', len(os.listdir('img')))
