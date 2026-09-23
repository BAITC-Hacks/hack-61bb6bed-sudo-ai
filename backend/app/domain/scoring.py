import math
import re

from app.domain.entities import Assessment, Brief, CriterionScore, Question

RUBRIC = {
    "problem": 15,
    "goal": 15,
    "deliverable": 15,
    "success_criteria": 15,
    "target_users": 10,
    "constraints": 10,
    "timeline": 10,
    "resources": 5,
    "risk_context": 5,
}
QUESTIONS = {
    "problem": "Какую проблему решаем, каков её масштаб и последствия?",
    "goal": "Что должно измениться для бизнеса после реализации?",
    "deliverable": "Какой конкретный результат должна передать команда?",
    "success_criteria": "Какие измеримые показатели подтвердят успех?",
    "target_users": "Кто будет пользоваться решением?",
    "constraints": "Какие есть технические, бюджетные или правовые ограничения?",
    "timeline": "Каков срок и какой объём работы входит в него?",
    "resources": "Какие данные, инструменты и помощь доступны команде?",
    "risk_context": "Какие риски и требования к защите данных нужно учесть?",
}


def quality_level(total: int) -> str:
    for threshold, name in [(90, "Excellent"), (80, "Strong"), (60, "Ready"), (40, "Basic")]:
        if total >= threshold:
            return name
    return "Draft"


def assess(
    brief: Brief,
    semantic: dict[str, tuple[float, str]] | None = None,
    warning: str | None = None,
) -> Assessment:
    """20% structural + 80% semantic; offline scores are conservative, at most 40/100."""
    scores = {}
    missing = []
    for name, maximum in RUBRIC.items():
        value = getattr(brief, name).strip()
        if not value:
            missing.append(name)
            scores[name] = CriterionScore(0, maximum, "Поле не заполнено.")
            continue
        structural = maximum // 5
        if semantic is not None:
            ratio, reason = semantic.get(name, (0.0, "Нет семантической оценки."))
            ratio = max(0.0, min(1.0, ratio)) if math.isfinite(ratio) else 0.0
            score = structural + round((maximum - structural) * ratio)
        else:
            # Length is only a completeness hint, never proof of semantic quality.
            detailed = len(set(re.findall(r"\w+", value.lower()))) >= 8
            score = structural + (structural if detailed else 0)
            reason = "Базовая проверка заполнения; смысл без AI не оценён."
        if name in {"success_criteria", "timeline"} and not re.search(r"\d", value):
            score = min(score, structural)
            reason += " Добавьте числовой показатель или срок."
        scores[name] = CriterionScore(score, maximum, reason)
    total = sum(item.score for item in scores.values())
    gaps = sorted(RUBRIC, key=lambda key: scores[key].maximum - scores[key].score, reverse=True)
    questions = [Question(key, QUESTIONS[key]) for key in gaps if scores[key].score < RUBRIC[key]][
        :3
    ]
    return Assessment(
        total,
        quality_level(total),
        "openai" if semantic is not None else "local_fallback",
        scores,
        missing,
        questions,
        warning,
    )


def match_skills(required: list[str], available: list[str]) -> dict:
    needs, skills = set(required), set(available)
    matched = sorted(needs & skills)
    return {
        "score": round(100 * len(matched) / len(needs)) if needs else 0,
        "matched_skills": matched,
        "missing_skills": sorted(needs - skills),
        "source": "skill_overlap",
        "reason": "Совпадение навыков" if needs else "Требуемые навыки ещё не указаны",
    }
