# =============================================================================
# Policy Coherence Kit -- constants.py
# All application-wide constants: ratings, colours, fonts, dimensions.
# =============================================================================

# -----------------------------------------------------------------------------
# Coherence rating vocabulary (order: most synergistic -> most conflicting)
# -----------------------------------------------------------------------------
COHERENCE_RATINGS = [
    "Indivisible",
    "Reinforcing",
    "Enabling",
    "Neutral",
    "Constraining",
    "Counteracting",
    "Cancelling",
]

DIAGONAL_VALUE = "Neutral"   # diagonal cells are always locked to this

# -----------------------------------------------------------------------------
# Colour coding per rating
# Background fill colour for matrix cells (hex strings)
# -----------------------------------------------------------------------------
RATING_COLORS = {
    "Indivisible":   "#1a6e3c",  # deep green
    "Reinforcing":   "#4caf7d",  # medium green
    "Enabling":      "#a8d5b5",  # light green
    "Neutral":       "#d9d9d9",  # neutral grey
    "Constraining":  "#f5c07a",  # light amber
    "Counteracting": "#e07b39",  # orange-red
    "Cancelling":    "#b71c1c",  # deep red
}

# Foreground (text) colour for each rated cell
RATING_TEXT_COLORS = {
    "Indivisible":   "#ffffff",
    "Reinforcing":   "#ffffff",
    "Enabling":      "#2d2d2d",
    "Neutral":       "#555555",
    "Constraining":  "#2d2d2d",
    "Counteracting": "#ffffff",
    "Cancelling":    "#ffffff",
}

# -----------------------------------------------------------------------------
# Application window
# -----------------------------------------------------------------------------
APP_TITLE         = "Policy Coherence Kit"
WINDOW_MIN_WIDTH  = 900
WINDOW_MIN_HEIGHT = 600

# -----------------------------------------------------------------------------
# Typography
# -----------------------------------------------------------------------------
FONT_FAMILY      = "Helvetica"
FONT_SIZE_SMALL  = 9
FONT_SIZE_NORMAL = 10
FONT_SIZE_HEADER = 11
FONT_SIZE_TITLE  = 14

# -----------------------------------------------------------------------------
# Matrix cell dimensions (in Tk character units)
# -----------------------------------------------------------------------------
CELL_WIDTH   = 14   # width of each data cell
HEADER_WIDTH = 14   # width of row/column header labels

# -----------------------------------------------------------------------------
# Application colour palette
# -----------------------------------------------------------------------------
COLOR_BG         = "#f4f1ec"   # warm off-white -- main background
COLOR_PANEL      = "#eae7e0"   # slightly darker -- toolbar / info bars
COLOR_ACCENT     = "#2c4a6e"   # deep navy -- headers, buttons, active tabs
COLOR_ACCENT2    = "#5a7fa8"   # lighter navy -- secondary actions
COLOR_TEXT       = "#1e1e1e"   # near-black -- body text
COLOR_TEXT_LIGHT = "#666666"   # muted -- hints, labels, subtitles
COLOR_BORDER     = "#c8c4bc"   # dividers and separators
COLOR_TAB_BG     = "#d8d4cd"   # inactive notebook tab background
COLOR_BUTTON     = "#2c4a6e"   # primary button fill (= COLOR_ACCENT)
COLOR_BUTTON_FG  = "#ffffff"   # primary button text
COLOR_DANGER     = "#b71c1c"   # destructive actions (remove, delete)

# Numeric score for each coherence rating (used for aggregation)
RATING_SCORES = {
    "Indivisible":   3,
    "Reinforcing":   2,
    "Enabling":      1,
    "Neutral":       0,
    "Constraining": -1,
    "Counteracting": -2,
    "Cancelling":   -3,
}
