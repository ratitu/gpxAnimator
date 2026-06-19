# gpxAnimator

Single-file Streamlit app: upload a GPX track, get an animated MP4 over a map.

## Run

```bash
pip install -r requirements.txt && streamlit run app.py
```

## Structure

- **`app.py`** — everything in one file (UI, logic, rendering, video encoding)
- **`bomJesusPerdoes.gpx`** — sample track loaded automatically when no file uploaded
- No tests, no CI, no lint config — edit `app.py` directly

## Key facts

| What | Detail |
|------|--------|
| State cache | GPX parsed data in `st.session_state`, keyed by `filename+size` |
| Frame rendering | `ThreadPoolExecutor` (max 4 workers), batches of 50 frames |
| Photo matching | EXIF timestamp → nearest anim frame (≥1hr diff rejected); fallback: nearest point by coords |
| Basemaps | OSM default, Esri satellite alt — URLs hardcoded in `app.py` |
| Video codec | `libx264` default, also `libx265`, `libvpx` via sidebar |
| Resolution presets | 480p, 720p, 1080p (all 1:1); plus 1080×1920 9:16 portrait |

## Gotchas

- `imageio-ffmpeg` is a **separate** dependency (required by moviepy for ffmpeg, listed in requirements.txt)
- `crf` quality presets: Low=23, Medium=18, High=14, Ultra=8
- At least 2 track points required; GPX without timestamps falls back to uniform spacing
- `.ruff_cache/` and `__pycache__/` are local artifacts — safe to ignore
