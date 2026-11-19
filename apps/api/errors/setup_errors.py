"""Setup errors: project, decision-maker and policy names, the request limits, and the rating matrices."""

from http import HTTPStatus

from errors.app_error import AppError


class InvalidSetupError(AppError):
    """A name rule or limit from the setup dialog (`dialogs.py:1080-1124`) failed. Uses the legacy message."""

    code = "invalid_setup"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "The project setup is invalid."


class InvalidRatingsError(AppError):
    """A decision-maker's ratings are not `n x n` or hold a label that is not on the rating scale."""

    code = "invalid_ratings"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "The ratings are invalid."
