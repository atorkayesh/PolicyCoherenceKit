"""Conversions between the legacy `(row, col)` cell dicts and the nested lists of the API, and policy codes."""

from typing import Dict, List, Optional, Tuple, TypeVar

T = TypeVar("T")
Cell = Tuple[int, int]


class MatrixConverter:
    """Converts cell dicts to `n x n` lists and back, and builds policy codes (`models.py:97-99`)."""

    def codes(self, policies: List[str]) -> List[str]:
        """
        Generate the positional policy codes.

        Args:
            policies: Policy names

        Returns:
            List[str]: `P1, P2, ...`
        """
        return [f"P{i + 1}" for i in range(len(policies))]

    def to_grid(self, cells: Dict[Cell, T], n: int) -> List[List[Optional[T]]]:
        """
        Convert a cell dict into an `n x n` list (missing cells become None).

        Args:
            cells: `(row, col) -> value`
            n: Matrix size

        Returns:
            List[List[Optional[T]]]: Row-major nested list
        """
        return [[cells.get((i, j)) for j in range(n)] for i in range(n)]

    def to_cells(self, grid: List[List[T]]) -> Dict[Cell, T]:
        """
        Convert an `n x n` list into a cell dict.

        Args:
            grid: Row-major nested list

        Returns:
            Dict[Cell, T]: `(row, col) -> value`
        """
        return {(i, j): value for i, row in enumerate(grid) for j, value in enumerate(row)}


matrix_converter = MatrixConverter()
