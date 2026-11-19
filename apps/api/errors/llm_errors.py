"""AI interpretation errors; public messages never hold the key or the raw response (L9 for the missing key)."""

from http import HTTPStatus

from errors.app_error import AppError


class MissingApiKeyError(AppError):
    """No API key was supplied."""

    code = "missing_api_key"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "Please enter your API key before generating."


class MissingAzureEndpointError(AppError):
    """Azure OpenAI needs an endpoint."""

    code = "missing_azure_endpoint"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "Azure OpenAI endpoint is required."


class MissingAzureDeploymentError(AppError):
    """Azure OpenAI needs the user's deployment name (there is no default)."""

    code = "missing_azure_deployment"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "Please enter your Azure deployment name."


class InvalidAzureDeploymentError(AppError):
    """The Azure deployment name has characters that cannot go into the deployment URL."""

    code = "invalid_azure_deployment"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "Azure deployment names use only letters, digits, '.', '_' and '-' (at most 64 characters)."


class InvalidAzureEndpointError(AppError):
    """The Azure OpenAI endpoint is not an https URL on an Azure OpenAI host."""

    code = "invalid_azure_endpoint"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "Enter a valid Azure OpenAI endpoint, for example https://YOUR-RESOURCE-NAME.openai.azure.com."


class LlmAuthError(AppError):
    """The provider rejected the key (401/403)."""

    code = "llm_auth_failed"
    status_code = HTTPStatus.BAD_GATEWAY
    public_message = "The AI provider rejected the API key."


class LlmRateLimitError(AppError):
    """The provider rate limit was reached (429)."""

    code = "llm_rate_limited"
    status_code = HTTPStatus.BAD_GATEWAY
    public_message = "The AI provider rate limit was reached. Try again later."


class LlmTimeoutError(AppError):
    """The provider did not answer in time."""

    code = "llm_timeout"
    status_code = HTTPStatus.GATEWAY_TIMEOUT
    public_message = "The AI provider did not answer in time."


class LlmProviderError(AppError):
    """Any other provider failure (HTTP error, unreachable, unexpected response)."""

    code = "llm_provider_error"
    status_code = HTTPStatus.BAD_GATEWAY
    public_message = "The AI provider could not be reached."


class UnsupportedModelError(AppError):
    """The requested model is not in the provider's model list."""

    code = "unsupported_model"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "The selected model is not available for this AI provider."


class AzureDeploymentNotFoundError(AppError):
    """Azure OpenAI answered 404 / DeploymentNotFound for the deployment name."""

    code = "azure_deployment_not_found"
    status_code = HTTPStatus.BAD_GATEWAY
    public_message = "Deployment not found. Check the deployment name in your Azure portal."


class EmptyInterpretationError(AppError):
    """The PDF export received no interpretation text (`llm_tab.py:906-910`)."""

    code = "empty_interpretation"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "Generate an interpretation first."
