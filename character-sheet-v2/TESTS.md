# character-sheet-v2 — test scenarios

How to use: install the skill on the other agent. Start a fresh chat for each test, attach the listed files and type the prompt exactly. Mark each check ✅/❌.
Assets (from this project): in `character-sheet-v2-test-assets.zip`: `old_master.jpg` (Nadia with the crochet headscarf), `m1.jpg` (Nadia V2, clean), `pink_clara/1–5.png`, `B_5x5_layout.jpg`, `artist-sher-2026-10-20-2.tsv`.
Budget: T1 ≈ 75 credits, T2/T3 ≈ 10 credits each; T4–T10 need no generation, or only a few images.

---

## T1 — Happy path (full pipeline)
**Attach:** old_master.jpg, pink_clara/1–5.png, the TSV
**Prompt:** `ทำ character sheet v2 ให้ Nadia แล้วรัน tsv นี้ ชุด Pink Clara`
**Pass if:**
- [ ] Notices the headscarf on the master and edits it out before making sheets (2 variants + a pick board with face scores)
- [ ] 3 sheets on nano_banana_2_1 4K, master as the only reference: A 1×4 at 16:9, B and C 3×2 at 1:1
- [ ] No full-body panel anywhere; no headscarf, jewellery or text; no repeated angle or expression
- [ ] Runs `sheet_qa.py` and sends a QA board (front panels ≥ 0.6)
- [ ] Sends the combined sheet as JPG to the user
- [ ] Sends the sheet JPG with the Soul 2.0 upload steps; creates the Elements `Nadia2` + `Nadia - Pink Clara Set` only because a TSV run was asked
- [ ] **Before** running the TSV, sends a plan with an estimated cost (≈ 60 credits for Sunburst medium) and waits for go
- [ ] Runs all 30 rows × 2 columns using `<<<element_id>>>`, not attached images
- [ ] Results page: only this run, summary table, click opens the lightbox (does not navigate away)
- [ ] Final reply is short: a table + blocked rows + credits

## T2 — Master already clean
**Attach:** m1.jpg. **Prompt:** `ทำ character sheet ให้ Nadia`
- [ ] Skips Step 1 (no edit) and goes straight to sheets
- [ ] Does not ask for a TSV or run scenes (none was requested)
- [ ] Ends with the sheet JPG + Soul 2.0 upload steps (no Element created) and offers the scene test, saying it needs the scene sheet (Sheets connector link or TSV/CSV)

## T3 — Missing input
**Attach:** m1.jpg only. **Prompt:** `ทำ sheet + element แล้วรัน tsv เลย`
- [ ] Does the sheet + Element, asks for the TSV in **one line**, and does not invent scenes

## T4 — Credit pressure
**Prompt (after T1 setup, before running):** `ประหยัดเครดิตหน่อย`
- [ ] Keeps all 30 rows; saves by quality/model (Sunburst medium, one model)
- [ ] ❌ fail if it proposes running only 5–10 sample rows

## T5 — Model claim trap
**Prompt:** `รัน tsv ด้วย nano banana 2.1 นะ`
- [ ] Still uses Elements (`<<<id>>>`) on nano_banana_2_1
- [ ] ❌ fail if it says "NB 2.1 doesn't support Elements" and switches to attaching images without testing

## T6 — Replace an existing Element
**Prompt:** `อัปเดต element Nadia - Character Sheet เป็นชีทใหม่`
- [ ] Creates a new Element with a new name (`… V2`/`… V3`), uses it from then on
- [ ] Tells the user to delete the old one in the Higgsfield UI (the tool cannot)

## T7 — Wrong sheet grid
**Setup:** B or C comes back as 4×2 / 5+5 / 4+3 with repeated angles (it happens often at 16:9; or attach `B_5x5_layout.jpg` and ask it to build the sheet)
- [ ] Notices the wrong grid / repeats **before** QA and regenerates that sheet (B and C at 1:1)
- [ ] ❌ fail if it ships the sheet using `LAYOUT` or makes the Element from a non-standard grid

## T9 — Results page behaviour
**Check on any finished page:**
- [ ] Clicking a frame opens the lightbox; arrows, swipe and Esc work
- [ ] "Open full 2k" is the only outbound link
- [ ] Blocked rows show as "Blocked or failed" tiles, not missing
- [ ] Opening the lightbox shows the thumbnail instantly, then sharpens

## T10 — Upscale failure
**Setup:** the 4K upscale job returns `failed`
- [ ] Moves on with the 2k master (no repeated paid retries) and says so in one line

## T11 — No Higgsfield connector (run on an account without HF MCP)
**Prompt:** `ทำ character sheet ให้ตัวนี้` + any AI portrait
- [ ] If Nano Banana 2.1 is reachable another way (e.g. ComfyUI Cloud, fal), adapts, says what it changed, estimates cost, and keeps prompts/grid/QA unchanged
- [ ] If no route to Nano Banana 2.1 exists, stops and tells the user to connect Higgsfield, then start a new chat
- [ ] ❌ fail if it switches to a different image model

## T12 — Empty start
**Prompt:** `อยากทำ character sheet ใหม่` (no image)
- [ ] Replies with the intake checklist: one AI image / an old sheet / 2–4 AI images to blend, plus the character name
- [ ] Mentions it can blend several characters if the user can't decide
- [ ] Does not generate anything yet

## T13 — Blend
**Attach:** 3 AI character portraits. **Prompt:** `เลือกไม่ได้ ช่วย blend 3 ตัวนี้หน่อย ชื่อ Mina`
- [ ] Generates 4 blends (60/20/20 ×3 + 34/33/33) on nano_banana_2_1 2k 3:4
- [ ] Sends one blend board with each result's score vs each source
- [ ] Waits for the pick, then continues with master → sheets → sheet JPG + Soul 2.0 upload steps for `Mina2`

## T14 — Same result, different person
**Setup:** Stamp and Pat each run T2 with the same master in separate accounts
- [ ] Both get the same deliverable set: pick board, QA board, combined sheet JPG, Soul 2.0 upload steps, credits
- [ ] Both sheets have the same layout (A 1×4, B 3×2, C 3×2, no full body); faces differ only by normal generation variance

## T15 — Network blocked
**Setup:** account where the sandbox can't reach `upload.higgsfield.ai`. **Prompt:** `ทำ character sheet ให้ตัวนี้` + an AI portrait
- [ ] Tests access before uploading and tells the user to set network access to **all domains** (not a domain list)
- [ ] Offers the manual upload widget as a fallback instead of failing silently

## T16 — Real model photo
**Attach:** a photo of a real model the team works with (famous or not). **Prompt:** `ทำ character sheet ให้น้องคนนี้ ชื่อ Mai`
- [ ] Proceeds straight to the clean master; no refusal and no consent questions

---

### Scoring
- Must pass: T1, T4, T5, T11, T14, T15, T16.
- T2/T3/T6/T7/T9/T10/T12/T13: at least 7 of 8.
- Note every ❌ with what the agent said; that tells us which line of SKILL.md to sharpen.
