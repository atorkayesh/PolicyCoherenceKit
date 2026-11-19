"""Matrices router: `POST /matrices/check` (completeness and aggregation options)."""

from fastapi import APIRouter
from starlette.responses import Response

from features.matrix_check_feature import matrix_check_feature
from models.check_models import MatrixCheckData
from models.project_models import ProjectInput
from models.response_model import ApiResponseModel
from utils.response_utils import response_builder

router = APIRouter(prefix="/matrices", tags=["matrices"])


@router.post("/check", response_model=ApiResponseModel[MatrixCheckData])
async def check_matrices(body: ProjectInput) -> Response:
    """
    Completeness of every matrix (blank cells allowed) and the options the decision-maker count allows.

    Returns:
        Response: ApiResponseModel[MatrixCheckData]; 422 for invalid setup or ratings
    """
    return response_builder.ok(matrix_check_feature.check(body), "Matrices checked")
