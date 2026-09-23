"""A real HTTP workflow; creates one synthetic example per run."""

import asyncio
import json
import sys

import httpx

from scripts.seed_demo_data import ALPHA_ID, BUSINESS_ID, STUDENT_ID


async def main(base_url: str = "http://127.0.0.1:8000") -> None:
    business = {"X-Demo-User": str(BUSINESS_ID)}
    student = {"X-Demo-User": str(STUDENT_ID)}
    async with httpx.AsyncClient(base_url=base_url, timeout=40) as client:

        async def call(method, path, headers=None, **kwargs):
            response = await client.request(method, "/api/v1" + path, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()

        await call("GET", "/ready")
        task = await call(
            "POST",
            "/tasks/draft",
            business,
            json={"raw_text": "Хотим автоматизировать обработку обращений."},
        )
        task_id = task["id"]
        initial = await call("POST", f"/tasks/{task_id}/analyze", business)
        await call(
            "PATCH",
            f"/tasks/{task_id}",
            business,
            json={
                "title": "Smoke demo: классификация обращений",
                "problem": "Операторы ежедневно сортируют 500 обращений вручную за 4 часа.",
                "goal": "Сократить время сортировки обращений до 1 часа в день.",
                "deliverable": "REST API классификатора с документацией запуска и отчётом метрик.",
                "success_criteria": "Точность не менее 80% на 100 тестовых примерах.",
                "target_users": "Операторы службы поддержки.",
                "constraints": (
                    "Использовать только синтетические обращения, без персональных данных."
                ),
                "timeline": "3 недели: baseline, API, тесты и демонстрация.",
                "resources": "100 синтетических обращений и консультация представителя бизнеса.",
                "risk_context": "Сложные обращения должен проверять оператор.",
                "skill_slugs": ["python", "llm"],
            },
        )
        analysis = await call("POST", f"/tasks/{task_id}/analyze", business)
        await call("POST", f"/tasks/{task_id}/publish", business)
        public = await call("GET", f"/tasks/{task_id}")
        assert public["status"] == "published" and "raw_text" not in public
        proposal = await call(
            "POST",
            f"/tasks/{task_id}/apply",
            student,
            json={
                "team_id": str(ALPHA_ID),
                "pitch": "Реализуем проверяемый MVP",
                "approach": "Начнём с baseline и измерения метрик",
                "timeline": "3 недели",
            },
        )
        selected = await call("POST", f"/proposals/{proposal['id']}/select", business)
        assert selected["status"] == "selected"
        final = await call("GET", f"/tasks/{task_id}", business)
        assert final["status"] == "team_selected"
        print(
            json.dumps(
                {
                    "result": "passed",
                    "task_id": task_id,
                    "status": final["status"],
                    "score_before": initial["quality_score"],
                    "score_after": analysis["quality_score"],
                    "analysis_source": analysis["assessment"]["source"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"))
