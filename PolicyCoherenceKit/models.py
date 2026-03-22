# =============================================================================
# Policy Coherence Kit -- models.py
# Data model: PolicyMatrix and helper functions.
# =============================================================================

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .constants import DIAGONAL_VALUE


@dataclass
class PolicyMatrix:
    """
    Represents one decision-maker's n x n policy coherence matrix.

    Rows   = influencing policies
    Columns = influenced policies
    Diagonal cells are always locked to DIAGONAL_VALUE ("Neutral").
    """

    decision_maker: str
    policies: List[str]          # full policy names, e.g. "Urban Mobility Plan"
    codes: List[str]             # short codes,       e.g. "P1", "P2", ...
    data: Dict[tuple, str] = field(default_factory=dict)  # (row, col) -> rating

    def __post_init__(self):
        """Lock all diagonal cells to DIAGONAL_VALUE on creation."""
        for i in range(len(self.policies)):
            self.data[(i, i)] = DIAGONAL_VALUE

    # ------------------------------------------------------------------
    # Read / write
    # ------------------------------------------------------------------

    def set_rating(self, row: int, col: int, rating: str):
        """Set the coherence rating for cell (row, col). Diagonal is ignored."""
        if row == col:
            return
        self.data[(row, col)] = rating

    def get_rating(self, row: int, col: int) -> str:
        """Return the current rating for cell (row, col), or '' if not yet set."""
        return self.data.get((row, col), "")

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def filled_count(self) -> int:
        """Number of off-diagonal cells that have been rated."""
        n = len(self.policies)
        return sum(
            1 for i in range(n) for j in range(n)
            if i != j and self.data.get((i, j), "")
        )

    def total_cells(self) -> int:
        """Total number of off-diagonal cells (n*n - n)."""
        n = len(self.policies)
        return n * n - n

    def is_complete(self) -> bool:
        """Return True if every off-diagonal cell has been rated."""
        return self.filled_count() == self.total_cells()

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def to_dict_records(self) -> List[dict]:
        """
        Return the matrix as a list of row dicts, suitable for
        writing to Excel or CSV.

        Example row:
            {"Code": "P1", "Policy": "Urban Mobility Plan",
             "P1": "Neutral", "P2": "Reinforcing", ...}
        """
        n = len(self.policies)
        records = []
        for i in range(n):
            row = {
                "Code":   self.codes[i],
                "Policy": self.policies[i],
            }
            for j in range(n):
                row[self.codes[j]] = self.data.get((i, j), "")
            records.append(row)
        return records


# =============================================================================
# Helpers
# =============================================================================

def generate_codes(policies: List[str]) -> List[str]:
    """Generate P1, P2, ... codes for a list of policy names."""
    return [f"P{i + 1}" for i in range(len(policies))]


def make_empty_matrix(decision_maker: str, policies: List[str]) -> PolicyMatrix:
    """Convenience factory: create a blank PolicyMatrix from a list of names."""
    codes = generate_codes(policies)
    return PolicyMatrix(
        decision_maker=decision_maker,
        policies=policies,
        codes=codes,
    )
