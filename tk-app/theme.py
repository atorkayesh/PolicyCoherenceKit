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
NEW_PROJECT_HEIGHT      = 35          # px
NEW_PROJECT_RADIUS      = 5           # px — border radius

# ── Border radii ───────────────────────────────────────────────────────────────
RADIUS_NEW_PROJECT_BTN  = 5     # "New Project" canvas button
RADIUS_TOOLBAR_BTN      = 4     # Export / Import / Aggregate toolbar buttons
RADIUS_PROJECT_HEADER   = 0     # Project header bar (flat, full-width)
RADIUS_DM_ROW           = 4     # Decision-maker hover rows
RADIUS_DIALOG           = 8     # Modal dialogs (e.g. New Project name dialog)

# ── Modal dialog ───────────────────────────────────────────────────────────────
MODAL_BG                 = "#eaeef4"   # modal background
MODAL_BORDER             = "#d0dbe7"   # modal border / outline
MODAL_RADIUS             = 11          # corner radius (px)
MODAL_TITLE_COLOR        = "#1f2937"
MODAL_TITLE_SIZE         = 22
MODAL_SUBTITLE_COLOR     = "#a3a3a3"
MODAL_SUBTITLE_SIZE      = 10
MODAL_CLOSE_ICON_COLOR   = "#a3a3a3"
MODAL_CLOSE_HOVER_BG     = "#dfe5ec"
MODAL_CLOSE_CANVAS_SIZE  = 32
MODAL_CLOSE_ICON_SIZE    = 10
MODAL_CLOSE_STROKE       = 1.4
MODAL_CLOSE_HOVER_RADIUS = 11
MODAL_DIVIDER_COLOR      = "#d3d3d3"
MODAL_SECTION_TITLE_COLOR = "#2c3b4e"
MODAL_SECTION_TITLE_SIZE  = 11
MODAL_SECTION_HINT_COLOR  = "#a3a3a3"
MODAL_SECTION_HINT_SIZE   = 10
MODAL_SECTION_ROW_GAP     = 4
MODAL_ADD_BTN_BG          = "#f5f7fa"
MODAL_ADD_BTN_HOVER_BG    = "#fafafa"
MODAL_ADD_BTN_ICON_COLOR  = "#30455c"
MODAL_ADD_BTN_BORDER      = "#e6e6e6"
MODAL_ADD_BTN_WIDTH       = 70
MODAL_ADD_BTN_HEIGHT      = 30
MODAL_ADD_BTN_RADIUS      = 5
MODAL_ADD_BTN_ICON_SIZE   = 9
MODAL_ADD_BTN_GAP         = 6
MODAL_ADD_BTN_STROKE      = 1.35
MODAL_ADD_BTN_TEXT        = "Add"
MODAL_ADD_BTN_TEXT_SIZE   = 10
MODAL_ACTION_BG          = "#ffffff"
MODAL_ACTION_HOVER_BG    = "#f3f4f6"
MODAL_ACTION_BORDER      = "#eaeef4"
MODAL_ACTION_FG          = "#2c3b4e"
MODAL_ACTION_HEIGHT      = 33
MODAL_ACTION_RADIUS      = 5
MODAL_ACTION_ICON_SIZE   = 14
MODAL_ACTION_GAP         = 7
MODAL_ACTION_PADX        = 24
MODAL_ACTION_TEXT_SIZE   = 11
MODAL_ACTION_IMPORT_TEXT = "Import from excel"
MODAL_FIELD_LABEL_COLOR  = "#2c3b4e"
MODAL_FIELD_LABEL_SIZE   = 11
MODAL_FIELD_BG           = "#ffffff"
MODAL_FIELD_BORDER       = "#e6e6e6"
MODAL_FIELD_HEIGHT       = 35
MODAL_FIELD_RADIUS       = 4
MODAL_FIELD_TEXT_SIZE    = 11
MODAL_FIELD_PLACEHOLDER  = "e.g. EU Clean Mobility Policy Coherence Assessment"
MODAL_FIELD_PLACEHOLDER_COLOR = "#d3d3d3"
MODAL_FIELD_PLACEHOLDER_SIZE  = 10
MODAL_PROJECT_HINT       = "Use a clear descriptive title for this project."
MODAL_DM_HINT            = "Add one or more decision-maker names."
MODAL_POLICY_HINT        = "Add at least 2 policy names."
MODAL_DM_PLACEHOLDER     = "e.g. Expert A"
MODAL_POLICY_PLACEHOLDER = "e.g. Policy 1"

# ── Sidebar: collapsed state ──────────────────────────────────────────────────
SIDEBAR_EXPANDED_WIDTH    = 380          # px
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
TOPBAR_EXCEL_PADX        = 20          # px — left/right inner padding
TOPBAR_EXCEL_TEXT_SIZE   = 11          # pt
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

# ── Results insights cards ────────────────────────────────────────────────────
RESULTS_CARD_BG            = "#ffffff"
RESULTS_CARD_BORDER        = "#d9d5ce"
RESULTS_CARD_RADIUS        = 6
RESULTS_CARD_INSET         = 2
RESULTS_CARD_GAP           = 18
RESULTS_SCATTER_BG         = "#fbfcfd"
RESULTS_SCATTER_BORDER     = "#e2e6ea"
RESULTS_SCATTER_AXIS       = "#90a0ad"
RESULTS_SCATTER_GUIDE      = "#d4dbe1"
RESULTS_SCATTER_LABEL      = "#9aa6b2"
RESULTS_SOFT_BG            = "#f7f8fa"
RESULTS_SOFT_BORDER        = "#eef0f2"
RESULTS_TEAL_BAR           = "#2b7a78"
RESULTS_BANNER_BG          = "#eaeef4"
RESULTS_BANNER_BORDER      = "#d8e5f2"
RESULTS_BANNER_LEFT_BG     = "#fffbeb"
RESULTS_BANNER_RIGHT_BG    = "#eef2ff"
RESULTS_BANNER_TITLE_COLOR = "#2c3b4e"
RESULTS_BANNER_TITLE_SIZE  = 30
RESULTS_BANNER_TEXT_COLOR  = "#37506d"
RESULTS_BANNER_TEXT_SIZE   = 15
RESULTS_BANNER_EMPH_COLOR  = "#1f2937"
RESULTS_BANNER_RELATION_COLOR = "#30455c"
RESULTS_BANNER_SUPPORTING_WRAP = 540
RESULTS_BANNER_OUTER_PADX  = 30
RESULTS_BANNER_OUTER_PADY  = 30
RESULTS_BANNER_COLUMN_GAP  = 24
RESULTS_BANNER_TITLE_GAP   = 16
RESULTS_BANNER_TEXT_GAP    = 14
RESULTS_BANNER_SUPPORTING_BOTTOM = 40
RESULTS_BANNER_INTERPRETATION_LABEL = "#30455c"
RESULTS_BANNER_INTERPRETATION_TEXT  = "#426387"
RESULTS_BANNER_STATS_PADX  = 24
RESULTS_BANNER_STATS_TOP   = 24
RESULTS_BANNER_STATS_GAP   = 10
RESULTS_BANNER_STATS_BOTTOM = 24
RESULTS_BANNER_META_HEIGHT = 50
RESULTS_BANNER_META_RADIUS = 4

# ── Coherence Scores page ────────────────────────────────────────────────────
COHERENCE_SCORES_METRIC_COLOR       = "#1f2937"
COHERENCE_SCORES_METRIC_SIZE        = 11
COHERENCE_SCORES_DESC_COLOR         = "#a3a3a3"
COHERENCE_SCORES_DESC_SIZE          = 12
COHERENCE_SCORES_LEGEND_TOP_PADY    = 2
COHERENCE_SCORES_LEGEND_PADX_LEFT   = 28
COHERENCE_SCORES_LEGEND_ROW_GAP     = 13
COHERENCE_SCORES_LEGEND_LABEL_WIDTH = 5
COHERENCE_SCORES_LEGEND_TEXT_GAP    = 10
COHERENCE_SCORES_DIVIDER_PADY_TOP   = 12
COHERENCE_SCORES_DIVIDER_PADY_BOTTOM = 20
COHERENCE_SCORES_TABLE_PADX         = 16
COHERENCE_SCORES_TABLE_PADY_BOTTOM  = 16
COHERENCE_SCORES_TABLE_SCROLL_GAP   = 10
COHERENCE_SCORES_SCROLL_STEP        = 0.12
COHERENCE_SCORES_SCROLL_DECAY       = 0.82
COHERENCE_SCORES_SCROLL_CUTOFF      = 0.0002
COHERENCE_SCORES_SCROLL_FRAME_MS    = 16
COHERENCE_SCORES_POLICY_COL_MIN     = 110
COHERENCE_SCORES_OI_COL_MIN         = 90
COHERENCE_SCORES_II_COL_MIN         = 90
COHERENCE_SCORES_WOI_COL_MIN        = 110
COHERENCE_SCORES_WII_COL_MIN        = 110
COHERENCE_SCORES_FULL_NAME_COL_MIN  = 420
COHERENCE_SCORES_TABLE_CELL_GAP     = 1
COHERENCE_SCORES_TABLE_HEADER_BG    = "#426387"
COHERENCE_SCORES_TABLE_HEADER_FG    = "#f5f7fa"
COHERENCE_SCORES_TABLE_HEADER_PADY  = 10
COHERENCE_SCORES_TABLE_HEADER_SIZE  = 10
COHERENCE_SCORES_TABLE_ROW_EVEN_BG  = "#f5f7fa"
COHERENCE_SCORES_TABLE_ROW_ODD_BG   = "#eaeef4"
COHERENCE_SCORES_TABLE_BODY_FG      = "#374151"
COHERENCE_SCORES_TABLE_POLICY_FG    = "#1f2937"
COHERENCE_SCORES_TABLE_BODY_PADY    = 11
COHERENCE_SCORES_TABLE_BORDER       = "#e5e7eb"
RESULTS_BANNER_META_TEXT_SIZE = 11
RESULTS_BANNER_STAT_HEIGHT_DELTA = 8
RESULTS_BANNER_TAG_HEIGHT  = 35
RESULTS_BANNER_TAG_RADIUS  = 4
RESULTS_BANNER_TAG_TEXT_SIZE = 10
RESULTS_BANNER_TAG_TOP_DRIVER_BG = "#DCFCE7"
RESULTS_BANNER_TAG_TOP_DRIVER_FG = "#166534"
RESULTS_BANNER_TAG_STRONGEST_BG  = "#DBEAFE"
RESULTS_BANNER_TAG_STRONGEST_FG  = "#1E40AF"
RESULTS_BANNER_TAG_CONTESTED_BG  = "#FEE2E2"
RESULTS_BANNER_TAG_CONTESTED_FG  = "#991B1B"
RESULTS_BANNER_METHOD_BG   = "#426387"
RESULTS_BANNER_METHOD_FG   = "#f5f7fa"
RESULTS_BANNER_POLICIES_BG = "#059669"
RESULTS_BANNER_POLICIES_FG = "#ecfdf5"
RESULTS_BANNER_DMS_BG      = "#808080"
RESULTS_BANNER_DMS_FG      = "#fafafa"
RESULTS_HEALTH_TITLE_COLOR = "#a3a3a3"
RESULTS_HEALTH_TITLE_SIZE  = 12
RESULTS_HEALTH_VALUE_COLOR = "#426387"
RESULTS_HEALTH_VALUE_SIZE  = 20
RESULTS_HEALTH_LABEL_COLOR = "#a3a3a3"
RESULTS_HEALTH_BAR_BG      = "#f5f5f5"
RESULTS_HEALTH_BAR_HEIGHT  = 4
RESULTS_HEALTH_SYNERGY     = "#15803d"
RESULTS_HEALTH_CONFLICT    = "#b91c1c"
RESULTS_HEALTH_UNCERTAINTY = "#b45309"
RESULTS_TOP_DRIVER_TITLE_COLOR    = "#2c3b4e"
RESULTS_TOP_DRIVER_TITLE_SIZE     = 30
RESULTS_TOP_DRIVER_SUBTITLE_COLOR = "#a3a3a3"
RESULTS_TOP_DRIVER_SUBTITLE_SIZE  = 11
RESULTS_TOP_DRIVER_SUBTITLE_GAP   = 2
RESULTS_TOP_DRIVER_VALUE_COLOR    = "#15803d"
RESULTS_TOP_DRIVER_VALUE_SIZE     = 40
RESULTS_TOP_DEPENDENT_TITLE_COLOR    = "#2c3b4e"
RESULTS_TOP_DEPENDENT_TITLE_SIZE     = 30
RESULTS_TOP_DEPENDENT_SUBTITLE_COLOR = "#a3a3a3"
RESULTS_TOP_DEPENDENT_SUBTITLE_SIZE  = 11
RESULTS_TOP_DEPENDENT_SUBTITLE_GAP   = 2
RESULTS_TOP_DEPENDENT_VALUE_COLOR    = "#b45309"
RESULTS_TOP_DEPENDENT_VALUE_SIZE     = 40
RESULTS_LINK_COLOR         = "#3B82F6"
RESULTS_STRONGEST_LINK_TITLE_COLOR   = "#4f46e5"
RESULTS_STRONGEST_LINK_TITLE_SIZE    = 12
RESULTS_STRONGEST_LINK_MAIN_COLOR    = "#1d4ed8"
RESULTS_STRONGEST_LINK_MAIN_SIZE     = 25
RESULTS_STRONGEST_LINK_VALUE_COLOR   = "#3b82f6"
RESULTS_STRONGEST_LINK_VALUE_SIZE    = 20
RESULTS_STRONGEST_LINK_TEXT_COLOR    = "#a3a3a3"
RESULTS_STRONGEST_LINK_TEXT_SIZE     = 10
RESULTS_CONTESTED_TITLE_COLOR        = "#F59E0B"
RESULTS_CONTESTED_TITLE_SIZE         = 12
RESULTS_CONTESTED_MAIN_COLOR         = "#B45309"
RESULTS_CONTESTED_MAIN_SIZE          = 25
RESULTS_CONTESTED_VALUE_COLOR        = "#D97706"
RESULTS_CONTESTED_VALUE_SIZE         = 20
RESULTS_CONTESTED_TEXT_COLOR         = "#a3a3a3"
RESULTS_CONTESTED_TEXT_SIZE          = 10
RESULTS_CONFLICT_RATIO_TITLE_COLOR   = "#DC2626"
RESULTS_CONFLICT_RATIO_TITLE_SIZE    = 12
RESULTS_CONFLICT_RATIO_MAIN_COLOR    = "#991B1B"
RESULTS_CONFLICT_RATIO_MAIN_SIZE     = 25
RESULTS_CONFLICT_RATIO_VALUE_COLOR   = "#B91C1C"
RESULTS_CONFLICT_RATIO_VALUE_SIZE    = 20
RESULTS_CONFLICT_RATIO_TEXT_COLOR    = "#a3a3a3"
RESULTS_CONFLICT_RATIO_TEXT_SIZE     = 10
RESULTS_AGREEMENT_ACCENT   = "#7C3AED"
RESULTS_CONFIG_PILL_FG     = "#30455c"
RESULTS_PROMINENCE_BAR_BG  = "#e7eef0"
RESULTS_RANKING_BAR_BG     = "#eef2f4"
RESULTS_HEATMAP_BG         = "#fbfcfd"
RESULTS_HEATMAP_DIAGONAL   = "#eef2f6"
RESULTS_CANVAS_LIGHT_TEXT  = "#ffffff"
RESULTS_ON_ACCENT_TEXT     = "#ffffff"
RESULTS_DRIVER             = "#2A9D8F"
RESULTS_DEPENDENT          = "#F4A261"
RESULTS_BALANCED           = "#6B7280"
RESULTS_HEAT_LOW           = "#fef2f2"
RESULTS_HEAT_HIGH          = "#30455c"
RESULTS_SURFACE            = "#f8fafc"
RESULTS_SOFT_RED           = "#fef2f2"
RESULTS_SOFT_GREEN         = "#ecfdf5"
RESULTS_SOFT_ORANGE        = "#fff7ed"
RESULTS_SOFT_BLUE          = "#eff6ff"
RESULTS_SOFT_PURPLE        = "#f5f3ff"
RESULTS_POSITIVE           = "#2A9D8F"
RESULTS_NEGATIVE           = "#C8643B"
RESULTS_MID                = "#E7B34A"

# ── Key Insights Card ─────────────────────────────────────────────────────────
KEY_INSIGHTS_LEFT_BG                    = "#FFFBEB"
KEY_INSIGHTS_RIGHT_BG                   = "#EEF2FF"
KEY_INSIGHTS_BORDER                     = "#d8e5f2"
KEY_INSIGHTS_RADIUS                     = 6
KEY_INSIGHTS_PADDING_X                  = 35
KEY_INSIGHTS_PADDING_Y                  = 35
KEY_INSIGHTS_COLUMN_GAP                 = 24
KEY_INSIGHTS_TITLE_COLOR                = "#2c3b4e"
KEY_INSIGHTS_TITLE_SIZE                 = 30
KEY_INSIGHTS_TEXT_COLOR                 = "#37506d"
KEY_INSIGHTS_TEXT_SIZE                  = 15
KEY_INSIGHTS_EMPH_COLOR                 = "#1f2937"
KEY_INSIGHTS_RELATION_COLOR             = "#30455c"
KEY_INSIGHTS_TITLE_GAP                  = 16
KEY_INSIGHTS_TEXT_GAP                   = 14
KEY_INSIGHTS_SUPPORTING_WRAP            = 540
KEY_INSIGHTS_SUPPORTING_BOTTOM          = 32
KEY_INSIGHTS_INTERPRETATION_LABEL_COLOR = "#30455c"
KEY_INSIGHTS_INTERPRETATION_TEXT_COLOR  = "#426387"
KEY_INSIGHTS_STATS_PADX                 = 24
KEY_INSIGHTS_STATS_TOP                  = 24
KEY_INSIGHTS_STATS_GAP                  = 10
KEY_INSIGHTS_STATS_BOTTOM               = 24
KEY_INSIGHTS_STAT_HEIGHT                = 58
KEY_INSIGHTS_STAT_RADIUS                = 4
KEY_INSIGHTS_STAT_TEXT_SIZE             = 11
KEY_INSIGHTS_METHOD_BG                  = "#426387"
KEY_INSIGHTS_METHOD_FG                  = "#f5f7fa"
KEY_INSIGHTS_POLICIES_BG                = "#059669"
KEY_INSIGHTS_POLICIES_FG                = "#ecfdf5"
KEY_INSIGHTS_DMS_BG                     = "#808080"
KEY_INSIGHTS_DMS_FG                     = "#fafafa"
KEY_INSIGHTS_TAG_HEIGHT                 = 40
KEY_INSIGHTS_TAG_RADIUS                 = 4
KEY_INSIGHTS_TAG_TEXT_SIZE              = 11
KEY_INSIGHTS_TAG_TOP_DRIVER_BG          = "#4ade80"
KEY_INSIGHTS_TAG_TOP_DRIVER_FG          = "#f0fdf4"
KEY_INSIGHTS_TAG_STRONGEST_BG           = "#60a5fa"
KEY_INSIGHTS_TAG_STRONGEST_FG           = "#eff6ff"
KEY_INSIGHTS_TAG_CONTESTED_BG           = "#f87171"
KEY_INSIGHTS_TAG_CONTESTED_FG           = "#fef2f2"
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

# ── Switcher bar: DM / Analysis tab labels ───────────────────────────────────
TAB_BG           = "#ffffff"   # tab strip background (matches switcher bar)
TAB_ACTIVE_FG    = "#30455c"   # active tab text colour
TAB_INACTIVE_FG  = "#a3a3a3"   # inactive tab text colour
TAB_UNDERLINE    = "#557ca2"   # 1px underline shown on the active tab
TAB_PADX         = 14          # px — horizontal inner padding on each label
TAB_UNDERLINE_EXTRA = 4        # px — underline extends this many px beyond text width on each side
TAB_TEXT_SIZE    = 12          # pt

# ── Status bar ("Ready") — bottom of notebook content area ───────────────────
STATUSBAR_BG           = "#ffffff"   # background
STATUSBAR_FG           = "#a6bcd3"   # text color
STATUSBAR_TEXT_SIZE    = 10          # pt
STATUSBAR_HEIGHT       = 35          # px
STATUSBAR_DIVIDER_COLOR = "#e6e6e6"  # 1px top divider

# ── Matrix widget ────────────────────────────────────────────────────────────
MATRIX_PADX           = 32      # px — right padding (cell area to widget right edge)
MATRIX_HDR_LEFT_PAD   = 28      # px — left padding (sidebar to row-header column)
MATRIX_HDR_CELL_GAP   = 5       # px — gap between row-header column and first cell
MATRIX_CELL_H         = 40      # px — cell height (also used for col/row header height)
MATRIX_HDR_W          = 120     # px — first column (P1, P2…) width
MATRIX_CELL_W_LARGE   = 160     # px — cell width when number of policies > 5
# When number of policies ≤ 5: cell widths expand to fill canvas width (full-width layout)
# When number of policies > 5: each cell is MATRIX_CELL_W_LARGE and the block is centred
MATRIX_HDR_BG         = "#426387"   # background colour for P1, P2… header boxes
MATRIX_HDR_FG         = "#f5f7fa"   # text colour for P1, P2… header boxes
MATRIX_HDR_TEXT_SIZE  = 10          # pt — header label font size (not bold)
MATRIX_LEGEND_H       = 40          # px — height of the "Click a cell to rate it:" strip
MATRIX_LEGEND_GAP     = 16          # px — empty space between legend and matrix grid
MATRIX_BADGE_H        = 25          # px — rating badge height inside legend
MATRIX_BADGE_PAD_X    = 10          # px — horizontal inner padding inside each badge (drives width)
MATRIX_BADGE_FONT_SIZE = 10         # pt — rating badge label font size
MATRIX_BADGE_GAP      = 3           # px — gap between consecutive badges
MATRIX_BADGE_RADIUS   = 4           # px — border radius of each rating badge
MATRIX_CELL_RADIUS    = 8           # px — border radius of all matrix cells and headers

# Thin overlay scrollbars (shown only when n > 5 and content overflows)
MATRIX_SCROLLBAR_W          = 7           # px — scrollbar thumb+trough width
MATRIX_SCROLLBAR_TROUGH     = "#f0f2f4"   # trough (track) colour
MATRIX_SCROLLBAR_THUMB      = "#c4ccd4"   # thumb colour (idle)
MATRIX_SCROLLBAR_THUMB_HOVER = "#8fa0b0"  # thumb colour (hover/active)
MATRIX_AXIS_H         = 22          # px — height of the axis-label row
MATRIX_CELL_GAP       = 4           # px — gap between cells / headers
MATRIX_PADX           = 24          # px — left / right padding around the grid block
MATRIX_LEGEND_LABEL_COLOR = "#a3a3a3"   # "Click a cell to rate it:" text colour

# Rating badge background colours (legend + matrix cells)
MATRIX_COLOR_INDIVISIBLE   = "#0B6E6E"
MATRIX_COLOR_REINFORCING   = "#2A9D8F"
MATRIX_COLOR_ENABLING      = "#6BAF92"
MATRIX_COLOR_NEUTRAL       = "#B0B7C3"
MATRIX_COLOR_CONSTRAINING  = "#E9C46A"
MATRIX_COLOR_COUNTERACTING = "#E76F51"
MATRIX_COLOR_CANCELLING    = "#9B2226"

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


# Key insights card: #fef3c7
# right card: #eef2ff
