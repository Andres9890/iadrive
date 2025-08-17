#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IAdrive - Download Google Drive files/folders and upload to Internet Archive

Usage:
  iadrive <url> [--metadata=<key:value>...] [--quiet] [--debug]
  iadrive -h | --help
  iadrive --version

Arguments:
  <url>                         Google Drive URL (file or folder)

Options:
  -h --help                    Show this screen
  --metadata=<key:value>       Custom metadata to add to the archive.org item
  -q --quiet                   Just print errors
  -d --debug                   Print all logs to stdout
"""

import sys
import docopt
import logging
import traceback

from iadrive.core import IAdrive
from iadrive.utils import key_value_to_dict
from iadrive import __version__


def main():
    args = docopt.docopt(__doc__, version=__version__)
    
    url = args['<url>']
    quiet_mode = args['--quiet']
    debug_mode = args['--debug']
    
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
    
    iadrive = IAdrive(verbose=not quiet_mode)
    
    try:
        identifier, meta = iadrive.archive_drive_url(url, metadata)
        print('\n:: Upload Finished. Item information:')
        print('Title: %s' % meta['title'])
        print('Item URL: https://archive.org/details/%s\n' % identifier)
    except Exception as e:
        print('\n\033[91m'
              'An exception occurred: %s\n'
              'If this isn\'t a connection problem, please report to '
              'https://github.com/Andres9890/iadrive/issues' % str(e))
        if debug_mode:
            traceback.print_exc()
        print('\033[0m')
        sys.exit(1)


if __name__ == '__main__':
    main()