import os
import re
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict


def key_value_to_dict(lst):
    """Convert key:value pair strings into a dictionary"""
    if not lst:
        return {}
    
    if not isinstance(lst, list):
        lst = [lst]
    
    result = defaultdict(list)
    for item in lst:
        if ':' not in item:
            continue
        key, value = item.split(':', 1)
        if value and value not in result[key]:
            result[key].append(value)
        elif not result[key]:
            result[key] = [value]
    
    return {k: v if len(v) > 1 else v[0] for k, v in result.items()}


def sanitize_identifier(identifier, replacement='-'):
    """Sanitize identifier for Internet Archive"""
    # IA identifiers must be lowercase alphanumeric with hyphens/underscores
    identifier = identifier.lower()
    identifier = re.sub(r'[^\w-]', replacement, identifier)
    # Remove consecutive hyphens
    identifier = re.sub(r'-+', '-', identifier)
    # Remove leading/trailing hyphens
    identifier = identifier.strip('-')
    return identifier


def get_oldest_file_date(files):
    """Get the oldest file modification date"""
    oldest_timestamp = float('inf')
    
    for file_path in files:
        if os.path.exists(file_path):
            mtime = os.path.getmtime(file_path)
            if mtime < oldest_timestamp:
                oldest_timestamp = mtime
    
    if oldest_timestamp == float('inf'):
        # Fallback to current date
        oldest_timestamp = time.time()
    
    dt = datetime.fromtimestamp(oldest_timestamp)
    return dt.strftime('%Y-%m-%d'), dt.strftime('%Y')


def extract_file_types(files):
    """Extract unique file extensions from file list"""
    extensions = set()
    for file_path in files:
        ext = Path(file_path).suffix.lower().lstrip('.')
        if ext:
            extensions.add(ext)
    return sorted(list(extensions))


def get_collaborators(drive_id):
    """
    Get collaborators for a Google Drive file/folder
    Note: This would require Google Drive API access in a real implementation
    For now, returns None to fall back to "IAdrive"
    """
    # TODO: Implement Google Drive API integration to get collaborators
    # This would require OAuth2 setup and drive API calls
    return None