# MegaFaucet TikTok — Free media pipeline

Public media repository for [MegaFaucet](https://mega-faucet.click/). TikTok: **@caesar_2111**.

## Automation status

| Phase | State |
| --- | --- |
| Public site mobile screenshots (Playwright) | Configured / validated on successful runs |
| Original short promo video with motion, neural English voice, music bed and captions | Configured / validated on successful runs |
| GitHub Actions rendering to MP4 + cover | Automatic, Monday–Friday |
| Up to 20 new drafts per month | Enforced by script + workflow |
| Publish to TikTok | **Not enabled** — requires content review and independent Metricool scheduling |
| Metricool draft upload from GitHub raw URL | Independently verified using earlier upload test |

**Do not publish test footage.** New videos are placed under \`media/drafts/\` and marked \`DRAFT_REQUIRES_CREATIVE_REVIEW\`. They contain real public-site captures only.

## Main automation

Workflow: [Produce narrated TikTok drafts](.github/workflows/daily-drafts.yml)

- GitHub Actions schedule: weekdays at 07:10 UTC (about 09:10 or 10:10 Kyiv depending on daylight savings).
- Can also run manually from GitHub Actions → \`Produce narrated TikTok drafts (REAL SITE)\` → Run workflow.
- It captures the live **public** landing page, uses \`edge-tts\` English neural voice (fails hard instead of falling back to robotic narration), adds dynamic text, encodes 1080×1920 H.264/AAC, verifies both streams and commits output.
- If public website or neural speech service fails, the workflow **fails without committing a bad draft**.
- Only 20 video drafts per month, with duplicates for a given local date avoided.
- \`media/latest.json\` points to newest public raw MP4.

## Structure

- \`capture_site.py\` — real screenshots from the public landing page using Playwright
- \`reel_v2.py\` — new 9:16 narrated motion-video renderer
- \`content/topics.json\` — 20 distinct grounded English scripts
- \`media/drafts/\` — generated files (when successful)
- \`media/covers/\` — cover frame thumbnails
- \`media/latest.json\` — current draft metadata
- \`make_reel.py\`, \`render-test.yml\` — legacy upload smoke test only

## Publishing safely

The Metricool connector can import a public raw GitHub MP4 URL into a **draft**, as verified previously. For a real publication, a reviewed video must be scheduled separately; GitHub Actions alone cannot call ChatGPT's Metricool connector. Never commit passwords, TikTok tokens or API keys. Do not imply that the GitHub schedule is a TikTok publication schedule.

## Verify draft locally (optional)

\`\`\`bash
python -m pip install pillow numpy playwright edge-tts
python -m playwright install chromium
python capture_site.py
python reel_v2.py --validate-only
python reel_v2.py --topic-index 0 --out media/drafts/manual-review.mp4
\`\`\`

Requires system FFmpeg and DejaVu fonts.
