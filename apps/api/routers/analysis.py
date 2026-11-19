"""Analysis router: `POST /analysis` (aggregation and every analysis of the current run)."""

from fastapi import APIRouter
from starlette.responses import Response

from features.analysis_feature import analysis_feature
from models.analysis_request_models import AnalysisRequest
from models.analysis_result_models import AnalysisData
from models.response_model import ApiResponseModel
from utils.response_utils import response_builder

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("", response_model=ApiResponseModel[AnalysisData])
async def run_analysis(body: AnalysisRequest) -> Response:
    """
    Aggregate the matrices and run the coherence scores, range of influence, PCA, network and insights.

    Returns:
        Response: ApiResponseModel[AnalysisData]; 422 for invalid setup, blank cells, weights or unresolved ties
    """
    return response_builder.ok(await analysis_feature.analyze(body), "Analysis completed")
