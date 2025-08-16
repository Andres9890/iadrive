
import os
import re
import pathlib
from typing import Tuple, Optional

def sanitize_name(name: str) -> str:
    name = name.strip().replace(os.sep, "_")
    return re.sub(r'[<>:"\\|?*\x00-\x1F]', "_", name)[:200]

def parse_drive_id_and_type(url: str) -> Tuple[Optional[str], Optional[str]]:
    ID_PATTERNS = [
        (re.compile(r"https?://drive\.google\.com/drive/folders/([a-zA-Z0-9_\-]+)"), "folder"),
        (re.compile(r"https?://drive\.google\.com/folderview\?id=([a-zA-Z0-9_\-]+)"), "folder"),
        (re.compile(r"https?://drive\.google\.com/file/d/([a-zA-Z0-9_\-]+)"), "file"),
        (re.compile(r"https?://drive\.google\.com/open\?id=([a-zA-Z0-9_\-]+)"), "file"),
        (re.compile(r"https?://drive\.google\.com/uc\?id=([a-zA-Z0-9_\-]+)"), "file"),
    ]
    for pat, typ in ID_PATTERNS:
        m = pat.search(url)
        if m:
            return m.group(1), typ
    m = re.search(r"[?&]id=([a-zA-Z0-9_\-]+)", url)
    if m:
        return m.group(1), "file"
    return None, None

def collect_file_extensions(root: str) -> list:
    exts = set()
    for p in pathlib.Path(root).rglob("*"):
        if p.is_file():
            ext = p.suffix.lower().lstrip(".")
            if ext:
                exts.add(ext)
    return sorted(exts)

def list_files_recursive(root: str) -> list:
    paths = []
    for p in pathlib.Path(root).rglob("*"):
        if p.is_file():
            paths.append(str(p))
    return paths
