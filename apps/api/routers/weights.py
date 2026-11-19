"""Weights router: `POST /weights/check` (the weight dialog's live sum and messages)."""

from fastapi import APIRouter
from starlette.responses import Response

from features.weight_check_feature import weight_check_feature
from models.check_models import WeightCheckData, WeightCheckRequest
from models.response_model import ApiResponseModel
from utils.response_utils import response_builder

router = APIRouter(prefix="/weights", tags=["weights"])


@router.post("/check", response_model=ApiResponseModel[WeightCheckData])
async def check_weights(body: WeightCheckRequest) -> Response:
    """
    Live sum, colour rule and the weight-dialog messages; always 200.

    Returns:
        Response: ApiResponseModel[WeightCheckData]
    """
    return response_builder.ok(weight_check_feature.check(body), "Weights checked")
