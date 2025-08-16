
import os
import pathlib
from typing import Tuple, List, Optional
from .utils import sanitize_name, parse_drive_id_and_type

def _ensure_imports():
    missing = []
    try:
        import gdown
    except Exception:
        missing.append("gdown")
    return missing

def ensure_requirements_or_raise():
    missing = _ensure_imports()
    if missing:
        raise RuntimeError(
            "Missing required packages: {pkgs}. Install with:\n  pip install -r requirements.txt"
            .format(pkgs=", ".join(missing))
        )

def download_google_drive(url: str, dest_base: str) -> Tuple[str, str, str, List[str]]:
    ensure_requirements_or_raise()
    import gdown

    drive_id, typ = parse_drive_id_and_type(url)
    if not drive_id or not typ:
        typ = "file"

    os.makedirs(dest_base, exist_ok=True)

    if typ == "folder":
        downloaded = gdown.download_folder(url, quiet=False, use_cookies=False, remaining_ok=True, output=dest_base)
        subdirs = [p for p in pathlib.Path(dest_base).iterdir() if p.is_dir()]
        if not subdirs:
            raise RuntimeError("Folder download failed or produced no directory.")
        anchor_dir = pathlib.Path(dest_base)
        if downloaded:
            parent_dirs = [pathlib.Path(p).parent for p in downloaded]
            parent_dirs = [p for p in parent_dirs if str(p).startswith(str(anchor_dir))]
            if parent_dirs:
                top = min(parent_dirs, key=lambda p: len(str(p)))
            else:
                top = subdirs[0]
        else:
            top = subdirs[0]
        title = top.name
        local_root = str(top)
        dl_files = []
        for p in pathlib.Path(local_root).rglob("*"):
            if p.is_file():
                dl_files.append(str(p))
        return local_root, "folder", title, dl_files
    else:
        path = gdown.download(url, output=dest_base, quiet=False, fuzzy=True)
        if not path:
            raise RuntimeError("File download failed.")
        path = str(path)
        filename = pathlib.Path(path).name
        title = filename
        stem = pathlib.Path(filename).stem
        wrapper = os.path.join(dest_base, sanitize_name(stem))
        os.makedirs(wrapper, exist_ok=True)
        new_path = os.path.join(wrapper, filename)
        if os.path.abspath(path) != os.path.abspath(new_path):
            os.replace(path, new_path)
        return wrapper, "file", title, [new_path]

def try_get_drive_owners(url: str) -> Optional[list]:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        from googleapiclient.discovery import build
    except Exception:
        return None

    file_id, typ = parse_drive_id_and_type(url)
    if not file_id:
        return None
    try:
        service = build("drive", "v3", developerKey=api_key, cache_discovery=False)
        fields = "id, name, owners(displayName)"
        req = service.files().get(fileId=file_id, fields=fields, supportsAllDrives=True)
        resp = req.execute()
        owners = [o.get("displayName") for o in (resp.get("owners") or []) if o.get("displayName")]
        if owners:
            return owners
    except Exception:
        return None
    return None
