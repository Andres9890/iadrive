[License Button]: https://img.shields.io/badge/License-MIT-black
[License Link]: https://github.com/Andres9890/iadrive/blob/main/LICENSE 'MIT License.'

[PyPI Button]: https://img.shields.io/pypi/v/iadrive?color=yellow&label=PyPI
[PyPI Link]: https://pypi.org/project/iadrive/ 'PyPI Package.'

# IAdrive
[![Lint](https://github.com/Andres9890/iadrive/actions/workflows/lint.yml/badge.svg)](https://github.com/Andres9890/iadrive/actions/workflows/lint.yml)
[![Unit Tests](https://github.com/Andres9890/iadrive/actions/workflows/unit-test.yml/badge.svg)](https://github.com/Andres9890/iadrive/actions/workflows/unit-test.yml)
[![License Button]][License Link]
[![PyPI Button]][PyPI Link]

IAdrive is a tool for archiving Google Drive files/folders and Google Docs/Sheets/Slides and uploading them to the [Internet Archive](https://archive.org/), It downloads the content, creates appropriate metadata, and uploads to IA with preservation of folder structure

- This project is heavily based off [tubeup](https://github.com/bibanon/tubeup) by bibanon, credits to them

## Features

- **Google Drive Support**: Downloads files and/or folders from Google Drive using [gdown](https://github.com/wkentaro/gdown)
- **Google Docs Integration**: Directly exports Google Docs, Sheets, and Slides in multiple formats
- **Multiple Format Export**: For Google Docs, automatically exports in all available formats (PDF, DOCX, TXT, HTML, etc)
- Preserves folder structure when uploading (can be disabled with `--disable-slash-files`)
- Extract file modification dates to determine the creation date for the item
- Pass custom metadata to Archive.org using `--metadata=<key:value>`
- Supports quiet mode (`--quiet`) and debug mode (`--debug`) for log output
- Automatically cleans up downloaded files after upload
- Sanitizes identifiers and truncates subject tags to fit Archive.org requirements
- Fetch file owner/last modifier as creator metadata using `--gdrive-token`
- When unable to determine a folder name, uses format `{platform} - {id}` (e.g., "Google Drive - 1dEuZpztEZqL3PZPIaFh9i4EjBmcEruHh")
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

## Usage

```bash
iadrive <url> [--metadata=<key:value>...] [--disable-slash-files] [--gdrive-token=<token>] [--quiet] [--debug]
```

Arguments:

- `<url>` – Google Drive file/folder URL or Google Docs/Sheets/Slides URL to archive

Options:

- `--metadata=<key:value>` – custom metadata to add to the IA item
- `--disable-slash-files` – upload files without preserving folder structure
- `--gdrive-token=<token>` – Google Drive API OAuth2 access token for fetching file owner/modifier as creator metadata
- `--quiet` – only print errors
- `--debug` – print all logs to stdout

## Google Docs Support

IAdrive can directly archive Google Docs, Sheets, and Slides by exporting them in all available formats, it uses public export URLs

### Available Formats

Google Documents:
- `pdf`
- `docx`
- `odt`
- `rtf`
- `txt`
- `html`
- `epub`

**Google Spreadsheets:**
- `xlsx`
- `ods`
- `pdf`
- `csv`
- `tsv`
- `html`

**Google Presentations:**
- `pdf`
- `pptx`
- `odp`
- `txt`
- `jpeg`
- `png`
- `svg`

### Automatic Export Behavior

For example, a Google Document will be automatically exported and uploaded as:
- `placeholder.pdf`
- `placeholder.docx`
- `placeholder.odt`
- `placeholder.rtf`
- `placeholder.txt`
- `placeholder.html`
- `placeholder.epub`

### Google Docs Examples

```bash

# Archive Google Document
iadrive https://docs.google.com/document/d/1abc123/edit

# Archive Google Spreadsheet
iadrive https://docs.google.com/spreadsheets/d/1abc123/edit

# Archive Google Slides with custom metadata
iadrive https://docs.google.com/presentation/d/1abc123/edit --metadata=collection:placeholder --metadata=creator:placeholder

# Debug mode with Google Docs
iadrive https://docs.google.com/document/d/1abc123/edit --debug
```

## Google Drive Examples

```bash
# Upload with folder structure preserved (default)
iadrive https://drive.google.com/drive/folders/placeholder --metadata=collection:placeholder

# Upload with flat structure
iadrive https://drive.google.com/drive/folders/placeholder --disable-slash-files

# Upload with file owner/modifier as creator metadata
iadrive https://drive.google.com/drive/folders/placeholder --gdrive-token=ya29.a0AfH6SMBx...

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
- `placeholder.txt`
- `placeholder.mp3`
- `placeholder.pdf`
- `placeholder.mp4`

Note: When using flat structure, duplicate filenames are automatically handled by adding a number (e.g., `placeholder.pdf`, `placeholder_1.pdf`).

## How it works

### Google Drive Files/Folders
1. `iadrive` uses `gdown` to fetch the specified Google Drive file or folder
2. It walks the downloaded directory and extracts file extensions and modification dates
3. Metadata is made including a file listing (with sizes), oldest file modification date, and original URL
4. The content is uploaded to Archive.org with identifier format `drive-{drive-id}`

### Google Docs/Sheets/Slides
1. `iadrive` detects Google Docs URLs and determines the document type
2. It automatically exports the document in **all available formats** using Google's public export URLs
3. Each format is downloaded and saved with descriptive filenames
4. Metadata includes comprehensive format information and document type
5. The content is uploaded to Archive.org with identifier format `docs-{doc-id}`

### Common Steps
- Identifiers are sanitized and subject tags are truncated to fit Archive.org requirements
- Publisher/creator defaults to "IAdrive" unless `--gdrive-token` is provided to fetch file owner/modifier
- Folder structure is preserved by default (can be disabled with `--disable-slash-files`)
- Downloaded files are automatically cleaned up after upload
- Errors are handled gracefully, and debug output is available with `--debug`
- If a folder name or title cannot be determined, falls back to format `{platform} - {id}`

## Supported Platforms

For a list of supported platforms for archiving, please see [`SUPPORTEDPLATFORMS.md`](SUPPORTEDPLATFORMS.md)

## Google Drive API Token

To fetch file owner and last modifier information as creator metadata, you can provide a Google Drive API OAuth2 access token using the `--gdrive-token` option:

```bash
iadrive <url> --gdrive-token=ya29.a0AfH6SMBx...
```

The token is used to call the Google Drive API v3 to retrieve:
- File owner information (name or email)
- Last modifying user (if owner is unavailable)

This information is then used to populate the `creator` field in the Internet Archive metadata instead of the default "IAdrive".

### Getting a Google Drive API Token

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Google Drive API
3. Create OAuth2 credentials
4. Generate an access token using OAuth2 flow
5. Pass the access token to iadrive using `--gdrive-token`

Note: Access tokens are typically short-lived. For production use, you may want to implement a refresh token mechanism.

## To-do list

- Batch processing