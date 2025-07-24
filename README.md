A Python GUI application to find and manage duplicate video files based on video frame hashes, duration, and file size. It supports manual review or automatic deletion modes, with a built-in recycle bin and undo functionality.

---

## Features

- Scan folders recursively for duplicate videos (`.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`).
- Detect duplicates by analyzing video frame perceptual hashes, durations, and file sizes.
- Two modes:
  - **Manual Review** — Review duplicates, play videos, and choose which to keep/delete.
  - **Auto Delete** — Automatically mark duplicates (except the first in each group) for deletion.
- Recycle Bin system for safe deletion, with an option to undo last delete.
- Light and Dark mode toggle for a comfortable user experience.
- Fun Snapple-style facts shown during scanning to keep you entertained.
- Progress bar and ability to kill scan mid-process.

---
## Installation

1. Clone this repository or download the script:

```bash
git clone (https://github.com/yeahitsjacobj/DeDuplicator.git)
cd TheDeDuplicator



2. Install the required Python packages:
```bash

pip install -r requirements.txt



## Usage
Run the main application script:


python TheDeDuplicator.py


Click Start Scan to select a folder to scan for duplicate videos.

Choose between Auto Delete or Manual Review mode.

In manual mode, preview videos and decide which files to keep or delete.

Use Undo Last Delete if you make a mistake.

Use Empty Recycle Bin to permanently delete marked files.

Toggle light/dark mode from the menu.
