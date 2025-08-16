
import argparse
import logging
import os
from . import __version__
from .utils import parse_drive_id_and_type, collect_file_extensions, list_files_recursive
from .drive import download_google_drive, try_get_drive_owners
from .ia_upload import ensure_ia_configured_or_raise, compute_oldest_date_iso, build_metadata, upload_directory

DEFAULT_COLLECTION = os.environ.get("IADRIVE_DEFAULT_COLLECTION", "opensource")
DEFAULT_MEDIATYPE = os.environ.get("IADRIVE_DEFAULT_MEDIATYPE", "data")

def build_identifier(link: str) -> str:
    file_id, _ = parse_drive_id_and_type(link)
    if not file_id:
        safe = link.replace("https://", "").replace("http://", "").replace("/", "-")
        return f"drive-{safe[:80]}"
    return f"drive-{file_id}"

def main():
    parser = argparse.ArgumentParser(description="IAdrive - Mirror Google Drive file/folder to archive.org")
    parser.add_argument("link", help="Google Drive file or folder URL")
    parser.add_argument("--identifier", help="Override Archive.org identifier (default: drive-<drive-id>)")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help=f"Archive.org collection (default: {DEFAULT_COLLECTION})")
    parser.add_argument("--mediatype", default=DEFAULT_MEDIATYPE, help=f"Archive.org mediatype (default: {DEFAULT_MEDIATYPE})")
    parser.add_argument("--dest", default="downloads", help="Destination base directory for downloads")
    parser.add_argument("--dry-run", action="store_true", help="Download and prepare metadata, but do not upload")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(levelname)s: %(message)s")
    log = logging.getLogger("iadrive")

    try:
        ensure_ia_configured_or_raise()
    except Exception as e:
        log.error(str(e))
        raise SystemExit(2)

    dest_base = os.path.abspath(args.dest)
    os.makedirs(dest_base, exist_ok=True)
    try:
        local_root, item_type, title, downloaded_paths = download_google_drive(args.link, dest_base)
    except Exception as e:
        log.error("Download failed: %s", e)
        raise SystemExit(2)

    log.info("Downloaded %d file(s) into %s", len(downloaded_paths), local_root)
    try:
        all_files = list_files_recursive(local_root)
        rels = []
        for f in all_files:
            try:
                rels.append(os.path.relpath(f, start=local_root))
            except Exception:
                rels.append(f)
        description = "Files:\n" + "\n".join(sorted(rels))
        filecount = len(all_files)
    except Exception:
        description = "Files: (listing unavailable)"
        filecount = len(downloaded_paths)

    identifier = args.identifier or build_identifier(args.link)
    log.info("Using identifier: %s", identifier)

    oldest_date_iso, year = compute_oldest_date_iso(local_root)

    owners = try_get_drive_owners(args.link)
    if owners and len(owners) > 1:
        publisher = "{" + ", ".join(owners) + "}"
    elif owners and len(owners) == 1:
        publisher = owners[0]
    else:
        publisher = "IAdrive"

    exts = collect_file_extensions(local_root)
    subjects = ["google", "drive"] + exts

    md = build_metadata(
        title=title,
        oldest_date_iso=oldest_date_iso,
        year=year,
        publisher_value=publisher,
        subjects=subjects,
        original_url=args.link,
        mediatype=args.mediatype,
        collection=args.collection,
        filecount=filecount,
        description=description,
    )

    try:
        upload_directory(identifier, local_root, md, dry_run=args.dry_run)
    except Exception as e:
        log.error("Upload failed: %s", e)
        raise SystemExit(2)

    log.info("Done.")
