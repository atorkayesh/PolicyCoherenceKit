"""Import router: `POST /imports/workbook` (one decision-maker matrix per sheet; `.xlsx`, ≤ 5 MB)."""

from typing import Annotated, List, Optional

from fastapi import APIRouter, File, Form, UploadFile
from starlette.responses import Response

from features.workbook_import_feature import workbook_import_feature
from models.import_models import ImportData
from models.response_model import ApiResponseModel
from utils.response_utils import response_builder

router = APIRouter(prefix="/imports", tags=["imports"])

UploadedFile = Annotated[UploadFile, File(description="`.xlsx` workbook, at most 5 MB")]
Names = Annotated[Optional[List[str]], Form()]


@router.post("/workbook", response_model=ApiResponseModel[ImportData])
async def import_workbook(file: UploadedFile, policies: Names = None, decision_makers: Names = None) -> Response:
    """
    Import every sheet as one decision-maker; the sheet name is the decision-maker's name.

    Returns:
        Response: ApiResponseModel[ImportData]; 413 too large, 422 unsupported, unreadable or invalid workbooks
    """
    return response_builder.ok(
        await workbook_import_feature.import_workbook(file, policies, decision_makers), "Workbook imported"
    )
