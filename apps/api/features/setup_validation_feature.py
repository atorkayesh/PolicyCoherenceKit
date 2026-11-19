"""
Project setup rules from the setup dialog (`dialogs.py:1080-1124`), the request limits, and the rating checks.

Order (plan, API Contract): project name → decision-makers (required, unique, existing) → limits → policies
(count, unique) → control characters → matrix shape → labels. Project-name uniqueness is dropped (one project per
session). Errors carry the legacy message, and `data` holds the message-box title and the request field.
"""

import re
from typing import List, Optional, Sequence, Set

from constants.aggregation_constants import AGGREGATION_RULES, SETUP_MESSAGES
from constants.rating_constants import RATING_LABELS
from errors.setup_errors import InvalidRatingsError, InvalidSetupError
from models.error_models import ErrorContextData
from models.setup_models import SetupValidateData, SetupValidateRequest
from utils.matrix_utils import matrix_converter

_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f]")


class SetupValidationFeature:
    """Validates names, limits and rating matrices with the legacy messages."""

    def check_names(
        self,
        project_name: Optional[str],
        decision_makers: Optional[List[str]],
        policies: Optional[List[str]],
        existing: Optional[Set[str]] = None,
        blanks_dropped: bool = True,
    ) -> None:
        """
        Check the parts that are present, in legacy order. Names must already be trimmed.

        Args:
            project_name: Project name, or None to skip
            decision_makers: Decision-maker names, or None to skip
            policies: Policy names, or None to skip
            existing: Decision-maker names already in the project
            blanks_dropped: True when blank entries were dropped (setup form); False when every entry counts

        Raises:
            InvalidSetupError: With the first failing rule's message
        """
        if project_name is not None and not project_name:
            self._fail("PROJECT_NAME_REQUIRED", "project_name")
        if decision_makers is not None:
            self._check_decision_makers(decision_makers, existing or set(), blanks_dropped)
        if policies is not None and len(policies) > AGGREGATION_RULES["MAX_POLICIES"]:
            self._fail("TOO_MANY_POLICIES", "policies")
        if policies is not None:
            if not blanks_dropped and any(not name for name in policies):
                self._fail("POLICY_BLANK", "policies")
            if len(policies) < AGGREGATION_RULES["MIN_POLICIES"]:
                self._fail("TOO_FEW_POLICIES", "policies")
            if len(policies) != len(set(policies)):
                self._fail("DUPLICATE_POLICIES", "policies")
        for field, names in (
            ("project_name", [project_name or ""]),
            ("decision_makers", decision_makers or []),
            ("policies", policies or []),
        ):
            if any(_CONTROL_CHARACTERS.search(name) for name in names):
                self._fail("CONTROL_CHARACTERS", field)

    def check_ratings(
        self, decision_makers: Sequence[str], ratings: Sequence[List[List[str]]], codes: List[str]
    ) -> None:
        """
        Check every matrix is `n x n` and holds blanks or canonical labels off the diagonal.

        Args:
            decision_makers: Decision-maker names, in request order
            ratings: One label matrix per decision-maker
            codes: Policy codes `P1 ... Pn`

        Raises:
            InvalidRatingsError: For the first wrong shape, then the first unrecognised label (row-major)
        """
        n = len(codes)
        title, shape_message = SETUP_MESSAGES["RATINGS_SHAPE"]
        for name, matrix in zip(decision_makers, ratings, strict=True):
            if len(matrix) != n or any(len(row) != n for row in matrix):
                raise InvalidRatingsError(
                    "ratings shape", public_message=shape_message.format(dm=name, n=n), data=self._data(title)
                )
        title, label_message = SETUP_MESSAGES["UNRECOGNISED_RATING"]
        allowed = set(RATING_LABELS) | {""}
        for name, matrix in zip(decision_makers, ratings, strict=True):
            for i, row in enumerate(matrix):
                for j, value in enumerate(row):
                    if i != j and value not in allowed:
                        message = label_message.format(value=value, dm=name, row=codes[i], col=codes[j])
                        raise InvalidRatingsError("unrecognised rating", public_message=message, data=self._data(title))

    def validate_setup(self, request: SetupValidateRequest) -> SetupValidateData:
        """
        `POST /setup/validate`: trim, drop empty entries, and check the parts present in legacy order.

        Args:
            request: The setup form

        Returns:
            SetupValidateData: Cleaned names and the policy codes
        """
        project = request.project_name.strip() if request.project_name is not None else None
        decision_makers = self.clean(request.decision_makers)
        policies = self.clean(request.policies)
        existing = set(self.clean(request.existing_decision_makers) or [])
        self.check_names(project, decision_makers, policies, existing)
        return SetupValidateData(
            project_name=project,
            decision_makers=decision_makers,
            policies=policies,
            codes=self.codes(policies) if policies is not None else None,
        )

    def clean(self, names: Optional[List[str]]) -> Optional[List[str]]:
        """
        Trim names and drop empty entries (the setup form ignores empty rows).

        Args:
            names: Raw names, or None

        Returns:
            Optional[List[str]]: Trimmed non-empty names, or None
        """
        if names is None:
            return None
        return [name.strip() for name in names if name.strip()]

    def codes(self, policies: List[str]) -> List[str]:
        """
        Return the policy codes.

        Args:
            policies: Policy names

        Returns:
            List[str]: `P1 ... Pn`
        """
        return matrix_converter.codes(policies)

    def _check_decision_makers(self, names: List[str], existing: Set[str], blanks_dropped: bool) -> None:
        """Required, no blanks (request only), unique, not existing, then the limit (`dialogs.py:1097-1108`)."""
        if not names:
            self._fail("DECISION_MAKERS_REQUIRED", "decision_makers")
        if not blanks_dropped and any(not name for name in names):
            self._fail("DECISION_MAKER_BLANK", "decision_makers")
        if len(names) != len(set(names)):
            self._fail("DUPLICATE_DECISION_MAKERS", "decision_makers")
        duplicates = sorted(set(names) & existing)
        if duplicates:
            title, message = SETUP_MESSAGES["EXISTING_DECISION_MAKERS"]
            raise InvalidSetupError(
                "existing decision-makers",
                public_message=message.format(names="\n".join(duplicates)),
                data=ErrorContextData(title=title, field="decision_makers"),
            )
        if len(names) > AGGREGATION_RULES["MAX_DECISION_MAKERS"]:
            self._fail("TOO_MANY_DECISION_MAKERS", "decision_makers")

    def _fail(self, key: str, field: str) -> None:
        """Raise the setup error for a message key (the log detail never holds user data)."""
        title, message = SETUP_MESSAGES[key]
        raise InvalidSetupError(key, public_message=message, data=ErrorContextData(title=title, field=field))

    def _data(self, title: str) -> ErrorContextData:
        return ErrorContextData(title=title, field="decision_makers")


setup_validation_feature = SetupValidationFeature()
