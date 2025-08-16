# IAdrive

IAdrive is a command-line tool for mirroring public Google Drive files or
folders into items on [archive.org](https://archive.org/). The utility downloads
the referenced drive content, builds metadata, and then uploads the result to
the Internet Archive.

## Features

- Download individual files or entire folders from Google Drive using
  [`gdown`](https://github.com/wkentaro/gdown).
- Extract file dates from images, PDFs, and media files to determine the oldest
  creation date for the item.
- Automatically build Archive.org metadata including title, date, publisher and
  subjects based on file extensions.
- Upload the prepared directory to the Internet Archive or run in `--dry-run`
  mode to preview the process without uploading.

## Installation

Requires Python 3.8 or newer.

```bash
git clone <REPOSITORY_URL>
cd iadrive
pip install -r requirements.txt  # installs the "iadrive" CLI
```

The package exposes a console script named `iadrive` once installed. You can
also install directly from the source using `pip install .`.

## Configuration

IAdrive requires Internet Archive credentials. The simplest way is to configure
the `internetarchive` package:

```bash
ia configure
```

This creates `~/.config/ia.ini` containing your access key and secret. As an
alternative you may set the `IA_ACCESS_KEY` and `IA_SECRET_KEY` environment
variables before running the tool.

Optional environment variables:

- `IADRIVE_DEFAULT_COLLECTION` – default Archive.org collection (default:
  `opensource`).
- `IADRIVE_DEFAULT_MEDIATYPE` – default mediatype (default: `data`).
- `GOOGLE_API_KEY` – if set, the tool attempts to look up the owner names of
  the Google Drive file or folder for the `publisher` field in metadata.

## Usage

```bash
iadrive LINK [--identifier IDENTIFIER] [--collection COLLECTION]
             [--mediatype MEDIATYPE] [--dest DIRECTORY] [--dry-run]
             [--log-level LEVEL]
```

Arguments:

- `LINK` – Google Drive file or folder URL to mirror.
- `--identifier` – override the generated Archive.org identifier
  (defaults to `drive-<drive-id>`).
- `--collection` – Archive.org collection to place the item in.
- `--mediatype` – Archive.org mediatype (`data`, `texts`, etc.).
- `--dest` – destination directory for downloaded files (default:
  `downloads`).
- `--dry-run` – download and prepare metadata without uploading.
- `--log-level` – logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`).

Example:

```bash
iadrive https://drive.google.com/drive/folders/EXAMPLE_ID --collection=mycol \
        --mediatype=data --log-level=DEBUG
```

## How it works

1. `iadrive` uses `gdown` to fetch the specified Google Drive file or folder.
2. It walks the downloaded directory and extracts file extensions and dates
   using optional libraries such as Pillow, mutagen, and pypdf.
3. Metadata is assembled including a file listing, earliest embedded date, and
   original URL.
4. The directory is uploaded to an Archive.org item using the
   `internetarchive` library.

## License

Distributed under the MIT License. See `LICENSE` for more information.

