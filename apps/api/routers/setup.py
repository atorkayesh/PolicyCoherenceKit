"""Setup router: `POST /setup/validate` (project name, decision-makers and policies)."""

from fastapi import APIRouter
from starlette.responses import Response

from features.setup_validation_feature import setup_validation_feature
from models.response_model import ApiResponseModel
from models.setup_models import SetupValidateData, SetupValidateRequest
from utils.response_utils import response_builder

router = APIRouter(prefix="/setup", tags=["setup"])


@router.post("/validate", response_model=ApiResponseModel[SetupValidateData])
async def validate_setup(body: SetupValidateRequest) -> Response:
    """
    Validate the parts of the setup form that are present, in legacy order.

    Returns:
        Response: ApiResponseModel[SetupValidateData]; 422 `invalid_setup` with the legacy message and title
    """
    return response_builder.ok(setup_validation_feature.validate_setup(body), "Setup is valid")
