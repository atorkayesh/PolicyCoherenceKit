# =============================================================================
# Policy Coherence Kit -- main.py
# Standalone entry point. Run with:  python main.py
# =============================================================================

import os
import sys
import subprocess
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
    PolicyCoherenceApp(root)
    root.after(100, lambda: _focus_window(root))
    root.mainloop()


if __name__ == "__main__":
    main()
