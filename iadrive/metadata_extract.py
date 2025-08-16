
import os
import subprocess
from datetime import datetime, timezone
from typing import List, Optional
from pathlib import Path

try:
    from PIL import Image, ExifTags  # type: ignore
except Exception:
    Image = None
    ExifTags = None

try:
    from mutagen import File as MutagenFile  # type: ignore
except Exception:
    MutagenFile = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    from pymediainfo import MediaInfo  # type: ignore
except Exception:
    MediaInfo = None

try:
    from dateutil import parser as dateparser  # type: ignore
except Exception:
    dateparser = None

def _parse_date_any(s: str) -> Optional[datetime]:
    if not s:
        return None
    if s.startswith("D:"):
        s = s[2:]
    try:
        if dateparser:
            dt = dateparser.parse(s, fuzzy=True)
            if not dt:
                return None
            if dt.tzinfo:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
    except Exception:
        pass
    try:
        parts = s.replace("-", ":").split()
        if len(parts) == 2 and parts[0].count(":") == 2 and parts[1].count(":") == 2:
            y, m, d = parts[0].split(":")
            hh, mm, ss = parts[1].split(":")
            return datetime(int(y), int(m), int(d), int(hh), int(mm), int(float(ss)))
    except Exception:
        return None
    return None

def _first_valid(dates: List[datetime]) -> Optional[datetime]:
    return min(dates) if dates else None

def _image_dates(path: Path) -> List[datetime]:
    out = []
    if Image is None:
        return out
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            if not exif:
                return out
            tag_map = {ExifTags.TAGS.get(k, str(k)): v for k, v in exif.items()}
            for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
                if key in tag_map:
                    dt = _parse_date_any(str(tag_map[key]))
                    if dt:
                        out.append(dt)
    except Exception:
        pass
    return out

def _pdf_dates(path: Path) -> List[datetime]:
    out = []
    if PdfReader is None:
        return out
    try:
        rdr = PdfReader(str(path))
        info = rdr.metadata or {}
        for key in ("/CreationDate", "/ModDate"):
            if key in info:
                dt = _parse_date_any(str(info[key]))
                if dt:
                    out.append(dt)
    except Exception:
        pass
    return out

def _mutagen_dates(path: Path) -> List[datetime]:
    out = []
    if MutagenFile is None:
        return out
    try:
        mf = MutagenFile(str(path))
        if not mf:
            return out
        for key in (" 9day", "creation_time", "date"):
            if key in mf.tags:
                val = mf.tags.get(key)
                if isinstance(val, (list, tuple)):
                    val = val[0]
                dt = _parse_date_any(str(val))
                if dt:
                    out.append(dt)
        for key in ("TDRC", "TDOR", "TYER"):
            if key in getattr(mf, "tags", {}):
                frame = mf.tags.get(key)
                try:
                    dt = _parse_date_any(str(frame.text[0]))
                    if dt:
                        out.append(dt)
                except Exception:
                    pass
    except Exception:
        pass
    return out

def _mediainfo_dates(path: Path) -> List[datetime]:
    out = []
    if MediaInfo is None:
        return out
    try:
        mi = MediaInfo.parse(str(path))
        for track in mi.tracks:
            for key in ("encoded_date", "tagged_date", "mastered_date", "file_created_date", "file_modified_date"):
                val = getattr(track, key, None)
                if val:
                    dt = _parse_date_any(str(val))
                    if dt:
                        out.append(dt)
    except Exception:
        pass
    return out

def _ffprobe_dates(path: Path) -> List[datetime]:
    out = []
    try:
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format_tags=creation_time:stream_tags=creation_time",
             "-of", "default=nk=1:nw=1", str(path)],
            capture_output=True, text=True, check=False
        )
        if p.returncode == 0:
            for line in (p.stdout or "").splitlines():
                dt = _parse_date_any(line.strip())
                if dt:
                    out.append(dt)
    except Exception:
        pass
    return out

IMAGE_EXTS = {".jpg", ".jpeg", ".tif", ".tiff", ".heic", ".png"}
PDF_EXTS = {".pdf"}
AUDIO_VIDEO_HINT = {".mp3", ".flac", ".m4a", ".mp4", ".mkv", ".mov", ".avi", ".wav", ".aac", ".ogg", ".opus"}

def extract_dates_from_file(path: str) -> List[datetime]:
    p = Path(path)
    ext = p.suffix.lower()
    dates: List[datetime] = []
    try:
        if ext in IMAGE_EXTS:
            dates += _image_dates(p)
        if ext in PDF_EXTS:
            dates += _pdf_dates(p)
        if ext in AUDIO_VIDEO_HINT:
            dates += _mutagen_dates(p)
            if not dates:
                dates += _mediainfo_dates(p)
            if not dates:
                dates += _ffprobe_dates(p)
    except Exception:
        pass
    return dates

def find_oldest_embedded_date(root_dir: str) -> Optional[datetime]:
    oldest: Optional[datetime] = None
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            for dt in extract_dates_from_file(fp):
                if oldest is None or dt < oldest:
                    oldest = dt
    return oldest
