import os
import re
import glob
import time
import logging
import subprocess
import internetarchive
import urllib.request
import urllib.error
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
        
        # Google Docs export formats
        self.docs_formats = {
            'document': {
                'pdf': 'PDF',
                'docx': 'Microsoft Word',
                'odt': 'OpenDocument Text',
                'rtf': 'Rich Text Format',
                'txt': 'Plain Text',
                'html': 'HTML',
                'epub': 'EPUB'
            },
            'spreadsheets': {
                'xlsx': 'Microsoft Excel',
                'ods': 'OpenDocument Spreadsheet',
                'pdf': 'PDF',
                'csv': 'CSV (first sheet)',
                'tsv': 'TSV (first sheet)',
                'html': 'HTML'
            },
            'presentation': {
                'pdf': 'PDF',
                'pptx': 'Microsoft PowerPoint',
                'odp': 'OpenDocument Presentation',
                'txt': 'Plain Text',
                'jpeg': 'JPEG (slides as images)',
                'png': 'PNG (slides as images)',
                'svg': 'SVG (slides as images)'
            }
        }
        
    
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
    
    def is_google_docs_url(self, url):
        """Check if URL is a Google Docs/Sheets/Slides URL"""
        docs_patterns = [
            r'docs\.google\.com/document',
            r'docs\.google\.com/spreadsheets',
            r'docs\.google\.com/presentation'
        ]
        return any(re.search(pattern, url) for pattern in docs_patterns)
    
    def get_google_docs_type(self, url):
        """Determine the type of Google Docs URL"""
        if 'docs.google.com/document' in url:
            return 'document'
        elif 'docs.google.com/spreadsheets' in url:
            return 'spreadsheets'
        elif 'docs.google.com/presentation' in url:
            return 'presentation'
        else:
            return None
    
    def extract_docs_id(self, url):
        """Extract Google Docs ID from URL"""
        patterns = [
            r'/document/d/([a-zA-Z0-9-_]+)',
            r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
            r'/presentation/d/([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Could not extract Google Docs ID from URL: {url}")
    
    def extract_drive_id(self, url):
        """Extract Google Drive file/folder ID from URL"""
        if self.is_google_docs_url(url):
            return self.extract_docs_id(url)
        
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
    
    def download_google_doc(self, url, doc_id, doc_type, formats=None):
        """Download Google Doc in all available formats for preservation"""
        all_formats = list(self.docs_formats.get(doc_type, {}).keys())
        
        if not all_formats:
            raise Exception(f"No formats available for document type: {doc_type}")
        
        download_path = os.path.join(self.dir_path, f"docs-{doc_id}")
        os.makedirs(download_path, exist_ok=True)
        
        if self.verbose:
            print(f"Downloading Google {doc_type.title()} from: {url}")
            print(f"Exporting ALL {len(all_formats)} available formats: {', '.join(all_formats)}")
            print(f"Download path: {download_path}")
        
        downloaded_files = []
        
        # Get document title from the original URL (try to fetch HTML and extract title)
        doc_title = self.get_google_docs_title(url, doc_id)
        
        for fmt in all_formats:
            # All formats in docs_formats are valid by definition
            try:
                export_url = f"https://docs.google.com/{doc_type}/d/{doc_id}/export?format={fmt}"
                
                # Create filename
                safe_title = re.sub(r'[^\w\s-]', '', doc_title)[:50]
                filename = f"{safe_title}.{fmt}" if safe_title else f"{doc_type}_{doc_id}.{fmt}"
                file_path = os.path.join(download_path, filename)
                
                if self.verbose:
                    print(f"  Downloading {fmt.upper()}: {filename}")
                
                # Download the file
                urllib.request.urlretrieve(export_url, file_path)
                
                # Check if file was downloaded successfully and has content
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    downloaded_files.append(file_path)
                    if self.verbose:
                        size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        print(f"    Downloaded successfully ({size_mb:.2f} MB)")
                else:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    if self.verbose:
                        print(f"    Failed to download or empty file")
                        
            except Exception as e:
                if self.verbose:
                    print(f"  Error downloading {fmt}: {e}")
                continue
        
        if not downloaded_files:
            raise Exception(f"Failed to download Google {doc_type} in any format")
        
        return download_path, doc_id, downloaded_files
    
    def get_google_docs_title(self, url, doc_id):
        """Try to get title of Google Doc"""
        try:
            # Try to fetch the document page and extract title
            response = urllib.request.urlopen(url, timeout=10)
            html = response.read().decode('utf-8', errors='ignore')
            
            # Look for title in HTML
            title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
            if title_match:
                title = title_match.group(1)
                # Remove " - Google Docs/Sheets/Slides" suffix
                title = re.sub(r' - Google (Docs|Sheets|Slides).*$', '', title)
                return title.strip()
        except:
            pass
        
        # Fallback to document ID
        return f"document_{doc_id}"
    
    def download_drive_content(self, url, formats=None):
        """Download Google Drive file/folder or Google Docs using gdown or direct export"""
        if self.is_google_docs_url(url):
            doc_id = self.extract_docs_id(url)
            doc_type = self.get_google_docs_type(url)
            return self.download_google_doc(url, doc_id, doc_type)  # No formats parameter needed
        else:
            # Handle regular Google Drive files/folders
            import gdown
            
            drive_id = self.extract_drive_id(url)
            download_path = os.path.join(self.dir_path, f"drive-{drive_id}")
            
            if self.verbose:
                print(f"Downloading from: {url}")
                print(f"Download path: {download_path}")
            
            try:
                if self.is_folder_url(url):
                    gdown.download_folder(url, output=download_path, quiet=not self.verbose)
                else:
                    os.makedirs(download_path, exist_ok=True)
                    gdown.download(url, output=download_path, quiet=not self.verbose, fuzzy=True)
                
                return download_path, drive_id, None
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
    
    def create_metadata(self, file_map, drive_id, original_url, custom_meta=None, is_google_docs=False, doc_type=None):
        """Create Internet Archive metadata from downloaded files"""
        if not file_map:
            raise Exception("No files found to upload")
        
        files = list(file_map.values())
        
        # Get oldest file date
        oldest_date, oldest_year = get_oldest_file_date(files)
        
        # Determine title
        if is_google_docs:
            # For Google Docs, we try to get a title from the first file
            first_file = list(file_map.keys())[0]
            title = os.path.splitext(first_file)[0]  # Remove extension
            if title.startswith(f"{doc_type}_"):
                title = title.replace(f"{doc_type}_", "").replace(drive_id, "Document")
        elif len(files) == 1 and os.path.isfile(files[0]):
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
        description_lines = []
        if is_google_docs:
            description_lines.append(f"Google {doc_type.title()} exported in:")
        else:
            description_lines.append("Files included:")
            
        for rel_path, abs_path in sorted(file_map.items()):
            file_size = os.path.getsize(abs_path)
            # Format size for readability
            if file_size > 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
            elif file_size > 1024:
                size_str = f"{file_size / 1024:.2f} KB"
            else:
                size_str = f"{file_size} bytes"
            
            if is_google_docs:
                # For Google Docs, show format information
                ext = os.path.splitext(rel_path)[1].lstrip('.')
                format_desc = self.docs_formats.get(doc_type, {}).get(ext, ext.upper())
                description_lines.append(f"- {rel_path} ({format_desc}, {size_str})")
            else:
                description_lines.append(f"- {rel_path} ({size_str})")
                
        description = "<br>".join(description_lines)
        
        # Create subject tags
        if is_google_docs:
            subject_tags = ["google", doc_type, "document"] + file_types
        else:
            subject_tags = ["google", "drive"] + file_types
        subject = ";".join(subject_tags) + ";"
        
        # Truncate subject if too long (IA limit is 255 bytes)
        while len(subject.encode('utf-8')) > 255:
            subject_tags.pop()
            subject = ";".join(subject_tags) + ";"
        
        # Add foldercount metadata (if any folders are present)
        folder_paths = set()
        for rel_path in file_map.keys():
            folder = os.path.dirname(rel_path)
            if folder and folder != '.':
                folder_paths.add(folder)
                
        # Set collection and mediatype based on content type
        if is_google_docs:
            collection = 'opensource_media'
            mediatype = 'texts' if doc_type in ['document'] else 'data'
        else:
            collection = 'opensource_media'
            mediatype = 'data'
                
        metadata = {
            'mediatype': mediatype,
            'collection': collection,
            'title': title,
            'description': description,
            'date': oldest_date,
            'year': oldest_year,
            'creator': creator,
            'subject': subject,
            'filecount': str(len(files)),
            'originalurl': original_url,
            'scanner': f'IAdrive Google Drive File Mirroring Application {__version__}',
            **({'foldercount': str(len(folder_paths))} if folder_paths else {}),
            **({'doctype': doc_type} if is_google_docs else {})
        }
        
        if custom_meta:
            metadata.update(custom_meta)
        
        return metadata
    
    def upload_to_ia(self, file_map, drive_id, metadata, is_google_docs=False):
        """Upload files to Internet Archive with optional folder structure preservation"""
        if is_google_docs:
            identifier = f"docs-{drive_id}"
        else:
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
            if self.verbose:
                print(f"  Uploading {len(upload_files)} files...")
            
            response = item.upload(upload_files, metadata=metadata, 
                                 retries=3, verbose=self.verbose)
            
            if self.verbose:
                print(f"Successfully uploaded {len(upload_files)} files")
        except Exception as e:
            raise Exception(f"Failed to upload to Internet Archive: {e}")
        
        return identifier, metadata
    
    def archive_drive_url(self, url, custom_meta=None, formats=None):
        """Main method to download from Google Drive/Docs and upload to IA"""
        # Check dependencies first
        self.check_dependencies()
        
        is_google_docs = self.is_google_docs_url(url)
        doc_type = self.get_google_docs_type(url) if is_google_docs else None
        
        # For Google Docs, we always export all formats
        if is_google_docs:
            download_path, drive_id, downloaded_files = self.download_drive_content(url)
        else:
            download_path, drive_id, _ = self.download_drive_content(url)
        
        # Get file list with structure preserved
        file_map = self.get_file_list_with_structure(download_path)
        if not file_map:
            raise Exception("No files downloaded")
        
        if self.verbose:
            print(f"Found {len(file_map)} files to upload")
            if is_google_docs:
                print(f"Google {doc_type.title()} exported in ALL available formats:")
                for rel_path in sorted(file_map.keys()):
                    ext = os.path.splitext(rel_path)[1].lstrip('.')
                    format_desc = self.docs_formats.get(doc_type, {}).get(ext, ext.upper())
                    print(f"  - {rel_path} ({format_desc})")
            else:
                if self.preserve_folders:
                    print("File structure:")
                    for rel_path in sorted(file_map.keys()):
                        print(f"  - {rel_path}")
                else:
                    print("Files will be uploaded with flat structure")
        
        # Create metadata
        metadata = self.create_metadata(file_map, drive_id, url, custom_meta, is_google_docs, doc_type)
        
        # Upload to Internet Archive with or without folder structure
        identifier, final_metadata = self.upload_to_ia(file_map, drive_id, metadata, is_google_docs)
        
        # Clean up downloaded files
        import shutil
        shutil.rmtree(download_path)
        if self.verbose:
            print("Cleaned up temporary files")
        
        return identifier, final_metadata