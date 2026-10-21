# SHER KOL — Character Sheet V2 skill

A Claude skill that turns an AI character image (or an old sheet, or a blend of 2–4 AI characters) into a standard character sheet for Higgsfield.

## Install
- **Quickest:** add `character-sheet-v2/SKILL.md` as a skill in Claude. It is self-contained: every script is embedded in its appendix.
- **Full:** download this repo as a zip (Code → Download ZIP) and install the `character-sheet-v2` folder.

## Before you start
1. Connect the **Higgsfield** connector in Claude (Settings → Connectors) with the SHER Higgsfield account.
2. Set Claude's network access to **All domains** (Higgsfield uses many storage subdomains).

## Use
Start a chat and say "make a character sheet" with one AI character image (or an old sheet, or 2–4 images to blend) and a name.
You get: pick board → QA board → sheet JPG. Then upload the sheet in Higgsfield → **Characters** → **Soul 2.0**.

## Files
- `character-sheet-v2/SKILL.md`: the skill (source of truth)
- `character-sheet-v2/scripts/`: the same scripts as the SKILL.md appendix
- `character-sheet-v2/TESTS.md`: test scenarios for checking the skill on another account
