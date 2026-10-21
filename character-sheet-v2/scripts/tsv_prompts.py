"""Turn a scene TSV into generate_image_batch request chunks that use Elements.

python3 -I tsv_prompts.py <scenes.tsv> <out_dir> --char <element_id> [--outfit <element_id>]
        [--model gpt_image_2_5] [--variant sunburst] [--quality medium] [--res 2k] [--ar 3:4]

TSV columns used: '#', 'Prompt', 'Prompt with References'.
- 'Prompt': the first "a young woman" becomes <<<char>>>.
- 'Prompt with References': every '@<Name> - Character Sheet' tag becomes <<<char>>>,
  every other '@<Name> - <Outfit>' tag becomes <<<outfit>>>.
Indices: 100+row for 'Prompt', 200+row for 'Prompt with References'.
Writes <out_dir>/prompts.json and <out_dir>/batch_NN.json (12 requests each, ready to paste).
Every TSV row is included: never drop rows to save credits.
"""
import argparse, csv, json, os, re
ap = argparse.ArgumentParser()
ap.add_argument('tsv'); ap.add_argument('out')
ap.add_argument('--char', required=True); ap.add_argument('--outfit')
ap.add_argument('--model', default='gpt_image_2_5'); ap.add_argument('--variant', default='sunburst')
ap.add_argument('--quality', default='medium'); ap.add_argument('--res', default='2k'); ap.add_argument('--ar', default='3:4')
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
rows = list(csv.DictReader(open(a.tsv, encoding='utf-8'), delimiter='\t'))
P, problems = {}, []
for r in rows:
    n = int(r['#'])
    p1 = re.sub(r'\ba young woman\b', f'<<<{a.char}>>>', r['Prompt'], count=1, flags=re.I)
    if a.char not in p1: problems.append(f'row {n} Prompt: no "a young woman" to replace')
    P[100 + n] = p1
    p2 = r.get('Prompt with References', '')
    if p2:
        p2 = re.sub(r'@[^@,()]*?-\s*Character Sheet', f'<<<{a.char}>>>', p2)
        if a.outfit:
            p2 = re.sub(r'@[A-Za-z]+ - [A-Za-z ]+?(?= \(| wearing|,|\.|$)', f'<<<{a.outfit}>>>', p2)
        if '@' in p2: problems.append(f'row {n} Prompt with References: tag left over')
        P[200 + n] = p2
params = {'model': a.model, 'resolution': a.res, 'aspect_ratio': a.ar}
if a.model.startswith('gpt_image'): params.update(variant=a.variant, quality=a.quality)
reqs = [{'index': k, 'params': dict(params, prompt=v)} for k, v in sorted(P.items())]
json.dump(P, open(f'{a.out}/prompts.json', 'w'), ensure_ascii=False, indent=0)
for i in range(0, len(reqs), 12):
    json.dump(reqs[i:i + 12], open(f'{a.out}/batch_{i // 12:02d}.json', 'w'), ensure_ascii=False)
print(f'{len(rows)} rows -> {len(reqs)} requests in {(len(reqs) + 11) // 12} batches')
print('problems:', problems or 'none')
