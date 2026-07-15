"""Point-in-time availability checks for research features."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .events import LookaheadError


class PointInTimeViolation(LookaheadError):
    """Raised when feature rows are used before they become available."""

    def __init__(self, row_ids: Sequence[str]):
        self.row_ids = tuple(str(row_id) for row_id in row_ids)
        self.count = len(self.row_ids)
        preview = ", ".join(self.row_ids[:5])
        suffix = "..." if self.count > 5 else ""
        super().__init__(
            f"{self.count} feature rows violate available_at <= decision_at: "
            f"{preview}{suffix}"
        )


def require_point_in_time(
    decision_at: Sequence[float] | np.ndarray,
    available_at: Sequence[float] | np.ndarray,
    *,
    row_ids: Sequence[str] | None = None,
) -> None:
    """Fail closed unless every row is available at its decision timestamp."""

    decisions = np.asarray(decision_at)
    availability = np.asarray(available_at)
    if decisions.shape != availability.shape:
        raise ValueError("decision_at and available_at must have identical shapes")
    if decisions.ndim != 1:
        raise ValueError("point-in-time timestamps must be one-dimensional")
    if row_ids is None:
        identifiers = [str(index) for index in range(decisions.size)]
    else:
        identifiers = [str(row_id) for row_id in row_ids]
        if len(identifiers) != decisions.size:
            raise ValueError("row_ids must align with timestamp rows")
    if np.issubdtype(decisions.dtype, np.datetime64):
        missing_decisions = np.isnat(decisions)
    else:
        missing_decisions = ~np.isfinite(decisions.astype(float))
    if np.issubdtype(availability.dtype, np.datetime64):
        missing_availability = np.isnat(availability)
    else:
        missing_availability = ~np.isfinite(availability.astype(float))
    violations = np.flatnonzero(
        missing_decisions | missing_availability | (availability > decisions)
    )
    if violations.size:
        raise PointInTimeViolation([identifiers[index] for index in violations])
