[License Button]: https://img.shields.io/badge/License-MIT-black
[License Link]: https://github.com/Andres9890/iadrive/blob/main/LICENSE 'MIT License.'

# IAdrive
[![License Button]][License Link]

IAdrive is A tool for archiving google drive files/folders and uploading them to the [Internet Archive](https://archive.org/), it downloads
the google drive's content, makes the metadata, and then uploads to IA

- this project is heavily based of off [tubeup](https://github.com/bibanon/tubeup) by bibanon, credits to them

## Features

- Downloads files and/or folders from Google Drive using [gdown](https://github.com/wkentaro/gdown)
- Extract file dates from images, PDFs, and media files to determine the creation date for the item

## Installation

Requires Python 3.9 or newer

```bash
git clone https://github.com/Andres9890/iadrive
cd iadrive
pip install -r requirements.txt
```

The package makes a console script named `iadrive` once installed, You can also install from the source using `pip install .`

## Configuration

```bash
ia configure
```

You're gonna be prompted to enter your IA account's email and password

Optional envs:

- `IADRIVE_DEFAULT_COLLECTION` – default Archive.org collection (default:
  `opensource`).
- `IADRIVE_DEFAULT_MEDIATYPE` – default mediatype (default: `data`).
- `GOOGLE_API_KEY` – if set, the tool attempts to look up the owner names of
  the Google Drive file or folder for the `publisher` field in metadata

## Usage

```bash
iadrive LINK [--identifier IDENTIFIER] [--collection COLLECTION]
             [--mediatype MEDIATYPE] [--dest DIRECTORY] [--dry-run]
             [--log-level LEVEL]
```

Arguments:

- `LINK` – Google Drive file or folder URL to mirror.
- `--identifier` – override the generated Archive.org identifier (default is `drive-<drive-id>`)
- `--collection` – Archive.org collection to put the item in
- `--mediatype` – Archive.org mediatype (example, `data`, `texts`, etc)
- `--dest` – destination directory for downloaded files (default is `downloads`)
- `--dry-run` – download and prepare metadata without uploading
- `--log-level` – logging level (example, `DEBUG`, `INFO`, `WARNING`, `ERROR`)

Example:

```bash
iadrive https://drive.google.com/drive/folders/placeholder --collection=mycol \
        --mediatype=data --log-level=DEBUG
```

## How it works

1. `iadrive` uses `gdown` to fetch the specified Google Drive file or folder
2. It walks the downloaded directory and extracts file extensions and dates using optional libraries such as Pillow, mutagen, and pypdf
3. Metadata is assembled including a file listing, earliest embedded date, and original URL
4. The directory is uploaded to an Archive.org item using the `internetarchive` library
