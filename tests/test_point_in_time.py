import numpy as np
import pytest

from microalpha.point_in_time import PointInTimeViolation, require_point_in_time


def test_point_in_time_gate_reports_exact_rows():
    with pytest.raises(PointInTimeViolation) as captured:
        require_point_in_time(
            np.array([1.0, 2.0, 3.0]),
            np.array([1.0, 4.0, 5.0]),
            row_ids=["safe", "late-b", "late-c"],
        )
    assert captured.value.count == 2
    assert captured.value.row_ids == ("late-b", "late-c")


def test_point_in_time_gate_accepts_available_rows():
    require_point_in_time(
        np.array([1.0, 2.0, 3.0]),
        np.array([0.0, 2.0, 2.5]),
        row_ids=["a", "b", "c"],
    )


@pytest.mark.parametrize(
    ("decision_at", "available_at"),
    [
        (np.array([1.0]), np.array([np.nan])),
        (
            np.array(["2026-01-02"], dtype="datetime64[D]"),
            np.array(["NaT"], dtype="datetime64[D]"),
        ),
    ],
)
def test_point_in_time_gate_fails_closed_on_missing_timestamps(
    decision_at, available_at
):
    with pytest.raises(PointInTimeViolation) as captured:
        require_point_in_time(decision_at, available_at, row_ids=["missing"])
    assert captured.value.row_ids == ("missing",)
