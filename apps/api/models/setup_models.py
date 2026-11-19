"""Setup validation request and response (`POST /setup/validate`)."""

from typing import List, Optional

from pydantic import BaseModel, Field


class SetupValidateRequest(BaseModel):
    """The setup form; only the parts present are validated. Empty entries are dropped and names trimmed."""

    project_name: Optional[str] = None
    decision_makers: Optional[List[str]] = None
    policies: Optional[List[str]] = None
    existing_decision_makers: Optional[List[str]] = Field(
        default=None, description="Names already in the project (adding decision-makers)"
    )


class SetupValidateData(BaseModel):
    """The cleaned setup."""

    project_name: Optional[str]
    decision_makers: Optional[List[str]]
    policies: Optional[List[str]]
    codes: Optional[List[str]] = Field(description="`P1 ... Pn` for the policies")
