"""
Export constants: XLSX layout values (`app.py:3085-3217`), sheet title templates (label fix L3), media types and
file names (`app.py:3053`, `llm_tab.py:917`).
"""

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PDF_MEDIA_TYPE = "application/pdf"

EXPORT_FILENAMES = {
    "XLSX_TEMPLATE": "{project}_coherence.xlsx",
    "PDF": "policy_interpretation.pdf",
}

# Header cells: white bold text on navy, centred, thin light-grey border (`app.py:3097-3110`).
XLSX_STYLE = {
    "HEADER_FILL": "2C4A6E",
    "HEADER_FONT_COLOUR": "FFFFFF",
    "BORDER_COLOUR": "CCCCCC",
    "SCORE_NUMBER_FORMAT": "0.00",
    "MIN_COLUMN_WIDTH": 14,
    "COLUMN_PADDING": 4,
}

XLSX_TEXT = {
    "POLICY_INDEX": "Policy Index",
    "CORNER": "Influencing / Influenced",
    "SCORES_HEADER": ("Code", "Policy", "OI", "II", "WOI", "WII"),
    "ENTROPY_HEADER": ("Code", "Policy", "Entropy", "Category"),
    "CENTRALITY_HEADER": ("Code", "Policy", "Betweenness", "Closeness"),
}

# Result sheet titles (L3): `{sl}` is the sheet label made from the method label.
RESULT_SHEET_TITLES = (
    "Aggregated ({sl})",
    "Coh Scores ({sl})",
    "Range Influence ({sl})",
    "Centrality ({sl})",
)

SHEET_TITLE_RULES = {
    "MAX_LENGTH": 31,
    "FORBIDDEN_CHARACTERS": "\\/?*[]:",
    "REPLACEMENT": "_",
    "EMPTY_TITLE": "Sheet",
}
