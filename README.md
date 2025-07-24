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
