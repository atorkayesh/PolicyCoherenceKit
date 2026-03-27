# =============================================================================
# Policy Coherence Kit -- main.py
# Standalone entry point. Run with:  python main.py
# =============================================================================

import tkinter as tk
from app import PolicyCoherenceApp

def main():
    root = tk.Tk()
    PolicyCoherenceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
