import os
import re
import glob
import time
import logging
import subprocess
import internetarchive
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from iadrive.utils import sanitize_identifier, get_oldest_file_date, extract_file_types, get_collaborators
from iadrive import __version__


class IAdrive:
    def __init__(self, verbose=False, dir_path='~/.iadrive'):
        """
        IAdrive - Google Drive to Internet Archive uploader
        
        :param verbose: Print detailed logs
        :param dir_path: Directory to store downloaded files
        """
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        self.dir_path = os.path.expanduser(dir_path)
        
        # Create download directory
        os.makedirs(self.dir_path, exist_ok=True)
        
        if not verbose:
            self.logger.setLevel(logging.ERROR)
    
    def check_dependencies(self):
        """Check if required dependencies are installed and configured"""
        try:
            import gdown
            import internetarchive
        except ImportError as e:
            raise Exception(f"Missing required package: {e}. Run 'pip install -r requirements.txt'")
        
        # Check if internetarchive is configured
        try:
            ia_config = internetarchive.get_session().config
            if not ia_config.get('s3', {}).get('access'):
                raise Exception("Internet Archive not configured. Run 'ia configure' first.")
        except Exception as e:
            raise Exception(f"Internet Archive configuration error: {e}")
    
    def extract_drive_id(self, url):
        """Extract Google Drive file/folder ID from URL"""
        patterns = [
            r'/folders/([a-zA-Z0-9-_]+)',
            r'/file/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Could not extract Google Drive ID from URL: {url}")
    
    def is_folder_url(self, url):
        """Check if URL is a Google Drive folder"""
        return '/folders/' in url
    
    def download_drive_content(self, url):
        """Download Google Drive file or folder using gdown"""
        import gdown
        
        drive_id = self.extract_drive_id(url)
        download_path = os.path.join(self.dir_path, f"drive-{drive_id}")
        
        if self.verbose:
            print(f"Downloading from: {url}")
            print(f"Download path: {download_path}")
        
        try:
            if self.is_folder_url(url):
                # Download folder
                gdown.download_folder(url, output=download_path, quiet=not self.verbose)
            else:
                # Download single file
                os.makedirs(download_path, exist_ok=True)
                gdown.download(url, output=download_path, quiet=not self.verbose, fuzzy=True)
            
            return download_path, drive_id
        except Exception as e:
            raise Exception(f"Failed to download from Google Drive: {e}")
    
    def get_file_list(self, path):
        """Get list of all files in the downloaded content"""
        files = []
        if os.path.isfile(path):
            files.append(path)
        else:
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
        return files
    
    def create_metadata(self, files, drive_id, original_url, custom_meta=None):
        """Create Internet Archive metadata from downloaded files"""
        if not files:
            raise Exception("No files found to upload")
        
        # Get oldest file date
        oldest_date, oldest_year = get_oldest_file_date(files)
        
        # Determine title
        if len(files) == 1 and os.path.isfile(files[0]):
            # Single file
            title = os.path.basename(files[0])
        else:
            # Folder or multiple files
            # Try to get folder name from the first file's path
            common_path = os.path.commonpath(files) if len(files) > 1 else os.path.dirname(files[0])
            title = os.path.basename(common_path) or f"drive-{drive_id}"
        
        # Extract file types
        file_types = extract_file_types(files)
        
        # Get collaborators (this would need Google Drive API access in a real implementation)
        creator = get_collaborators(drive_id) or "IAdrive"
        
        # Create file listing for description
        description_lines = ["Files included in this archive:"]
        for file_path in files:
            rel_path = os.path.relpath(file_path, os.path.dirname(files[0]))
            file_size = os.path.getsize(file_path)
            description_lines.append(f"- {rel_path} ({file_size} bytes)")
        description = "<br>".join(description_lines)
        
        # Create subject tags
        subject_tags = ["google", "drive"] + file_types
        subject = ";".join(subject_tags) + ";"
        
        # Truncate subject if too long (IA limit is 255 bytes)
        while len(subject.encode('utf-8')) > 255:
            subject_tags.pop()
            subject = ";".join(subject_tags) + ";"
        
        metadata = {
            'mediatype': 'data',
            'collection': 'opensource',
            'title': title,
            'description': description,
            'date': oldest_date,
            'year': oldest_year,
            'creator': creator,
            'subject': subject,
            'filecount': str(len(files)),
            'originalurl': original_url,
            'scanner': f'IAdrive Google Drive File Mirroring Application v{__version__}'
        }
        
        if custom_meta:
            metadata.update(custom_meta)
        
        return metadata
    
    def upload_to_ia(self, files, drive_id, metadata):
        """Upload files to Internet Archive"""
        identifier = f"drive-{drive_id}"
        identifier = sanitize_identifier(identifier)
        
        if self.verbose:
            print(f"Uploading to Internet Archive with identifier: {identifier}")
        
        item = internetarchive.get_item(identifier)
        
        # Check if item already exists
        if item.exists:
            if self.verbose:
                print(f"Item {identifier} already exists on archive.org")
            return identifier, metadata
        
        # Upload files
        try:
            item.upload(files, metadata=metadata, retries=3, verbose=self.verbose)
            if self.verbose:
                print(f"Successfully uploaded {len(files)} files")
        except Exception as e:
            raise Exception(f"Failed to upload to Internet Archive: {e}")
        
        return identifier, metadata
    
    def archive_drive_url(self, url, custom_meta=None):
        """Main method to download from Google Drive and upload to IA"""
        # Check dependencies first
        self.check_dependencies()
        
        # Download content
        download_path, drive_id = self.download_drive_content(url)
        
        # Get file list
        files = self.get_file_list(download_path)
        if not files:
            raise Exception("No files downloaded")
        
        if self.verbose:
            print(f"Found {len(files)} files to upload")
        
        # Create metadata
        metadata = self.create_metadata(files, drive_id, url, custom_meta)
        
        # Upload to Internet Archive
        identifier, final_metadata = self.upload_to_ia(files, drive_id, metadata)
        
        # Clean up downloaded files
        import shutil
        shutil.rmtree(download_path)
        if self.verbose:
            print("Cleaned up temporary files")
        
        return identifier, final_metadata