---
name: character-sheet-v2
description: Build a SHER KOL character sheet V2 (ready for a Higgsfield Soul 2.0 character) from an AI character image, an old sheet, or a blend of AI characters; optionally run a scene TSV. Use for any character sheet, blend or TSV test request.
---

# Character Sheet V2

Pipeline: preflight → intake → (blend) → clean master → 3 sheets (A/B/C) → grid check + face QA → combined sheet → user uploads it as a Soul 2.0 character → (Element + TSV run → results page, only when asked).
Everything needed is in this file. Do not rely on earlier chats or on who the user is: any team member running this skill must get the same kind of result. Follow the fixed settings exactly; do not swap models, aspect ratios or prompts.
Show images, keep text short. Reply in the user's language (casual Thai by default) with English technical terms.

## Fixed vs adaptable
This skill is written for Claude + the Higgsfield connector, but any agent in any setup may run it by adapting the tooling. What makes two runs match is the **fixed** part; the rest is plumbing.
- **Fixed (never change):** the model (Nano Banana 2.1) with the resolution and aspect ratio in the Fixed settings table; the clean master as the only reference for the sheets; the prompts word for word; the standard grid with no full-body panels; the QA thresholds; the deliverables.
- **Adaptable:** which service runs the model (Higgsfield, ComfyUI Cloud, fal or another provider), how images are uploaded, how the scripts are run (e.g. without `-I` if that hides installed packages), and any helper script you need to write.
- When you adapt, say in one line what you changed. Before paid generation on a provider without fixed prices, estimate the cost, keep a running total and stop before going past the user's budget.
- If Nano Banana 2.1 can't be reached anywhere in your setup, stop and say so; do not swap in another image model.
- The final Soul 2.0 character is always created in Higgsfield by the user (Step 6), whatever ran the generation.

## Step 0 — Preflight (always first)
1. **Higgsfield connector.** Check that the Higgsfield (HF) MCP tools are available (`generate_image_batch`, `jobs_wait`, `media_upload`, `media_confirm`, `manage_reference_elements`; load them with tool search if they are deferred).
   - If they are missing but you can run Nano Banana 2.1 another way, adapt (see Fixed vs adaptable) and say so in one line. If you can't, stop and tell the user in one short message: connect the Higgsfield connector in Claude (Settings → Connectors → add Higgsfield, sign in with the SHER Higgsfield account), then start a new chat and run the request again.
2. **Sandbox network access (Higgsfield setup).** The sandbox must reach Higgsfield to upload images (`curl PUT`) and download results. Test once:
   `curl -s -o /dev/null -w "%{http_code}" https://upload.higgsfield.ai` and the same for `https://d8j0ntlcm91z4.cloudfront.net` (a real HTTP response = reachable; `000`, a connection error or a proxy refusal = blocked).
   - If blocked, tell the user in one short message to set Claude's network access to **allow all domains** (Settings → Capabilities → code execution / network access → All domains; on Team/Enterprise an admin sets it in Admin settings → Capabilities), then start a new chat. Do not suggest a domain allowlist: Higgsfield serves storage from many changing subdomains, so a list breaks.
   - Until it is allowed, fall back to `media_upload_widget` so the user uploads each image to Higgsfield by hand, and say face QA may be unavailable.
3. **Credits.** Call `balance` if available. A sheet costs ~15–20 credits; a 30-row TSV test ~60 more. If the balance is lower, say so before generating.

## Step 1 — Intake: what the user can send
If the user starts without an image, reply with this checklist (short) and wait:

| Send this | What happens |
|---|---|
| **A. One character image**: AI character or a real model's photo (portrait or half body, face clear, front or near-front) | Used as the master source |
| **B. An old character sheet** (e.g. V1) | Crop the clearest front / close-up panel and use it as the master source |
| **C. 2–4 AI character images and "blend"** (can't decide a base) | Step 2 blend board, the user picks one |
| **Character name** (required), e.g. `Amara2` | Used for file names and the Soul 2.0 character name |
| Optional: hair change, age, vibe notes | Added to the master edit |

Rules for inputs:
- Any character source works: an AI character, a character SHER already owns, or a photo of a real model the team works with. No consent check is needed. The one exception: don't build a character from a celebrity or public figure.
- Low-resolution or tiny images are fine for the master edit; blurry faces with eyes closed or heavy occlusion are not. Ask for another image in that case.
- If the name is missing, ask for it in one line and keep going with everything else.

## Step 2 — Blend (only when the user asks to mix characters)
Upload all sources (`media_upload` → curl PUT → `media_confirm`). Generate on `nano_banana_2_1`, `2k`, `3:4`, all sources as `image_references` in the stated order. Make one image per ratio:

| Sources | Ratios to generate |
|---|---|
| 2 | 75/25 · 50/50 · 25/75 |
| 3 | 60/20/20 · 20/60/20 · 20/20/60 · 34/33/33 |
| 4 | 55/15/15/15 for each source as the base (4 images) |

Prompt:
```
A new original woman whose face is a blend of the women in the reference images: about [X]% image 1, [Y]% image 2[, Z% image 3 …]. Take the overall face shape, eyes and nose mainly from the dominant image and let the others shift the features slightly. She is one consistent new person, not a collage. [Hair description, taken from the dominant image unless the user says otherwise]. Plain fitted black tank top, no jewellery, nothing on her head. Early-to-mid 20s, mature adult face, light natural makeup. Soft even studio light, plain light grey backdrop, head-and-shoulders front-facing portrait, eyes to lens. Photographic, natural skin texture.
```
Run `board.py blend_board.jpg --ref src1 --ref src2 … <results> --labels 75/25,50/50,…` and send the **blend board**: sources on top, results below, each labelled with its ratio and its score vs each source. Note: one source often dominates even at 20–25%, and an even split (33/33/33) tends to lose identity; say so if the scores show it. The user picks one; it becomes the master source.

## Step 3 — Clean master
The master must have **nothing on the head**, no jewellery, and a plain black tank top. Anything on the master leaks into the sheets and every scene.
Edit on `nano_banana_2_1`, `2k`, `3:4`, with the master source (plus at most one extra angle of the same character) as `image_references`. Always make **2 variants**:
```
Same woman as image 1, same face exactly: same eyes, brows, nose, lips, jaw, skin tone and freckles, same calm neutral expression. [Remove the headscarf / earrings / accessory completely.] Her hair: [hair description], full volume, visible hairline. Nothing on her head, no jewellery. She wears a plain fitted black tank top. Early-to-mid 20s, mature adult face, light natural makeup. Soft even studio light, plain light grey seamless backdrop, head-and-shoulders front-facing portrait, eyes to lens. Photographic, natural skin texture.
```
Run `board.py pick_board.jpg --ref <source> m1.png m2.png --labels M1,M2` and send the pick board. Use the higher score / closer look unless the user picks. Skip any upscale; the 2k master is enough.

## Step 4 — Three sheets (standard grid, no full body)
`generate_image_batch`, 3 requests, `nano_banana_2_1`, `4k`, the clean master as the **only** reference.
**No full-body panels anywhere.** A full body locks a body shape into the character and fights the body shape the scene prompt sets when the outfit is swapped. Every panel is head-and-shoulders, cropped at the upper chest.

| Sheet | Grid | Aspect | Cells, in order |
|---|---|---|---|
| A turnaround | 1×4 | 16:9 | front · three-quarter · side profile · back |
| B head angles | 3×2 | 1:1 | top: front · 3/4 to image-left · 3/4 to image-right / bottom: profile · high camera · low camera |
| C expressions | 3×2 | 1:1 | top: neutral · closed-mouth smile · open laugh / bottom: serious · surprised · confident half smile |

B and C must be 1:1: at 16:9 or 3:2 the model turns 3×2 into 4×2 and fills the extra cells with repeats.

Shared tail:
```
[hair description], full hair volume. Plain fitted black tank top; no jewellery, no earrings, nothing on her head. Early-to-mid 20s, mature adult face, light natural makeup. White seamless studio background, soft even light, photographic, natural skin texture. No text, no labels, no borders, one person per cell.
```
- **A:** `Head-and-shoulders turnaround sheet of the woman in image 1, same face exactly. Four panels side by side in one row, each the same size and same framing, cropped at the upper chest (no full body): front view; three-quarter view; side profile view; back view showing the back of her head and her hair. Neutral relaxed expression.` + tail
- **B:** `Head-angle reference sheet of the woman in image 1, same face exactly. Six cells only: 3 columns by 2 rows, equal-size portrait cells filling the whole frame edge to edge. Do not add more cells. Every cell shows a different head direction. Top row, left to right: 1) straight front view, eyes to lens; 2) three-quarter view, face turned toward the left side of the image; 3) three-quarter view, face turned toward the right side of the image (mirror of cell 2). Bottom row, left to right: 4) full side profile, nose pointing to the right side of the image; 5) high camera angle looking down at her, she looks up at the lens; 6) low camera angle looking up at her chin. Neutral relaxed expression.` + tail
- **C:** `Expression reference sheet of the woman in image 1, same face exactly. Six cells only: 3 columns by 2 rows, equal-size front-facing head-and-shoulders portrait cells filling the whole frame edge to edge. Do not add more cells. Every cell a different expression. Top row, left to right: 1) neutral; 2) soft closed-mouth smile; 3) open laugh showing teeth. Bottom row, left to right: 4) serious, slight frown; 5) surprised, eyebrows raised, mouth slightly open; 6) confident half smile with one brow slightly raised.` + tail

## Step 5 — Grid check + QA
1. **Look at every sheet yourself first.** Count cells and check each matches its slot. Wrong cell count, a repeated angle or expression, a missing direction, empty gaps, text, jewellery or any full body → **redo that sheet** with the same prompt (up to 2 retries). Never patch a wrong grid with `LAYOUT` and ship it.
2. Put `master.png`, `A.png`, `B.png`, `C.png` in one folder, run `sheet_qa.py`.
3. Score bands for front-facing and expression cells:
   - **≥ 0.6: pass** (typical 0.7–0.9).
   - **0.363–0.6: pass with a note.** Do not redo automatically; list those cells to the user and ask them to check by eye before uploading.
   - **< 0.363: fail**, redo that sheet.
   Profile cells at 0.3–0.6 are normal (the detector is weak on side views; check them by eye); the back has no face. Send the QA board.
4. If the scripts can't run (no Python, models can't download), do the visual check only and say in one line that face scores are unavailable.

## Step 6 — Combined sheet + Soul 2.0 handoff
1. Run `clean_sheet.py` (master + A on top, B + C below, no text). Save as JPG q92 and send the JPG to the user (the PNG is often over the 30 MB send limit).
2. **Do not create the character yourself.** The team's character is a **Soul 2.0** character made in the Higgsfield UI from the single sheet image; the tools here can't run that same flow. Tell the user in a few lines: download the sheet JPG → Higgsfield → **Characters** → upload the sheet → choose **Soul 2.0** → name it (e.g. `Amara2`).
3. **Element (only when asked, or when a scene test needs one):** upload the JPG (`media_upload` → curl PUT → `media_confirm`), then `manage_reference_elements` with action `create`, category `character`, `medias: [{id, url}]`, name = what the user asked, default `<Name>2`. The tool cannot edit or delete Elements: to replace one, ask the user to delete the old Element in the Higgsfield UI first, then create the same name again.
4. Outfit Element (when product photos are sent for a scene test): one Element with all product angles, named `<Name> - <Outfit name>`.

**Deliverables (every run, same set):** pick board (and blend board if Step 2 ran) · QA board · combined sheet JPG · the Soul 2.0 upload steps · credits used.
End with a short offer of the scene test that also says what it needs (the test runs with an Element built from the same sheet, created at that point):
- The scene list as a sheet. Either connect the Google Drive / Sheets connector in Claude (Settings → Connectors) and send the sheet link, or export the sheet as TSV/CSV and attach it.
- Same columns as SHER's scene sheet, one scene per row (~30 rows). Show the user this example (header + one full row, tab-separated):
```tsv
#	Location	Light	Palette	Camera	Pose	References	Prompt	Prompt with References
1	(1) the Rosewood Bangkok lobby	Indoors by day	ivory, taupe, greige, veined marble, dark stained wood, brass	Eye level	Standing	@Hanna - Character Sheet, @Hanna - Pink Clara Set	An eye-level, mid-distance shot of a young woman standing in the Rosewood Bangkok lobby, weight dropped onto one hip as if she paused mid-walk, a small woven cane bag hanging from one hand at her side, her gaze drifting past the lens. Her dark hair is tucked behind one ear. She wears a sleeveless ivory knit top, wide taupe linen trousers and flat leather sandals. It sits on her body with natural weight: slight creasing and fold where fabric meets the figure, worn and not floating, and her pose never hides it. Behind her, the lobby runs deep: a long reception desk, a porter wheeling luggage at the far edge of the frame, a guest reading on a sofa. The light comes from one direction and the shadows show it: daylight through a tall window from one side is the main light, and an on-camera flash lifts her, close and hard, the lobby dropping darker just behind her. Nothing casts a shadow across the outfit, and soft shading stays on its folds and seams. The palette is ivory, taupe and greige, set in veined marble, dark stained wood and brass. Shot on an iPhone main camera, 24mm equivalent, deep focus, the lobby as sharp as she is. She fills a good part of the frame, a little off-center and tilted, one elbow clipped by the edge. A touch of motion blur on the swinging bag; her face and the outfit stay sharp. Processed the way a phone processes it: shadows lifted flat, highlights clipping abruptly, edges over-sharpened, fine texture smeared where the light runs out, luminance noise in the shadows, noise and not film grain. Modern Influencer fashion content, real and clean enough for her social media feed, easy and unbothered. No over-smoothed skin, no distorted proportions, no exaggerated filter or grade, no stiff, hovering, mannequin-like fabric.	An eye-level, mid-distance shot of @Hanna - Character Sheet wearing @Hanna - Pink Clara Set (with nothing changes or invented) standing in the Rosewood Bangkok lobby, weight dropped onto one hip as if she paused mid-walk, a small woven cane bag hanging from one hand at her side, her gaze drifting past the lens. Her dark hair is tucked behind one ear. The garment sits on her body with natural weight: slight creasing and fold where fabric meets the figure, worn and not floating, and her pose never hides it. Behind her, the lobby runs deep: a long reception desk, a porter wheeling luggage at the far edge of the frame, a guest reading on a sofa. The light comes from one direction and the shadows show it: daylight through a tall window from one side is the main light, and an on-camera flash lifts her, close and hard, the lobby dropping darker just behind her. Nothing casts a shadow across the garment, and soft shading stays on its folds and seams. The palette is ivory, taupe and greige, set in veined marble, dark stained wood and brass. Shot on an iPhone main camera, 24mm equivalent, deep focus, the lobby as sharp as she is. She fills a good part of the frame, a little off-center and tilted, one elbow clipped by the edge. A touch of motion blur on the swinging bag; her face and the garment stay sharp. Processed the way a phone processes it: shadows lifted flat, highlights clipping abruptly, edges over-sharpened, fine texture smeared where the light runs out, luminance noise in the shadows, noise and not film grain. Modern Influencer fashion content, real and clean enough for her social media feed, easy and unbothered. No over-smoothed skin, no distorted proportions, no exaggerated filter or grade, no stiff, hovering, mannequin-like fabric.
```

## Step 7 — Scene TSV run (only when asked)
- **Elements are the method.** Use `<<<element_id>>>` in the prompt. They work on `gpt_image_2_5` (Sunburst) and `nano_banana_2_1`. Never attach the sheet as an image instead without asking.
- **Run every row of the TSV, in every column asked for.** Never sample rows to save credits; save on model and quality instead.
- Before running, send a short plan with an estimated cost and wait for a go (unless already given). Default: Sunburst `medium` (1 credit per 2k image), both columns; offer `high` (2.75) or a second model as add-ons.
- Create the character Element first (Step 6.3) if there isn't one yet.
- Run `tsv_prompts.py`, submit each `batch_NN.json` with `generate_image_batch`, save job ids to a file right away. `jobs_wait` in groups of ≤ 12. `nsfw`/`failed` → `-`; never resubmit a job whose outcome is unknown.
- Download to `run_dir/raw/<index>.png`, write `urls.txt`, look at a contact sheet yourself before publishing.

## Step 8 — Results page
Run `build_page.py`, publish `index.html` with `img/` and `lg/` as an Artifact. Only the current run. Clicking a frame opens the lightbox in place; the full 2k link sits inside the lightbox. Reply in 3–5 lines: generated count, face avg/min per column, blocked rows, credits.

## Scripts (`scripts/`, run with `python3 -I`; needs opencv-python ≥ 4.8 and pillow)
If the `scripts/` folder is missing (skill installed as SKILL.md only), write the scripts you need from the appendix into a `scripts/` folder first: `face.py`, `board.py`, `sheet_qa.py`, `clean_sheet.py` for every run; `tsv_prompts.py`, `build_page.py` for a scene test.
- `face.py`: face match (YuNet + SFace), downloads models on first use. Same person: cosine > 0.363.
- `board.py <out.jpg> --ref <src> [--ref …] <cand …> --labels …`: pick board / blend board with scores vs each source.
- `sheet_qa.py <dir> <NAME> <out.jpg>`: splits A/B/C by the standard grid, scores each cell vs `master.png`, writes the QA board, prints `FAIL (redo these)`.
- `clean_sheet.py <dir> <out.png>`: combined sheet.
- `tsv_prompts.py <tsv> <out_dir> --char <id> [--outfit <id>] [--quality medium]`: batch JSONs for all rows.
- `build_page.py <tsv> <run_dir> <master.png> --title … --model-label … --char-name …`: results page.

## Fixed settings (do not change)
| Step | Model | Res | Aspect | References |
|---|---|---|---|---|
| Blend | nano_banana_2_1 | 2k | 3:4 | all sources, in order |
| Master ×2 | nano_banana_2_1 | 2k | 3:4 | source (+1 angle max) |
| Sheet A | nano_banana_2_1 | 4k | 16:9 | master only |
| Sheets B, C | nano_banana_2_1 | 4k | 1:1 | master only |
| TSV scenes | gpt_image_2_5 Sunburst medium | 2k | per TSV | Elements via `<<<id>>>` |

## Costs (Higgsfield, Oct 2026)
| Step | Credits |
|---|---|
| Blend board | 2 per image (6–8) |
| Master ×2 | ~4 |
| Sheets A/B/C | ~9, +3 per redo |
| TSV 30 rows × 2 columns, Sunburst medium | ≤ 60 (blocked jobs not charged) |

## Rules
- Preflight first: no Higgsfield connector → adapt with Nano Banana 2.1 elsewhere or stop and explain how to connect; sandbox can't reach Higgsfield → tell the user to allow all domains.
- Adapt the tooling, never the fixed part (model, prompts, grid, QA, deliverables).
- AI characters and the team's real models are both fine; no celebrities or public figures.
- Fixed settings and the standard grid, no full-body panels.
- Never drop TSV rows. Never switch Elements ↔ attached images without saying so.
- Facts about what a model supports come from a test, not the tool doc.
- Keep replies short: images first, numbers second.

## Appendix — scripts (write these if `scripts/` is missing)

### scripts/face.py
```python
"""Shared face-match helper (OpenCV YuNet + SFace). Same person: cosine > 0.363.
Models are downloaded once into ./models next to this file."""
import os, urllib.request, cv2
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
URL = {
    'yunet.onnx': 'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx',
    'sface.onnx': 'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx',
}
os.makedirs(D, exist_ok=True)
for n, u in URL.items():
    p = os.path.join(D, n)
    if not os.path.exists(p) or os.path.getsize(p) < 100000:  # guard against Git LFS pointer files
        urllib.request.urlretrieve(u, p)
_det = cv2.FaceDetectorYN.create(os.path.join(D, 'yunet.onnx'), '', (320, 320), 0.7)
_rec = cv2.FaceRecognizerSF.create(os.path.join(D, 'sface.onnx'), '')
THRESH = 0.363


def emb(img, max_side=1600):
    """img: path or BGR array. Returns embedding of the largest face, or None."""
    im = cv2.imread(img) if isinstance(img, str) else img
    k = max_side / max(im.shape[:2])
    if k < 1:  # large images must be downscaled or detection fails
        im = cv2.resize(im, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    h, w = im.shape[:2]
    _det.setInputSize((w, h))
    _, r = _det.detect(im)
    if r is None:
        return None
    r = max(r, key=lambda x: x[2] * x[3])
    return _rec.feature(_rec.alignCrop(im, r)).copy()


def sim(a, b):
    if a is None or b is None:
        return None
    return round(float(_rec.match(a, b, cv2.FaceRecognizerSF_FR_COSINE)), 2)
```

### scripts/board.py
```python
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
```

### scripts/sheet_qa.py
```python
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
```

### scripts/clean_sheet.py
```python
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
```

### scripts/tsv_prompts.py
```python
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
```

### scripts/build_page.py
```python
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
```
