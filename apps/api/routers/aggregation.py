"""Aggregation router: `POST /aggregation/preview` (the tie step; ties may be unresolved)."""

from fastapi import APIRouter
from starlette.responses import Response

from features.aggregation_flow_feature import aggregation_flow_feature
from models.aggregation_models import AggregationData
from models.analysis_request_models import AnalysisRequest
from models.response_model import ApiResponseModel
from utils.response_utils import response_builder

router = APIRouter(prefix="/aggregation", tags=["aggregation"])


@router.post("/preview", response_model=ApiResponseModel[AggregationData])
async def preview_aggregation(body: AnalysisRequest) -> Response:
    """
    Aggregate without requiring every tie to be resolved.

    Returns:
        Response: ApiResponseModel[AggregationData]; 422 for blank cells, weights or invalid tie choices
    """
    return response_builder.ok(await aggregation_flow_feature.preview(body), "Aggregation previewed")
