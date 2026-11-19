"""
Completeness before aggregation: `check_completeness` (`aggregator.py:97-119`) verbatim, the legacy
`Incomplete Matrices` message (`app.py:2546-2556`, label fix L11), and the aggregation options the decision-maker
count allows (`app.py:2558-2585`).
"""

from typing import List, Optional, Tuple

from constants.aggregation_constants import AGGREGATION_MESSAGES, AGGREGATION_RULES, AggregationMethod
from errors.analysis_errors import IncompleteMatricesError
from models.aggregation_models import RatingMatrix
from models.check_models import AggregationOptions, BlankCell, DecisionMakerCompleteness, MatrixCheckData
from models.error_models import ErrorContextData
from models.project_models import ProjectInput

Incomplete = List[Tuple[str, List[Tuple[str, str]]]]


class MatrixCheckFeature:
    """Finds blank cells and reports what the aggregation step may offer."""

    def rating_matrices(self, project: ProjectInput) -> List[RatingMatrix]:
        """
        Build the legacy matrices from a request: diagonal Neutral, blank cells unset.

        Args:
            project: Validated project

        Returns:
            List[RatingMatrix]: One per decision-maker, in request order
        """
        codes = [f"P{i + 1}" for i in range(len(project.policies))]
        matrices = []
        for dm in project.decision_makers:
            matrix = RatingMatrix(decision_maker=dm.name, policies=list(project.policies), codes=codes)
            for i, row in enumerate(dm.ratings):
                for j, label in enumerate(row):
                    if i != j and label:
                        matrix.data[(i, j)] = label
            matrices.append(matrix)
        return matrices

    def check_completeness(self, matrices: List[RatingMatrix]) -> Incomplete:
        """Return `(decision_maker, [(code_row, code_col), ...])` for every matrix with a blank cell."""
        incomplete = []
        for matrix in matrices:
            blanks = []
            n = len(matrix.policies)
            for i in range(n):
                for j in range(n):
                    if i == j:
                        continue
                    if not matrix.get_rating(i, j):
                        blanks.append((matrix.codes[i], matrix.codes[j]))
            if blanks:
                incomplete.append((matrix.decision_maker, blanks))
        return incomplete

    def incomplete_message(self, incomplete: Incomplete) -> Optional[str]:
        """
        Build the legacy message: the first 10 blank cells per decision-maker and `(+k more)`.

        Args:
            incomplete: Output of `check_completeness`

        Returns:
            Optional[str]: The message, or None when every matrix is complete
        """
        if not incomplete:
            return None
        shown = AGGREGATION_RULES["BLANK_CELLS_SHOWN"]
        lines = []
        for dm_name, blanks in incomplete:
            cells = ", ".join(AGGREGATION_MESSAGES["CELL"].format(row=r, col=c) for r, c in blanks[:shown])
            more = len(blanks) - shown
            suffix = AGGREGATION_MESSAGES["INCOMPLETE_SUFFIX"].format(count=more) if more > 0 else ""
            lines.append(AGGREGATION_MESSAGES["INCOMPLETE_LINE"].format(dm=dm_name, cells=cells, suffix=suffix))
        return AGGREGATION_MESSAGES["INCOMPLETE"][1].format(lines="\n".join(lines))

    def require_complete(self, matrices: List[RatingMatrix]) -> None:
        """
        Raise when any matrix has a blank cell.

        Raises:
            IncompleteMatricesError: With the legacy message and title
        """
        message = self.incomplete_message(self.check_completeness(matrices))
        if message is not None:
            title = AGGREGATION_MESSAGES["INCOMPLETE"][0]
            raise IncompleteMatricesError("blank cells", public_message=message, data=ErrorContextData(title=title))

    def aggregation_options(self, decision_maker_count: int) -> AggregationOptions:
        """
        The options the aggregation step offers for a decision-maker count.

        Args:
            decision_maker_count: Number of decision-makers

        Returns:
            AggregationOptions: Method choice from 3 decision-makers; median choice for even counts
        """
        available = decision_maker_count >= AGGREGATION_RULES["METHOD_CHOICE_MIN_DECISION_MAKERS"]
        return AggregationOptions(
            decision_maker_count=decision_maker_count,
            method_choice_available=available,
            forced_method=None if available else AggregationMethod.AVERAGE,
            median_choice_applies=available and decision_maker_count % 2 == 0,
        )

    def check(self, project: ProjectInput) -> MatrixCheckData:
        """
        Report the completeness of every matrix.

        Args:
            project: Validated project (blank cells allowed)

        Returns:
            MatrixCheckData: Per-decision-maker counts, the first 10 blanks, the legacy message and the options
        """
        matrices = self.rating_matrices(project)
        n = len(project.policies)
        shown = AGGREGATION_RULES["BLANK_CELLS_SHOWN"]
        rows = []
        for matrix in matrices:
            blanks = [(i, j) for i in range(n) for j in range(n) if i != j and not matrix.get_rating(i, j)]
            cells = [BlankCell(row=i, col=j, code_row=matrix.codes[i], code_col=matrix.codes[j]) for i, j in blanks]
            total = n * n - n
            rows.append(
                DecisionMakerCompleteness(
                    name=matrix.decision_maker,
                    filled=total - len(blanks),
                    total=total,
                    complete=not blanks,
                    blank_count=len(blanks),
                    blank_cells=cells[:shown],
                )
            )
        message = self.incomplete_message(self.check_completeness(matrices))
        return MatrixCheckData(
            complete=message is None,
            decision_makers=rows,
            incomplete_message=message,
            aggregation_options=self.aggregation_options(len(matrices)),
        )


matrix_check_feature = MatrixCheckFeature()
