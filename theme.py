# Theme — colors, typography, spacing, and other design tokens

# ── Sidebar: Project title (app name) ────────────────────────────────────────
PROJECT_TITLE_COLOR     = "#1f2937"
PROJECT_TITLE_TEXT_SIZE = 20          # pt
SIDEBAR_HEADER_HEIGHT   = 90          # px — fixed height of the title/slogan section (expanded and collapsed)

# ── Sidebar: Slogan ───────────────────────────────────────────────────────────
SLOGAN_COLOR     = "#a3a3a3"
SLOGAN_TEXT_SIZE = 10                 # pt

# ── Sidebar: "PROJECTS" label ─────────────────────────────────────────────────
PROJECTS_COLOR     = "#a3a3a3"
PROJECTS_TEXT_SIZE = 9                # pt  (FONT_SIZE_SMALL, bold)

# ── Sidebar: Empty state (no projects) ────────────────────────────────────────
EMPTY_STATE_COLOR     = "#a3a3a3"
EMPTY_STATE_TEXT_SIZE = 11            # pt

# ── Sidebar: Project name rows ────────────────────────────────────────────────
PROJ_NAME_COLOR     = "#2c3b4e"
PROJ_NAME_TEXT_SIZE = 14              # pt

# ── Sidebar: DM name rows ─────────────────────────────────────────────────────
DM_NAME_COLOR     = "#426387"
DM_NAME_TEXT_SIZE = 13                # pt

# ── Sidebar: Icons (chevron + folder) ────────────────────────────────────────
ICONS_COLOR        = "#a3a3a3"
ICONS_STROKE_WIDTH = 1.35

# ── Sidebar: DM row hover ────────────────────────────────────────────────────
DM_ROW_HOVER_BG    = "#ebebeb"    # "DECISION-MAKERS" button hover bg
DM_NAME_HOVER_BG   = "#eaeef4"   # DM name row hover bg
DM_ROW_HEIGHT      = 20           # vertical padding (pady) inside the DM name rows
DM_BTN_ROW_HEIGHT  = 30           # px — fixed height of the "DECISION-MAKERS" button row
DM_BTN_TEXT_SIZE   = 11           # pt — font size of the "DECISION-MAKERS" label

# ── Sidebar: DM section padding ───────────────────────────────────────────────
DM_SECTION_PADX = 12           # left/right padding on "DECISION-MAKERS" button and DM name rows

# ── Sidebar: "New Project" button ─────────────────────────────────────────────
NEW_PROJECT_BG_NORMAL   = "#eaeef4"
NEW_PROJECT_BG_HOVER    = "#d0dbe7"
NEW_PROJECT_FG          = "#1f2937"
NEW_PROJECT_ICON_COLOR  = "#1f2937"
NEW_PROJECT_ICON_STROKE = 1.35
NEW_PROJECT_ICON_SIZE   = 18          # px (scaled from 24×24 viewBox)
NEW_PROJECT_HEIGHT      = 40          # px
NEW_PROJECT_RADIUS      = 5           # px — border radius

# ── Border radii ───────────────────────────────────────────────────────────────
RADIUS_NEW_PROJECT_BTN  = 5     # "New Project" canvas button
RADIUS_TOOLBAR_BTN      = 4     # Export / Import / Aggregate toolbar buttons
RADIUS_PROJECT_HEADER   = 0     # Project header bar (flat, full-width)
RADIUS_DM_ROW           = 4     # Decision-maker hover rows
RADIUS_DIALOG           = 6     # Modal dialogs (e.g. New Project name dialog)

# ── Sidebar: collapsed state ──────────────────────────────────────────────────
SIDEBAR_EXPANDED_WIDTH    = 320          # px
SIDEBAR_COLLAPSED_WIDTH   = 80           # px

# PCK badge (shown in header when sidebar is collapsed)
PCK_BADGE_BG      = "#1f2937"
PCK_BADGE_FG      = "#f5f7fa"
PCK_BADGE_RADIUS  = 6                    # px
PCK_BADGE_PADDING = 7                    # px — inner padding on each side
PCK_BADGE_TEXT    = "PCK"
PCK_BADGE_TEXT_SIZE = 12                 # pt, bold

# Project name badge (shown per project when sidebar is collapsed)
PROJ_BADGE_BG      = "#426387"
PROJ_BADGE_FG      = "#f5f7fa"
PROJ_BADGE_RADIUS  = 5                   # px
PROJ_BADGE_PADDING = 3                   # px — inner padding on each side
PROJ_BADGE_TEXT_SIZE = 9                 # pt
PROJ_BADGE_WORDS   = 2                   # number of words from project name to show

# Collapsed bottom "+" icon
COLLAPSED_PLUS_COLOR       = "#a3a3a3"
COLLAPSED_PLUS_STROKE      = 1.5
COLLAPSED_PLUS_CANVAS_SIZE = 28          # px

# ── Top bar ───────────────────────────────────────────────────────────────────
TOPBAR_BG              = "#ffffff"
TOPBAR_HEIGHT          = 70           # px — fixed height of the top bar
TOPBAR_DIVIDER_COLOR   = "#e6e6e6"   # 1px separator below the top bar
TOPBAR_PADX            = 20          # px — left/right edge padding

# Project name (left, top line)
TOPBAR_PROJECT_NAME_COLOR     = "#2c3b4e"
TOPBAR_PROJECT_NAME_TEXT_SIZE = 12          # pt, bold

# Stats line (left, below project name)
TOPBAR_STATS_DM_COLOR       = "#7799b9"   # dm name color
TOPBAR_STATS_TEXT_COLOR     = "#a3a3a3"   # policies / cells text color
TOPBAR_STATS_SEP_COLOR      = "#808080"   # . and | separators
TOPBAR_STATS_TEXT_SIZE      = 9           # pt

# Button shared styles (flat tk.Button — Export, Import, Delete, Rename)
TOPBAR_BTN_BG          = "#ffffff"   # matches topbar bg
TOPBAR_BTN_HOVER_BG    = "#f5f7fa"   # subtle grey on hover
TOPBAR_BTN_PADX        = 10          # px — horizontal inner padding
TOPBAR_BTN_PADY        = 5           # px — vertical inner padding

# Run Analysis button (canvas rounded button)
TOPBAR_RUN_ANALYSIS_BG          = "#2c3b4e"   # dark navy
TOPBAR_RUN_ANALYSIS_HOVER_BG    = "#37506d"   # lighter navy on hover
TOPBAR_RUN_ANALYSIS_FG          = "#f5f7fa"   # icon + text color
TOPBAR_RUN_ANALYSIS_HEIGHT      = 33          # px
TOPBAR_RUN_ANALYSIS_RADIUS      = 5           # px — corner radius
TOPBAR_RUN_ANALYSIS_ICON_SIZE   = 11          # px (Lucide play path, scaled from 24×24 viewBox)
TOPBAR_RUN_ANALYSIS_ICON_STROKE = 1.35        # SVG stroke-width
TOPBAR_RUN_ANALYSIS_ICON_COLOR  = "#f5f7fa"  # icon stroke color
TOPBAR_RUN_ANALYSIS_ICON_GAP    = 7           # px — gap between icon and label
TOPBAR_RUN_ANALYSIS_PADX        = 18          # px — left/right inner padding
TOPBAR_RUN_ANALYSIS_TEXT_SIZE   = 11          # pt, regular weight
# Icon SVG path (Lucide play): rendered via cairosvg at runtime
# M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z

# Export / Import Excel buttons (canvas rounded buttons, shared design)
TOPBAR_EXCEL_BG          = "#f5f7fa"
TOPBAR_EXCEL_HOVER_BG    = "#eaeef4"
TOPBAR_EXCEL_BORDER      = "#eaeef4"
TOPBAR_EXCEL_FG          = "#2c3b4e"   # icon + text color
TOPBAR_EXCEL_HEIGHT      = 33          # px — matches Run Analysis height
TOPBAR_EXCEL_RADIUS      = 5           # px
TOPBAR_EXCEL_ICON_SIZE   = 14          # px (Lucide file-up/file-down, 24×24 viewBox)
TOPBAR_EXCEL_ICON_STROKE = 1.35
TOPBAR_EXCEL_ICON_GAP    = 7           # px — gap between icon and label
TOPBAR_EXCEL_PADX        = 16          # px — left/right inner padding
TOPBAR_EXCEL_TEXT_SIZE   = 11          # pt
TOPBAR_EXCEL_PADX        = 20          # px — increased for wider buttons (was 16)
# Export icon: Lucide file-up   — arrow pointing up inside document
# Import icon: Lucide file-down — arrow pointing down inside document

# Rename Tab button (canvas, same design as Import/Export)
TOPBAR_RENAME_TAB_FG   = "#2c3b4e"   # icon + text color (= TOPBAR_EXCEL_FG)
# Rename icon: Lucide pencil

# Delete Tab button (canvas, same design as Import/Export)
TOPBAR_DELETE_TAB_FG   = "#DC2626"   # danger red — icon + text color
# Delete icon: Lucide trash

# Button order (left → right): Rename Tab | Delete Tab | sep | Import Excel | Export Excel | sep | Run Analysis

# Vertical separators between button groups
TOPBAR_SEP_COLOR       = "#e6e6e6"
TOPBAR_SEP_WIDTH       = 1           # px
TOPBAR_SEP_PADY        = 8           # px — top/bottom inset so separator doesn't span full height
TOPBAR_SEP_PADX        = 6           # px — horizontal gap around each separator

# ── Empty state — instruction panel (shown when no project exists) ────────────
EMPTY_STATE_PANEL_WIDTH       = 500          # px — fixed panel width
EMPTY_STATE_BADGE_SIZE        = 58           # px — icon badge square
EMPTY_STATE_BADGE_BG          = "#eaeef4"   # badge background
EMPTY_STATE_BADGE_RADIUS      = 8           # px — badge corner radius
EMPTY_STATE_ICON_SIZE         = 26          # px — network icon inside badge
EMPTY_STATE_ICON_COLOR        = "#30455c"   # icon stroke color
EMPTY_STATE_ICON_STROKE       = 1.6         # stroke-width
EMPTY_STATE_TITLE_COLOR       = "#1f2937"
EMPTY_STATE_TITLE_SIZE        = 23          # pt
EMPTY_STATE_SUBTITLE_COLOR    = "#808080"
EMPTY_STATE_SUBTITLE_SIZE     = 12          # pt
EMPTY_STATE_WORKFLOW_BG            = "#fafbfc"
EMPTY_STATE_WORKFLOW_BORDER        = "#f5f7fa"
EMPTY_STATE_WORKFLOW_RADIUS        = 6           # px — border radius
EMPTY_STATE_WORKFLOW_PADX          = 28          # px — inner horizontal padding
EMPTY_STATE_WORKFLOW_PADY          = 26          # px — inner vertical padding
EMPTY_STATE_WORKFLOW_SHADOW_COLOR  = "#e8eaed"
EMPTY_STATE_WORKFLOW_SHADOW_OFFSET = 1.25        # px
EMPTY_STATE_WORKFLOW_LBL_COLOR     = "#a3a3a3"
EMPTY_STATE_WORKFLOW_LBL_SIZE      = 12          # pt
EMPTY_STATE_WORKFLOW_STEP_BG       = "#ffffff"
EMPTY_STATE_WORKFLOW_STEP_BORDER   = "#f5f5f5"
EMPTY_STATE_WORKFLOW_STEP_RADIUS   = 4           # px
EMPTY_STATE_WORKFLOW_STEP_HEIGHT   = 55          # px
EMPTY_STATE_WORKFLOW_STEP_GAP      = 8           # px between steps
EMPTY_STATE_WORKFLOW_STEP_NUM_COLOR = "#d3d3d3"
EMPTY_STATE_WORKFLOW_STEP_NUM_SIZE  = 10         # pt
EMPTY_STATE_WORKFLOW_STEP_COLOR    = "#1f2937"
EMPTY_STATE_WORKFLOW_STEP_SIZE     = 13          # pt
EMPTY_STATE_BTN_BG            = "#426387"
EMPTY_STATE_BTN_HOVER         = "#30455c"
EMPTY_STATE_BTN_FG            = "#eaeef4"
EMPTY_STATE_BTN_HEIGHT        = 40          # px
EMPTY_STATE_BTN_RADIUS        = 4           # px
EMPTY_STATE_BTN_ICON_SIZE     = 16          # px
EMPTY_STATE_BTN_TEXT_SIZE     = 11          # pt

# ── View switcher pill toggle (Decision Makers / Analysis) ───────────────────
# ── View switcher pill toggle (Decision Makers / Analysis) ───────────────────
# Pill colours
VIEW_TOGGLE_TRACK_BG     = "#a6bcd3"   # outer pill background
VIEW_TOGGLE_THUMB_BG     = "#e8eef4"   # active-side floating thumb
VIEW_TOGGLE_ACT_FG       = "#30455c"   # icon colour on active (thumb) side
VIEW_TOGGLE_INACT_FG     = "#ffffff"   # icon colour on inactive (track) side

# Pill geometry
VIEW_TOGGLE_PILL_HEIGHT  = 30          # px — overall pill height
VIEW_TOGGLE_PILL_RADIUS  = 15          # px — corner radius (= height/2 → full pill)
VIEW_TOGGLE_THUMB_PAD    = 3           # px — gap between track edge and thumb
VIEW_TOGGLE_MARGIN       = 1           # px — extra canvas margin so edge arcs aren't clipped
VIEW_TOGGLE_ICON_SIZE    = 16          # px — icon drawing area (scaled from 24×24 viewBox)
VIEW_TOGGLE_SEG_PADDING  = 28          # px — total horizontal padding around icon in each segment
VIEW_TOGGLE_ICON_STROKE  = 1.4        # stroke-width for both icons

# Bar that hosts the toggle
VIEW_TOGGLE_BAR_BG       = "#ffffff"   # switcher bar background
VIEW_TOGGLE_BAR_HEIGHT   = 46          # px — switcher bar height
VIEW_TOGGLE_BAR_SEP      = "#e8eaed"   # 1px separator below the bar
VIEW_TOGGLE_BAR_PADX     = 12          # px — right margin between toggle and window edge

# Tooltip
VIEW_TOGGLE_TIP_BG       = "#2c3b4e"   # tooltip background
VIEW_TOGGLE_TIP_FG       = "#ffffff"   # tooltip text colour
VIEW_TOGGLE_TIP_SIZE     = 10          # pt — tooltip font size
VIEW_TOGGLE_TIP_PADX     = 8           # px — tooltip horizontal inner padding
VIEW_TOGGLE_TIP_PADY     = 4           # px — tooltip vertical inner padding
VIEW_TOGGLE_TIP_OFFSET_Y = 6           # px — gap between pill bottom and tooltip top

# ── Status bar ("Ready") — bottom of notebook content area ───────────────────
STATUSBAR_BG        = "#f5f7fa"   # background
STATUSBAR_FG        = "#a6bcd3"   # text color
STATUSBAR_TEXT_SIZE = 11          # pt
STATUSBAR_HEIGHT    = 27          # px

# ── Misc ──────────────────────────────────────────────────────────────────────
BG_COLOR        = "#ffffff"   # main content background
SIDEBAR_BG      = "#fafbfc"   # sidebar background
COLOR_ERROR     = "#DC2626"   # main error / danger red
GREY            = "#808080"
DIVIDER_COLOR   = "#e6e6e6"
MAIN_COLOR      = "#1F2937"

# ── Sidebar: logo badge ───────────────────────────────────────────────────────
LOGO_BADGE_BG      = "#1f2937"   # dark badge background
LOGO_BADGE_FG      = "#f5f7fa"   # icon color
LOGO_BADGE_SIZE    = 35          # px — badge square
LOGO_BADGE_RADIUS  = 5           # px — corner radius
LOGO_ICON_SIZE     = 17          # px — icon drawing area inside badge
LOGO_ICON_PAD      = 9           # px — padding around icon
# Icon: Lucide waypoints (4 circles at N/S/E/W connected by lines)



