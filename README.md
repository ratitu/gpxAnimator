# gpxAnimator

Streamlit app that generates animated MP4 videos from GPX track files overlaid on maps.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Features

- **GPX Track Animation**: Upload a GPX file to animate your route on a map
- **Photo Overlay**: Upload photos with EXIF data that display during the animation at the matching timestamp/location
- **Two Basemaps**: OpenStreetMap (default) or Esri World Imagery (satellite)
- **Follow Mode**: Camera centers on current position, or shows full track
- **Configurable Settings**:
  - Frames Per Second (5-60)
  - Target video duration (5-120 seconds)
  - Track color
  - Map zoom level (1-20)
  - Video resolution (480p, 720p, 1080p)
  - Photo display duration (1-10 seconds)

## Photo Matching

Photos are matched to the animation using:
1. **Timestamp matching** (priority): GPS timestamp from EXIF data matched to GPX track times
2. **Location fallback**: If no valid timestamp, photo is matched to nearest track point by coordinates

## Key Dependencies

- `streamlit` - Web UI framework
- `gpxpy` - GPX file parsing
- `staticmap` - Map tile rendering
- `moviepy` - Video generation (requires `imageio-ffmpeg` for codec)

## Notes

- Default basemap uses OpenStreetMap tiles (`http://a.tile.osm.org/{z}/{x}/{y}.png`)
- Satellite basemap uses Esri World Imagery
- A sample GPX file (`bomJesusPerdoes.gpx`) is included for testing
- Video codec: `libx264` (requires ffmpeg via `imageio-ffmpeg`)
