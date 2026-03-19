# =============================================================================
# Policy Coherence Kit -- __init__.py
# Package entry point. Exposes PolicyCoherenceApp and the run() launcher.
# =============================================================================

from .app import PolicyCoherenceApp

__version__ = "0.1.0"
__all__     = ["PolicyCoherenceApp", "run"]


def run():
    """Launch the Policy Coherence Kit desktop application."""
    import tkinter as tk
    root = tk.Tk()
    PolicyCoherenceApp(root)
    root.mainloop()
