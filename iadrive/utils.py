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
    # IA identifiers must be alphanumeric with hyphens/underscores
    # Remove the lowercase conversion to preserve original case from Drive/Docs IDs
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


def get_collaborators(drive_id, google_drive_token=None):
    """
    Get collaborators for a Google Drive file/folder
    Uses Google Drive API v3 to fetch file owner and last modifier information

    :param drive_id: The Google Drive file/folder ID
    :param google_drive_token: Google Drive API access token (OAuth2)
    :return: Creator information (owner or last modifier name), or None if unavailable
    """
    if not google_drive_token or not drive_id:
        return None

    try:
        import urllib.request
        import json

        # Google Drive API v3 endpoint to get file metadata
        # We request owner and lastModifyingUser information
        api_url = f"https://www.googleapis.com/drive/v3/files/{drive_id}"
        params = "?fields=owners,lastModifyingUser"

        # Create request with authorization header
        request = urllib.request.Request(
            api_url + params,
            headers={'Authorization': f'Bearer {google_drive_token}'}
        )

        # Make the API call
        response = urllib.request.urlopen(request, timeout=10)
        data = json.loads(response.read().decode('utf-8'))

        # Try to get the owner first, then fall back to last modifier
        creator = None

        # Get owner information
        if 'owners' in data and len(data['owners']) > 0:
            owner = data['owners'][0]
            # Prefer displayName, fall back to emailAddress
            creator = owner.get('displayName') or owner.get('emailAddress')

        # If no owner, try last modifying user
        if not creator and 'lastModifyingUser' in data:
            modifier = data['lastModifyingUser']
            creator = modifier.get('displayName') or modifier.get('emailAddress')

        return creator

    except Exception as e:
        # If API call fails, return None to fall back to "IAdrive"
        return None


def get_latest_pypi_version(package_name="iadrive"):
    """
    Request PyPI for the latest version
    Returns the version string, or None if it cannot be determined
    """
    import json
    import urllib.request
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.load(response)
            return data["info"]["version"]
    except Exception:
        return None