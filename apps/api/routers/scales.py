"""Scales router: `GET /scales` (constants the web app renders)."""

from fastapi import APIRouter
from starlette.responses import Response

from features.scales_feature import scales_feature
from models.response_model import ApiResponseModel
from models.scale_models import ScalesData
from utils.response_utils import response_builder

router = APIRouter(tags=["scales"])


@router.get("/scales", response_model=ApiResponseModel[ScalesData])
async def get_scales() -> Response:
    """
    The rating scale, methods, rules, colour bands, network layouts and import limits.

    Returns:
        Response: ApiResponseModel[ScalesData]
    """
    return response_builder.ok(scales_feature.get_scales(), "Scales loaded")
