"""Analysis chart router: `POST /analysis/charts/network` (chart data for the browser; no images)."""

from typing import Optional

from fastapi import APIRouter
from starlette.responses import Response

from constants.chart_constants import DEFAULT_NETWORK_LAYOUT, NetworkLayout
from features.network_chart_data_feature import network_chart_data_feature
from models.analysis_request_models import AnalysisRequest
from models.chart_models import NetworkChartData
from models.response_model import ApiResponseModel
from utils.response_utils import response_builder

router = APIRouter(prefix="/analysis/charts", tags=["analysis"])


@router.post("/network", response_model=ApiResponseModel[NetworkChartData])
async def network_chart(
    body: AnalysisRequest, layout: NetworkLayout = DEFAULT_NETWORK_LAYOUT, focus: Optional[int] = None
) -> Response:
    """
    Node positions, edges and texts of one layout; `focus` (0-based policy index) gives the ego view.

    Returns:
        Response: ApiResponseModel[NetworkChartData]; 422 `invalid_focus_policy` and the analysis errors
    """
    return response_builder.ok(await network_chart_data_feature.chart(body, layout, focus), "Chart data built")
