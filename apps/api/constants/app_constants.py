"""
Application constants: port, project details, docs URLs, and filesystem paths.
"""

from pathlib import Path

PORT = 50002

PROJECT_DETAILS = {
    "PROJECT_NAME": "Policy Coherence Kit API",
    "DESCRIPTION": "Policy Coherence Kit API - aggregation, analyses, chart data, imports, exports, AI text",
    "VERSION": "0.1.0",
}

PROJECT_SETTINGS = {
    "API_DOCS_URL": "/api/docs",
    "REDOC_URL": "/api/redoc",
    "OPENAPI_URL": "/api/openapi.json",
}

# Paths resolve from the apps/api root, so they do not depend on the working directory.
API_ROOT = Path(__file__).resolve().parents[1]

PROJECT_PATHS = {
    "API_ROOT": API_ROOT,
}

# Every response under this prefix gets `Cache-Control: no-store` unless it sets its own header.
CACHE_CONTROL_SETTINGS = {
    "PATH_PREFIX": "/api/",
    "VALUE": "no-store",
}
