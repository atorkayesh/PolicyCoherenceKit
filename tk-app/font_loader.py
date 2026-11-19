# =============================================================================
# font_loader.py
# Registers the bundled Inter font files so tkinter can use "Inter" by name.
# Must be called before the Tk root window is created.
# =============================================================================

import os
import sys
import shutil

_FONTS_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")

_FONT_FILES = [
    "Inter-Regular.ttf",
    "Inter-Medium.ttf",
    "Inter-Bold.ttf",
    "Inter-Italic.ttf",
]


def load_inter():
    """Register Inter with the OS font system for the current session."""
    if sys.platform == "darwin":
        _load_macos()
    elif sys.platform == "win32":
        _load_windows()
    else:
        _load_linux()


# -----------------------------------------------------------------------------
# macOS — copy to ~/Library/Fonts (skips files already present)
# -----------------------------------------------------------------------------

def _load_macos():
    dest_dir = os.path.expanduser("~/Library/Fonts")
    os.makedirs(dest_dir, exist_ok=True)
    for fname in _FONT_FILES:
        src  = os.path.join(_FONTS_DIR, fname)
        dest = os.path.join(dest_dir, fname)
        if not os.path.exists(dest):
            shutil.copy2(src, dest)


# -----------------------------------------------------------------------------
# Windows — temporarily add fonts for this process via GDI
# -----------------------------------------------------------------------------

def _load_windows():
    import ctypes
    gdi = ctypes.windll.gdi32
    for fname in _FONT_FILES:
        path = os.path.join(_FONTS_DIR, fname)
        gdi.AddFontResourceExW(path, 0x10, 0)   # FR_PRIVATE = 0x10


# -----------------------------------------------------------------------------
# Linux — copy to ~/.local/share/fonts and refresh font cache
# -----------------------------------------------------------------------------

def _load_linux():
    import subprocess
    dest_dir = os.path.expanduser("~/.local/share/fonts")
    os.makedirs(dest_dir, exist_ok=True)
    copied = False
    for fname in _FONT_FILES:
        src  = os.path.join(_FONTS_DIR, fname)
        dest = os.path.join(dest_dir, fname)
        if not os.path.exists(dest):
            shutil.copy2(src, dest)
            copied = True
    if copied:
        subprocess.call(["fc-cache", "-f"], stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
