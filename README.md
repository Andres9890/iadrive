[License Button]: https://img.shields.io/badge/License-MIT-black
[License Link]: https://github.com/Andres9890/iadrive/blob/main/LICENSE 'MIT License.'

[PyPI Button]: https://img.shields.io/pypi/v/iadrive?color=yellow&label=PyPI
[PyPI Link]: https://pypi.org/project/iadrive/ 'PyPI Package.'

# IAdrive
[![Lint](https://github.com/Andres9890/iadrive/actions/workflows/lint.yml/badge.svg)](https://github.com/Andres9890/iadrive/actions/workflows/lint.yml)
[![Unit Tests](https://github.com/Andres9890/iadrive/actions/workflows/unit-test.yml/badge.svg)](https://github.com/Andres9890/iadrive/actions/workflows/unit-test.yml)
[![License Button]][License Link]
[![PyPI Button]][PyPI Link]

IAdrive is A tool for archiving google drive files/folders and uploading them to the [Internet Archive](https://archive.org/), it downloads
the google drive's content, makes the metadata, and then uploads to IA

- this project is heavily based of off [tubeup](https://github.com/bibanon/tubeup) by bibanon, credits to them

## Features

- Downloads files and/or folders from Google Drive using [gdown](https://github.com/wkentaro/gdown)
- Preserves folder structure when uploading (can be disabled with `--disable-slash-files`)
- Extract file modification dates to determine the creation date for the item
- Pass custom metadata to Archive.org using `--metadata=<key:value>`
- Supports quiet mode (`--quiet`) and debug mode (`--debug`) for log output
- Automatically cleans up downloaded files after upload
- Sanitizes identifiers and truncates subject tags to fit Archive.org requirements
- Falls back to "IAdrive" as publisher since Google Drive collaborators fetching is not yet implemented
- Improved error handling and debug output

## Installation

Requires Python 3.9 or newer

```bash
pip install iadrive
```

The package makes a console script named `iadrive` once installed, You can also install from the source using `pip install .`

## Configuration

```bash
ia configure
```

You're gonna be prompted to enter your IA account's email and password

Optional envs:

- `GOOGLE_API_KEY` – if set, the tool attempts to look up the owner names of
  the Google Drive file or folder for the `creator` field in metadata (not yet implemented)

## Usage

```bash
iadrive <url> [--metadata=<key:value>...] [--disable-slash-files] [--quiet] [--debug]
```

Arguments:

- `<url>` – Google Drive file or folder URL to mirror (required)

Options:

- `--metadata=<key:value>` – custom metadata to add to the Archive.org item (can be used multiple times)
- `--disable-slash-files` – upload files without preserving folder structure
- `--quiet` – only print errors
- `--debug` – print all logs to stdout (for troubleshooting)

Examples:

```bash
# Upload with folder structure preserved (default)
iadrive https://drive.google.com/drive/folders/placeholder --metadata=collection:placeholder

# Upload with flat structure
iadrive https://drive.google.com/drive/folders/placeholder --disable-slash-files

# Debug mode with custom metadata
iadrive https://drive.google.com/drive/folders/placeholder --metadata=collection:placeholder \
        --metadata=mediatype:data --debug
```

## Folder Structure Preservation

By default, IAdrive preserves the folder structure from Google Drive when uploading to Internet Archive, For example, if your Google Drive link contains:

```
placeholder.txt
placeholder.mp3
folder/
  ├── placeholder.pdf
  └── folder/
      └── placeholder.mp4
```

The files will be uploaded to Internet Archive as:
- `placeholder.txt`
- `placeholder.mp3`
- `folder/placeholder.pdf`
- `folder/folder/placeholder.mp4`

If you use the `--disable-slash-files` command argument, all files will be uploaded to the root level:
- `file1.txt`
- `file2.txt`
- `document.pdf`
- `data.csv`

Note: When using flat structure, duplicate filenames are automatically handled by adding a number (e.g., `placeholder.pdf`, `placeholder_1.pdf`).

## How it works

1. `iadrive` uses `gdown` to fetch the specified Google Drive file or folder
2. It walks the downloaded directory and extracts file extensions and modification dates
3. Metadata is assembled including a file listing (with sizes), oldest file modification date, and original URL. Identifiers are sanitized and subject tags are truncated to fit Archive.org requirements. Publisher defaults to "IAdrive" since collaborator fetching is not yet implemented.
4. The directory is uploaded to an Archive.org item using the `internetarchive` library with a fixed identifier format `drive-{drive-id}`, collection `opensource`, and mediatype `data`, Folder structure is preserved by default (can be disabled with `--disable-slash-files`)
5. Downloaded files are automatically cleaned up after upload
6. Errors are handled gracefully, and debug output is available with `--debug`

## Supported Platforms

For a list of supported platforms for archiving, please see [`SUPPORTEDPLATFORMS.md`](SUPPORTEDPLATFORMS.md)

## To-do list

- Google Drive collaborator fetching to use as creator metadata through the Google API