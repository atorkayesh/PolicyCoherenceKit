"""Aggregation and analysis errors. Public messages are the legacy dialog texts with the label fixes."""

from http import HTTPStatus

from errors.app_error import AppError


class IncompleteMatricesError(AppError):
    """At least one off-diagonal cell is blank (`app.py:2546-2556`)."""

    code = "incomplete_matrices"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "Please fill all cells before aggregating."


class InvalidWeightsError(AppError):
    """The weights are missing, out of range, or do not sum to 1 within ±0.01."""

    code = "invalid_weights"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "The weights are invalid."


class UnresolvedTieError(AppError):
    """A majority tie has no valid choice (`aggregation_dialog.py:779-787`)."""

    code = "unresolved_tie"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "Please select a rating for every tied cell."


class InvalidTieChoiceError(AppError):
    """A tie choice is not one of the tied ratings, or a cell has more than one choice."""

    code = "invalid_tie_choice"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "A tie choice is invalid."


class InvalidFocusPolicyError(AppError):
    """The ego-view focus index is not a policy index."""

    code = "invalid_focus_policy"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "The focus policy is invalid."
