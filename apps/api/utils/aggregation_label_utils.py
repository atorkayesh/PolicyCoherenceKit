"""
The single source of method names (label fix L1): `aggregation_method_label` (`aggregator.py:373-391`) verbatim,
and the XLSX sheet label derived from it (label fix L3).
"""

from typing import Union

from constants.aggregation_constants import METHOD_LABELS
from models.aggregation_models import AggregationResult


class AggregationLabeler:
    """Builds user-facing method labels."""

    def method_label(self, result_or_method: Union[AggregationResult, str]) -> str:
        """
        Return the label of a result (`Median (Lower)` / `Median (Upper)` for even medians) or a method.

        Args:
            result_or_method: Aggregation result or method key

        Returns:
            str: `Average`, `Median`, `Median (Lower)`, `Median (Upper)`, `Majority Rule` or `Weighted`
        """
        if isinstance(result_or_method, AggregationResult):
            result = result_or_method
            if result.method == "median":
                if result.median_even_choice == "lower":
                    return "Median (Lower)"
                if result.median_even_choice == "upper":
                    return "Median (Upper)"
                return "Median"
            method = result.method
        else:
            method = str(getattr(result_or_method, "value", result_or_method))
        return METHOD_LABELS.get(method, method.title())

    def sheet_label(self, label: str) -> str:
        """
        Make the XLSX sheet label (L3): `" ("` becomes `" "` and `")"` is removed.

        Args:
            label: Method label

        Returns:
            str: For example `Median Lower` or `Majority Rule`
        """
        return label.replace(" (", " ").replace(")", "")


aggregation_labeler = AggregationLabeler()
