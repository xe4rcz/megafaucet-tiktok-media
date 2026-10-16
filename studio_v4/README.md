# MegaFaucet motion-edit candidate V4

This is a **screenshot-based motion edit**, not a CapCut export, live screen
recording, or a finished unattended professional studio. No paid plan, model
credits, subscriptions, or licensed music samples are used.

## Verified CapCut limitation

Sign-in succeeded in the ChatGPT Work cloud browser. Opening **Video Editor →
Create new** redirected to CapCut's incompatibility page. CapCut explicitly
reported `browser_unsupported_feature: [WebGL2]`. No editor timeline opened and
no CapCut project was created. This was a graphics capability failure, not a
CAPTCHA, paywall, or inferred bot block. No browser safeguards were bypassed.

## Assets and editing

- `assets/home.jpg` and `assets/payments.jpg`: actual public MegaFaucet website
  viewports captured through the Work browser during this task.
- `assets/dashboard.png`, `offers.png`, `withdraw.png`: product image rectangles
  extracted from the existing public master configured in
  `regional_campaign/regions.json`. The surrounding old advertising titles were
  removed; the pre-existing UI image content was retained. These assets inherit
  the original source's resolution and framing limitations.
- No payment totals, testimonials, or interfaces are fabricated.
- Full captured views stay visible; separate magnified details provide context.
- Typography, entrances, edge accents, beat-aligned cuts, and an original music
  bed are rendered in code. Narration reuses existing regional MP3s without
  tempo processing. Source voice files remain unchanged.
- English US, English UK, Hindi, Urdu, Russian, Kazakh, Uzbek, Azerbaijani,
  Romanian use existing localized copy. Arabic and Devanagari require RAQM and
  Noto script fonts (bundled with upstream license).

## Run

Installed dependencies: Python, Pillow with RAQM, NumPy, FFmpeg/ffprobe.

```bash
python studio_v4/render.py --regions cis-ru
python studio_v4/render.py
python studio_v4/qa.py media/studio-v4/*.mp4 --output media/studio-v4/qa.json
```

Output: H.264/yuv420p 1080×1920 at 30 FPS, AAC stereo 48 kHz/192 kbps,
fast-start MP4. The mix uses measured two-pass loudness normalization around
−16 LUFS with a −1.5 dBTP target. QA decodes the complete export, checks format,
AV duration, clipped samples, loudness and true peak. Final exports are promoted
only after the temporary mux passes container/duration checks.

Technical QA cannot certify natural voice quality, translation, conversion,
or the sound of TikTok's subsequent transcoding. No claim that the reported
post-publication robotic voice has been reproduced or fixed is made.

## Publication state checked

Metricool brand **7471113**, TikTok **@caesar_2111** already has nine regional
posts pending. Existing schedule (Europe/Moscow):

| Version | Existing scheduled time |
|---|---|
| Hindi | 2026-10-18 17:30 |
| US English | 2026-10-19 02:30 |
| UK English / Europe | 2026-10-20 20:30 |
| Urdu | 2026-10-22 17:30 |
| Russian | 2026-10-24 19:30 |
| Kazakh | 2026-10-27 17:30 |
| Uzbek | 2026-10-29 17:30 |
| Azerbaijani | 2026-10-31 18:30 |
| Romanian / Moldova | 2026-11-02 20:30 |

One older post was confirmed PUBLISHED, platform video ID
`7697393553894296833`; another earlier attempt had a frame-rate error.
The scheduled Russian upload decoded successfully and already uses AAC
48 kHz stereo. This alone does not establish naturalness or eliminate a
TikTok playback/transcoding issue.

V4 exports are candidates with `CREATIVE_REVIEW_REQUIRED` status. No duplicate
posts were created and no scheduled creative was replaced during this task.
There is no unattended publishing workflow in V4. Future different scripts
require distinct editorial storyboards and suitable real footage, not just
rotating headlines over the same screenshots.
