"""Excel import errors. Public messages are the legacy importer and app texts, or the new hardening texts."""

from http import HTTPStatus

from errors.app_error import AppError


class UploadTooLargeError(AppError):
    """The upload exceeds 5 MB (checked while streaming)."""

    code = "upload_too_large"
    status_code = HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    public_message = "The workbook is larger than 5 MB."


class UnsupportedFileError(AppError):
    """The upload is not an `.xlsx` file (label fix L5)."""

    code = "unsupported_file"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "Only .xlsx workbooks are supported."


class InvalidWorkbookError(AppError):
    """openpyxl, zip or XML could not read the workbook, or a zip entry is too large."""

    code = "invalid_workbook"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "The file could not be read as an Excel workbook (.xlsx)."


class InvalidImportError(AppError):
    """The workbook was read but a sheet breaks an import rule (legacy or new message)."""

    code = "invalid_import"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "The workbook could not be imported."


class NothingImportedError(AppError):
    """No sheet produced a matrix (`app.py:2961-2965`)."""

    code = "nothing_imported"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "No valid matrices were found in the workbook."


class PolicyListMismatchError(AppError):
    """A sheet's policy list differs from the reference list (`app.py:2964-2978`)."""

    code = "policy_list_mismatch"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "All matrices must share the same policy list."


class ExistingDecisionMakersError(AppError):
    """A sheet name clashes with an existing decision-maker (`dialogs.py:1102-1108`)."""

    code = "existing_decision_makers"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    public_message = "These decision-maker names already exist in the project."
