# MegaFaucet TikTok Media Studio

Repository for verified **public** creative media for **MegaFaucet** (https://mega-faucet.click/). Destination TikTok: `@caesar_2111`.

## Current status — 2026-10-17

**Preferred generator:** `studio_reel.py` (Studio V3). It generates a four-scene, ~20-second vertical creative with real Playwright website screenshots, Inter/DejaVu typography, subtle motion graphics, English neural narration, custom-produced music and sound accents, and captions. It produces a DRAFT only.

Verified GitHub Actions success: [Studio V3 render](https://github.com/xe4rcz/megafaucet-tiktok-media/actions/runs/38969001157).

**Current preview**: [Studio V3 MP4](media/studio/studio-v3-preview.mp4) • [cover](media/studio/studio-v3-cover.jpg) • [voice and technical metadata](media/studio/studio-v3-preview.mp4.json).

**Metricool editorial draft**: [Open studio V3](https://app.metricool.com/planner/calendar?blogId=7471113&openWithPostUuid=4646421288497139645). Confirmed: `draft=true`, `autoPublish=false`, `privacyOption=SELF_ONLY`. **Not posted on TikTok**. AI media label set for the draft.

## Safety + truthful marketing

- Footage is taken from the publicly available website, not hand-drawn fake product screenshots.
- No fabricated earnings, testimonials, deposits, guaranteed income or fake withdrawal claims.
- The latest V3 creative is a candidate for visual review, **not a claim of professional certification**. Verify clarity, pacing and composition before granting automatic publication.
- If the website or neural speech is unavailable, the build fails rather than quietly substituting false interface footage or robotic voice.
- Never commit social credentials, private user information or business secrets to this public repository.

## What is automated

1. `capture_site.py` retrieves real mobile screenshots of MegaFaucet (public pages only).
2. `studio_reel.py` creates the H.264/AAC vertical video and voice.
3. `.github/workflows/studio-preview.yml` runs the preview and commits the draft MP4 and cover to `media/studio` using GitHub Actions. Manual runs are available through GitHub Actions.
4. The ChatGPT Metricool connector has independently and successfully imported the GitHub raw MP4 URL as a *draft*. The import does not happen by GitHub Actions itself.

## Paused pending creative review

The **old weekday** renderer `reel_v2.py` generated one older style clip. Its `daily-drafts.yml` automatic triggers were deliberately paused, leaving manual runs only. The separate ChatGPT daily draft-import reminder was also paused. We do not want to auto-distribute low-quality material. No automatic public posting is active.

Once the Studio V3 quality meets the brand standard, the next change is to parameterize its topic + schedule, add an editorial visual-quality review gate and a verified non-duplicating import path, and finally test explicit public post delivery. TikTok publication must not be represented as completed before it is confirmed on the target account.

## Topic rotation

`content/topics.json` has 20 content themes for later use. `studio_reel.py --topic-index 0` selects the initial general overview; indices 1–19 rotate the content. The neural narration lines are edited per topic.

## Run a preview on a GitHub runner

Open [Studio V3 workflow](https://github.com/xe4rcz/megafaucet-tiktok-media/actions/workflows/studio-preview.yml), choose Run workflow. The result is committed to `media/studio/studio-v3-preview.mp4` and is **never automatically posted**.

## Legacy files

- `make_reel.py`: original connectivity proof
- `.github/workflows/render-test.yml`: original connectivity proof, manual runs
- `reel_v2.py`: previous lower-quality narrated format, retired
- `media/github-upload-test.mp4`: first pipeline connectivity test, not for promotion
