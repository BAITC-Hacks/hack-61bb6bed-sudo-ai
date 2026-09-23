import math

import pytest

from app.domain.entities import Brief
from app.domain.scoring import RUBRIC, assess, match_skills, quality_level


def complete_brief():
    return Brief(
        **{
            name: "Конкретное описание с 10 измеримыми результатами для этой задачи."
            for name in RUBRIC
        }
    )


def test_empty_fields_cannot_get_ai_points():
    result = assess(Brief(), {name: (1.0, "perfect") for name in RUBRIC})
    assert result.total == 0
    assert set(result.missing_fields) == set(RUBRIC)
    assert len(result.next_questions) == 3


def test_maximum_and_clamping():
    result = assess(complete_brief(), {name: (4.0, "specific") for name in RUBRIC})
    assert result.total == 100
    assert result.level == "Excellent"
    assert result.next_questions == []
    for ratio in [-100.0, math.inf, math.nan]:
        result = assess(complete_brief(), {name: (ratio, "bad") for name in RUBRIC})
        assert result.total == 20


def test_vague_success_and_timeline_are_capped_even_if_ai_is_optimistic():
    brief = Brief(success_criteria="Чтобы всё хорошо работало", timeline="Побыстрее")
    result = assess(brief, {name: (1.0, "great") for name in RUBRIC})
    assert result.scores["success_criteria"].score == 3
    assert result.scores["timeline"].score == 2


def test_fallback_is_honest_and_conservative():
    result = assess(complete_brief())
    assert result.total <= 40
    assert result.source == "local_fallback"


@pytest.mark.parametrize(
    "score,level",
    [
        (0, "Draft"),
        (39, "Draft"),
        (40, "Basic"),
        (59, "Basic"),
        (60, "Ready"),
        (79, "Ready"),
        (80, "Strong"),
        (89, "Strong"),
        (90, "Excellent"),
        (100, "Excellent"),
    ],
)
def test_levels(score, level):
    assert quality_level(score) == level


def test_matching_handles_duplicates_and_empty_requirements():
    assert match_skills([], ["python"])["score"] == 0
    result = match_skills(["python", "llm", "python"], ["python", "react"])
    assert result["score"] == 50
    assert result["missing_skills"] == ["llm"]
