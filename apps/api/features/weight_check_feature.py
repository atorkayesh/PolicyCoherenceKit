"""
Weight inputs as the weight dialog checks them (`aggregation_dialog.py:558-613`).

`_update_sum` gives the live sum text and colour; `_on_ok` validates in order (missing → invalid → out of range
per decision-maker, then the sum with the L2 text). The sum is checked only when every weight is valid.
"""

import math
from typing import List, Optional

from constants.aggregation_constants import AGGREGATION_MESSAGES, AGGREGATION_RULES
from models.check_models import WeightCheckData, WeightCheckRequest, WeightError


class WeightCheckFeature:
    """Validates raw weight inputs."""

    def check(self, request: WeightCheckRequest) -> WeightCheckData:
        """
        Check the inputs.

        Args:
            request: Decision-maker names and raw inputs (one per decision-maker; missing inputs count as empty)

        Returns:
            WeightCheckData: Sum, sum text, tolerance colour rule, parsed weights and the dialog messages
        """
        raws = [(value or "") for value in request.weights]
        raws += [""] * (len(request.decision_makers) - len(raws))
        total = self._live_total(raws)
        within = total is not None and abs(total - AGGREGATION_RULES["WEIGHT_SUM_TARGET"]) <= self._tolerance()
        sum_text = (
            AGGREGATION_MESSAGES["WEIGHT_SUM_TEXT"].format(total=round(total, 4))
            if total is not None
            else AGGREGATION_MESSAGES["WEIGHT_SUM_UNPARSABLE"]
        )
        weights: List[Optional[float]] = []
        errors: List[WeightError] = []
        for index, (name, raw) in enumerate(zip(request.decision_makers, raws, strict=False)):
            weight, error = self._parse(index, name, raw.strip())
            weights.append(weight)
            if error is not None:
                errors.append(error)
        if not errors:
            errors.extend(self._sum_errors([w for w in weights if w is not None]))
        return WeightCheckData(
            total=total if total is not None and math.isfinite(total) else None,
            sum_text=sum_text,
            within_tolerance=within,
            valid=not errors,
            weights=weights,
            errors=errors,
            first_error=errors[0] if errors else None,
        )

    def _live_total(self, raws: List[str]) -> Optional[float]:
        """`_update_sum`: sum of the non-empty inputs, or None when one does not parse."""
        try:
            return sum(float(raw) for raw in raws if raw.strip())
        except ValueError:
            return None

    def _parse(self, index: int, name: str, raw: str):
        """Missing, then invalid, then out of range (`_on_ok`)."""
        if not raw:
            return None, self._error(index, name, "WEIGHT_MISSING", dm=name)
        try:
            weight = float(raw)
        except ValueError:
            return None, self._error(index, name, "WEIGHT_INVALID", raw=raw, dm=name)
        if not (AGGREGATION_RULES["WEIGHT_MIN"] <= weight <= AGGREGATION_RULES["WEIGHT_MAX"]):
            return (weight if math.isfinite(weight) else None), self._error(index, name, "WEIGHT_RANGE", dm=name)
        return weight, None

    def _sum_errors(self, weights: List[float]) -> List[WeightError]:
        """The sum check: `abs(round(sum, 10) - 1.0) > 0.01` (L2 text)."""
        total = round(sum(weights), 10)
        if abs(total - AGGREGATION_RULES["WEIGHT_SUM_TARGET"]) > self._tolerance():
            return [self._error(None, None, "WEIGHT_SUM", total=round(total, 4))]
        return []

    def _error(self, index: Optional[int], name: Optional[str], key: str, **values) -> WeightError:
        title, message = AGGREGATION_MESSAGES[key]
        return WeightError(index=index, decision_maker=name, title=title, message=message.format(**values))

    def _tolerance(self) -> float:
        return AGGREGATION_RULES["WEIGHT_SUM_TOLERANCE"]


weight_check_feature = WeightCheckFeature()
