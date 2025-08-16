
import os
import time
import configparser
from datetime import datetime
from typing import List, Dict, Tuple
import logging
from .utils import list_files_recursive, collect_file_extensions
from .metadata_extract import find_oldest_embedded_date
from . import SCANNER_NAME

log = logging.getLogger("iadrive")

def ensure_ia_configured_or_raise():
    if os.getenv("IA_ACCESS_KEY") and os.getenv("IA_SECRET_KEY"):
        return
    cfg_path = os.path.expanduser("~/.config/ia.ini")
    if not os.path.exists(cfg_path):
        raise RuntimeError("Internet Archive is not configured. Run: ia configure")
    cp = configparser.ConfigParser()
    cp.read(cfg_path)
    if not (cp.has_section("s3") and cp.has_option("s3", "access") and cp.has_option("s3", "secret")):
        raise RuntimeError("~/.config/ia.ini is missing s3 credentials. Run: ia configure")

def compute_oldest_mtime_iso(root_dir: str) -> Tuple[str, str]:
    oldest = None
    for fp in list_files_recursive(root_dir):
        try:
            m = os.path.getmtime(fp)
            if oldest is None or m < oldest:
                oldest = m
        except FileNotFoundError:
            continue
    if oldest is None:
        dt = datetime.utcnow()
    else:
        dt = datetime.utcfromtimestamp(oldest)
    return dt.strftime("%Y-%m-%d"), str(dt.year)

def build_metadata(title: str, oldest_date_iso: str, year: str, publisher_value: str, subjects: List[str], original_url: str, mediatype: str, collection: str, filecount: int, description: str) -> Dict[str, str]:
    md = {
        "title": title,
        "mediatype": mediatype,
        "collection": collection,
        "scanner": SCANNER_NAME,
        "date": oldest_date_iso,
        "year": year,
        "publisher": publisher_value,
        "subject": subjects,
        "originalurl": original_url,
        "filecount": str(filecount),
        "description": description,
    }
    return md

def upload_directory(identifier: str, root_dir: str, metadata: Dict[str, str], dry_run: bool = False):
    import internetarchive as ia  # type: ignore
    files = list_files_recursive(root_dir)
    if not files:
        raise RuntimeError("No files found to upload in %r" % root_dir)
    log.info("Preparing to upload %d files to item %s", len(files), identifier)
    if dry_run:
        log.info("[DRY RUN] Would upload: %s", files[:10])
        return
    r = ia.upload(identifier, files, metadata=metadata, verbose=True, queue_derive=False, ignore_existing=True)
    ok = True
    for res in r:
        if not res[0].ok:
            ok = False
            log.error("Failed to upload %s: %s", res[1], res[0].text)
    if not ok:
        raise RuntimeError("One or more files failed to upload. See log above.")

def compute_oldest_date_iso(root_dir: str) -> Tuple[str, str]:
    try:
        dt = find_oldest_embedded_date(root_dir)
    except Exception:
        dt = None
    if dt is None:
        return compute_oldest_mtime_iso(root_dir)
    return dt.strftime("%Y-%m-%d"), str(dt.year)
