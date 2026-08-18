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
import urllib.request
import threading
import math
from collections import OrderedDict

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

# 3D Terrain
st.sidebar.header("3D Terrain")
use_3d = st.sidebar.checkbox("3D Terrain View", value=False)
if use_3d:
    vert_exag = st.sidebar.slider("Vertical Exaggeration", 1.0, 5.0, 2.0, 0.5)
    cam_angle = st.sidebar.slider("Camera Angle (°)", 10, 60, 30)
    cam_direction = st.sidebar.slider("Camera Direction (°)", 0, 360, 45)
    follow_heading = st.sidebar.checkbox("Follow Track Heading", value=True)
    cam_distance = st.sidebar.slider("Camera Distance", 0.5, 2.5, 1.0, 0.1)
    terrain_detail = st.sidebar.select_slider(
        "Terrain Detail", ["Low", "Medium", "High"], value="Medium"
    )
    hillshading = st.sidebar.checkbox("Hillshading", value=True)
    dem_zoom = 13  # fixed - Copernicus DEM 30m native resolution
    mesh_n = {"Low": 40, "Medium": 56, "High": 72}[terrain_detail]
else:
    vert_exag = 2.0
    cam_angle = 30
    cam_direction = 45
    follow_heading = True
    cam_distance = 1.0
    hillshading = True
    dem_zoom = 13
    mesh_n = 56

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


# ---------------------------------------------------------------------------
# 3D Terrain rendering (Copernicus DEM 30m elevation + draped basemap)
# ---------------------------------------------------------------------------

_COPERNICUS_DEM_BASE = "https://copernicus-dem-30m.s3.amazonaws.com"
_TILE_CACHE = OrderedDict()
_TILE_CACHE_LOCK = threading.Lock()
_TILE_CACHE_MAX = 512
_DEM_GRID_CACHE = OrderedDict()
_DEM_GRID_LOCK = threading.Lock()
_DEM_GRID_CACHE_MAX = 24
_DEM_FETCH_LOCKS = {}


def _fetch_bytes(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "gpxAnimator/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _load_basemap_tile(z, x, y, url_template):
    """Fetch a basemap tile with a global LRU cache (staticmap refetches every
    frame, so we cache tiles ourselves)."""
    key = (z, x, y, url_template)
    with _TILE_CACHE_LOCK:
        tile = _TILE_CACHE.get(key)
        if tile is not None:
            _TILE_CACHE.move_to_end(key)
            return tile
    url = (
        url_template.replace("{z}", str(z))
        .replace("{x}", str(x))
        .replace("{y}", str(y))
    )
    data = None
    for attempt in range(2):
        try:
            data = _fetch_bytes(url)
            break
        except Exception:
            if attempt == 0:
                time.sleep(0.3)
    if data is None:
        raise RuntimeError(f"Failed to fetch basemap tile {url}")
    arr = np.array(Image.open(io.BytesIO(data)).convert("RGB"))
    with _TILE_CACHE_LOCK:
        _TILE_CACHE[key] = arr
        _TILE_CACHE.move_to_end(key)
        while len(_TILE_CACHE) > _TILE_CACHE_MAX:
            _TILE_CACHE.popitem(last=False)
    return arr


def _copernicus_tile_url(lat_band, lon_band):
    """Return the public S3 URL of the Copernicus DEM 30m COG tile for the
    given integer degree band (e.g. lat_band=-24, lon_band=-47)."""
    ns = "N" if lat_band >= 0 else "S"
    ew = "E" if lon_band >= 0 else "W"
    name = (
        f"Copernicus_DSM_COG_10_{ns}{abs(lat_band):02d}_00_{ew}{abs(lon_band):03d}_00_DEM"
    )
    return f"{_COPERNICUS_DEM_BASE}/{name}/{name}.tif"


def _read_copernicus_window(bounds, gw, gh):
    """Read Copernicus DEM 30m for `bounds` (lon_min, lat_min, lon_max,
    lat_max) into an (gh, gw) float32 grid, rows north -> south, by doing
    windowed COG reads of the intersecting 1-degree tiles via rio-tiler."""
    lon0, lat0, lon1, lat1 = bounds
    lat_b0 = int(math.floor(lat0))
    lat_b1 = int(math.floor(lat1 - 1e-9))
    lon_b0 = int(math.floor(lon0))
    lon_b1 = int(math.floor(lon1 - 1e-9))
    px_w = (lon1 - lon0) / gw
    px_h = (lat1 - lat0) / gh
    grid = np.zeros((gh, gw), dtype=np.float32)
    try:
        from rio_tiler.io import COGReader
    except ImportError:
        raise RuntimeError(
            "Copernicus DEM elevation requires rio-tiler: pip install rasterio rio-tiler"
        )
    for lat_band in range(lat_b0, lat_b1 + 1):
        for lon_band in range(lon_b0, lon_b1 + 1):
            i_left = max(lon0, float(lon_band))
            i_right = min(lon1, float(lon_band + 1))
            i_top = min(lat1, float(lat_band + 1))
            i_bottom = max(lat0, float(lat_band))
            if i_right <= i_left or i_top <= i_bottom:
                continue
            cols = max(1, int(round((i_right - i_left) / px_w)))
            rows = max(1, int(round((i_top - i_bottom) / px_h)))
            url = _copernicus_tile_url(lat_band, lon_band)
            with COGReader(url) as cog:
                d = cog.part(
                    (i_left, i_bottom, i_right, i_top),
                    width=cols,
                    height=rows,
                    resampling_method="bilinear",
                )
            arr = d.data[0].astype(np.float32)
            arr[arr < -1000.0] = 0.0
            if d.mask is not None:
                arr[d.mask == 0] = 0.0
            c0 = max(0, min(gw - 1, int(round((i_left - lon0) / px_w))))
            r0 = max(0, min(gh - 1, int(round((lat1 - i_top) / px_h))))
            c1 = min(gw, c0 + cols)
            r1 = min(gh, r0 + rows)
            if r1 > r0 and c1 > c0:
                grid[r0:r1, c0:c1] = arr[: r1 - r0, : c1 - c0]
    return grid


def _lon_to_x(lon, z):
    return ((lon + 180.0) / 360.0) * (2 ** z)


def _lat_to_y(lat, z):
    lat = max(-85.05112878, min(85.05112878, lat))
    lat_rad = math.radians(lat)
    return (
        (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi)
        / 2.0
        * (2 ** z)
    )


def _x_to_lon(x, z):
    return x / (2 ** z) * 360.0 - 180.0


def _y_to_lat(y, z):
    return math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * y / (2 ** z)))))


def _view_bounds(center, zoom, w, h):
    """World bounds (lon_min, lat_min, lon_max, lat_max) of a viewport,
    mirroring staticmap's math."""
    xc = _lon_to_x(center[0], zoom)
    yc = _lat_to_y(center[1], zoom)
    x0 = xc - 0.5 * w / 256.0
    x1 = xc + 0.5 * w / 256.0
    y0 = yc - 0.5 * h / 256.0
    y1 = yc + 0.5 * h / 256.0
    return (_x_to_lon(x0, zoom), _y_to_lat(y1, zoom), _x_to_lon(x1, zoom), _y_to_lat(y0, zoom))


def _texture_zoom_for(bounds, w, h):
    lon_span = max(bounds[2] - bounds[0], 1e-9)
    z = round(math.log2(max(w, h) * 360.0 / (256.0 * lon_span)))
    return max(1, min(19, z))


def _composite_basemap(bounds, z, w, h, url_template):
    """Compose the basemap tiles covering `bounds` into an (h, w, 3) canvas."""
    center = ((bounds[0] + bounds[2]) / 2.0, (bounds[1] + bounds[3]) / 2.0)
    xc = _lon_to_x(center[0], z)
    yc = _lat_to_y(center[1], z)
    x_min = math.floor(xc - 0.5 * w / 256.0)
    x_max = math.ceil(xc + 0.5 * w / 256.0)
    y_min = math.floor(yc - 0.5 * h / 256.0)
    y_max = math.ceil(yc + 0.5 * h / 256.0)
    n_world = 2 ** z
    canvas = np.zeros((h, w, 3), dtype=np.uint8)
    for ty in range(y_min, y_max + 1):
        for tx in range(x_min, x_max + 1):
            try:
                tile = _load_basemap_tile(z, tx % n_world, ty % n_world, url_template)
            except Exception:
                continue
            px0 = int(round((tx - xc) * 256.0 + w / 2.0))
            py0 = int(round((ty - yc) * 256.0 + h / 2.0))
            sx0 = max(0, px0)
            sy0 = max(0, py0)
            sx1 = min(w, px0 + 256)
            sy1 = min(h, py0 + 256)
            if sx1 <= sx0 or sy1 <= sy0:
                continue
            canvas[sy0:sy1, sx0:sx1] = tile[sy0 - py0:sy1 - py0, sx0 - px0:sx1 - px0]
    return canvas


def _elevation_grid(bounds, dem_zoom, n, height=None):
    """Fetch Copernicus DEM 30m covering `bounds` and resample to an
    (height or n, n) float32 grid (rows north -> south).

    `dem_zoom` is accepted for call-site compatibility but ignored:
    Copernicus DEM 30m is a fixed native-resolution dataset. Grids are
    cached keyed by discretized bounds + size, and in-flight fetch locks
    prevent duplicate concurrent reads of the same window."""
    gw = n
    gh = height or n
    key = (
        round(bounds[0], 4),
        round(bounds[1], 4),
        round(bounds[2], 4),
        round(bounds[3], 4),
        gw,
        gh,
    )
    with _DEM_GRID_LOCK:
        cached = _DEM_GRID_CACHE.get(key)
        if cached is not None:
            _DEM_GRID_CACHE.move_to_end(key)
            return cached
        lock = _DEM_FETCH_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _DEM_FETCH_LOCKS[key] = lock
    with lock:
        with _DEM_GRID_LOCK:
            cached = _DEM_GRID_CACHE.get(key)
            if cached is not None:
                _DEM_GRID_CACHE.move_to_end(key)
                return cached
        try:
            grid = _read_copernicus_window(bounds, gw, gh)
        finally:
            with _DEM_GRID_LOCK:
                _DEM_FETCH_LOCKS.pop(key, None)
        with _DEM_GRID_LOCK:
            _DEM_GRID_CACHE[key] = grid
            _DEM_GRID_CACHE.move_to_end(key)
            while len(_DEM_GRID_CACHE) > _DEM_GRID_CACHE_MAX:
                _DEM_GRID_CACHE.popitem(last=False)
    return grid


def _meters_per_deg(lat):
    rad = math.radians(lat)
    m_lat = 111132.92 - 559.82 * math.cos(2 * rad) + 1.175 * math.cos(4 * rad)
    m_lon = 111412.84 * math.cos(rad) - 93.5 * math.cos(3 * rad) + 0.118 * math.cos(5 * rad)
    return m_lat, m_lon


def _build_mesh(bounds, elev, n, exag):
    """Build a terrain mesh: verts (x, y, z meters), triangle indices, uvs,
    per-vertex normals, extent in meters, and world center."""
    lon_min, lat_min, lon_max, lat_max = bounds
    lat_c = (lat_min + lat_max) / 2.0
    m_lat, m_lon = _meters_per_deg(lat_c)
    w_m = (lon_max - lon_min) * m_lon
    h_m = (lat_max - lat_min) * m_lat
    xs = np.linspace(-w_m / 2.0, w_m / 2.0, n)
    ys = np.linspace(-h_m / 2.0, h_m / 2.0, n)
    xs_g, ys_g = np.meshgrid(xs, ys)
    verts = np.stack(
        [xs_g.ravel(), ys_g.ravel(), (elev * exag).ravel()], axis=1
    ).astype(np.float32)
    uu, vv = np.meshgrid(np.linspace(0.0, 1.0, n), np.linspace(0.0, 1.0, n))
    uvs = np.stack([uu.ravel(), vv.ravel()], axis=1).astype(np.float32)
    rows, cols = np.mgrid[0:n - 1, 0:n - 1]
    a = (rows * n + cols).ravel()
    b = a + 1
    c = (rows * n + cols + n).ravel()
    d = c + 1
    tris = np.concatenate(
        [np.stack([a, b, c], axis=1), np.stack([b, d, c], axis=1)]
    ).astype(np.int32)
    dx_m = w_m / (n - 1)
    dy_m = h_m / (n - 1)
    gx = np.gradient(elev, axis=1) / dx_m
    gy = np.gradient(elev, axis=0) / dy_m
    nx = -gx
    ny = gy
    nz = np.ones_like(elev)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    normals = np.stack(
        [(nx / norm).ravel(), (ny / norm).ravel(), (nz / norm).ravel()], axis=1
    ).astype(np.float32)
    return verts, tris, uvs, normals, (w_m, h_m), ((lon_min + lon_max) / 2.0, lat_c)


def _auto_fit_distance(extent_m, elev_deg, fov_deg=45.0, fill=0.85):
    s = max(extent_m)
    d = s * math.sin(math.radians(elev_deg)) / (
        2.0 * math.tan(math.radians(fov_deg) / 2.0) * fill
    )
    return max(d, 1.0)


def _heading_azimuth(p0, p1, m_lat, m_lon):
    dx = (p1["lon"] - p0["lon"]) * m_lon
    dy = (p1["lat"] - p0["lat"]) * m_lat
    return math.degrees(math.atan2(dx, dy)) % 360.0


def _camera_basis(cam_pos, target):
    forward = target - cam_pos
    norm_f = np.linalg.norm(forward)
    if norm_f < 1e-9:
        forward = np.array([0.0, 0.0, 1.0])
    else:
        forward = forward / norm_f
    right = np.cross(forward, np.array([0.0, 0.0, 1.0]))
    norm_r = np.linalg.norm(right)
    if norm_r < 1e-9:
        right = np.array([1.0, 0.0, 0.0])
    else:
        right = right / norm_r
    up = np.cross(right, forward)
    return right, up, forward


def _project_points(pts_xyz, cam_pos, right, up, forward, f, cx, cy):
    pts_xyz = np.asarray(pts_xyz, dtype=np.float32)
    d = pts_xyz - cam_pos
    x_cam = d @ right
    y_cam = d @ up
    z_cam = d @ forward
    with np.errstate(divide="ignore", invalid="ignore"):
        sx = cx + x_cam / z_cam * f
        sy = cy - y_cam / z_cam * f
    return sx, sy, z_cam


def _rasterize(w, h, verts, tris, uvs, normals, texture, cam_pos, target, hillshade):
    """Perspective rasterizer: drape `texture` over the mesh with per-vertex
    hillshading, z-buffering and distance fog. zbuf keeps the minimum z_cam
    (closest to camera), so later draws must be closer to paint."""
    right, up, forward = _camera_basis(cam_pos, target)
    f = (h / 2.0) / math.tan(math.radians(45.0) / 2.0)
    cx = w / 2.0
    cy = h / 2.0

    t = np.linspace(0.0, 1.0, h)[:, None]
    sky_top = np.array([120.0, 170.0, 220.0])
    sky_horizon = np.array([235.0, 242.0, 250.0])
    img = (
        sky_top[None, None, :] * (1.0 - t[:, :, None])
        + sky_horizon[None, None, :] * t[:, :, None]
    )
    img = np.broadcast_to(img, (h, w, 3)).copy()
    zbuf = np.full((h, w), np.inf, dtype=np.float32)

    dist = float(np.linalg.norm(cam_pos - target))
    light_dir = (cam_pos - target) / max(dist, 1e-9)
    if hillshade:
        shade = np.clip(normals @ light_dir, 0.0, 1.0)
    else:
        shade = np.ones(len(verts), dtype=np.float32)
    tex = texture.astype(np.float32)
    th, tw = tex.shape[0], tex.shape[1]
    fog_near = 0.35 * dist
    fog_far = 1.3 * dist
    fog_color = np.array([232.0, 240.0, 249.0])
    near = 0.1

    sx, sy, zc = _project_points(verts, cam_pos, right, up, forward, f, cx, cy)

    for idx in range(len(tris)):
        i0, i1, i2 = tris[idx]
        z0, z1, z2 = zc[i0], zc[i1], zc[i2]
        if z0 < near or z1 < near or z2 < near:
            continue
        s0, t0 = sx[i0], sy[i0]
        s1, t1 = sx[i1], sy[i1]
        s2, t2 = sx[i2], sy[i2]
        bx0 = max(0, int(math.floor(min(s0, s1, s2))))
        bx1 = min(w - 1, int(math.ceil(max(s0, s1, s2))))
        by0 = max(0, int(math.floor(min(t0, t1, t2))))
        by1 = min(h - 1, int(math.ceil(max(t0, t1, t2))))
        if bx1 < bx0 or by1 < by0:
            continue
        X = np.arange(bx0, bx1 + 1, dtype=np.float32) + 0.5 - s0
        Y = np.arange(by0, by1 + 1, dtype=np.float32) + 0.5 - t0
        area = (s1 - s0) * (t2 - t0) - (t1 - t0) * (s2 - s0)
        if abs(area) < 1e-9:
            continue
        inv_area = 1.0 / area
        w1 = (X[None, :] * (t2 - t0) - Y[:, None] * (s2 - s0)) * inv_area
        w2 = ((s1 - s0) * Y[:, None] - (t1 - t0) * X[None, :]) * inv_area
        w0 = 1.0 - w1 - w2
        mask = (w0 >= 0.0) & (w1 >= 0.0) & (w2 >= 0.0)
        if not mask.any():
            continue
        iz0, iz1, iz2 = 1.0 / z0, 1.0 / z1, 1.0 / z2
        iz = w0 * iz0 + w1 * iz1 + w2 * iz2
        z = 1.0 / iz
        zc_mask = np.where(mask, z, np.inf)
        visible = mask & (zc_mask < zbuf[by0:by1 + 1, bx0:bx1 + 1])
        if not visible.any():
            continue
        u = (w0 * uvs[i0, 0] * iz0 + w1 * uvs[i1, 0] * iz1 + w2 * uvs[i2, 0] * iz2) / iz
        v = (w0 * uvs[i0, 1] * iz0 + w1 * uvs[i1, 1] * iz1 + w2 * uvs[i2, 1] * iz2) / iz
        u = np.clip(u, 0.0, 0.9999999)
        v = np.clip(v, 0.0, 0.9999999)
        fu = u * (tw - 1)
        fv = v * (th - 1)
        u0i = np.floor(fu).astype(np.int32)
        v0i = np.floor(fv).astype(np.int32)
        u1i = np.minimum(u0i + 1, tw - 1)
        v1i = np.minimum(v0i + 1, th - 1)
        wu = (fu - u0i)[..., None]
        wv = (fv - v0i)[..., None]
        c = (
            tex[v0i, u0i] * (1.0 - wu) * (1.0 - wv)
            + tex[v0i, u1i] * wu * (1.0 - wv)
            + tex[v1i, u0i] * (1.0 - wu) * wv
            + tex[v1i, u1i] * wu * wv
        )
        sh = np.clip(
            w0 * shade[i0] + w1 * shade[i1] + w2 * shade[i2], 0.0, 1.0
        )[..., None]
        lit = c * (0.55 + 0.45 * sh)
        fog = np.clip((z - fog_near) / (fog_far - fog_near), 0.0, 1.0)[..., None]
        out = np.clip(lit * (1.0 - fog) + fog_color * fog, 0.0, 255.0)
        region = img[by0:by1 + 1, bx0:bx1 + 1]
        zregion = zbuf[by0:by1 + 1, bx0:bx1 + 1]
        region[visible] = out[visible].astype(np.uint8)
        zregion[visible] = z[visible]

    return np.clip(img, 0.0, 255.0).round().astype(np.uint8), zbuf, (
        right,
        up,
        forward,
        f,
        cx,
        cy,
    )


def _paint_disc(img, zbuf, sx, sy, z_cam, radius, color):
    """Draw a depth-tested filled disc (screen-space)."""
    h, w = img.shape[:2]
    x0 = max(0, int(sx - radius))
    x1 = min(w - 1, int(sx + radius + 1))
    y0 = max(0, int(sy - radius))
    y1 = min(h - 1, int(sy + radius + 1))
    if x1 < x0 or y1 < y0:
        return
    yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
    mask = (xx - sx) ** 2 + (yy - sy) ** 2 <= radius * radius
    region = img[y0:y1 + 1, x0:x1 + 1]
    zregion = zbuf[y0:y1 + 1, x0:x1 + 1]
    visible = mask & (z_cam < zregion)
    if not visible.any():
        return
    region[visible] = color
    zregion[visible] = z_cam


def _draw_world_polyline(
    img, zbuf, pts_world_list, cam_pos, right, up, forward, f, cx, cy,
    width, color_rgb, extent_m,
):
    """Draw a 3D track polyline: world-space sampling with exact depth
    testing against the terrain z-buffer."""
    h, w = img.shape[:2]
    near = 0.1
    pts = np.asarray(pts_world_list, dtype=np.float32)
    if len(pts) < 2:
        return
    sx, sy, zc = _project_points(pts, cam_pos, right, up, forward, f, cx, cy)
    extent = max(extent_m)
    radius = width / 2.0
    for k in range(len(pts) - 1):
        if zc[k] < near or zc[k + 1] < near:
            continue
        if (
            (sx[k] < -radius and sx[k + 1] < -radius)
            or (sx[k] > w + radius and sx[k + 1] > w + radius)
            or (sy[k] < -radius and sy[k + 1] < -radius)
            or (sy[k] > h + radius and sy[k + 1] > h + radius)
        ):
            continue
        p0 = pts[k]
        p1 = pts[k + 1]
        seg = p1 - p0
        seg_len = float(np.linalg.norm(seg))
        if seg_len < 1e-9:
            continue
        sub_step = max(seg_len / 32.0, max(8.0, extent * 0.02))
        n_sub = max(1, int(math.ceil(seg_len / sub_step)))
        ts = np.linspace(0.0, 1.0, n_sub + 1)
        sub_pts = p0[None, :] + seg[None, :] * ts[:, None]
        ssx, ssy, szc = _project_points(sub_pts, cam_pos, right, up, forward, f, cx, cy)
        for j in range(len(sub_pts)):
            if szc[j] < near:
                continue
            if (
                ssx[j] < -radius or ssx[j] > w + radius
                or ssy[j] < -radius or ssy[j] > h + radius
            ):
                continue
            _paint_disc(img, zbuf, float(ssx[j]), float(ssy[j]), float(szc[j]), radius, color_rgb)


def _hex_to_rgb(hex_color):
    return (
        int(hex_color[1:3], 16),
        int(hex_color[3:5], 16),
        int(hex_color[5:7], 16),
    )


def _render_3d_scene(
    i, anim_points, size, color, follow, url_template, track_bounds,
    cam_az, cam_el, cam_dist_mult, exag, mesh_n, hillshade, dem_zoom, follow_heading,
):
    """Render one 3D terrain frame as a numpy image."""
    map_w, map_h = size
    current_pt = anim_points[i]
    lon_min, lat_min, lon_max, lat_max = track_bounds
    lon_c = (lon_min + lon_max) / 2.0
    lat_c = (lat_min + lat_max) / 2.0
    lon_span = max(lon_max - lon_min, 1e-9)
    lat_span = max(lat_max - lat_min, 1e-9)
    m_lat, m_lon = _meters_per_deg(lat_c)

    if follow:
        # The camera follows the current track point, but the terrain
        # window stays fixed to the whole track: the mesh, basemap and
        # elevation grid are then identical every frame (deterministic
        # cache hits, no swimming terrain). Only the camera moves.
        center = (current_pt["lon"], current_pt["lat"])
        bounds = track_bounds
    else:
        center = (lon_c, lat_c)
        bounds = (
            center[0] - lon_span / 2.0,
            center[1] - lat_span / 2.0,
            center[0] + lon_span / 2.0,
            center[1] + lat_span / 2.0,
        )

    tex_z = _texture_zoom_for(bounds, map_w, map_h)
    texture = _composite_basemap(bounds, tex_z, map_w, map_h, url_template)
    elev = _elevation_grid(bounds, dem_zoom, mesh_n)
    verts, tris, uvs, normals, extent_m, (wc_lon, wc_lat) = _build_mesh(
        bounds, elev, mesh_n, exag
    )

    def world_xy(lon, lat):
        return ((lon - wc_lon) * m_lon, (lat - wc_lat) * m_lat)

    def elev_at(lon, lat):
        fx = (lon - bounds[0]) / (bounds[2] - bounds[0]) * (mesh_n - 1)
        fy = (bounds[3] - lat) / (bounds[3] - bounds[1]) * (mesh_n - 1)
        fx = max(0.0, min(mesh_n - 1.0, fx))
        fy = max(0.0, min(mesh_n - 1.0, fy))
        x0i = int(fx)
        y0i = int(fy)
        x1i = min(x0i + 1, mesh_n - 1)
        y1i = min(y0i + 1, mesh_n - 1)
        wx = fx - x0i
        wy = fy - y0i
        return (
            elev[y0i, x0i] * (1 - wx) * (1 - wy)
            + elev[y0i, x1i] * wx * (1 - wy)
            + elev[y1i, x0i] * (1 - wx) * wy
            + elev[y1i, x1i] * wx * wy
        )

    tx, ty = world_xy(center[0], center[1])
    target = np.array([tx, ty, elev_at(center[0], center[1]) * exag], dtype=np.float32)

    if follow and follow_heading:
        idx2 = min(i + 5, len(anim_points) - 1)
        az = _heading_azimuth(anim_points[i], anim_points[idx2], m_lat, m_lon)
    else:
        az = cam_az
    dist = _auto_fit_distance(extent_m, cam_el) * cam_dist_mult
    az_r = math.radians(az)
    el_r = math.radians(cam_el)
    cam_pos = target + dist * np.array(
        [
            math.sin(az_r) * math.cos(el_r),
            math.cos(az_r) * math.cos(el_r),
            math.sin(el_r),
        ],
        dtype=np.float32,
    )

    img, zbuf, (right, up, forward, f, cx, cy) = _rasterize(
        map_w, map_h, verts, tris, uvs, normals, texture, cam_pos, target, hillshade
    )

    lift = max(0.2, 0.004 * max(extent_m)) * exag
    base_rgb = _hex_to_rgb(color)
    dim_rgb = _hex_to_rgb(dim_color(color, 0.35))
    pad_lon = 0.35 * lon_span
    pad_lat = 0.35 * lat_span
    bb = (bounds[0] - pad_lon, bounds[1] - pad_lat, bounds[2] + pad_lon, bounds[3] + pad_lat)

    def point_world(pt):
        px, py = world_xy(pt["lon"], pt["lat"])
        return np.array(
            [px, py, elev_at(pt["lon"], pt["lat"]) * exag + lift], dtype=np.float32
        )

    traveled = [
        point_world(p)
        for p in anim_points[: i + 1]
        if bb[0] <= p["lon"] <= bb[2] and bb[1] <= p["lat"] <= bb[3]
    ]
    if len(traveled) > 1:
        _draw_world_polyline(
            img, zbuf, traveled, cam_pos, right, up, forward, f, cx, cy,
            2, dim_rgb, extent_m,
        )
        recent = traveled[-max(10, len(anim_points) // 20):]
        if len(recent) > 1:
            _draw_world_polyline(
                img, zbuf, recent, cam_pos, right, up, forward, f, cx, cy,
                3, base_rgb, extent_m,
            )

    if bb[0] <= anim_points[0]["lon"] <= bb[2] and bb[1] <= anim_points[0]["lat"] <= bb[3]:
        p0 = point_world(anim_points[0])
        s0x, s0y, z0c = _project_points(p0[None, :], cam_pos, right, up, forward, f, cx, cy)
        _paint_disc(img, zbuf, float(s0x[0]), float(s0y[0]), float(z0c[0]), 5, (0, 180, 0))
    if bb[0] <= anim_points[-1]["lon"] <= bb[2] and bb[1] <= anim_points[-1]["lat"] <= bb[3]:
        pn = point_world(anim_points[-1])
        snx, sny, znc = _project_points(pn[None, :], cam_pos, right, up, forward, f, cx, cy)
        _paint_disc(img, zbuf, float(snx[0]), float(sny[0]), float(znc[0]), 5, (220, 40, 40))
    pc = point_world(current_pt)
    scx, scy, zcc = _project_points(pc[None, :], cam_pos, right, up, forward, f, cx, cy)
    _paint_disc(img, zbuf, float(scx[0]), float(scy[0]), float(zcc[0]), 6, (255, 255, 255))
    _paint_disc(img, zbuf, float(scx[0]), float(scy[0]), float(zcc[0]), 3.5, base_rgb)

    return img


def render_frame_3d(args):
    """Render a single 3D terrain frame. Returns (i, image, error)."""
    (
        i,
        anim_points,
        photos,
        photo_events,
        (map_w, map_h),
        color,
        follow,
        url_template,
        track_bounds,
        cam_az,
        cam_el,
        cam_dist_mult,
        exag,
        mesh_n,
        hillshade,
        dem_zoom,
        cum_dist,
        elevations,
        follow_heading,
    ) = args
    try:
        if max(map_w, map_h) >= 720:
            rw = int(map_w * 0.5)
            rh = int(map_h * 0.5)
        else:
            rw, rh = map_w, map_h
        img = _render_3d_scene(
            i, anim_points, (rw, rh), color, follow, url_template, track_bounds,
            cam_az, cam_el, cam_dist_mult, exag, mesh_n, hillshade, dem_zoom,
            follow_heading,
        )
        if (rw, rh) != (map_w, map_h):
            img = np.asarray(
                Image.fromarray(img).resize((map_w, map_h), Image.BILINEAR)
            )
        image = Image.fromarray(img)
        _paste_photo_overlay(image, i, photo_events)
        _paste_logo(image)
        _draw_elevation_chart(image, i, anim_points, cum_dist, elevations, color)
        return i, np.array(image), None
    except Exception as e:
        return i, None, f"3D frame {i} failed: {e}"


def create_animation_3d(
    points,
    fps,
    speed,
    size,
    color,
    follow,
    url_template,
    photos,
    photo_dur,
    codec,
    crf,
    audio_path=None,
    audio_volume=0.5,
    cam_az=45,
    cam_el=30,
    cam_dist_mult=1.0,
    exag=2.0,
    mesh_n=56,
    hillshade=True,
    dem_zoom=13,
    follow_heading=True,
):
    duration = _video_duration(points, speed)

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

    photo_events = _build_photo_events(photos, anim_points, fps, photo_dur)

    lons = [p["lon"] for p in points]
    lats = [p["lat"] for p in points]
    lon_span = max(lons) - min(lons)
    lat_span = max(lats) - min(lats)
    if lon_span < 1e-9:
        lon_span = 0.0005
    if lat_span < 1e-9:
        lat_span = 0.0005
    track_bounds = (
        min(lons) - 0.08 * lon_span,
        min(lats) - 0.08 * lat_span,
        max(lons) + 0.08 * lon_span,
        max(lats) + 0.08 * lat_span,
    )

    batch_size = 50
    num_batches = (len(anim_points) + batch_size - 1) // batch_size
    frame_dir = tempfile.mkdtemp()

    progress_bar = st.progress(0)
    status_text = st.empty()
    start_time = time.time()

    # Preflight: render frame 0 synchronously so failures surface early instead
    # of failing all 50 frames in the first batch.
    preflight_args = (
        0, anim_points, photos, photo_events, size, color, follow, url_template,
        track_bounds, cam_az, cam_el, cam_dist_mult, exag, mesh_n, hillshade,
        dem_zoom, cum_dist, elevations, follow_heading,
    )
    _, preflight_frame, preflight_err = render_frame_3d(preflight_args)
    if preflight_err:
        st.error(
            "Could not render 3D terrain frames. Copernicus DEM elevation "
            "data may be unavailable (check your internet connection) or the "
            "region is out of range. Try disabling 3D Terrain View or using "
            f"a different track. ({preflight_err})"
        )
        shutil.rmtree(frame_dir, ignore_errors=True)
        return None

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
                color,
                follow,
                url_template,
                track_bounds,
                cam_az,
                cam_el,
                cam_dist_mult,
                exag,
                mesh_n,
                hillshade,
                dem_zoom,
                cum_dist,
                elevations,
                follow_heading,
            )
            for i in range(batch_start, batch_end)
        ]

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(render_frame_3d, args_list))

        for i, frame_array, frame_err in results:
            if frame_array is not None:
                path = os.path.join(frame_dir, f"frame_{i:06d}.jpg")
                Image.fromarray(frame_array).save(path, quality=90)
            elif frame_err:
                st.error(
                    "3D terrain rendering failed mid-animation. Copernicus DEM "
                    "elevation data may be unavailable. Try disabling 3D "
                    f"Terrain View or using a different track. ({frame_err})"
                )
                shutil.rmtree(frame_dir, ignore_errors=True)
                return None

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


def _hillshade(elev, az_deg=315.0, alt_deg=45.0):
    """Compute an 8-bit hillshade from an elevation grid (light from NW)."""
    gx, gy = np.gradient(elev)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gy, gx)
    az_rad = math.radians(az_deg)
    alt_rad = math.radians(alt_deg)
    shaded = (
        np.cos(alt_rad) * np.cos(slope)
        + np.sin(alt_rad) * np.sin(slope) * np.cos(az_rad - aspect)
    )
    return (255.0 * np.clip(shaded, 0.0, 1.0)).astype(np.uint8)


def download_srtm(points, dem_zoom):
    """Download Copernicus DEM elevation for the track area and return stats
    plus hillshade preview and downloadable bytes."""
    lons = [p["lon"] for p in points]
    lats = [p["lat"] for p in points]
    lon_span = max(lons) - min(lons)
    lat_span = max(lats) - min(lats)
    if lon_span < 1e-9:
        lon_span = 0.0005
    if lat_span < 1e-9:
        lat_span = 0.0005
    pad_lon = 0.05 * lon_span
    pad_lat = 0.05 * lat_span
    bounds = (
        min(lons) - pad_lon,
        min(lats) - pad_lat,
        max(lons) + pad_lon,
        max(lats) + pad_lat,
    )
    aspect = max(0.25, min(2.0, lat_span / max(lon_span, 1e-9)))
    n_w = 256
    n_h = max(128, min(512, int(round(256 * aspect))))
    elev = _read_copernicus_window(bounds, n_w, n_h)
    stats = {
        "min": float(np.min(elev)),
        "max": float(np.max(elev)),
        "range": float(np.max(elev) - np.min(elev)),
        "mean": float(np.mean(elev)),
    }
    shade_img = Image.fromarray(_hillshade(elev), mode="L")
    png_buf = io.BytesIO()
    shade_img.save(png_buf, format="PNG")
    npy_buf = io.BytesIO()
    np.save(npy_buf, elev)
    png_buf.seek(0)
    npy_buf.seek(0)
    return {
        "bounds": bounds,
        "elev": elev,
        "stats": stats,
        "hillshade_pil": shade_img,
        "png_bytes": png_buf,
        "npy_bytes": npy_buf,
    }


def _video_duration(points, speed):
    """Compute the animation duration in seconds from GPX timestamps and speed."""
    if points[0]["time"] is not None and points[-1]["time"] is not None:
        real_secs = (points[-1]["time"] - points[0]["time"]).total_seconds()
        duration = real_secs / speed
        duration = max(5, min(300, duration))
    else:
        duration = 15
    return duration


def _build_photo_events(photos, anim_points, fps, photo_dur):
    """Match photos to animation frames by timestamp (or coordinates) and build
    display events: {target_frame, start_frame, end_frame, image}."""
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

    return photo_events


def _paste_photo_overlay(image, i, photo_events):
    """Paste the closest active photo as a bordered thumbnail in the bottom-right."""
    active_candidates = []
    for event in photo_events:
        if event["start_frame"] <= i <= event["end_frame"]:
            dist = abs(i - event["target_frame"])
            active_candidates.append((dist, event["image"]))

    if not active_candidates:
        return

    active_candidates.sort(key=lambda x: x[0])
    _, best_photo_array = active_candidates[0]
    photo_img = Image.fromarray(best_photo_array)
    max_thumb = int(min(image.width, image.height) / 2.2)
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
        (image.width - framed_photo.width - 15, image.height - framed_photo.height - 15),
    )


def _paste_logo(image):
    """Paste the app logo in the top-right corner."""
    logo = _get_logo()
    if not logo:
        return
    logo_w = min(image.width, image.height) // 12
    logo_h = int(logo.height * (logo_w / logo.width))
    logo_resized = logo.resize((logo_w, logo_h), Image.LANCZOS)
    image.paste(logo_resized, (image.width - logo_w - 10, 10), logo_resized)


def _draw_elevation_chart(image, i, anim_points, cum_dist, elevations, color):
    """Draw the traveled-distance/elevation chart overlay in the bottom-left."""
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 12)
    except IOError:
        font = ImageFont.load_default()

    if len(cum_dist) > 1 and any(p["elevation"] is not None for p in anim_points):
        chart_w = min(200, max(100, image.width // 5))
        chart_h = 55
        pad = 5
        cx = 10
        cy = image.height - chart_h - 16
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


def render_frame(args):
    """Render a single 2D frame (for batch processing)."""
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

    _paste_photo_overlay(image, i, photo_events)
    _paste_logo(image)
    _draw_elevation_chart(image, i, anim_points, cum_dist, elevations, color)

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
    duration = _video_duration(points, speed)

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

    photo_events = _build_photo_events(photos, anim_points, fps, photo_dur)

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

            if st.button("Render 3D Preview", key="preview3d"):
                with st.spinner("Rendering 3D terrain preview..."):
                    try:
                        lons3d = [p["lon"] for p in points]
                        lats3d = [p["lat"] for p in points]
                        lon_span3d = (max(lons3d) - min(lons3d)) or 0.0005
                        lat_span3d = (max(lats3d) - min(lats3d)) or 0.0005
                        tb3d = (
                            min(lons3d) - 0.08 * lon_span3d,
                            min(lats3d) - 0.08 * lat_span3d,
                            max(lons3d) + 0.08 * lon_span3d,
                            max(lats3d) + 0.08 * lat_span3d,
                        )
                        img3d = _render_3d_scene(
                            i=len(points) // 2,
                            anim_points=points,
                            size=(480, 480),
                            color=line_color,
                            follow=False,
                            url_template=map_url,
                            track_bounds=tb3d,
                            cam_az=cam_direction,
                            cam_el=cam_angle,
                            cam_dist_mult=cam_distance,
                            exag=vert_exag,
                            mesh_n=mesh_n,
                            hillshade=hillshading,
                            dem_zoom=dem_zoom,
                            follow_heading=False,
                        )
                        st.image(img3d, caption="3D Terrain Preview")
                    except Exception:
                        st.error(
                            "Could not load Copernicus DEM elevation data. Check internet connection or disable 3D Terrain View."
                        )

            if st.button("⬇️ Download DEM Data", key="srtm"):
                with st.spinner("Downloading Copernicus DEM elevation data..."):
                    try:
                        srtm_result = download_srtm(points, dem_zoom)
                        srtm_stats = srtm_result["stats"]
                        st.image(
                            srtm_result["hillshade_pil"],
                            caption=(
                                f"Elevation: min {srtm_stats['min']:.0f} m · "
                                f"max {srtm_stats['max']:.0f} m · "
                                f"range {srtm_stats['range']:.0f} m"
                            ),
                        )
                        st.download_button(
                            "Download Hillshade PNG",
                            srtm_result["png_bytes"],
                            "srtm_hillshade.png",
                            "image/png",
                        )
                        st.download_button(
                            "Download Raw Elevation (.npy)",
                            srtm_result["npy_bytes"],
                            "srtm_elevation.npy",
                            "application/octet-stream",
                        )
                    except Exception:
                        st.error(
                            "Failed to download elevation data. Check your internet connection."
                        )

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
                if use_3d:
                    video_path = create_animation_3d(
                        points,
                        fps,
                        speed_multiplier,
                        map_size,
                        line_color,
                        follow_mode,
                        map_url,
                        photos,
                        photo_display_duration,
                        video_codec,
                        crf_value,
                        audio_tmp_path,
                        audio_volume,
                        cam_direction,
                        cam_angle,
                        cam_distance,
                        vert_exag,
                        mesh_n,
                        hillshading,
                        dem_zoom,
                        follow_heading,
                    )
                else:
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
