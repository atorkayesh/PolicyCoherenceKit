"""Analysis export router: `POST /analysis/export/xlsx` (the legacy `Export Excel`, current run only)."""

from fastapi import APIRouter
from starlette.responses import Response

from constants.export_constants import XLSX_MEDIA_TYPE
from features.xlsx_export_feature import xlsx_export_feature
from models.analysis_request_models import AnalysisRequest
from utils.response_utils import response_builder

router = APIRouter(prefix="/analysis/export", tags=["analysis"])


@router.post("/xlsx", response_class=Response, responses={200: {"content": {XLSX_MEDIA_TYPE: {}}}})
async def export_xlsx(body: AnalysisRequest) -> Response:
    """
    Download `{project}_coherence.xlsx`.

    Returns:
        Response: The workbook as an attachment; 422 as `POST /analysis`
    """
    return response_builder.download_bytes(*await xlsx_export_feature.export(body), XLSX_MEDIA_TYPE)
