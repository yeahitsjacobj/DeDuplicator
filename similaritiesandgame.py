import os
import cv2
from PIL import Image
import imagehash
from collections import defaultdict
import threading
import time
import curses

# Settings
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
FRAME_TIME = 5  # Seconds into video to grab thumbnail frame

def is_video_file(filename):
    return os.path.splitext(filename)[1].lower() in VIDEO_EXTENSIONS

def get_video_duration_and_frame(video_path, time_sec):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None, None

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration_sec = int(frame_count / fps) if fps > 0 else 0

    target_time = min(time_sec, duration_sec / 2)

    cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps * target_time))
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return duration_sec, None
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return duration_sec, frame

def get_image_hash(frame):
    img = Image.fromarray(frame)
    return str(imagehash.phash(img))

def scan_folder_for_duplicates_by_hash_duration_size(folder):
    dupe_map = defaultdict(list)
    for root, _, files in os.walk(folder):
        for file in files:
            if is_video_file(file):
                path = os.path.join(root, file)
                try:
                    duration, frame = get_video_duration_and_frame(path, FRAME_TIME)
                    if frame is not None and duration > 0:
                        hash_val = get_image_hash(frame)
                        size = os.path.getsize(path)
                        key = (hash_val, duration, size)
                        dupe_map[key].append(path)
                except Exception as e:
                    print(f"Error processing {path}: {e}")
    return {k: v for k, v in dupe_map.items() if len(v) > 1}

def auto_delete_duplicates(dupe_groups):
    for key, files in dupe_groups.items():
        # Keep first file, delete rest silently
        for f in files[1:]:
            try:
                os.remove(f)
                time.sleep(0.1)
            except Exception as e:
                print(f"Error deleting {f}: {e}")

# Simple Nyan Cat frames (ASCII art + rainbow trail)
NYAN_CAT_FRAMES = [
    r"""
_,------,
_|  /\_/\  
-| ( o.o ) 
_| > ^ <  
""",
    r"""
_,------,
_|  /\_/\  
-| ( o.o ) 
_| > - <  
""",
]

RAINBOW_COLORS = [
    curses.COLOR_RED,
    curses.COLOR_YELLOW,
    curses.COLOR_GREEN,
    curses.COLOR_CYAN,
    curses.COLOR_BLUE,
    curses.COLOR_MAGENTA,
]

def nyan_cat_animation(stdscr, stop_event):
    curses.curs_set(0)
    stdscr.nodelay(True)
    frame_index = 0
    height, width = stdscr.getmaxyx()

    # Setup color pairs
    for i, color in enumerate(RAINBOW_COLORS, 1):
        curses.init_pair(i, color, curses.COLOR_BLACK)

    x_pos = 0

    while not stop_event.is_set():
        stdscr.clear()

        # Draw rainbow trail
        for i, color_id in enumerate(range(1, len(RAINBOW_COLORS)+1)):
            for y in range(2):
                for x in range(x_pos - i*3, x_pos - i*3 + 3):
                    if 0 <= x < width:
                        try:
                            stdscr.addstr(y, x, '=', curses.color_pair(color_id))
                        except curses.error:
                            pass

        # Draw Nyan Cat ASCII art
        lines = NYAN_CAT_FRAMES[frame_index].splitlines()
        for i, line in enumerate(lines):
            try:
                stdscr.addstr(3 + i, x_pos, line)
            except curses.error:
                pass

        frame_index = (frame_index + 1) % len(NYAN_CAT_FRAMES)
        x_pos += 1
        if x_pos > width:
            x_pos = 0

        stdscr.refresh()
        time.sleep(0.2)

def main():
    print("Choose mode:")
    print("  m = Manual mode (ask before deleting)")
    print("  a = Auto mode (auto delete duplicates + Nyan Cat animation)")
    mode = input("Enter mode (m/a): ").strip().lower()

    folder = input("Enter folder to scan: ").strip()
    if not os.path.isdir(folder):
        print("Invalid folder.")
        return

    dupe_groups = scan_folder_for_duplicates_by_hash_duration_size(folder)
    if not dupe_groups:
        print("No duplicates found with matching thumbnail, duration, and size.")
        return

    if mode == "m":
        for (hash_val, duration, size), files in dupe_groups.items():
            print(f"\nFound {len(files)} videos with:")
            print(f"  - Thumbnail hash: {hash_val}")
            print(f"  - Duration: {duration} seconds")
            print(f"  - File size: {size} bytes")
            for i, f in enumerate(files):
                print(f"  [{i}] {f}")

            print("\nOptions:")
            print("  k N   -> keep only file number N, delete the rest")
            print("  ka    -> keep all (do nothing)")
            print("  s     -> skip this group")

            choice = input("Enter your choice: ").strip().lower()
            if choice.startswith("k "):
                try:
                    keep_index = int(choice.split()[1])
                    for i, f in enumerate(files):
                        if i != keep_index:
                            os.remove(f)
                            print(f"Deleted: {f}")
                except Exception as e:
                    print(f"Error: {e}")
            elif choice == "ka":
                print("Keeping all.")
            elif choice == "s":
                print("Skipped.")
            else:
                print("Invalid input. Skipped.")
    elif mode == "a":
        stop_event = threading.Event()
        delete_thread = threading.Thread(target=lambda: (auto_delete_duplicates(dupe_groups), stop_event.set()))
        delete_thread.start()

        curses.wrapper(nyan_cat_animation, stop_event)

        delete_thread.join()
        print("\nAuto deletion complete! Thanks for watching Nyan Cat.")
    else:
        print("Invalid mode selected.")

if __name__ == "__main__":
    main()
