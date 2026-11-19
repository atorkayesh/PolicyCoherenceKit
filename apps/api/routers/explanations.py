"""
Explanation router: `GET /explanations/providers` (model catalogue), `POST /explanations` (per-request key) and
`POST /explanations/export/pdf` (`policy_interpretation.pdf`).
"""

from fastapi import APIRouter
from starlette.responses import Response

from constants.export_constants import EXPORT_FILENAMES, PDF_MEDIA_TYPE
from features.explanation_feature import explanation_feature
from features.explanation_providers_feature import explanation_providers_feature
from features.interpretation_pdf_feature import interpretation_pdf_feature
from models.explanation_models import (
    ExplanationData,
    ExplanationProvidersData,
    ExplanationRequest,
    InterpretationPdfRequest,
)
from models.response_model import ApiResponseModel
from utils.response_utils import response_builder

router = APIRouter(prefix="/explanations", tags=["explanations"])


@router.get("/providers", response_model=ApiResponseModel[ExplanationProvidersData])
async def list_providers() -> Response:
    """
    AI providers with their models and cheap default model (the API's single model catalogue).

    Returns:
        Response: ApiResponseModel[ExplanationProvidersData]
    """
    return response_builder.ok(explanation_providers_feature.list_providers(), "Providers loaded")


@router.post("", response_model=ApiResponseModel[ExplanationData])
async def explain(body: ExplanationRequest) -> Response:
    """
    Interpret an analysis with Anthropic, Azure OpenAI, Gemini, Groq, OpenAI or OpenRouter. The key is used once.

    Returns:
        Response: ApiResponseModel[ExplanationData]; 422 missing key, endpoint, unlisted model or analysis errors,
        502/504 provider failures
    """
    return response_builder.ok(await explanation_feature.explain(body), "Interpretation generated")


@router.post("/export/pdf", response_class=Response, responses={200: {"content": {PDF_MEDIA_TYPE: {}}}})
async def export_pdf(body: InterpretationPdfRequest) -> Response:
    """
    Download the interpretation as `policy_interpretation.pdf`.

    Returns:
        Response: The PDF as an attachment; 422 `empty_interpretation`
    """
    return response_builder.download_bytes(
        await interpretation_pdf_feature.export(body.text), EXPORT_FILENAMES["PDF"], PDF_MEDIA_TYPE
    )
