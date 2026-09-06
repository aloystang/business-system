"""五维评分单元测试。"""
from __future__ import annotations

import pytest

from app.services import scoring


@pytest.mark.parametrize("total,grade", [
    (90, "S"), (100, "S"), (89, "A"), (80, "A"), (79, "B"), (70, "B"), (69, "C"), (0, "C"),
])
def test_grade_thresholds(total, grade):
    assert scoring.grade_for(total) == grade


def test_total_and_grade():
    total, grade = scoring.total_and_grade([19, 18, 17, 18, 17])
    assert total == 89 and grade == "A"


def test_total_and_grade_full_marks_is_s():
    total, grade = scoring.total_and_grade([20, 20, 20, 20, 20])
    assert total == 100 and grade == "S"


@pytest.mark.parametrize("dims", [[21, 0, 0, 0, 0], [-1, 0, 0, 0, 0], [None, 0, 0, 0, 0]])
def test_out_of_range_raises(dims):
    with pytest.raises(ValueError):
        scoring.total_and_grade(dims)
