"""
Project request models: one project per browser session (Settled Decision 3), sent in full with every request.

The validator applies the setup rules and messages (`features/setup_validation_feature.py`, one source) and trims
the names. Validation errors are `AppError`s, so they reach the client with the legacy message and title.
"""

from typing import List

from pydantic import BaseModel, Field, model_validator

from features.setup_validation_feature import setup_validation_feature


class DecisionMakerInput(BaseModel):
    """One decision-maker and their rating matrix."""

    name: str = Field(description="Trimmed; non-empty; unique (case-sensitive)")
    ratings: List[List[str]] = Field(
        description=(
            "n x n; row = influencing policy, column = influenced policy. Each off-diagonal cell is blank or an "
            "exact rating label; the diagonal is ignored and forced to Neutral"
        )
    )


class ProjectInput(BaseModel):
    """The project: name, policies (2-100) and decision-makers (1-50) with their ratings; blanks allowed."""

    project_name: str = Field(description="Trimmed; non-empty")
    policies: List[str] = Field(description="2-100 names; trimmed; non-empty; unique (case-sensitive)")
    decision_makers: List[DecisionMakerInput] = Field(description="1-50 decision-makers, in display order")

    @model_validator(mode="after")
    def _check_project(self) -> "ProjectInput":
        """Trim names, then check names, limits and ratings in legacy order."""
        self.project_name = self.project_name.strip()
        self.policies = [name.strip() for name in self.policies]
        for decision_maker in self.decision_makers:
            decision_maker.name = decision_maker.name.strip()
        names = [decision_maker.name for decision_maker in self.decision_makers]
        setup_validation_feature.check_names(self.project_name, names, self.policies, blanks_dropped=False)
        codes = setup_validation_feature.codes(self.policies)
        setup_validation_feature.check_ratings(names, [dm.ratings for dm in self.decision_makers], codes)
        return self
