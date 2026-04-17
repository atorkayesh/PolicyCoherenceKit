# =============================================================================
# Policy Coherence Kit -- main.py
# Standalone entry point. Run with:  python main.py
# =============================================================================

import os
import sys
import subprocess

# CRITICAL: Enable DPI awareness BEFORE importing tkinter
# This must happen before any GUI code is loaded
if sys.platform == "win32":
    try:
        import ctypes
        # Try Windows 10 1703+ Per-Monitor V2 (best quality)
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            # Fallback: Windows 8.1+ Per-Monitor V1
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                # Fallback: Vista+ System DPI Aware
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

import tkinter as tk
from font_loader import load_inter
from app import PolicyCoherenceApp


def _focus_window(root: tk.Tk):
    """Bring the window to the front on any platform."""
    if sys.platform == "darwin":
        subprocess.call([
            "osascript", "-e",
            f'tell application "System Events" to set frontmost of the first process'
            f' whose unix id is {os.getpid()} to true',
        ])
    elif sys.platform == "win32":
        root.lift()
        root.focus_force()
    else:
        # Linux / other
        root.lift()
        root.attributes("-topmost", True)
        root.after(200, lambda: root.attributes("-topmost", False))


def main():
    load_inter()
    root = tk.Tk()

    # On Windows, set proper Tk scaling for high-DPI displays
    if sys.platform == "win32":
        try:
            from ctypes import windll
            root.update_idletasks()
            # Get the DPI for the window
            hwnd = windll.user32.GetParent(root.winfo_id())
            dpi = windll.user32.GetDpiForWindow(hwnd)
            if dpi == 0:
                dpi = windll.user32.GetDpiForSystem()
            # Scale Tk widgets accordingly (96 DPI = 1.0 scaling)
            scale_factor = dpi / 96.0
            root.tk.call('tk', 'scaling', scale_factor)
        except Exception:
            pass

    PolicyCoherenceApp(root)
    root.after(100, lambda: _focus_window(root))
    root.mainloop()


if __name__ == "__main__":
    main()
