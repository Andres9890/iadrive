#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IAdrive - Download Google Drive files/folders, Google Docs, and Mega.nz files and upload to Internet Archive

Usage:
  iadrive <url> [--metadata=<key:value>...] [--disable-slash-files] [--gdrive-token=<token>] [--quiet] [--debug]
  iadrive -h | --help
  iadrive --version

Arguments:
  <url>                         Google Drive URL (file or folder), Google Docs URL, or Mega.nz URL

Options:
  -h --help                    Show this screen
  --metadata=<key:value>       Custom metadata to add to the archive.org item
  --disable-slash-files        Upload files without preserving folder structure
  --gdrive-token=<token>       Google Drive API token for fetching file metadata (owner/modifier)
  -q --quiet                   Just print errors
  -d --debug                   Print all logs to stdout

Supported platforms:
  • Google Drive files and folders
  • Google Docs/Sheets/Slides
  • Mega.nz files and folders

Note: Google Docs are automatically exported in all available formats:
  Documents: PDF, DOCX, ODT, RTF, TXT, HTML, EPUB
  Spreadsheets: XLSX, ODS, PDF, CSV, TSV, HTML
  Presentations: PDF, PPTX, ODP, TXT, JPEG, PNG, SVG
"""

import sys
import docopt
import logging
import traceback

from iadrive.core import IAdrive
from iadrive.utils import key_value_to_dict, get_latest_pypi_version
from iadrive import __version__


def print_supported_platforms():
    """Print supported platforms and formats"""
    print("\nSupported platforms:")
    print("  • Google Drive: files and folders")
    print("  • Google Docs: Documents, Spreadsheets, Presentations")
    print("  • Mega.nz: files and folders")
    print("\nGoogle Docs formats:")
    print("  Documents: PDF, DOCX, ODT, RTF, TXT, HTML, EPUB")
    print("  Spreadsheets: XLSX, ODS, PDF, CSV, TSV, HTML") 
    print("  Presentations: PDF, PPTX, ODP, TXT, JPEG, PNG, SVG")
    print("\nFor maximum preservation, IAdrive exports ALL available formats automatically.")


def detect_platform(url):
    """Detect which platform the URL is from"""
    if 'docs.google.com' in url:
        return 'Google Docs'
    elif 'drive.google.com' in url:
        return 'Google Drive'
    elif 'mega.nz' in url or 'mega.co.nz' in url:
        return 'Mega.nz'
    else:
        return 'Unknown'


def main():
    args = docopt.docopt(__doc__, version=__version__)
    
    url = args['<url>']
    quiet_mode = args['--quiet']
    debug_mode = args['--debug']
    disable_slash_files = args['--disable-slash-files']
    gdrive_token = args['--gdrive-token']
    
    if debug_mode:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '\033[92m[DEBUG]\033[0m %(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        root.addHandler(ch)
    
    metadata = key_value_to_dict(args['--metadata'])
    
    platform = detect_platform(url)
    
    if not quiet_mode:
        print(f"Detected {platform} URL.")
        
        if platform == 'Google Docs':
            print("All available formats will be exported")
            print_supported_platforms()
        elif platform == 'Mega.nz':
            print("Mega.nz support requires mega.py package")
            print("Install with: pip install mega.py")
        elif platform == 'Google Drive':
            print("Google Drive support via gdown")
        elif platform == 'Unknown':
            print("Warning: URL platform not recognized")
            print("Supported platforms: Google Drive, Google Docs, Mega.nz")
        
        print()
    
    iadrive = IAdrive(verbose=not quiet_mode, preserve_folders=not disable_slash_files, google_drive_token=gdrive_token)
    
    try:
        identifier, meta = iadrive.archive_drive_url(url, metadata)
        print('\n:: Upload Finished. Item information:')
        print('Title: %s' % meta['title'])
        print('Item URL: https://archive.org/details/%s\n' % identifier)
        
    except Exception as e:
        error_msg = str(e)
        print('\n\033[91m'
              f'An exception occurred: {error_msg}\n')
        
        if 'mega.py' in error_msg.lower():
            print('Mega.nz support requires the mega.py package')
            print('Install with: pip install mega.py')
        elif 'gdown' in error_msg.lower():
            print('Google Drive support requires the gdown package')
            print('Install with: pip install gdown')
        elif 'internetarchive' in error_msg.lower():
            print('Internet Archive upload requires configuration')
            print('Run: ia configure')
        
        print('\nIf this isn\'t a connection problem, please report to '
              'https://github.com/Andres9890/iadrive/issues')
        
        if debug_mode:
            traceback.print_exc()
        print('\033[0m')
        sys.exit(1)
    finally:
        # Version check after upload attempt (success or fail)
        latest_version = get_latest_pypi_version()
        if latest_version and latest_version != __version__:
            print(f"\033[93mA newer version of IAdrive is available: \033[92m{latest_version}\033[0m")
            print("Update with: pip install --upgrade iadrive\n")


if __name__ == '__main__':
    main()