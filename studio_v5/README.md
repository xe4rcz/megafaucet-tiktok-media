# MegaFaucet Neon V5 — reference-directed first cut

One Russian-language cut, using the user's cyan/violet neon reference as an
art direction reference. The generated/reference UI is not used as product
footage. Actual source images are in `studio_v4/assets`; hero artwork comes
from the genuine site's public hero viewport. Other images inherit the
resolution and framing of the previous user-site master.

The edit has seven shots, a dense mobile composition, large type, a hero-art
close-up, full site overviews, separate detail insets, animated light trails,
particles and short directional wipes. This is animated screenshot footage,
not a continuous recording of live site usage.

Existing Russian speech is preserved at its original tempo and pitch.
Extended silent intervals above 650 ms are shortened to 300 ms, with a 250 ms
final pause. Spoken audio is not sped up. Music and transition accents are
synthesized locally without paid services or licensed samples. The final
mix uses measured two-pass loudness mastering; the export is H.264 1080×1920
30 FPS, AAC 48 kHz stereo.

```bash
python studio_v5/render.py
python studio_v4/qa.py media/studio-v5/MegaFaucet_Neon_V5_RU.mp4 --output media/studio-v5/qa.json
```

Requires the same installed dependencies as V4: Python, Pillow, NumPy,
FFmpeg/ffprobe and DejaVu Sans fonts. No website login, AI credits or paid
stock is used. This script does not publish or change any scheduled post.
A technical QA pass does not certify subjective voice naturalness, marketing
performance or the result of TikTok's later transcoding.

