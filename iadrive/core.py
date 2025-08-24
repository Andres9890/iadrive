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
    def __init__(self, verbose=False, dir_path='~/.iadrive', preserve_folders=True):
        """
        IAdrive - Google Drive to Internet Archive uploader
        
        :param verbose: Print detailed logs
        :param dir_path: Directory to store downloaded files
        :param preserve_folders: Whether to preserve folder structure in uploaded files
        """
        self.verbose = verbose
        self.preserve_folders = preserve_folders
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
    
    def get_file_list_with_structure(self, path):
        """
        Get list of all files with their relative paths preserved
        Returns a dictionary mapping relative paths to absolute paths
        """
        file_map = {}
        
        if os.path.isfile(path):
            # Single file case
            file_map[os.path.basename(path)] = path
        else:
            # Directory case - walk through and preserve structure
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    abs_path = os.path.join(root, filename)
                    # Get relative path from the download directory
                    rel_path = os.path.relpath(abs_path, path)
                    # Use forward slashes for consistency in archive
                    rel_path = rel_path.replace(os.sep, '/')
                    file_map[rel_path] = abs_path
        
        return file_map
    
    def get_file_list(self, path):
        """Get list of all files in the downloaded content (for backward compatibility)"""
        file_map = self.get_file_list_with_structure(path)
        return list(file_map.values())
    
    def create_metadata(self, file_map, drive_id, original_url, custom_meta=None):
        """Create Internet Archive metadata from downloaded files"""
        if not file_map:
            raise Exception("No files found to upload")
        
        files = list(file_map.values())
        
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
        
        # Create file listing for description with folder structure
        description_lines = ["Files included:"]
        for rel_path, abs_path in sorted(file_map.items()):
            file_size = os.path.getsize(abs_path)
            # Format size for readability
            if file_size > 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
            elif file_size > 1024:
                size_str = f"{file_size / 1024:.2f} KB"
            else:
                size_str = f"{file_size} bytes"
            description_lines.append(f"- {rel_path} ({size_str})")
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
            'scanner': f'IAdrive Google Drive File Mirroring Application {__version__}'
        }
        
        if custom_meta:
            metadata.update(custom_meta)
        
        return metadata
    
    def upload_to_ia(self, file_map, drive_id, metadata):
        """Upload files to Internet Archive with optional folder structure preservation"""
        identifier = f"drive-{drive_id}"
        identifier = sanitize_identifier(identifier)
        
        if self.verbose:
            print(f"Uploading to Internet Archive with identifier: {identifier}")
            if self.preserve_folders:
                print("Folder structure will be preserved")
            else:
                print("Files will be uploaded with flat structure (no folders)")
        
        item = internetarchive.get_item(identifier)
        
        # Check if item already exists
        if item.exists:
            if self.verbose:
                print(f"Item {identifier} already exists on archive.org")
            return identifier, metadata
        
        # Prepare files for upload
        upload_files = {}
        
        if self.preserve_folders:
            # Preserve folder structure
            for rel_path, abs_path in file_map.items():
                # Sanitize the relative path for IA (replace problematic characters)
                # But keep the folder structure with forward slashes
                safe_rel_path = rel_path.replace('\\', '/')
                # Remove any leading slash
                safe_rel_path = safe_rel_path.lstrip('/')
                upload_files[safe_rel_path] = abs_path
                
                if self.verbose:
                    print(f"  Preparing: {abs_path} -> {safe_rel_path}")
        else:
            # Flat structure - use only filenames, handle duplicates
            filename_counts = {}
            for rel_path, abs_path in file_map.items():
                filename = os.path.basename(abs_path)
                
                # Handle duplicate filenames by adding a counter
                if filename in filename_counts:
                    filename_counts[filename] += 1
                    name, ext = os.path.splitext(filename)
                    filename = f"{name}_{filename_counts[filename]}{ext}"
                else:
                    filename_counts[filename] = 0
                
                upload_files[filename] = abs_path
                
                if self.verbose:
                    print(f"  Preparing: {abs_path} -> {filename}")
        
        # Upload files
        try:
            # Upload each file with its intended name
            for dest_name, source_path in upload_files.items():
                if self.verbose:
                    print(f"  Uploading: {dest_name}")
                item.upload(source_path, metadata=metadata, 
                           target=dest_name, retries=3, verbose=self.verbose)
            
            if self.verbose:
                print(f"Successfully uploaded {len(upload_files)} files")
        except Exception as e:
            raise Exception(f"Failed to upload to Internet Archive: {e}")
        
        return identifier, metadata
    
    def archive_drive_url(self, url, custom_meta=None):
        """Main method to download from Google Drive and upload to IA"""
        # Check dependencies first
        self.check_dependencies()
        
        # Download content
        download_path, drive_id = self.download_drive_content(url)
        
        # Get file list with structure preserved
        file_map = self.get_file_list_with_structure(download_path)
        if not file_map:
            raise Exception("No files downloaded")
        
        if self.verbose:
            print(f"Found {len(file_map)} files to upload")
            if self.preserve_folders:
                print("File structure:")
                for rel_path in sorted(file_map.keys()):
                    print(f"  - {rel_path}")
            else:
                print("Files will be uploaded with flat structure")
        
        # Create metadata
        metadata = self.create_metadata(file_map, drive_id, url, custom_meta)
        
        # Upload to Internet Archive with or without folder structure
        identifier, final_metadata = self.upload_to_ia(file_map, drive_id, metadata)
        
        # Clean up downloaded files
        import shutil
        shutil.rmtree(download_path)
        if self.verbose:
            print("Cleaned up temporary files")
        
        return identifier, final_metadata