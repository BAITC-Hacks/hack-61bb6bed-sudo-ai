from dataclasses import asdict
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domain.entities import Brief
from app.domain.scoring import RUBRIC
from app.infrastructure.ai import AnalysisOutput, OpenAIAnalyzer


def provider(output=None, status="completed", error=None):
    parse = AsyncMock(
        return_value=SimpleNamespace(output_parsed=output, status=status), side_effect=error
    )
    return SimpleNamespace(responses=SimpleNamespace(parse=parse))


async def test_without_key_does_not_invent_facts():
    brief, score = await OpenAIAnalyzer(None, "", 1).analyze("Нужен AI", Brief(), False)
    assert brief.problem == "Нужен AI"
    assert brief.title == brief.timeline == brief.goal == ""
    assert score.source == "local_fallback" and score.warning


@pytest.mark.parametrize(
    "status,error", [("completed", None), ("incomplete", None), ("completed", TimeoutError())]
)
async def test_refusals_incomplete_and_timeout_preserve_manual_data(status, error):
    original = Brief(problem="Ручная обработка", goal="Сократить время")
    brief, score = await OpenAIAnalyzer(
        provider(status=status, error=error), "test-model", 1
    ).analyze(
        "Старая идея",
        original,
        True,
    )
    assert brief == original
    assert score.source == "local_fallback"


async def test_valid_structured_response_is_scored_by_backend():
    brief = Brief(problem="Обрабатываем 500 заявок вручную")
    output = AnalysisOutput.model_validate(
        {
            "brief": asdict(brief),
            "scores": {name: {"quality": 1, "reason": "Понятно"} for name in RUBRIC},
        }
    )
    client = provider(output)
    result, score = await OpenAIAnalyzer(client, "test-model", 1).analyze(
        brief.problem, Brief(), False
    )
    assert result == brief
    assert score.total == 15  # Empty fields receive zero regardless of the model.
    assert client.responses.parse.call_args.kwargs["store"] is False


async def test_analysis_cannot_silently_rewrite_manual_fields():
    output = AnalysisOutput.model_validate(
        {
            "brief": asdict(Brief(problem="Придуманный факт")),
            "scores": {name: {"quality": 1, "reason": "Понятно"} for name in RUBRIC},
        }
    )
    original = Brief(problem="Факт пользователя")
    result, score = await OpenAIAnalyzer(provider(output), "test-model", 1).analyze(
        "Идея", original, False
    )
    assert result == original
    assert score.source == "local_fallback"
