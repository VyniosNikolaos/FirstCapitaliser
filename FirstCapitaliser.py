"""
FirstCapitaliser.py

A lightweight utility to capitalize the first character of every file and directory
name in a given tree. Designed for cross-platform consistency and safe operation on
case-insensitive filesystems.

Key design considerations:
 - Bottom-up traversal ensures child items are renamed before their parent,
   preventing stale path references.
 - Two-phase rename on case-insensitive OS (Windows/macOS) to force the
   filesystem to register case-only changes.
 - Idempotent operation: running twice has no further effect
"""
import os
import uuid
import tkinter as tk
from tkinter import filedialog, messagebox


def capitalize_first_letter(name: str) -> str:
    """
    Capitalize only the first character of `name`, leaving the rest intact.
    Empty strings are returned unchanged to prevent index errors.
    """
    # Use idiomatic slicing plus conditional guard
    return name[0].upper() + name[1:] if name else name


def safe_rename(old_path: str, new_path: str):
    """
    Perform a robust rename that works on case-insensitive filesystems.

    On Windows/macOS, renaming 'foo.txt' to 'Foo.txt' directly is a no-op.
    We break the operation into two steps via a UUID-based temporary filename,
    guaranteeing the rename takes effect.
    """
    # Compare normalized paths for case-only differences
    if os.path.normcase(old_path) == os.path.normcase(new_path):
        dirpath = os.path.dirname(old_path)
        # Generate a cryptographically random fallback name
        temp_name = str(uuid.uuid4())
        temp_path = os.path.join(dirpath, temp_name)
        os.rename(old_path, temp_path)
        os.rename(temp_path, new_path)
    else:
        # On case-sensitive FS or full name change, a single rename suffices
        os.rename(old_path, new_path)


def rename_items_in_dir(path: str):
    """
    Recursively traverse `path` bottom-up and rename each entry so its
    basename starts with an uppercase letter.

    Raises:
        NotADirectoryError: if `path` is not a valid directory.
    """
    if not os.path.isdir(path):
        raise NotADirectoryError(f"Not a directory: {path}")

    # Bottom-up ensures children renamed before their parent directory
    for root, dirs, files in os.walk(path, topdown=False):
        # Iterate files first
        for fname in files:
            new_fname = capitalize_first_letter(fname)
            if new_fname != fname:
                old_path = os.path.join(root, fname)
                new_path = os.path.join(root, new_fname)
                # Skip genuine collisions, but allow case-only changes
                if os.path.exists(new_path) and not os.path.normcase(old_path) == os.path.normcase(new_path):
                    print(f"[WARN] Skipping {old_path}: '{new_fname}' already exists")
                else:
                    safe_rename(old_path, new_path)
        # Then directories
        for dname in dirs:
            new_dname = capitalize_first_letter(dname)
            if new_dname != dname:
                old_path = os.path.join(root, dname)
                new_path = os.path.join(root, new_dname)
                if os.path.exists(new_path) and not os.path.normcase(old_path) == os.path.normcase(new_path):
                    print(f"[WARN] Skipping {old_path}: '{new_dname}' already exists")
                else:
                    safe_rename(old_path, new_path)


def run():
    """
    Entry point for the GUI. Reads the path from the user, invokes
    renaming logic, and reports success/errors via dialogs.
    """
    path = entry.get().strip()
    if not path:
        messagebox.showerror("Error", "Please enter or select a directory path.")
        return
    try:
        rename_items_in_dir(path)
        messagebox.showinfo("Done", f"Capitalization complete in:\n{path}")
    except Exception as e:
        # Bubble up unexpected errors for diagnostics
        messagebox.showerror("Error", str(e))


def browse():
    """
    Open a native directory-selection dialog and populate the entry field.
    """
    selected = filedialog.askdirectory()
    if selected:
        entry.delete(0, tk.END)
        entry.insert(0, selected)


# --- GUI Initialization ---
root = tk.Tk()
root.title("Capitalize First Letters")

# Padding frame for neat layout
frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

# Directory input label + entry
tk.Label(frame, text="Directory Path:").grid(row=0, column=0, sticky="w")
entry = tk.Entry(frame, width=50)
entry.grid(row=0, column=1, padx=(5,0))

# Browse button
browse_btn = tk.Button(frame, text="Browse...", command=browse)
browse_btn.grid(row=0, column=2, padx=(5,0))

# Execute button
run_btn = tk.Button(frame, text="Run", width=10, command=run)
run_btn.grid(row=1, column=1, pady=(10,0))

# Enter main event loop
root.mainloop()

# To build an executable with PyInstaller:
# 1. Install: pip install pyinstaller
# 2. Run: pyinstaller --onefile --windowed FirstCapitaliser.py
#    - --onefile bundles into a single exe
#    - --windowed hides the console on Windows