"""
Excel import settings and messages (`importer.py:39-192`, `app.py:2950-2998`), with label fixes L4, L5 and L11
and the new hardening and validation messages (plan Phase 5.1).
"""

IMPORT_SETTINGS = {
    "MAX_UPLOAD_BYTES": 5 * 1024 * 1024,
    "CHUNK_BYTES": 64 * 1024,
    # Room for the multipart boundaries, part headers and the `policies`/`decision_makers` fields.
    "MULTIPART_OVERHEAD_BYTES": 64 * 1024,
    "UPLOAD_PATH": "/api/v1/imports/workbook",
    "ALLOWED_EXTENSIONS": (".xlsx",),
    "MAX_SHEETS": 50,
    "MAX_ENTRY_BYTES": 50 * 1024 * 1024,
    "MAX_TOTAL_BYTES": 200 * 1024 * 1024,
    "BLANK_CELLS_SHOWN": 10,
    "BAD_VALUES_SHOWN": 10,
    "HEADER_MISMATCHES_SHOWN": 5,
}

IMPORT_MESSAGES = {
    "TOO_LARGE": "The workbook is larger than 5 MB.",
    "UNSUPPORTED": "Only .xlsx workbooks are supported.",
    "INVALID_WORKBOOK": "The file could not be read as an Excel workbook (.xlsx).",
    "TOO_MANY_SHEETS": "The workbook has more than 50 sheets.",
    "EMPTY_SHEET": 'Sheet "{sheet}": empty, skipped.',
    "SHORT_HEADER": 'Sheet "{sheet}": fewer than 2 policies in header row, skipped.',
    "HEADER_GAP": 'Sheet "{sheet}": header row has a blank policy name in column {letter}.',
    "DUPLICATE_POLICIES": 'Sheet "{sheet}": Policy names must be unique.',
    "HEADER_MISMATCH": 'Sheet "{sheet}": row and column headers do not match.\n{detail}',
    "HEADER_MISMATCH_LINE": '  row {row}: "{row_header}" vs col "{col_header}"',
    "BAD_VALUES": 'Sheet "{sheet}": unrecognised rating values:\n{lines}{more}\n\nAllowed values: {allowed}',
    "BAD_VALUE_LINE": '  {row} → {col}: "{value}"',
    "BAD_VALUES_MORE": "\n  ...",
    "BLANKS": '"{sheet}": {count} blank cell(s): {cells}{suffix}',
    "BLANK_CELL": "{row} → {col}",
    "BLANKS_SUFFIX": " (+{count} more)",
    "SHEET_NAMES": "Sheet names must be non-empty and unique after trimming spaces.",
    "NOTHING_IMPORTED": "No valid matrices were found in the workbook.",
    "POLICY_LIST_MISMATCH": (
        "The following sheets have a different policy list and cannot be imported:\n\n{lines}\n\n"
        "All matrices must share the same policy list."
    ),
    "POLICY_LIST_MISMATCH_LINE": "  - {dm}",
    "SUCCESS": "{count} matrix/matrices imported successfully.",
    "WITH_WARNINGS": "{count} matrix/matrices imported.",
}

# Warning groups (L4): kind and heading, in display order.
IMPORT_WARNING_GROUPS = (
    ("skipped", "The following sheets were skipped:"),
    ("blank_cells", "The following sheets have blank cells:"),
)

IMPORT_TITLES = {
    "ERROR": "Import Error",
    "NOTHING_IMPORTED": "Nothing Imported",
    "POLICY_LIST_MISMATCH": "Policy List Mismatch",
    "EXISTING_DECISION_MAKERS": "Existing Decision-Makers",
}
