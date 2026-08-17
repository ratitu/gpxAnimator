import streamlit as st
import gpxpy
import numpy as np
from staticmap import StaticMap, Line, CircleMarker
from moviepy import ImageSequenceClip, AudioFileClip, concatenate_audioclips
from PIL import Image, ExifTags, ImageDraw, ImageFont
import tempfile
import os
import time
import io
import shutil
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

_LOGO = None

def _get_logo():
    global _LOGO
    if _LOGO is None:
        _LOGO = Image.open("logo-no-background.png").convert("RGBA")
    return _LOGO

st.set_page_config(page_title="GPX Animator", layout="wide", page_icon="🗺️")

st.markdown(
    """
    <style>

@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Outfit:wght@400;500;600&display=swap');

/* ============ BASE ============ */
html, body, [data-testid="stAppViewContainer"], .stApp {
  font-family: "Outfit", "Space Grotesk", sans-serif;
}
h1, h2, h3, h4, h5, h6, [data-testid="stHeading"] {
  font-family: "Space Grotesk", "Outfit", sans-serif;
}

/* ============ HERO ============ */
.gpx-hero {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 14px 0 10px;
  flex-wrap: wrap;
}
.gpx-hero-logo {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  flex-shrink: 0;
  box-shadow: 0 0 26px rgba(182, 255, 0, 0.28), 0 6px 20px rgba(0, 0, 0, 0.45);
}
.gpx-hero .gpx-hero-eyebrow {
  font-family: "Space Grotesk", "Outfit", sans-serif;
  font-weight: 600;
  font-size: 11px;
  letter-spacing: 0.42em;
  text-transform: uppercase;
  color: rgba(232, 237, 243, 0.5);
  margin: 0 0 3px;
}
.gpx-hero .gpx-hero-title {
  font-family: "Space Grotesk", "Outfit", sans-serif;
  font-weight: 700;
  font-size: 42px;
  line-height: 1.05;
  letter-spacing: -0.02em;
  color: #E8EDF3;
  margin: 0 0 5px;
}
.gpx-hero-title .gpx-accent {
  background: linear-gradient(92deg, #B6FF00 5%, #F2FF00 95%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
}
.gpx-hero .gpx-hero-tagline {
  font-family: "Outfit", "Space Grotesk", sans-serif;
  font-weight: 500;
  font-size: 11.5px;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: rgba(232, 237, 243, 0.58);
  margin: 0;
}

/* ============ ATMOSPHERE ============ */
.gpx-glow {
  position: fixed;
  pointer-events: none;
  z-index: 1;
  border-radius: 50%;
}
.gpx-glow-tl {
  top: -220px;
  left: -180px;
  width: 640px;
  height: 640px;
  background: radial-gradient(circle, rgba(182, 255, 0, 0.10) 0%, rgba(182, 255, 0, 0.04) 35%, transparent 68%);
}
.gpx-glow-tr {
  top: -240px;
  right: -200px;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(242, 255, 0, 0.07) 0%, rgba(242, 255, 0, 0.03) 35%, transparent 68%);
}
.gpx-grain {
  position: fixed;
  inset: 0;
  z-index: 9999;
  pointer-events: none;
  opacity: 0.04;
  background-image: url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHdpZHRoPScxNjAnIGhlaWdodD0nMTYwJz48ZmlsdGVyIGlkPSduJz48ZmVUdXJidWxlbmNlIHR5cGU9J2ZyYWN0YWxOb2lzZScgYmFzZUZyZXF1ZW5jeT0nMC44NScgbnVtT2N0YXZlcz0nMicgc3RpdGNoVGlsZXM9J3N0aXRjaCcvPjxmZUNvbG9yTWF0cml4IHR5cGU9J3NhdHVyYXRlJyB2YWx1ZXM9JzAnLz48L2ZpbHRlcj48cmVjdCB3aWR0aD0nMTYwJyBoZWlnaHQ9JzE2MCcgZmlsdGVyPSd1cmwoI24pJy8+PC9zdmc+");
}

/* ============ SIDEBAR ============ */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #111820 0%, #0C121B 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}
[data-testid="stSidebar"] h2 {
  font-family: "Space Grotesk", "Outfit", sans-serif;
  font-weight: 600;
  font-size: 12.5px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #B6FF00;
  margin: 26px 0 12px;
  padding-top: 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
}
[data-testid="stSidebar"] h2::before {
  content: "\25C6";
  font-size: 8px;
  margin-right: 9px;
  vertical-align: 2px;
  color: #B6FF00;
  opacity: 0.85;
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
  font-family: "Outfit", "Space Grotesk", sans-serif;
  font-weight: 500;
  font-size: 13px;
  color: rgba(232, 237, 243, 0.78);
}

/* ============ SIDEBAR WIDGETS ============ */
[data-testid="stSelectbox"] div[role="group"] {
  background: #0A0E14;
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 8px;
}
[data-testid="stSelectbox"] input[role="combobox"] {
  color: #E8EDF3;
  font-family: "Outfit", "Space Grotesk", sans-serif;
}
[data-testid="stSlider"] [data-testid="stSliderThumbValue"] p {
  font-family: "Space Grotesk", "Outfit", sans-serif;
  font-weight: 600;
  color: #B6FF00;
}
[data-testid="stColorPicker"] button {
  background: #0A0E14;
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 8px;
}
[data-testid="stColorPickerBlock"] {
  border-radius: 6px;
}
[data-testid="stCheckbox"] label p {
  font-family: "Outfit", "Space Grotesk", sans-serif;
  color: rgba(232, 237, 243, 0.85);
}

/* ============ UPLOADERS ============ */
[data-testid="stFileUploader"] [data-testid="stWidgetLabel"] p {
  font-family: "Space Grotesk", "Outfit", sans-serif;
  font-weight: 600;
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(232, 237, 243, 0.65);
}
[data-testid="stFileUploaderDropzone"] {
  background: rgba(10, 14, 20, 0.55);
  border: 1.5px dashed rgba(182, 255, 0, 0.35);
  border-radius: 12px;
  transition: border-color 0.25s ease, box-shadow 0.25s ease, background-color 0.25s ease;
}
[data-testid="stFileUploaderDropzone"]:hover {
  border-color: #B6FF00;
  background: rgba(182, 255, 0, 0.04);
  box-shadow: 0 0 20px rgba(182, 255, 0, 0.12);
}
[data-testid="stFileUploaderDropzoneInstructions"] {
  color: rgba(232, 237, 243, 0.6);
}

/* ============ ALERTS ============ */
[data-testid="stAlertContainer"] {
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-left: 3px solid #B6FF00;
}
[data-testid="stAlertContentInfo"] { background: rgba(182, 255, 0, 0.05); }
[data-testid="stAlertContentSuccess"] { background: rgba(182, 255, 0, 0.07); }
[data-testid="stAlertContentWarning"] { background: rgba(242, 255, 0, 0.05); }
[data-testid="stAlertContentError"] { background: rgba(255, 90, 90, 0.06); }
[data-testid="stAlert"] p {
  color: #E8EDF3;
}

/* ============ METRICS ============ */
[data-testid="stMetric"] {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 16px 18px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35);
  animation: gpx-fade-up 0.5s ease-out both;
}
[data-testid="stMetricLabel"] p {
  font-family: "Outfit", "Space Grotesk", sans-serif;
  font-weight: 500;
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(232, 237, 243, 0.55);
}
[data-testid="stMetricValue"] p {
  font-family: "Space Grotesk", "Outfit", sans-serif;
  font-weight: 700;
  font-size: 24px;
  line-height: 1.15;
  color: #B6FF00;
}
[data-testid="stHorizontalBlock"] [data-testid="stColumn"]:nth-child(1) [data-testid="stMetric"] { animation-delay: 0.05s; }
[data-testid="stHorizontalBlock"] [data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"] { animation-delay: 0.15s; }
[data-testid="stHorizontalBlock"] [data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"] { animation-delay: 0.25s; }
[data-testid="stHorizontalBlock"] [data-testid="stColumn"]:nth-child(4) [data-testid="stMetric"] { animation-delay: 0.35s; }
[data-testid="stHorizontalBlock"] [data-testid="stColumn"]:nth-child(5) [data-testid="stMetric"] { animation-delay: 0.45s; }

/* ============ BUTTONS ============ */
[data-testid="stButton"] button {
  font-family: "Space Grotesk", "Outfit", sans-serif;
  font-weight: 600;
  font-size: 15px;
  letter-spacing: 0.02em;
  background: linear-gradient(135deg, #B6FF00 0%, #F2FF00 100%);
  color: #0A0E14;
  border: none;
  border-radius: 12px;
  padding: 0.55rem 1.5rem;
  animation: gpx-pulse 2.4s ease-in-out infinite;
  transition: transform 0.2s ease;
}
[data-testid="stButton"] button:hover {
  transform: translateY(-2px);
  animation: none;
  box-shadow: 0 0 32px rgba(182, 255, 0, 0.55), 0 10px 24px rgba(0, 0, 0, 0.5);
}
[data-testid="stButton"] button:active {
  transform: translateY(0);
}
[data-testid="stButton"] button p {
  color: #0A0E14;
}
[data-testid="stExpander"] [data-testid="stButton"] button {
  background: transparent;
  color: #E8EDF3;
  border: 1px solid rgba(255, 255, 255, 0.16);
  box-shadow: none;
  animation: none;
  padding: 0.45rem 1.2rem;
  font-size: 14px;
}
[data-testid="stExpander"] [data-testid="stButton"] button:hover {
  border-color: #B6FF00;
  color: #B6FF00;
  box-shadow: 0 0 16px rgba(182, 255, 0, 0.18);
}
[data-testid="stExpander"] [data-testid="stButton"] button p {
  color: inherit;
}
[data-testid="stDownloadButton"] button {
  font-family: "Space Grotesk", "Outfit", sans-serif;
  font-weight: 600;
  background: rgba(182, 255, 0, 0.08);
  color: #B6FF00;
  border: 1px solid rgba(182, 255, 0, 0.35);
  border-radius: 10px;
  transition: background 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stDownloadButton"] button:hover {
  background: rgba(182, 255, 0, 0.16);
  box-shadow: 0 0 18px rgba(182, 255, 0, 0.2);
}
[data-testid="stDownloadButton"] button p {
  color: #B6FF00;
}

/* ============ EXPANDER ============ */
[data-testid="stExpander"] {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}
[data-testid="stExpander"] summary {
  font-family: "Space Grotesk", "Outfit", sans-serif;
  font-weight: 600;
  color: #E8EDF3;
}
[data-testid="stExpander"] summary:hover {
  color: #B6FF00;
}
[data-testid="stExpander"] summary p {
  color: inherit;
}

/* ============ MISC ============ */
[data-testid="stProgress"] [role="progressbar"] > div {
  background: linear-gradient(90deg, #B6FF00, #F2FF00);
}
[data-testid="stSpinner"] p {
  color: rgba(232, 237, 243, 0.85);
}
[data-testid="stVideo"] video {
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
}
[data-testid="stImage"] img {
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}
[data-testid="stException"] {
  background: rgba(255, 90, 90, 0.05);
  border: 1px solid rgba(255, 90, 90, 0.25);
  border-radius: 10px;
}

/* ============ MOTION ============ */
@keyframes gpx-pulse {
  0%, 100% {
    box-shadow: 0 0 18px rgba(182, 255, 0, 0.30), 0 6px 18px rgba(0, 0, 0, 0.45);
  }
  50% {
    box-shadow: 0 0 0 12px rgba(182, 255, 0, 0), 0 0 30px rgba(182, 255, 0, 0.45), 0 6px 18px rgba(0, 0, 0, 0.45);
  }
}
@keyframes gpx-fade-up {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (prefers-reduced-motion: reduce) {
  [data-testid="stButton"] button { animation: none; }
  [data-testid="stMetric"] { animation: none; }
}
    </style>

<div class="gpx-glow gpx-glow-tl"></div>
<div class="gpx-glow gpx-glow-tr"></div>
<div class="gpx-grain"></div>

<div class="gpx-hero">
  <img class="gpx-hero-logo" src="data:image/png;base64,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" alt="GPX Animator logo">
      <div>
  <p class="gpx-hero-eyebrow">Map Video</p>
  <h1 class="gpx-hero-title">GPX <span class="gpx-accent">ANIMATOR</span></h1>
  <p class="gpx-hero-tagline">Upload a GPX file and photos to generate an animated video of your track.</p>
</div>
</div>
""",
    unsafe_allow_html=True,
)

# Sidebar Settings
st.sidebar.header("Animation Settings")
fps = st.sidebar.slider("Frames Per Second (FPS)", 5, 60, 24)
speed_options = [1, 2, 5, 10, 20, 50, 100, 200, 500]
speed_multiplier = st.sidebar.select_slider("Speed (× real time)", speed_options, value=10)
line_color = st.sidebar.color_picker("Track Color", "#FF0000")
zoom_level = st.sidebar.slider("Map Zoom Level", 1, 20, 14)
resolutions = {
    "480p (1:1)": (480, 480),
    "720p (1:1)": (720, 720),
    "1080p (1:1)": (1080, 1080),
    "1080p (9:16 Portrait)": (1080, 1920),
}
res_label = st.sidebar.selectbox("Video Resolution", list(resolutions.keys()), index=1)
map_size = resolutions[res_label]
follow_mode = st.sidebar.checkbox("Follow Mode (Center on current point)", value=True)

# Video Output Settings
st.sidebar.header("Video Output")
video_codec = st.sidebar.selectbox("Codec", ["libx264", "libx265", "libvpx"], index=0)
video_quality = st.sidebar.select_slider(
    "Quality", ["Low", "Medium", "High", "Ultra"], value="High"
)
quality_presets = {"Low": 23, "Medium": 18, "High": 14, "Ultra": 8}
crf_value = quality_presets[video_quality]

# Basemap Selection
basemap_options = {
    "OpenStreetMap": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "Satellite (Esri)": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    "Topographic (OpenTopoMap)": "https://tile.opentopomap.org/{z}/{x}/{y}.png",
    "Light (CartoDB)": "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
    "Dark (CartoDB)": "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
}
selected_basemap = st.sidebar.selectbox("Basemap", list(basemap_options.keys()))
map_url = basemap_options[selected_basemap]

# Photo Settings
st.sidebar.header("Photo Settings")
photo_display_duration = st.sidebar.slider("Photo Display Duration (seconds)", 1, 10, 3)

st.sidebar.header("Background Music")
uploaded_audio = st.sidebar.file_uploader(
    "Add music (optional)", type=["mp3", "wav", "ogg", "m4a", "flac"]
)
audio_volume = st.sidebar.slider("Music Volume", 0.0, 1.0, 0.5, 0.1)

uploaded_file = st.file_uploader("Choose a GPX file", type=["gpx"])
uploaded_photos = st.file_uploader(
    "Upload Photos (with EXIF info)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

# Fallback to local file if it exists and no file is uploaded
default_gpx = "bomJesusPerdoes.gpx"
if uploaded_file is None and os.path.exists(default_gpx):
    st.info(f"Using default GPX file: {default_gpx}")
    with open(default_gpx, "rb") as f:
        gpx_data = f.read()
        uploaded_file = io.BytesIO(gpx_data)


def get_exif_data(image):
    """Extract EXIF data from an image."""
    exif_data = {}
    try:
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = ExifTags.TAGS.get(tag, tag)
                exif_data[decoded] = value
    except Exception:
        pass
    return exif_data


def get_decimal_from_dms(dms, ref):
    """Convert DMS (Degrees, Minutes, Seconds) to decimal degrees."""
    try:
        degrees = float(dms[0])
        minutes = float(dms[1])
        seconds = float(dms[2])

        decimal = degrees + minutes / 60.0 + seconds / 3600.0
        if ref in ["S", "W"]:
            decimal = -decimal
        return decimal
    except (TypeError, IndexError, ValueError):
        return None


def get_lat_lon(exif_data):
    """Extract latitude and longitude from EXIF data."""
    lat = None
    lon = None

    if "GPSInfo" in exif_data:
        gps_info = exif_data["GPSInfo"]

        # GPS tags in PIL EXIF (often numeric keys in the sub-dict)
        # 1: LatitudeRef, 2: Latitude, 3: LongitudeRef, 4: Longitude
        gps_lat = gps_info.get(2)
        gps_lat_ref = gps_info.get(1)
        gps_lon = gps_info.get(4)
        gps_lon_ref = gps_info.get(3)

        if gps_lat and gps_lat_ref and gps_lon and gps_lon_ref:
            lat = get_decimal_from_dms(gps_lat, gps_lat_ref)
            lon = get_decimal_from_dms(gps_lon, gps_lon_ref)

    return lat, lon


def get_photo_timestamp(exif_data):
    """Extract timestamp from EXIF data, prioritizing GPS time."""
    # 1. Try GPS Time Stamp (usually UTC)
    if "GPSInfo" in exif_data:
        gps_info = exif_data["GPSInfo"]
        gps_time = gps_info.get(7)  # GPSTimeStamp
        gps_date = gps_info.get(29)  # GPSDateStamp
        if gps_time and gps_date:
            try:
                if isinstance(gps_date, bytes):
                    gps_date = gps_date.decode("utf-8")
                # gps_time is typically a tuple of rationals
                h = float(gps_time[0])
                m = float(gps_time[1])
                s = float(gps_time[2])
                dt_str = f"{gps_date} {int(h):02d}:{int(m):02d}:{int(s):02d}"
                return datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
            except (ValueError, TypeError, IndexError):
                pass

    # 2. Fallback to standard EXIF tags
    timestamp_str = exif_data.get("DateTimeOriginal") or exif_data.get("DateTime")
    if timestamp_str:
        if isinstance(timestamp_str, bytes):
            timestamp_str = timestamp_str.decode("utf-8")
        try:
            return datetime.strptime(timestamp_str, "%Y:%m:%d %H:%M:%S")
        except ValueError:
            pass
    return None


def process_photos(photos, gpx_points):
    processed = []
    if not gpx_points:
        return []

    for uploaded_photo in photos:
        try:
            image_bytes = uploaded_photo.getvalue()
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")
            image_array = np.array(image)
            exif = get_exif_data(image)
            lat, lon = get_lat_lon(exif)
            ts = get_photo_timestamp(exif)

            if ts or (lat is not None and lon is not None):
                processed.append(
                    {
                        "image": image_array,
                        "timestamp": ts,
                        "lat": lat,
                        "lon": lon,
                        "name": uploaded_photo.name,
                    }
                )
        except Exception as e:
            st.sidebar.error(f"Error processing {uploaded_photo.name}: {e}")
    return processed


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers."""
    from math import radians, sin, cos, sqrt, atan2

    R = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def parse_gpx(file):
    if hasattr(file, "getvalue"):
        gpx = gpxpy.parse(file.getvalue().decode("utf-8"))
    else:
        gpx = gpxpy.parse(file)
    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append(
                    {
                        "lon": point.longitude,
                        "lat": point.latitude,
                        "time": point.time,
                        "elevation": point.elevation,
                    }
                )
    return points, gpx


def get_track_stats(points):
    """Calculate track statistics."""
    if not points or len(points) < 2:
        return None

    total_distance = 0.0
    elevation_gain = 0.0
    elevation_loss = 0.0

    for i in range(1, len(points)):
        prev = points[i - 1]
        curr = points[i]
        total_distance += haversine(prev["lat"], prev["lon"], curr["lat"], curr["lon"])

        if prev["elevation"] is not None and curr["elevation"] is not None:
            elev_diff = curr["elevation"] - prev["elevation"]
            if elev_diff > 0:
                elevation_gain += elev_diff
            else:
                elevation_loss += abs(elev_diff)

    times = [p["time"] for p in points if p["time"] is not None]
    duration = None
    if len(times) >= 2:
        duration = (times[-1] - times[0]).total_seconds()

    return {
        "distance_km": total_distance,
        "distance_mi": total_distance * 0.621371,
        "elevation_gain_m": elevation_gain,
        "elevation_loss_m": elevation_loss,
        "duration_sec": duration,
        "num_points": len(points),
    }


def dim_color(hex_color, factor=0.35):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    r = int(r * factor + 255 * (1 - factor))
    g = int(g * factor + 255 * (1 - factor))
    b = int(b * factor + 255 * (1 - factor))
    return f"#{r:02x}{g:02x}{b:02x}"


def render_frame(args):
    """Render a single frame (for batch processing)."""
    (
        i,
        anim_points,
        photos,
        photo_events,
        (map_w, map_h),
        zoom,
        color,
        follow,
        url_template,
        center,
        cum_dist,
        elevations,
    ) = args
    current_pt = anim_points[i]
    current_track = [(p["lon"], p["lat"]) for p in anim_points[: i + 1]]

    frame_map = StaticMap(map_w, map_h, url_template=url_template)

    for photo in photos:
        if photo["lat"] is not None and photo["lon"] is not None:
            coord = (photo["lon"], photo["lat"])
            frame_map.add_marker(CircleMarker(coord, "black", 12))
            frame_map.add_marker(CircleMarker(coord, "yellow", 8))

    if len(current_track) > 1:
        dimmed = dim_color(color, 0.35)
        frame_map.add_line(Line(current_track, dimmed, 2))
        trail_len = max(10, len(anim_points) // 20)
        recent_start = max(0, len(current_track) - trail_len)
        if len(current_track) - recent_start > 1:
            recent_track = current_track[recent_start:]
            frame_map.add_line(Line(recent_track, color, 3))

    frame_map.add_marker(
        CircleMarker((current_pt["lon"], current_pt["lat"]), "white", 10)
    )
    frame_map.add_marker(CircleMarker((current_pt["lon"], current_pt["lat"]), color, 6))

    if follow:
        image = frame_map.render(
            zoom=zoom, center=(current_pt["lon"], current_pt["lat"])
        )
    else:
        image = frame_map.render(zoom=zoom, center=center)

    active_candidates = []
    for event in photo_events:
        if event["start_frame"] <= i <= event["end_frame"]:
            dist = abs(i - event["target_frame"])
            active_candidates.append((dist, event["image"]))

    if active_candidates:
        active_candidates.sort(key=lambda x: x[0])
        _, best_photo_array = active_candidates[0]
        photo_img = Image.fromarray(best_photo_array)
        max_thumb = int(min(map_w, map_h) / 2.2)
        photo_img.thumbnail((max_thumb, max_thumb))
        border = 5
        framed_photo = Image.new(
            "RGB",
            (photo_img.width + 2 * border, photo_img.height + 2 * border),
            "white",
        )
        framed_photo.paste(photo_img, (border, border))
        image.paste(
            framed_photo,
            (map_w - framed_photo.width - 15, map_h - framed_photo.height - 15),
        )

    logo = _get_logo()
    if logo:
        logo_w = min(map_w, map_h) // 12
        logo_h = int(logo.height * (logo_w / logo.width))
        logo_resized = logo.resize((logo_w, logo_h), Image.LANCZOS)
        image.paste(logo_resized, (map_w - logo_w - 10, 10), logo_resized)

    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 12)
    except IOError:
        font = ImageFont.load_default()

    if len(cum_dist) > 1 and any(p["elevation"] is not None for p in anim_points):
        chart_w = min(200, max(100, map_w // 5))
        chart_h = 55
        pad = 5
        cx = 10
        cy = map_h - chart_h - 16
        cy_end = cy + chart_h

        overlay = Image.new("RGBA", (chart_w, chart_h), (0, 0, 0, 140))
        image.paste(overlay, (cx, cy), overlay)

        clean_el = [e if e is not None else 0 for e in elevations]
        total_dist = cum_dist[-1]
        el_min = min(clean_el)
        el_max = max(clean_el)
        el_range = max(el_max - el_min, 1)

        traveled = min(i + 1, len(cum_dist))
        pts = []
        for j in range(traveled):
            x = cx + pad + (cum_dist[j] / total_dist) * (chart_w - 2 * pad)
            y = cy_end - pad - ((clean_el[j] - el_min) / el_range) * (chart_h - 2 * pad)
            pts.append((int(x), int(y)))

        if len(pts) > 1:
            draw.line(pts, fill=color, width=2)
        label = f"{cum_dist[min(traveled, len(cum_dist)) - 1]:.1f}km  {clean_el[min(traveled, len(clean_el)) - 1]:.0f}m"
        draw.text((cx + 4, cy + 4), label, fill="white", font=font)

    return i, np.array(image)


def create_animation(
    points,
    fps,
    speed,
    size,
    zoom,
    color,
    follow,
    url_template,
    photos,
    photo_dur,
    codec,
    crf,
    audio_path=None,
    audio_volume=0.5,
):
    if points[0]["time"] is not None and points[-1]["time"] is not None:
        real_secs = (points[-1]["time"] - points[0]["time"]).total_seconds()
        duration = real_secs / speed
        duration = max(5, min(300, duration))
    else:
        duration = 15

    total_frames = int(fps * duration)
    if len(points) < 2:
        st.error("Not enough points in GPX file.")
        return None

    indices = np.linspace(0, len(points) - 1, total_frames).astype(int)
    anim_points = [points[i] for i in indices]

    cum_dist = [0.0]
    elevations = [anim_points[0]["elevation"] or 0]
    for j in range(1, len(anim_points)):
        d = haversine(
            anim_points[j - 1]["lat"], anim_points[j - 1]["lon"],
            anim_points[j]["lat"], anim_points[j]["lon"],
        )
        cum_dist.append(cum_dist[-1] + d)
        elevations.append(anim_points[j]["elevation"] or 0)

    photo_events = []
    frames_to_show = int(fps * photo_dur)
    half_dur = frames_to_show // 2

    for photo in photos:
        best_frame_idx = -1

        if photo["timestamp"]:
            min_time_diff = float("inf")
            photo_ts = photo["timestamp"].replace(tzinfo=None)
            for i, pt in enumerate(anim_points):
                if pt["time"]:
                    diff = abs(
                        (pt["time"].replace(tzinfo=None) - photo_ts).total_seconds()
                    )
                    if diff < min_time_diff:
                        min_time_diff = diff
                        best_frame_idx = i
            if min_time_diff > 3600:
                best_frame_idx = -1

        if (
            best_frame_idx == -1
            and photo["lat"] is not None
            and photo["lon"] is not None
        ):
            min_dist = float("inf")
            for i, pt in enumerate(anim_points):
                dist = np.sqrt(
                    (photo["lat"] - pt["lat"]) ** 2 + (photo["lon"] - pt["lon"]) ** 2
                )
                if dist < min_dist:
                    min_dist = dist
                    best_frame_idx = i
            if min_dist > 0.005:
                best_frame_idx = -1

        if best_frame_idx != -1:
            photo_events.append(
                {
                    "target_frame": best_frame_idx,
                    "start_frame": max(0, best_frame_idx - half_dur),
                    "end_frame": best_frame_idx + half_dur,
                    "image": photo["image"],
                }
            )

    center = None
    if not follow:
        lons = [p["lon"] for p in points]
        lats = [p["lat"] for p in points]
        center = (np.mean(lons), np.mean(lats))

    batch_size = 50
    num_batches = (len(anim_points) + batch_size - 1) // batch_size
    frame_dir = tempfile.mkdtemp()

    progress_bar = st.progress(0)
    status_text = st.empty()
    start_time = time.time()

    for batch_idx in range(num_batches):
        batch_start = batch_idx * batch_size
        batch_end = min(batch_start + batch_size, len(anim_points))

        args_list = [
            (
                i,
                anim_points,
                photos,
                photo_events,
                size,
                zoom,
                color,
                follow,
                url_template,
                center,
                cum_dist,
                elevations,
            )
            for i in range(batch_start, batch_end)
        ]

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(render_frame, args_list))

        for i, frame_array in results:
            if frame_array is not None:
                path = os.path.join(frame_dir, f"frame_{i:06d}.jpg")
                Image.fromarray(frame_array).save(path, quality=90)

        batch_progress = batch_end / len(anim_points)
        elapsed = time.time() - start_time
        if batch_progress > 0:
            eta = elapsed / batch_progress - elapsed
            status_text.text(
                f"Rendering frame {batch_end}/{len(anim_points)}... ETA: {int(eta)}s"
            )
        progress_bar.progress(min(batch_progress, 1.0))

    progress_bar.progress(1.0)
    status_text.text("Compiling video...")

    try:
        frame_paths = sorted(
            os.path.join(frame_dir, f) for f in os.listdir(frame_dir)
        )
        clip = ImageSequenceClip(frame_paths, fps=fps)
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")

        ffmpeg_params = []
        if codec in ["libx264", "libx265"]:
            ffmpeg_params.extend(["-crf", str(crf)])

        has_audio = False
        if audio_path and os.path.exists(audio_path):
            try:
                audio = AudioFileClip(audio_path)
                if audio_volume != 1.0:
                    audio = audio.with_volume_scaled(audio_volume)
                if audio.duration < clip.duration:
                    n = int(clip.duration / audio.duration) + 1
                    audio = concatenate_audioclips([audio] * n)
                if audio.duration > clip.duration:
                    audio = audio.subclipped(0, clip.duration)
                clip = clip.with_audio(audio)
                has_audio = True
            except Exception as e:
                st.warning(f"Could not load background music: {e}")

        status_text.text("Compiling video with ffmpeg...")
        clip.write_videofile(
            tmp_file.name,
            codec=codec,
            audio=has_audio,
            preset="medium",
            logger=None,
            ffmpeg_params=ffmpeg_params,
        )
        return tmp_file.name
    except Exception as e:
        st.error(f"Error during video generation: {e}")
        return None
    finally:
        shutil.rmtree(frame_dir, ignore_errors=True)


if uploaded_file is not None:
    try:
        file_key = getattr(uploaded_file, "name", default_gpx) + str(
            getattr(uploaded_file, "size", 0)
        )

        if (
            "gpx_cache" not in st.session_state
            or st.session_state.get("gpx_cache_key") != file_key
        ):
            points, gpx_data = parse_gpx(uploaded_file)
            st.session_state["gpx_cache"] = (points, gpx_data)
            st.session_state["gpx_cache_key"] = file_key
        else:
            points, gpx_data = st.session_state["gpx_cache"]

        st.success(f"Parsed {len(points)} GPS points.")

        has_time_data = any(p["time"] is not None for p in points)
        if not has_time_data:
            st.warning(
                "GPX file has no timestamp data. Animation will use uniform timing."
            )

        stats = get_track_stats(points)
        if stats:
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Distance", f"{stats['distance_km']:.2f} km")
            col2.metric("Distance", f"{stats['distance_mi']:.2f} mi")
            col3.metric("Elevation Gain", f"{stats['elevation_gain_m']:.0f} m")
            col4.metric("Elevation Loss", f"{stats['elevation_loss_m']:.0f} m")
            if stats["duration_sec"]:
                mins = int(stats["duration_sec"] // 60)
                secs = int(stats["duration_sec"] % 60)
                col5.metric("Duration", f"{mins}m {secs}s")
            else:
                col5.metric("Duration", "N/A")

        photos = []
        if uploaded_photos:
            with st.spinner("Processing photos..."):
                photos = process_photos(uploaded_photos, points)
                st.success(f"Successfully processed {len(photos)} photos.")

        if stats and stats["duration_sec"]:
            est = stats["duration_sec"] / speed_multiplier
            st.info(f"⏱️ **Estimated video:** {int(est // 60)}m {int(est % 60)}s at {speed_multiplier}× speed")

        with st.expander("🗺️ Map Preview", expanded=False):
            if st.button("Render Preview", key="preview"):
                with st.spinner("Rendering preview..."):
                    lons = [p["lon"] for p in points]
                    lats = [p["lat"] for p in points]
                    pc = (np.mean(lons), np.mean(lats))
                    track_pts = [(p["lon"], p["lat"]) for p in points]
                    pmap = StaticMap(480, 480, url_template=map_url)
                    pmap.add_line(Line(track_pts, line_color, 3))
                    pmap.add_marker(CircleMarker(track_pts[0], "green", 10))
                    pmap.add_marker(CircleMarker(track_pts[-1], "red", 10))
                    img = pmap.render(zoom=zoom_level, center=pc)
                    st.image(np.array(img), caption=f"Start (green) → End (red)  ·  Zoom {zoom_level}")

        if st.button("Generate Video"):
            start_time = time.time()
            audio_tmp_path = None
            if uploaded_audio is not None:
                ext = os.path.splitext(uploaded_audio.name)[1] or ".mp3"
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                tmp.write(uploaded_audio.getvalue())
                tmp.close()
                audio_tmp_path = tmp.name

            with st.spinner("Generating animation..."):
                video_path = create_animation(
                    points,
                    fps,
                    speed_multiplier,
                    map_size,
                    zoom_level,
                    line_color,
                    follow_mode,
                    map_url,
                    photos,
                    photo_display_duration,
                    video_codec,
                    crf_value,
                    audio_tmp_path,
                    audio_volume,
                )

            if audio_tmp_path:
                os.remove(audio_tmp_path)

            if video_path:
                st.video(video_path)
                with open(video_path, "rb") as f:
                    st.download_button(
                        "Download Video", f, "gpx_animation.mp4", "video/mp4"
                    )
                os.remove(video_path)
    except Exception as e:
        st.error(f"Error: {e}")
        st.exception(e)
