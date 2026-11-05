# One Pace Assistant

An unofficial CLI tool to download and organize [One Pace](https://onepace.net) arcs for media servers like Plex, Jellyfin, and Emby.

> 🏴‍☠️ **[One Pace](https://onepace.net)** is a fan project that re-edits the One Piece anime to follow the manga more closely — cutting filler, improving pacing, and delivering a tighter viewing experience. This tool is built entirely on their incredible work. **Please visit [onepace.net](https://onepace.net) to learn more and support the project!**

> 📢 This project is a successor to the now-archived [one-pace-plex-assistant](https://github.com/JakeLunn/one-pace-plex-assistant), rebuilt from the ground up with broader media server support.

> ⚠️ **Disclaimer:** This is an unofficial tool that relies on scraping [onepace.net](https://onepace.net). If the site undergoes major changes, this tool may break until updated. Please [open an issue](https://github.com/JakeLunn/one-pace-assistant/issues) if you encounter problems.

## Features

- 📥 **Download arcs** with configurable resolution, audio, and subtitles
- 📝 **Auto-generate NFO metadata** compatible with Jellyfin, Emby, and Plex
- 🖼️ **Poster management** for rich media library presentation
- 🔄 **Rsync to remote servers** — transfer files to a Jellyfin/Plex/Emby host over SSH
- 📋 **Multiple output formats** (table, JSON, plain) for scripting

## Installation

### Method 1: Standalone Executable (Recommended)

Download the latest version for your operating system from the [GitHub Releases](https://github.com/JakeLunn/one-pace-assistant/releases) page.

- **Windows**: `onepace-windows.exe`
- **macOS**: `onepace-macos.zip`
- **Linux**: `onepace-linux.tar.gz`

#### Adding to PATH

To run `onepace` from any terminal, you need to add the executable to your system's PATH.

**Windows (PowerShell)**:
1.  Move `onepace-windows.exe` to a permanent location (e.g., `C:\Program Files\OnePace\`).
2.  **Rename the file to `onepace.exe`** (this allows you to run it by just typing `onepace`).
3.  Open PowerShell as Administrator.
4.  Run the following command to append the directory to your User PATH:
    ```powershell
    [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\OnePace", "User")
    ```
5.  Restart your terminal for changes to take effect.

**macOS**:
1.  Unzip the file: `unzip onepace-macos.zip`
2.  Move the binary to `/usr/local/bin` (no need to edit PATH if this directory is already included):
    ```bash
    sudo mv onepace /usr/local/bin/onepace
    sudo chmod +x /usr/local/bin/onepace
    ```
3.  You can now run `onepace` from any terminal.

**Linux**:
1.  Extract the tarball: `tar -xzvf onepace-linux.tar.gz`
2.  Move the binary to `/usr/local/bin`:
    ```bash
    sudo mv onepace /usr/local/bin/onepace
    sudo chmod +x /usr/local/bin/onepace
    ```
3.  You can now run `onepace` from any terminal.

### Method 2: Python Package

Requires Python 3.11+.

```bash
# Clone the repository
git clone https://github.com/JakeLunn/one-pace-assistant.git
cd one-pace-assistant

# Install with pip
pip install .

# Or install in editable mode for development
pip install -e ".[dev]"
```

## Quick Start

```bash
# List all available arcs
onepace list

# Download an arc at 1080p (default)
onepace download romance-dawn

# That's it! Files are saved to ./downloads with NFO metadata
```

## Commands

### `onepace list` — Browse Available Arcs

View all downloadable One Pace arcs with their metadata.

```bash
# Display as formatted table (default)
onepace list

# Include specials and side stories
onepace list --all

# Output as JSON (useful for scripting)
onepace list --format json

# Plain text output (tab-separated)
onepace list --format plain
```

**Example output:**
```
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Slug             ┃ Title                  ┃ Chapters   ┃ Resolutions   ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ romance-dawn     │ Romance Dawn           │ 1-7        │ 480p, 720p... │
│ orange-town      │ Orange Town            │ 8-21       │ 480p, 720p... │
│ ...              │ ...                    │ ...        │ ...           │
└──────────────────┴────────────────────────┴────────────┴───────────────┘
```

---

### `onepace info <arc>` — Arc Details

Get detailed information about a specific arc, including available languages and resolutions.

```bash
onepace info romance-dawn
onepace info water-seven
onepace info wano

# Fetch French metadata or combine selected site languages
onepace info wano --language fr
onepace info wano -l fr -l en

# Discover and fetch all site languages (multiple network requests)
onepace info wano --all-languages
```

Without language options, `info` uses English metadata. Repeat `--language` for
multiple site language codes, such as `fr`, `en`, or `pt-BR`. The first requested
language supplies the displayed title and description; playlists are merged
without duplicate language/cut entries. Failed language fetches produce warnings;
the command fails if none succeed. Site locales do not guarantee every arc has a
playlist in that language.

**Example output:**
```
Romance Dawn
Slug: romance-dawn

The story begins with...

📖 Manga Chapters: 1-7
📺 Anime Episodes: 1-3
🎬 Resolutions: 1080p, 720p, 480p

Available Variants:
  • Sub: en, Dub: ja
  • Sub: none, Dub: en
```

---

### `onepace download <arc>` — Download Content

Download an arc with full control over resolution, audio, and subtitles.

```bash
# Download at 1080p with Japanese audio and English subs (default)
onepace download romance-dawn

# Choose a different resolution
onepace download romance-dawn --resolution 720
onepace download romance-dawn -r 480

# Download Japanese audio with French subtitles
onepace download wano --sub fr --dub ja

# Choose the extended cut with French subtitles
onepace download wano --sub fr --variant extended

# Download English dub version (no subtitles)
onepace download romance-dawn --dub en --sub none

# Download extended dub version (some arcs like Wano have this)
onepace download wano --dub en --variant extended

# Custom output directory
onepace download romance-dawn --output ~/media/anime/OnePace
onepace download romance-dawn -o /mnt/media/anime

# Preview what will be downloaded (no actual download)
onepace download wano --dry-run

# Skip NFO file generation
onepace download romance-dawn --no-nfo

# Disable resume (start fresh)
onepace download romance-dawn --no-resume

# Include posters from a local directory
onepace download romance-dawn --posters-dir ~/posters
```

An explicit `--sub` language selects the corresponding site metadata automatically.
`--sub none` requests no subtitles. With subtitles omitted, existing English/Japanese
defaults apply; other dub codes select their matching site locale and prefer no
subtitles, then subtitles matching the dub language. Subtitle and
audio availability must match a published playlist. Downloads select one language
combination per invocation.

**Download Methods:**

```bash
# Individual file downloads (default, shows progress per file)
onepace download romance-dawn --method individual

# Bulk ZIP download (single archive, may help with rate limits)
onepace download romance-dawn --method zip

# Auto mode (tries ZIP first, falls back to individual on failure)
onepace download romance-dawn --method auto
```

### 📦 Arc-Based Downloads

This CLI downloads **entire arcs at once**. If you need to download individual episodes, visit [onepace.net](https://onepace.net) directly.

---

### ⚠️ About Rate Limits:

One Pace files are hosted on [PixelDrain](https://pixeldrain.com), which has bandwidth limits for free users. After hitting your bandwidth limit, currently **6GB per day**, your download speeds will drop to **1mbps**.

To avoid interruptions and support the service that makes these downloads possible, consider [subscribing to PixelDrain Pro](https://pixeldrain.com/home#pro) — it's affordable and helps keep the platform running for everyone.

> 💡 **Tip:** Use `--method zip` to download arcs as a single archive, which reduces requests and has slightly smaller download size.

**Full options reference:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | `./downloads` | Output directory |
| `--resolution` | `-r` | `1080` | Video resolution (480, 720, 1080) |
| `--sub` | `-s` | auto | Subtitle language (e.g., en, fr, pt-BR, none) |
| `--dub` | `-d` | `ja` | Audio language (ja, en) |
| `--variant` | — | — | Arc variant (e.g., `extended` for extended dub) |
| `--dry-run` | `-n` | — | Preview without downloading |
| `--no-nfo` | — | — | Skip NFO metadata generation |
| `--resume/--no-resume` | — | resume | Resume interrupted downloads |
| `--method` | `-m` | `individual` | Download method (individual, zip, auto) |
| `--posters-dir` | — | — | Directory with poster images |

---

### `onepace generate-nfo` — Generate Metadata for Existing Files

Already have One Pace video files? Generate NFO metadata for your existing library.

```bash
# Generate NFOs for all arcs in a directory
onepace generate-nfo --input ~/media/OnePace

# Also copy matching poster images
onepace generate-nfo --input ~/media/OnePace --posters ~/posters
```

**Expected directory structure:**
```
~/media/OnePace/
├── romance-dawn/
│   ├── Romance Dawn 01.mkv
│   ├── Romance Dawn 02.mkv
│   └── Romance Dawn 03.mkv
├── orange-town/
│   ├── Orange Town 01.mkv
│   └── ...
└── ...
```

The command will:
1. Create a `tvshow.nfo` in the root directory
2. Generate episode `.nfo` files next to each video
3. Optionally copy matching posters as `poster.jpg` in each arc folder

---

### `onepace add-posters` — Add Poster Images

Add poster images to your existing arc directories.

```bash
# Copy posters to all arc directories
onepace add-posters --input ~/media/OnePace --posters ~/posters

# Only add posters where NFO files exist
onepace add-posters --input ~/media/OnePace --posters ~/posters --require-nfo

# Overwrite existing poster.jpg files
onepace add-posters --input ~/media/OnePace --posters ~/posters --force
```

**Poster file naming:**

Poster files should contain the arc slug (or a close match) in their filename.

- Supported formats: `.jpg`, `.jpeg`, `.png`, `.webp`
- Examples: `romance-dawn.jpg`, `Romance Dawn poster.png`, `water-seven-cover.jpg`

**Expected poster directory structure:**
```
~/posters/
├── romance-dawn.jpg
├── orange-town.jpg
├── syrup-village.png
├── baratie.jpg
└── ...
```

**Where to find posters:**

You can create your own poster images or find fan-made sets online. A popular community-made set is available here:

> 🖼️ [One Pace Custom Season Posters (Full Set)](https://www.reddit.com/r/OnePiece/comments/1cllxos/one_pace_custom_season_posters_full_set_link_in/) — high-quality posters for all arcs

---

### `onepace rsync` — Sync Files to a Remote Server

Transfer your downloaded files to a remote machine (e.g., a server running Jellyfin, Plex, or Emby) via rsync over SSH.

> ⚠️ **Requires rsync** installed on both the local and remote machine. The command will check both before starting and provide install instructions if missing.

```bash
# Sync downloads to a remote server
onepace rsync --target user@myserver:/media/anime/OnePace

# Sync from a custom source directory
onepace rsync --source ~/OnePace --target user@myserver:/media/anime/OnePace

# Preview what would be transferred (no actual transfer)
onepace rsync --target user@myserver:/media/anime/OnePace --dry-run

# Use a specific SSH key and port
onepace rsync --target user@myserver:/media/anime/OnePace --ssh-key ~/.ssh/id_rsa --port 2222

# Limit bandwidth to 5000 KBps
onepace rsync --target user@myserver:/media/anime/OnePace --bwlimit 5000

# Remove remote files that no longer exist locally
onepace rsync --target user@myserver:/media/anime/OnePace --delete

# Exclude certain files from the sync
onepace rsync --target user@myserver:/media/anime/OnePace --exclude "*.nfo" --exclude "poster.jpg"
```

**Full options reference:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--source` | `-s` | `./downloads` | Local directory to sync from |
| `--target` | `-t` | — | Remote target (e.g., `user@host:/path`) **required** |
| `--ssh-key` | — | — | Path to SSH private key |
| `--port` | — | 22 | SSH port |
| `--dry-run` | `-n` | — | Preview without transferring |
| `--delete` | — | — | Delete remote files not present locally |
| `--exclude` | — | — | Exclude pattern (repeatable) |
| `--bwlimit` | — | — | Bandwidth limit (e.g., `5000` KBps, `10m` MBps) |

---

## Media Server Setup

### Jellyfin / Emby

NFO files are automatically generated alongside downloads. Your media server should pick up the metadata automatically—no additional configuration required.

### Plex

Plex requires the [XBMCnfoTVImporter](https://github.com/gboudreau/XBMCnfoTVImporter.bundle) agent to read NFO files. Follow the installation instructions in that repository to enable NFO support.

**Alternative Method for Plex**

Plex does not have any (good) native capability of adding custom shows. Their metadata is purely driven by external databases which do not have metadata for One Pace. To get around this, you can 'override' the "One Piece" TV show's metadata in Plex and upload your One Pace episodes. This functionality existed in [the previous cli](https://github.com/JakeLunn/one-pace-plex-assistant) and worked well - albeit has one major caveat: You can't have both a "One Piece" show and a "One Pace" show in the same library at the same time.

This feature is experimental and available over in the [plex-api branch](https://github.com/JakeLunn/one-pace-assistant/tree/plex-api). 


---

## Global Options

These options work with any command:

```bash
# Show version
onepace --version

# Verbose output (more details)
onepace -v download romance-dawn

# Quiet mode (minimal output)
onepace -q download romance-dawn
```

---

## Examples

**Download your first arc:**
```bash
onepace download romance-dawn
```

**Build a complete library:**
```bash
# Download multiple arcs
onepace download romance-dawn -o ~/OnePace
onepace download orange-town -o ~/OnePace
onepace download syrup-village -o ~/OnePace

# Or script it with JSON output
for slug in $(onepace list --format json | jq -r '.[].slug'); do
  onepace download "$slug" -o ~/OnePace
done
```

**Set up existing files for Plex/Jellyfin:**
```bash
# You already have video files organized by arc
onepace generate-nfo --input ~/media/OnePace --posters ~/posters
```

**Download and sync to a remote server:**
```bash
# Download an arc, then sync to your media server
onepace download romance-dawn -o ~/OnePace
onepace rsync -s ~/OnePace -t user@myserver:/media/anime/OnePace
```

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .
```

**Important:** We use **Conventional Commits** to automatically increment the release version. Please use [Conventional Commits as defined here](https://www.conventionalcommits.org/en/v1.0.0/#summary) when making your commit messages for PRs. Failing to do is punishable by a disapproving grunt.

## License

MIT
