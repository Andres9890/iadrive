#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IAdrive - Download Google Drive files/folders and Google Docs and upload to Internet Archive

Usage:
  iadrive <url> [--metadata=<key:value>...] [--disable-slash-files] [--quiet] [--debug]
  iadrive -h | --help
  iadrive --version

Arguments:
  <url>                         Google Drive URL (file or folder) or Google Docs URL

Options:
  -h --help                    Show this screen
  --metadata=<key:value>       Custom metadata to add to the archive.org item
  --disable-slash-files        Upload files without preserving folder structure
  -q --quiet                   Just print errors
  -d --debug                   Print all logs to stdout

Note: Google Docs are automatically exported in all available formats for preservation:
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


def print_supported_formats():
    """Print supported formats for Google Docs"""
    print("\nGoogle Docs formats (ALL are automatically exported):")
    print("  Documents: PDF, DOCX, ODT, RTF, TXT, HTML, EPUB")
    print("  Spreadsheets: XLSX, ODS, PDF, CSV, TSV, HTML") 
    print("  Presentations: PDF, PPTX, ODP, TXT, JPEG, PNG, SVG")
    print("\nFor maximum preservation, IAdrive exports ALL available formats automatically.")


def main():
    args = docopt.docopt(__doc__, version=__version__)
    
    url = args['<url>']
    quiet_mode = args['--quiet']
    debug_mode = args['--debug']
    disable_slash_files = args['--disable-slash-files']
    
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
    
    # Check if this is a Google Docs URL and provide info
    is_docs_url = any(pattern in url for pattern in ['docs.google.com/document', 'docs.google.com/spreadsheets', 'docs.google.com/presentation'])
    
    if is_docs_url and not quiet_mode:
        print("Detected Google Docs URL.")
        print("All available formats will be automatically exported for comprehensive preservation.")
        print_supported_formats()
        print()
    
    iadrive = IAdrive(verbose=not quiet_mode, preserve_folders=not disable_slash_files)
    
    try:
        identifier, meta = iadrive.archive_drive_url(url, metadata)
        print('\n:: Upload Finished. Item information:')
        print('Title: %s' % meta['title'])
        print('Item URL: https://archive.org/details/%s\n' % identifier)
        
        # Show what was uploaded for Google Docs
        if is_docs_url and not quiet_mode:
            doc_type = None
            if 'docs.google.com/document' in url:
                doc_type = 'document'
            elif 'docs.google.com/spreadsheets' in url:
                doc_type = 'spreadsheets'  
            elif 'docs.google.com/presentation' in url:
                doc_type = 'presentation'
                
            if doc_type:
                format_count = len([ext for ext in ['pdf', 'docx', 'odt', 'rtf', 'txt', 'html', 'epub', 'xlsx', 'ods', 'csv', 'tsv', 'pptx', 'odp', 'jpeg', 'png', 'svg']])
                print(f"Google {doc_type.title()} was exported and uploaded in ALL available formats.")
                print("Check the Internet Archive item for complete format preservation.\n")
        
    except Exception as e:
        error_msg = str(e)
        print('\n\033[91m'
              f'An exception occurred: {error_msg}\n')
              
        print('If this isn\'t a connection problem, please report to '
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