import os
import cv2
import imagehash
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import queue
import random
from PIL import Image
from moviepy import VideoFileClip
from collections import defaultdict

# --- About 50 Snapple-style Fun Facts ---
snapple_facts = [
    "A snail can sleep for three years.",
    "The average person walks the equivalent of three times around the world in a lifetime.",
    "Slugs have four noses.",
    "An ostrich's eye is bigger than its brain.",
    "The fingerprints of a koala are so indistinguishable from humans that they have on occasion been confused at a crime scene.",
    "A crocodile cannot stick out its tongue.",
    "Butterflies taste with their feet.",
    "Octopuses have three hearts.",
    "Bananas are berries, but strawberries are not.",
    "There are more fake flamingos in the world than real ones.",
    "A bolt of lightning contains enough energy to toast 100,000 slices of bread.",
    "Tigers have striped skin, not just striped fur.",
    "A group of flamingos is called a flamboyance.",
    "A small child could swim through the veins of a blue whale.",
    "The heart of a shrimp is located in its head.",
    "Giraffes have no vocal cords.",
    "Sea otters hold hands when they sleep.",
    "Wombat poop is cube-shaped.",
    "Some cats are allergic to humans.",
    "Scotland's national animal is the unicorn.",
    "The wood frog can hold its pee for up to eight months.",
    "Cows have best friends and can become stressed when they are separated.",
    "Honey never spoils.",
    "A jiffy is an actual unit of time: 1/100th of a second.",
    "Sharks are older than trees.",
    "The Eiffel Tower can grow more than six inches in summer.",
    "It's impossible to hum while holding your nose.",
    "A group of porcupines is called a prickle.",
    "Penguins propose with pebbles.",
    "The blob of toothpaste that sits on your toothbrush is called a nurdle.",
    "There are more trees on Earth than stars in the Milky Way.",
    "Mosquitoes are attracted to people who just ate bananas.",
    "Hot water freezes faster than cold water.",
    "The first alarm clock could only ring at 4 a.m.",
    "M&M stands for Mars and Murrie.",
    "A baby puffin is called a puffling.",
    "Banging your head against a wall for one hour burns 150 calories.",
    "Chewing gum boosts mental proficiency.",
    "A crocodile can't stick out its tongue.",
    "Carrots were originally purple.",
    "Elephants can't jump.",
    "Your nose can remember 50,000 different scents.",
    "A single strand of spaghetti is called a spaghetto.",
    "Lobsters have blue blood.",
    "Dolphins have names for each other.",
    "Bats always turn left when exiting a cave.",
    "Most wasabi consumed is not real wasabi.",
    "Cats can't taste sweetness.",
    "Some turtles can breathe through their butts."
]

class ProgressPopup(tk.Toplevel):
    def __init__(self, parent, max_value, get_theme_colors):
        super().__init__(parent)
        self.parent = parent
        self.get_theme_colors = get_theme_colors  # function to get current colors
        self.title("Scanning for duplicates...")
        self.geometry("500x160")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Style according to current theme
        self.apply_theme()

        # Progress bar
        self.progress = ttk.Progressbar(self, orient="horizontal", length=450, mode="determinate", maximum=max_value)
        self.progress.pack(pady=(10, 5))

        # Status label
        self.status_label = tk.Label(self, text="Starting scan...", bg=self.colors["bg"], fg=self.colors["fg"])
        self.status_label.pack()

        # Fun fact label below progress bar
        self.fun_fact_label = tk.Label(self, text="", wraplength=460, justify="center",
                                       font=("Arial", 10, "italic"), fg="blue", bg=self.colors["bg"])
        self.fun_fact_label.pack(pady=(10, 5))

        self.after_id = None
        self.update_fun_fact()

    def apply_theme(self):
        self.colors = self.get_theme_colors()
        self.configure(bg=self.colors["bg"])

    def update_progress(self, current, total, filename=None):
        self.progress['value'] = current
        percent = (current / total) * 100 if total else 0
        if filename:
            self.status_label.config(text=f"Scanning ({current}/{total}): {os.path.basename(filename)}")
        else:
            self.status_label.config(text=f"Scanning... {int(percent)}%")
        self.update_idletasks()

    def update_fun_fact(self):
        fact = random.choice(snapple_facts)
        self.fun_fact_label.config(text=f"💡 Fun Fact: {fact}")
        # Update every 2000 ms (2 seconds)
        self.after_id = self.after(2000, self.update_fun_fact)

    def destroy(self):
        if self.after_id:
            self.after_cancel(self.after_id)
        super().destroy()


def get_video_hash_duration_size(path):
    try:
        cap = cv2.VideoCapture(path)
        success, frame = cap.read()
        if not success:
            return None, None, None
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        img_hash = str(imagehash.phash(img))
        duration = VideoFileClip(path).duration
        size = os.path.getsize(path)
        cap.release()
        return img_hash, round(duration, 1), size
    except Exception:
        return None, None, None


def scan_folder(folder, log, progress_queue=None, kill_flag=None):
    log("🔍 Scanning for duplicates...")
    seen = defaultdict(list)
    files_to_scan = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
                files_to_scan.append(os.path.join(root, file))

    total_files = len(files_to_scan)
    for idx, full_path in enumerate(files_to_scan, 1):
        if kill_flag and kill_flag.is_set():
            log("❌ Scan killed by user.")
            return {}
        hash_val, duration, size = get_video_hash_duration_size(full_path)
        if None not in (hash_val, duration, size):
            seen[(hash_val, duration, size)].append(full_path)
        log(f"Indexed file {idx}/{total_files}: {os.path.basename(full_path)}")

        if progress_queue:
            progress_queue.put((idx, total_files, full_path))

    dupes = {k: v for k, v in seen.items() if len(v) > 1}
    log(f"📁 Found {len(dupes)} duplicate groups.")
    return dupes


class DeDupGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Video De-Duplicator")
        self.root.geometry("850x600")
        self.mode = tk.StringVar(value="manual")

        # Light/Dark mode state
        self.dark_mode = tk.BooleanVar(value=False)

        # Define styles for light and dark
        self.styles = {
            "light": {
                "bg": "#f0f0f0",
                "fg": "#000000",
                "button_bg": "#e1e1e1",
                "button_fg": "#000000",
                "text_bg": "white",
                "text_fg": "black",
                "highlight_bg": "#c8dafc"
            },
            "dark": {
                "bg": "#2e2e2e",
                "fg": "#f0f0f0",
                "button_bg": "#444444",
                "button_fg": "#ffffff",
                "text_bg": "#3c3f41",
                "text_fg": "#f0f0f0",
                "highlight_bg": "#5a5a8f"
            }
        }

        self.create_widgets()
        self.apply_theme()  # Set initial theme

    def get_theme_colors(self):
        return self.styles["dark"] if self.dark_mode.get() else self.styles["light"]

    def create_widgets(self):
        # Top frame for buttons and mode toggle
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10)

        # Start Scan button
        self.start_button = tk.Button(top_frame, text="Start Scan", command=self.start_scan, width=12)
        self.start_button.pack(side="left", padx=5)

        # Kill Scan button
        self.kill_button = tk.Button(top_frame, text="Kill Scan", command=self.kill_scan, fg="red", state="disabled", width=12)
        self.kill_button.pack(side="left", padx=5)

        # Light/Dark Mode toggle checkbox
        self.mode_toggle = tk.Checkbutton(top_frame, text="Dark Mode", variable=self.dark_mode, command=self.toggle_theme)
        self.mode_toggle.pack(side="left", padx=20)

        # Mode selection radios
        mode_frame = tk.Frame(self.root)
        mode_frame.pack(pady=5)

        tk.Radiobutton(mode_frame, text="Auto Delete", variable=self.mode, value="auto").pack(side="left", padx=15)
        tk.Radiobutton(mode_frame, text="Manual Review", variable=self.mode, value="manual").pack(side="left", padx=15)

        # Folder path label
        self.folder_label = tk.Label(self.root, text="No folder selected", font=("Arial", 10, "bold"))
        self.folder_label.pack(pady=(10, 15))

        # Output scrolled text
        self.output = scrolledtext.ScrolledText(self.root, height=20, width=100, state="disabled", font=("Consolas", 10))
        self.output.pack(padx=10)

        # Undo and Empty Recycle Bin buttons
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(pady=15)

        self.undo_button = tk.Button(bottom_frame, text="Undo Last Delete & Go Back", command=self.undo_last_delete, state="disabled", width=20)
        self.undo_button.pack(side="left", padx=10)

        self.empty_bin_button = tk.Button(bottom_frame, text="Empty Recycle Bin", command=self.empty_recycle_bin, state="disabled", width=20)
        self.empty_bin_button.pack(side="left", padx=10)

        # Initialize variables for scan
        self.dupe_groups = []
        self.deleted_count = 0
        self.skipped_groups_stack = []
        self.recycle_bin = []
        self.progress_popup = None
        self.progress_queue = queue.Queue()
        self.kill_flag = threading.Event()
        self.current_group = None
        self.last_deleted_group = None

    def apply_theme(self):
        colors = self.get_theme_colors()

        # Root window colors
        self.root.configure(bg=colors["bg"])

        # Buttons and frames
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.configure(bg=colors["bg"])
                for child in widget.winfo_children():
                    if isinstance(child, (tk.Button, tk.Checkbutton, tk.Radiobutton)):
                        child.configure(
                            bg=colors["button_bg"],
                            fg=colors["button_fg"],
                            activebackground=colors["highlight_bg"],
                            activeforeground=colors["button_fg"],
                            selectcolor=colors["bg"] if isinstance(child, tk.Radiobutton) else None,
                            highlightbackground=colors["bg"]
                        )
                    elif isinstance(child, tk.Label):
                        child.configure(bg=colors["bg"], fg=colors["fg"])

            elif isinstance(widget, tk.Label):
                widget.configure(bg=colors["bg"], fg=colors["fg"])

        # Folder label
        self.folder_label.configure(bg=colors["bg"], fg=colors["fg"])

        # Output Text widget colors
        self.output.configure(
            bg=colors["text_bg"],
            fg=colors["text_fg"],
            insertbackground=colors["fg"],  # cursor color
            selectbackground=colors["highlight_bg"],
            selectforeground=colors["text_fg"],
            relief="sunken",
            bd=2,
        )

    def toggle_theme(self):
        self.apply_theme()
        # Update popup theme if open
        if self.progress_popup:
            self.progress_popup.apply_theme()
            # Update labels bg/fg manually because Progressbar is ttk and harder to style
            colors = self.get_theme_colors()
            self.progress_popup.status_label.configure(bg=colors["bg"], fg=colors["fg"])
            self.progress_popup.fun_fact_label.configure(bg=colors["bg"])

    # --- Rest of your existing methods below ---

    def log(self, msg):
        self.output.configure(state="normal")
        self.output.insert("end", msg + "\n")
        self.output.yview("end")
        self.output.configure(state="disabled")

    def start_scan(self):
        folder = filedialog.askdirectory(title="Select folder to scan")
        if not folder:
            return

        self.folder_label.config(text=f"Folder Selected: {folder}")

        self.output.configure(state="normal")
        self.output.delete(1.0, "end")
        self.output.configure(state="disabled")
        self.log(f"Selected folder: {folder}")

        # Reset kill flag, recycle bin, undo states
        self.kill_flag.clear()
        self.recycle_bin.clear()
        self.skipped_groups_stack.clear()
        self.undo_button.config(state="disabled")
        self.empty_bin_button.config(state="disabled")
        self.last_deleted_group = None

        self.progress_popup = ProgressPopup(self.root, max_value=1, get_theme_colors=self.get_theme_colors)
        self.kill_button.config(state="normal")
        threading.Thread(target=self.threaded_scan, args=(folder,), daemon=True).start()
        self.root.after(100, self.update_progress_bar)

    def kill_scan(self):
        self.kill_flag.set()
        self.kill_button.config(state="disabled")
        self.log("❌ Kill switch activated: stopping scan...")

    def threaded_scan(self, folder):
        dupes = scan_folder(folder, self.log, progress_queue=self.progress_queue, kill_flag=self.kill_flag)
        self.dupe_groups = list(dupes.items())
        self.deleted_count = 0

        if self.progress_popup:
            self.root.after(0, self.progress_popup.destroy)
            self.progress_popup = None

        self.kill_button.config(state="disabled")

        self.root.after(0, self.post_scan_actions)

    def update_progress_bar(self):
        if not self.progress_popup:
            return
        try:
            while True:
                current, total, filename = self.progress_queue.get_nowait()
                self.progress_popup.progress['maximum'] = total
                self.progress_popup.update_progress(current, total, filename)
        except queue.Empty:
            pass

        if self.progress_popup:
            self.root.after(100, self.update_progress_bar)

    def post_scan_actions(self):
        if not self.dupe_groups:
            self.log("✅ No duplicates found.")
            return

        if self.mode.get() == "auto":
            count = self.auto_delete_with_progress()
            self.log(f"✅ Auto mode complete. {count} duplicates marked for deletion (in recycle bin).")
            self.ask_run_again()
        else:
            self.process_next_manual_group()

    def auto_delete_with_progress(self):
        count = 0
        total_groups = len(self.dupe_groups)
        progress_win = ProgressPopup(self.root, max_value=total_groups, get_theme_colors=self.get_theme_colors)
        for idx, (key, files) in enumerate(self.dupe_groups, 1):
            if self.kill_flag.is_set():
                self.log("❌ Auto deletion stopped by user.")
                break
            for f in files[1:]:
                self.recycle_bin.append(f)
                self.log(f"Marked for deletion: {f}")
                count += 1
            progress_win.update_progress(idx, total_groups, f"{len(files)} files in group")
            self.root.update_idletasks()
        progress_win.destroy()
        self.empty_bin_button.config(state="normal")
        self.undo_button.config(state="normal")
        return count

    def process_next_manual_group(self):
        if not self.dupe_groups:
            self.log(f"\n✅ Manual mode complete. {self.deleted_count} duplicates marked for deletion.")
            self.ask_run_again()
            return

        key, files = self.dupe_groups.pop(0)
        self.current_group = (key, files)
        self.log(f"\nDuplicate Group: Hash={key[0]} | Duration={key[1]}s | Size={key[2]} bytes")
        for idx, f in enumerate(files):
            self.log(f" [{idx}] {f}")
        self.prompt_user_for_manual_deletion(files)

    def prompt_user_for_manual_deletion(self, files):
        win = tk.Toplevel(self.root)
        win.title("Select File to Keep")
        win.geometry("600x400")

        # Apply theme to this popup as well
        colors = self.get_theme_colors()
        win.configure(bg=colors["bg"])

        label = tk.Label(win, text="Choose which file to KEEP:", font=("Arial", 12, "bold"), bg=colors["bg"], fg=colors["fg"])
        label.pack(pady=5)

        for idx, path in enumerate(files):
            frame = tk.Frame(win, bg=colors["bg"])
            frame.pack(fill="x", padx=5, pady=2)

            tk.Button(frame, text=f"Keep [{idx}]", command=lambda i=idx: self.delete_except(files, i, win),
                      bg=colors["button_bg"], fg=colors["button_fg"], activebackground=colors["highlight_bg"], width=10).pack(side="left")
            tk.Button(frame, text="▶️", command=lambda p=path: self.play_video(p),
                      bg=colors["button_bg"], fg=colors["button_fg"], activebackground=colors["highlight_bg"], width=3).pack(side="left", padx=4)

            tk.Label(frame, text=os.path.basename(path), anchor="w", bg=colors["bg"], fg=colors["fg"]).pack(side="left", fill="x", expand=True)

        btn_frame = tk.Frame(win, bg=colors["bg"])
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Skip Group", command=lambda: self.skip_group(win),
                  bg=colors["button_bg"], fg=colors["button_fg"], activebackground=colors["highlight_bg"], width=12).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Stop Scanning", command=lambda: self.stop_manual_scan(win),
                  bg=colors["button_bg"], fg=colors["button_fg"], activebackground=colors["highlight_bg"], width=12).pack(side="left", padx=5)

    def delete_except(self, files, keep_index, win):
        to_delete = [f for i, f in enumerate(files) if i != keep_index]
        for f in to_delete:
            self.recycle_bin.append(f)
            self.log(f"Marked for deletion: {f}")
            self.deleted_count += 1
        self.undo_button.config(state="normal")
        self.empty_bin_button.config(state="normal")
        self.last_deleted_group = to_delete
        win.destroy()
        self.process_next_manual_group()

    def skip_group(self, win):
        if self.current_group:
            self.skipped_groups_stack.append(self.current_group)
        win.destroy()
        self.process_next_manual_group()

    def stop_manual_scan(self, win):
        self.log(f"❌ Manual scanning stopped. {self.deleted_count} files marked for deletion.")
        win.destroy()

    def play_video(self, path):
        try:
            if os.name == "nt":
                os.startfile(path)
            elif os.uname().sysname == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play video: {e}")

    def undo_last_delete(self):
        if self.last_deleted_group:
            for f in self.last_deleted_group:
                if f in self.recycle_bin:
                    self.recycle_bin.remove(f)
                    self.log(f"Undo deletion: {f}")
                    self.deleted_count -= 1
            self.last_deleted_group = None
            self.undo_button.config(state="disabled")
            if not self.recycle_bin:
                self.empty_bin_button.config(state="disabled")

    def empty_recycle_bin(self):
        if messagebox.askyesno("Confirm", "Permanently delete all marked duplicates from recycle bin?"):
            for f in self.recycle_bin:
                try:
                    os.remove(f)
                    self.log(f"Deleted file: {f}")
                except Exception as e:
                    self.log(f"Failed to delete {f}: {e}")
            self.recycle_bin.clear()
            self.empty_bin_button.config(state="disabled")
            self.log("♻️ Recycle bin emptied.")

    def ask_run_again(self):
        if messagebox.askyesno("Done", "Processing complete.\nDo you want to scan another folder?"):
            self.start_scan()
        else:
            self.log("Program idle. Select 'Start Scan' to begin a new scan.")

if __name__ == "__main__":
    root = tk.Tk()
    app = DeDupGUI(root)
    root.mainloop()
