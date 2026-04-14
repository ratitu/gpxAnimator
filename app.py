import streamlit as st
import gpxpy
import numpy as np
from staticmap import StaticMap, Line, CircleMarker
from moviepy import ImageSequenceClip
from PIL import Image, ExifTags
import tempfile
import os
import time
import io
from datetime import datetime

st.set_page_config(page_title="GPX Animator", layout="wide", page_icon="🗺️")

st.title("🗺️ GPX Map Video Animator")
st.markdown("Upload a GPX file and photos to generate an animated video of your track.")

# Sidebar Settings
st.sidebar.header("Animation Settings")
fps = st.sidebar.slider("Frames Per Second (FPS)", 5, 60, 24)
duration_target = st.sidebar.slider("Target Video Duration (seconds)", 5, 120, 15)
line_color = st.sidebar.color_picker("Track Color", "#FF0000")
zoom_level = st.sidebar.slider("Map Zoom Level", 1, 20, 14)
map_size = st.sidebar.selectbox("Video Resolution", [480, 720, 1080], index=1)
follow_mode = st.sidebar.checkbox("Follow Mode (Center on current point)", value=True)

# Basemap Selection
basemap_options = {
    "OpenStreetMap": "http://a.tile.osm.org/{z}/{x}/{y}.png",
    "Satellite (Esri World Imagery)": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
}
selected_basemap = st.sidebar.selectbox("Basemap", list(basemap_options.keys()))
map_url = basemap_options[selected_basemap]

# Photo Settings
st.sidebar.header("Photo Settings")
photo_display_duration = st.sidebar.slider("Photo Display Duration (seconds)", 1, 10, 3)

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
            exif = get_exif_data(image)
            lat, lon = get_lat_lon(exif)
            ts = get_photo_timestamp(exif)

            if ts or (lat is not None and lon is not None):
                processed.append(
                    {
                        "image": image,
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


def create_animation(
    points, fps, duration, size, zoom, color, follow, url_template, photos, photo_dur
):
    total_frames = fps * duration
    if len(points) < 2:
        st.error("Not enough points in GPX file.")
        return None

    step = max(1, len(points) // total_frames)
    anim_points = points[::step]

    # Calculate display frames for each photo based on TIMESTAMP
    photo_events = []
    frames_to_show = int(fps * photo_dur)
    half_dur = frames_to_show // 2

    for photo in photos:
        best_frame_idx = -1

        if photo["timestamp"]:
            # Match by Time
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
            # Ignore if time difference is too large (e.g. > 1 hour)
            if min_time_diff > 3600:
                best_frame_idx = -1

        if (
            best_frame_idx == -1
            and photo["lat"] is not None
            and photo["lon"] is not None
        ):
            # Fallback to Match by Location
            min_dist = float("inf")
            for i, pt in enumerate(anim_points):
                dist = np.sqrt(
                    (photo["lat"] - pt["lat"]) ** 2 + (photo["lon"] - pt["lon"]) ** 2
                )
                if dist < min_dist:
                    min_dist = dist
                    best_frame_idx = i
            # Ignore if too far
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

    frames = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    if not follow:
        lons = [p["lon"] for p in points]
        lats = [p["lat"] for p in points]
        center = (np.mean(lons), np.mean(lats))

    for i in range(len(anim_points)):
        current_pt = anim_points[i]
        current_track = [(p["lon"], p["lat"]) for p in anim_points[: i + 1]]

        frame_map = StaticMap(size, size, url_template=url_template)

        # Add markers for ALL photos
        for photo in photos:
            if photo["lat"] is not None and photo["lon"] is not None:
                coord = (photo["lon"], photo["lat"])
                photo_marker = CircleMarker(coord, "black", 12)
                photo_marker_inner = CircleMarker(coord, "yellow", 8)
                frame_map.add_marker(photo_marker)
                frame_map.add_marker(photo_marker_inner)

        if len(current_track) > 1:
            line = Line(current_track, color, 3)
            frame_map.add_line(line)

        marker = CircleMarker((current_pt["lon"], current_pt["lat"]), "white", 10)
        marker_inner = CircleMarker((current_pt["lon"], current_pt["lat"]), color, 6)
        frame_map.add_marker(marker)
        frame_map.add_marker(marker_inner)

        if follow:
            image = frame_map.render(
                zoom=zoom, center=(current_pt["lon"], current_pt["lat"])
            )
        else:
            image = frame_map.render(zoom=zoom, center=center)

        # Overlay photo if active
        active_candidates = []
        for event in photo_events:
            if event["start_frame"] <= i <= event["end_frame"]:
                dist = abs(i - event["target_frame"])
                active_candidates.append((dist, event["image"]))

        if active_candidates:
            active_candidates.sort(key=lambda x: x[0])
            _, best_photo_img = active_candidates[0]

            photo_img = best_photo_img.copy()
            photo_img.thumbnail((size // 2.2, size // 2.2))

            border = 5
            framed_photo = Image.new(
                "RGB",
                (photo_img.width + 2 * border, photo_img.height + 2 * border),
                "white",
            )
            framed_photo.paste(photo_img, (border, border))
            image.paste(
                framed_photo,
                (size - framed_photo.width - 15, size - framed_photo.height - 15),
            )

        frames.append(np.array(image))

        if i % max(1, len(anim_points) // 20) == 0:
            progress = i / len(anim_points)
            progress_bar.progress(progress)
            status_text.text(f"Rendering frame {i}/{len(anim_points)}...")

    progress_bar.progress(1.0)
    status_text.text("Compiling video...")

    try:
        clip = ImageSequenceClip(frames, fps=fps)
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        clip.write_videofile(tmp_file.name, codec="libx264", audio=False, logger=None)
        return tmp_file.name
    except Exception as e:
        st.error(f"Error during video generation: {e}")
        return None


if uploaded_file is not None:
    try:
        points, gpx_data = parse_gpx(uploaded_file)
        st.success(f"Parsed {len(points)} GPS points.")

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

        if st.button("Generate Video"):
            start_time = time.time()
            with st.spinner("Generating animation..."):
                video_path = create_animation(
                    points,
                    fps,
                    duration_target,
                    map_size,
                    zoom_level,
                    line_color,
                    follow_mode,
                    map_url,
                    photos,
                    photo_display_duration,
                )

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
