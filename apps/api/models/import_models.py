"""Workbook import response (`POST /imports/workbook`) and the data of a `nothing_imported` error."""

from typing import List, Optional

from pydantic import BaseModel, Field


class ImportedMatrix(BaseModel):
    """One sheet as a decision-maker matrix."""

    decision_maker: str = Field(description="The trimmed sheet name")
    ratings: List[List[str]] = Field(description='n x n; "Neutral" diagonal and "" for blank cells')


class WarningGroup(BaseModel):
    """Import warnings of one kind (label fix L4); the messages are the legacy texts."""

    kind: str = Field(description="`skipped` or `blank_cells`")
    heading: str
    messages: List[str]


class ImportData(BaseModel):
    """The imported matrices."""

    policies: List[str]
    codes: List[str]
    matrices: List[ImportedMatrix]
    warning_groups: List[WarningGroup]
    imported_count: int
    summary_message: str
    suggested_project_name: str = Field(description="Stem of the uploaded file name")


class ImportErrorData(BaseModel):
    """`data` of an import error: the legacy message-box title and, when nothing was imported, the warnings."""

    title: Optional[str] = None
    warning_groups: List[WarningGroup] = Field(default_factory=list)
