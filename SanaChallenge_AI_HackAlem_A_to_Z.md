# SanaChallenge AI — полный план создания простого, сильного и работающего MVP

> **Цель:** создать простой, аккуратный и профессионально сделанный MVP с полностью работающим сквозным сценарием: от сырой бизнес-идеи до публикации задачи, отклика студенческой команды и выбора команды бизнесом.

---

# 1. Кратко: что именно мы строим

Мы создаём не просто каталог задач, а **AI Business Challenge Builder**.

Главная идея:

```text
Сырая идея бизнеса
        ↓
AI-анализ
        ↓
Рейтинг качества 0–100
        ↓
AI объясняет, чего не хватает
        ↓
Короткое адаптивное интервью
        ↓
Улучшенная карточка задачи
        ↓
Публикация в каталоге
        ↓
Студенты находят задачу
        ↓
AI может показать релевантность задачи команде
        ↓
Команда сама нажимает "Подать предложение"
        ↓
Бизнес просматривает предложения
        ↓
Бизнес сам выбирает команду
```

Ключевая формулировка продукта:

> **Мы превращаем сырую бизнес-потребность в понятную, измеримую и готовую к реализации студентами задачу.**

---

# 1.1. Принципы MVP

Этот проект должен быть:

- **простым** — без лишних функций;
- **полностью рабочим** — основной сценарий должен проходить от начала до конца;
- **быстрым** — async backend, PostgreSQL, минимальное количество лишних запросов;
- **понятным** — пользователь сразу понимает, что делать;
- **визуально аккуратным** — современный интерфейс без перегрузки;
- **профессиональным по архитектуре** — Clean Architecture, Docker, PostgreSQL, Alembic;
- **надёжным** — ошибки OpenAI/NVIDIA не должны ломать весь продукт;
- **демонстрационным** — жюри должно быстро понять ценность решения.

Главное правило:

> **Не делать много функций. Сделать несколько ключевых функций очень хорошо.**

Обязательный end-to-end flow:

```text
Business Idea
→ AI Analysis
→ Quality Score
→ Improve
→ Publish
→ Catalog
→ Student Apply
→ Business Select
```

# 2. Как решение соответствует кейсу

Обязательный сценарий кейса:

1. Представитель бизнеса описывает первоначальную потребность.
2. Система помогает превратить её в полноценную карточку.
3. Система оценивает качество заполнения.
4. Чем качественнее карточка, тем выше её рейтинг.
5. Задача публикуется в открытом каталоге.
6. Студенты сами выбирают интересные задачи.
7. Студенты подают предложения.
8. Представитель бизнеса выбирает, с какой командой продолжить работу.
9. Система может рекомендовать задачи, но не назначает команды автоматически.

Наш MVP закрывает все 9 пунктов.

---

# 3. Главная продуктовая концепция

## 3.1. Название

Рабочие варианты:

- **SanaChallenge AI**
- **SanaBrief AI**
- **ChallengeCraft AI**
- **TaskForge AI**
- **Business2Challenge**
- **AI Challenge Builder**

Для хакатона я бы выбрал:

# **SanaChallenge AI**

Подзаголовок:

> From business need to student-ready challenge.

---

# 4. Пользовательские роли

В MVP достаточно двух ролей.

## 4.1. Business

Представитель бизнеса может:

- создать черновик задачи;
- получить AI-анализ;
- увидеть Quality Score;
- ответить на уточняющие вопросы;
- улучшить карточку;
- опубликовать задачу;
- увидеть отклики;
- открыть профиль/предложение команды;
- выбрать одну команду.

## 4.2. Student Team

Студенческая команда может:

- открыть каталог;
- фильтровать задачи;
- сортировать по качеству;
- открыть подробную карточку;
- увидеть рекомендованный процент соответствия;
- подать предложение;
- посмотреть статус своего предложения.

---

# 5. Что НЕ нужно делать

Для MVP не нужно перегружать продукт следующими функциями:

- полноценную регистрацию через OAuth;
- подтверждение email;
- восстановление пароля;
- чат между бизнесом и студентами;
- Telegram-бота;
- уведомления;
- WebSocket;
- полноценную админ-панель;
- загрузку файлов;
- платежи;
- сложный RBAC;
- Kubernetes;
- микросервисную архитектуру;
- собственное обучение LLM;
- мобильное приложение;
- real-time коллаборацию.

Для демонстрации можно использовать **Demo Role Switcher**:

```text
[ Business Mode ] [ Student Mode ]
```

Это намного безопаснее по времени.

---

# 6. Главная фишка — Quality Score

## 6.1. Почему рейтинг нельзя полностью отдавать LLM

Нельзя просто спрашивать модель:

> "Оцени эту задачу от 0 до 100."

Это будет:

- непрозрачно;
- нестабильно;
- трудно объяснить;
- трудно повторить;
- легко получить разные результаты.

Нужно сделать **гибридный рейтинг**:

```text
Quality Score =
структурная проверка backend
+
семантическая AI-оценка
```

---

# 7. Рекомендуемая система оценки 100 баллов

## 7.1. Рубрика

| Критерий | Максимум |
|---|---:|
| Проблема бизнеса | 15 |
| Цель | 15 |
| Ожидаемый результат / deliverable | 15 |
| Критерии успеха | 15 |
| Целевая аудитория | 10 |
| Ограничения | 10 |
| Сроки и scope | 10 |
| Доступные данные / ресурсы | 5 |
| Риски / безопасность / доп. контекст | 5 |
| **Итого** | **100** |

---

# 8. Как считать баллы

## 8.1. Пример: "Проблема бизнеса" — 15 баллов

```text
0 баллов
Поле отсутствует.

5 баллов
Проблема названа, но слишком общо.

10 баллов
Есть конкретная проблема и контекст.

15 баллов
Есть конкретная проблема + масштаб + последствия.
```

Пример плохого текста:

> "Нам нужен AI."

Пример среднего:

> "Хотим автоматизировать ответы клиентам."

Пример сильного:

> "Операторы получают около 250 повторяющихся обращений в день. Среднее время ответа — 15 минут, что приводит к жалобам клиентов и перегрузке операторов."

---

## 8.2. Критерии успеха — 15 баллов

Плохо:

> "Чтобы всё хорошо работало."

AI должен определить:

```text
Поле заполнено: да
Измеримость: нет
Баллы: 3/15
```

Хорошо:

> "Не менее 70% типовых вопросов должны обрабатываться автоматически, а среднее время ответа — быть ниже 3 минут."

```text
Поле заполнено: да
Измеримость: да
Баллы: 15/15
```

---

# 9. Уровни качества задачи

```text
0–39   Draft
40–59  Basic
60–79  Ready
80–89  Strong
90–100 Excellent
```

UI:

```text
34/100
Draft

↓ после улучшений

61/100
Ready

↓ после улучшений

91/100
Excellent
```

---

# 10. Геймификация

Важно: геймификация направлена **на бизнес**, а не на студентов.

## 10.1. Механики

### Live Score

Большая шкала:

```text
            74
           /100

        STRONG BRIEF
```

### "Как получить ещё +18 баллов"

```text
+8  Добавьте измеримый критерий успеха
+5  Уточните ограничения
+3  Укажите доступные данные
+2  Уточните срок
```

### Progress Levels

```text
Idea
 ↓
Problem defined
 ↓
Goal defined
 ↓
Success measurable
 ↓
Scope ready
 ↓
Excellent Challenge
```

### Badges

- Clear Problem
- Measurable
- Time-bound
- Data Ready
- Safe Scope
- Excellent Brief

Не нужно делать монетки, магазин аватаров и XP ради XP.

---

# 11. AI-интервью

Вместо огромной формы AI задаёт только нужные вопросы.

Пример:

```text
Business:
Нам нужен AI для автоматизации заявок.

AI:
Я понимаю общую идею, но пока не хватает деталей.
Кто сейчас обрабатывает заявки?

Business:
Операторы.

AI:
Сколько заявок поступает примерно в день?

Business:
500.

AI:
Какой результат будет считаться успешным?

Business:
Хотим автоматически обрабатывать минимум 60%.
```

После каждого ответа:

```text
32 → 48 → 63 → 81
```

---

# 12. AI Task Simulator

Это дополнительная сильная функция.

Показываем бизнесу:

## Что понял студент

> "Нужно автоматизировать обработку входящих заявок."

## Что студент НЕ понял

- какие данные доступны;
- какой итоговый продукт нужен;
- как измерить успех;
- какой срок;
- какие ограничения.

Это отлично объясняет, зачем вообще нужен рейтинг.

---

# 13. Финальная карточка задачи

Пример:

# AI-система для автоматизации обработки заявок

**Проблема**

Операторы компании вручную обрабатывают около 500 заявок ежедневно, из-за чего растёт время ответа и нагрузка на сотрудников.

**Цель**

Автоматизировать обработку типовых заявок.

**Целевая аудитория**

Операторы службы поддержки.

**Что необходимо создать**

Рабочий прототип веб-сервиса или API, который классифицирует заявки и формирует предложенный ответ.

**Ожидаемый результат**

MVP с загрузкой заявки, определением категории и генерацией ответа.

**Критерии успеха**

- минимум 60% заявок автоматически классифицируются;
- время обработки одной заявки меньше 5 секунд;
- сложные запросы передаются человеку.

**Срок**

3 недели.

**Доступные ресурсы**

Обезличенный набор примеров обращений.

**Ограничения**

Нельзя использовать реальные персональные данные.

**Quality Score**

92/100 — Excellent

---

# 14. Открытый каталог

Пример интерфейса:

```text
Discover Challenges

[ All ] [ AI ] [ Web ] [ Data ] [ Cybersecurity ]

Sort:
[ Quality ↓ ] [ Newest ] [ Recommended ]
```

Карточка:

```text
92/100
AI-классификация заявок

AI • NLP • Python
3 weeks
5 proposals

[ View Challenge ]
```

Качественные задачи должны появляться выше при сортировке по Quality.

---

# 15. Recommendation Engine

Система может рекомендовать задачи командам, но не назначать.

Пример профиля команды:

```text
Python
FastAPI
React
PostgreSQL
LLM
Computer Vision
```

Для задачи:

```text
Recommended for your team
89%

Why?

✓ Python
✓ FastAPI
✓ LLM
✓ React

Missing:
○ Docker
```

Кнопка всё равно:

```text
[ Apply ]
```

Никакого:

```text
"You have been assigned to this task."
```

---

# 16. Отклик команды

Форма:

```text
Team name
Team members
Skills
Our approach
Why us?
Expected timeline
Portfolio / links (optional)
```

Пример:

> Мы предлагаем реализовать FastAPI backend с классификацией заявок через LLM, добавить web-интерфейс на React и метрики качества.

Кнопка:

```text
[ Submit Proposal ]
```

---

# 17. Кабинет бизнеса

```text
Challenge:
AI-классификация заявок

5 proposals
```

Карточка команды:

```text
Team Alpha

Skill Match: 92%

Python ✓
FastAPI ✓
React ✓
LLM ✓

Approach:
"Сначала создадим классификатор..."

[ View ] [ Select Team ]
```

Решение принимает представитель бизнеса.

---

# 18. Полный пользовательский сценарий

## Business Flow

```text
Landing
 ↓
Create Challenge
 ↓
Raw Idea
 ↓
AI Analyze
 ↓
Quality Score
 ↓
AI Interview
 ↓
Task Builder
 ↓
Final Preview
 ↓
Publish
 ↓
Dashboard
 ↓
View Proposals
 ↓
Select Team
```

## Student Flow

```text
Landing
 ↓
Student Mode
 ↓
Catalog
 ↓
Challenge Details
 ↓
Recommendation Score
 ↓
Apply
 ↓
Proposal Submitted
```

---

# 19. Экранная структура

Достаточно 8 экранов.

## 1. Landing

Главный CTA:

```text
Turn business needs into student-ready challenges.

[ Create Challenge ]
[ Explore Challenges ]
```

---

## 2. Raw Idea

Большое поле:

```text
Describe your business need in your own words.

[________________________________]
[________________________________]

[ Analyze with AI ]
```

---

## 3. AI Analysis

```text
Quality Score
34/100

Problem clarity       7/15
Goal                  5/15
Deliverable           5/15
Success criteria      0/15
Audience              6/10
Constraints           4/10
Timeline              0/10
Resources             4/5
Risk context          3/5
```

---

## 4. AI Interview / Task Builder

Слева — чат.

Справа — live preview.

---

## 5. Final Challenge Preview

Красиво оформленная карточка + Publish.

---

## 6. Catalog

Список задач + фильтры.

---

## 7. Proposal

Форма команды.

---

## 8. Business Proposals

Список откликов + выбор команды.

---

# 20. Технологический стек

Проект должен создаваться как **профессиональное production-like веб-приложение**, а не как одноразовый прототип.

## Frontend

```text
React
Vite
TypeScript
Tailwind CSS
```

Дополнительно:

```text
Framer Motion
Lucide React
TanStack Query
Axios / Fetch wrapper
```

Требования к frontend:

- TypeScript обязателен;
- компоненты должны быть переиспользуемыми;
- API-логика не должна находиться внутри UI-компонентов;
- состояния загрузки, ошибки и empty state должны быть предусмотрены;
- не хранить секреты во frontend;
- использовать понятную структуру `pages / components / features / api / types`.

## Backend

```text
FastAPI
Python 3.11+
Pydantic v2
SQLAlchemy 2.x Async
asyncpg
Alembic
```

### Backend должен быть асинхронным

Все I/O-операции должны выполняться асинхронно:

```python
async def ...
await ...
```

Обязательно использовать:

```text
AsyncSession
asyncpg
httpx.AsyncClient
async OpenAI client
```

Нельзя строить backend так, чтобы синхронные сетевые или DB-операции блокировали event loop.

Цель:

- быстрый API;
- параллельная обработка AI-запросов;
- высокая отзывчивость;
- возможность масштабирования после хакатона.

## Database

**Только PostgreSQL. SQLite не использовать.**

```text
PostgreSQL 16+
SQLAlchemy Async
asyncpg
Alembic migrations
```

PostgreSQL является основной и единственной БД проекта.

Требования:

- нормальная реляционная схема;
- внешние ключи;
- индексы;
- timestamps;
- enum/status поля;
- Alembic migrations;
- никакого хранения основной бизнес-логики в JSON-файлах;
- seed/demo данные можно добавлять отдельным скриптом.

## AI

```text
OpenAI API
Structured Outputs
Async OpenAI SDK
```

OpenAI используется для:

- semantic analysis;
- AI interview;
- quality assessment;
- structured challenge generation;
- recommendations/explanations.

## NVIDIA

```text
NVIDIA Brev
NVIDIA GPU
Embedding / recommendation service
```

При необходимости:

```text
NVIDIA NIM
```

## Docker

**Docker обязателен.**

Проект должен запускаться контейнерами.

Минимальная инфраструктура:

```text
docker-compose.yml

frontend
backend
postgres
```

При наличии NVIDIA integration:

```text
frontend
backend
postgres
nvidia-matching-service
```

Docker должен обеспечивать:

- одинаковое окружение у всей команды;
- быстрый локальный запуск;
- простую демонстрацию;
- профессиональную структуру проекта;
- независимость от локальных версий Python/Node/PostgreSQL.

## Deployment

Рекомендуемая схема:

```text
Frontend → Vercel / container hosting
Backend → Dockerized FastAPI
Database → Managed PostgreSQL / PostgreSQL container
NVIDIA service → NVIDIA Brev
```

Для локального запуска:

```bash
docker compose up --build
```

---

# 21. Архитектура

Проект строится по принципам **Clean Architecture / Layered Architecture**.

Главное правило:

> UI, бизнес-логика, работа с БД и внешние AI-сервисы не должны быть перемешаны.

Высокоуровневая схема:

```text
                     ┌──────────────────────┐
                     │      React/Vite      │
                     │       Frontend       │
                     └──────────┬───────────┘
                                │
                             REST API
                                │
                                ▼
                  ┌───────────────────────────┐
                  │     FastAPI API Layer     │
                  │ routers / schemas / auth  │
                  └─────────────┬─────────────┘
                                │
                                ▼
                  ┌───────────────────────────┐
                  │     Application Layer     │
                  │ use cases / orchestration │
                  └─────────────┬─────────────┘
                                │
                                ▼
                  ┌───────────────────────────┐
                  │       Domain Layer        │
                  │ entities / business rules │
                  └─────────────┬─────────────┘
                                │
                                ▼
                  ┌───────────────────────────┐
                  │   Infrastructure Layer    │
                  │ DB / OpenAI / NVIDIA      │
                  └───────┬─────────┬─────────┘
                          │         │
                          ▼         ▼
                    PostgreSQL    OpenAI API
                          │
                          ▼
                    NVIDIA Brev
                          │
                          ▼
                 Embedding / Matching
```

## Backend layers

### `api/`

Отвечает только за HTTP:

- routers;
- request/response schemas;
- dependency injection;
- validation;
- status codes.

### `application/`

Use cases:

- create draft;
- analyze challenge;
- answer AI interview;
- publish challenge;
- apply to challenge;
- select team.

### `domain/`

Чистая бизнес-логика:

- scoring rules;
- challenge status;
- proposal status;
- validation rules;
- domain entities.

Domain-слой не должен зависеть от FastAPI, OpenAI или PostgreSQL.

### `infrastructure/`

Интеграции:

- PostgreSQL repositories;
- OpenAI client;
- NVIDIA client;
- external services;
- cache, если будет нужен.

## Принцип зависимости

```text
API → Application → Domain
Infrastructure → Domain/Application interfaces
```

Не наоборот.

---

# 22. OpenAI — что именно поручить модели

OpenAI отвечает за:

1. понимание сырого описания;
2. оценку смысла;
3. поиск недостающей информации;
4. генерацию следующих вопросов;
5. проверку измеримости;
6. поиск противоречий;
7. структурирование карточки;
8. улучшение формулировок;
9. объяснение баллов.

---

# 23. Формат ответа OpenAI

Нужно использовать структурированный JSON.

Пример:

```json
{
  "summary": "Компания хочет автоматизировать обработку обращений.",
  "scores": {
    "problem": {
      "score": 7,
      "max": 15,
      "reason": "Проблема указана, но нет масштаба."
    },
    "goal": {
      "score": 8,
      "max": 15,
      "reason": "Цель понятна, но не измерима."
    },
    "deliverable": {
      "score": 4,
      "max": 15,
      "reason": "Не определён конечный продукт."
    }
  },
  "missing_fields": [
    "success_criteria",
    "deadline",
    "constraints"
  ],
  "next_questions": [
    "Сколько заявок обрабатывается в день?",
    "Какой результат будет считаться успешным?",
    "Есть ли ограничения по данным?"
  ],
  "suggested_improvements": [
    "Добавьте измеримую цель.",
    "Укажите срок.",
    "Опишите доступные данные."
  ]
}
```

---

# 24. Prompt для AI-анализатора

Системный промпт:

```text
Ты — AI-бизнес-аналитик платформы SanaChallenge AI.

Твоя задача — помогать представителю бизнеса превращать сырое описание проблемы
в качественную задачу, которую студентам легко понять и выполнить.

Оценивай:
1. Problem
2. Goal
3. Deliverable
4. Success criteria
5. Target users
6. Constraints
7. Timeline/scope
8. Available data/resources
9. Risk/security context

Правила:
- Не придумывай факты за пользователя.
- Если информации нет — укажи, что её нет.
- Не давай высокий балл только потому, что поле заполнено.
- Проверяй конкретность и измеримость.
- Формулируй максимум 3 следующих вопроса.
- Вопросы должны закрывать самые дорогие по баллам пробелы.
- Ответ возвращай строго в JSON.
```

---

# 25. Prompt для улучшения карточки

```text
На основе исходного описания и ответов пользователя:
1. Сформируй структурированную бизнес-задачу.
2. Не добавляй факты, которых пользователь не сообщал.
3. Если поле неизвестно — оставь его пустым или явно пометь как unknown.
4. Сделай текст понятным студентам.
5. Сохрани деловой и краткий стиль.
```

---

# 26. Backend Quality Engine

Рейтинг лучше считать на backend.

Псевдокод:

```python
def calculate_score(ai_result, task):
    score = 0

    score += ai_result.problem.score
    score += ai_result.goal.score
    score += ai_result.deliverable.score
    score += ai_result.success_criteria.score
    score += ai_result.target_users.score
    score += ai_result.constraints.score
    score += ai_result.timeline.score
    score += ai_result.resources.score
    score += ai_result.risk_context.score

    return min(score, 100)
```

---

# 27. Защита от "набивания баллов"

Нужно показать, что качество важнее заполненности.

Пользователь пишет:

```text
Success criteria:
Хороший результат.
```

AI:

```text
Поле есть: да.
Измеримость: нет.
Конкретность: низкая.
Score: 3/15.
```

Это отличная демонстрационная фишка.

---

# 28. База данных

База данных проекта — **PostgreSQL**.

Используем:

```text
PostgreSQL 16+
SQLAlchemy 2.x Async
asyncpg
Alembic
```

## Требования к модели данных

- UUID или bigint primary keys;
- foreign keys;
- `created_at` / `updated_at`;
- индексы на поля поиска и сортировки;
- enum/status поля;
- cascade rules должны быть определены осознанно;
- транзакции для критичных операций;
- async repositories;
- миграции только через Alembic.

## users

```text
id
name
email
role
created_at
updated_at
```

Индексы:

```text
email UNIQUE
role
```

## teams

```text
id
name
description
created_at
updated_at
```

## skills

```text
id
name
slug
```

## team_skills

```text
team_id
skill_id
level
```

Навыки лучше хранить в нормализованной таблице, а не только в одном JSON.

## team_members

```text
id
team_id
user_id
created_at
```

## tasks

```text
id
business_id
raw_text
title
problem
goal
target_users
deliverable
success_criteria
constraints
timeline
resources
risk_context
quality_score
quality_level
status
created_at
updated_at
published_at
```

Рекомендуемые индексы:

```text
quality_score
status
published_at
business_id
```

## task_skills

```text
task_id
skill_id
required_level
```

## task_scores

```text
id
task_id
problem_score
goal_score
deliverable_score
success_score
audience_score
constraints_score
timeline_score
resources_score
risk_score
feedback_jsonb
created_at
```

## task_score_history

```text
id
task_id
score
reason
created_at
```

Это позволяет показывать:

```text
29 → 51 → 73 → 91
```

## proposals

```text
id
task_id
team_id
pitch
approach
timeline
status
created_at
updated_at
```

Ограничение:

```text
UNIQUE(task_id, team_id)
```

Чтобы одна команда не отправляла один и тот же отклик много раз.

## matches

```text
id
task_id
team_id
similarity
skill_overlap
final_score
reasons_jsonb
created_at
```

## Рекомендуемая транзакция выбора команды

При `Select Team`:

1. выбранному proposal поставить `selected`;
2. остальным proposal этой задачи поставить `rejected/closed`;
3. task перевести в `team_selected`;
4. выполнить всё в одной PostgreSQL transaction.

---

# 29. API endpoints

## Tasks

```text
POST   /api/tasks/draft
POST   /api/tasks/{id}/analyze
POST   /api/tasks/{id}/answer
POST   /api/tasks/{id}/improve
POST   /api/tasks/{id}/publish
GET    /api/tasks
GET    /api/tasks/{id}
```

## Student

```text
GET    /api/recommendations
POST   /api/tasks/{id}/apply
GET    /api/my-proposals
```

## Business

```text
GET    /api/business/tasks
GET    /api/business/tasks/{id}/proposals
POST   /api/proposals/{id}/select
```

---

# 30. NVIDIA Brev — зачем он нужен

Не использовать Brev просто как дорогой хостинг.

Лучшее применение:

# Recommendation Engine

На GPU/AI-сервисе:

```text
Task text
    ↓
Embedding
    ↓
Vector A

Team profile
    ↓
Embedding
    ↓
Vector B

Cosine similarity
    ↓
0.89
    ↓
89% Match
```

---

# 31. Что отправлять в embedding

Для задачи:

```text
Title
Problem
Goal
Deliverable
Skills
Constraints
```

Для команды:

```text
Skills
Experience
Preferred domains
Tech stack
```

---

# 32. Формула matching

Базовая:

```text
semantic_similarity * 0.70
+
skill_overlap * 0.30
```

Пример:

```text
semantic = 0.88
skills = 0.93

score =
0.88 * 0.70 +
0.93 * 0.30
= 0.895

≈ 90%
```

---

# 33. Fallback для matching

Если NVIDIA/Brev не успели:

```text
skill_overlap =
intersection(required_skills, team_skills)
/
required_skills_count
```

Это позволит продукту работать.

После этого NVIDIA можно добавить как stretch goal.

---

# 34. Структура проекта

Структура должна выглядеть профессионально и поддерживать Clean Architecture.

```text
sana-challenge-ai/
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── pages/
│   │   ├── features/
│   │   │   ├── challenge-builder/
│   │   │   ├── catalog/
│   │   │   ├── proposals/
│   │   │   └── team-matching/
│   │   ├── components/
│   │   ├── api/
│   │   ├── hooks/
│   │   ├── types/
│   │   ├── utils/
│   │   └── main.tsx
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   │       ├── tasks.py
│   │   │       ├── proposals.py
│   │   │       ├── teams.py
│   │   │       └── health.py
│   │   │
│   │   ├── application/
│   │   │   ├── use_cases/
│   │   │   ├── dto/
│   │   │   └── interfaces/
│   │   │
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   ├── enums/
│   │   │   ├── services/
│   │   │   └── exceptions/
│   │   │
│   │   ├── infrastructure/
│   │   │   ├── db/
│   │   │   │   ├── models/
│   │   │   │   ├── repositories/
│   │   │   │   ├── session.py
│   │   │   │   └── migrations/
│   │   │   ├── openai/
│   │   │   │   ├── client.py
│   │   │   │   └── prompts.py
│   │   │   └── nvidia/
│   │   │       └── client.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   └── security.py
│   │   │
│   │   └── schemas/
│   │
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example
│
├── nvidia-service/
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
│
├── scripts/
│   └── seed_demo_data.py
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

Ключевой принцип:

> Никаких файлов `main.py` на 1000 строк, никаких SQL-запросов внутри router, никаких OpenAI-вызовов напрямую из endpoint.

---

# 35. Environment variables

```text
OPENAI_API_KEY=
NVIDIA_API_KEY=
DATABASE_URL=
FRONTEND_URL=
```

Никогда не коммитить:

```text
.env
```

`.gitignore`:

```text
.env
.env.local
.env.production
node_modules/
__pycache__/
*.db
```

В GitHub только:

```text
.env.example
```

---

# 36. Безопасность

С учётом официальных правил хакатона:

- не публиковать API-ключи;
- не вставлять ключи в GitHub;
- не вставлять секреты в презентацию;
- не пересылать токены в чат;
- использовать только разрешённые аккаунты;
- не использовать реальные персональные данные;
- использовать demo/synthetic data;
- проверять AI-generated код;
- не проводить сканирование сети;
- не проводить нагрузочные тесты;
- не использовать чужие ресурсы;
- после хакатона удалить временные ключи при необходимости.

---

# 37. Git workflow

Использовать выданный организаторами командный репозиторий.

Минимально:

```text
main
```

Можно не делать сложные branches в рамках MVP.

Но участникам удобно делать:

```text
feature/frontend
feature/backend
feature/ai
feature/deploy
```

Потом merge в main.

---

# 38. Каждый участник должен иметь вклад

Чтобы вклад был очевиден:

## Participant 1

```text
Frontend / UI
```

## Participant 2

```text
Backend / Database
```

## Participant 3

```text
OpenAI / Scoring
```

## Participant 4

```text
NVIDIA / Matching / Deploy
```

## Participant 5

```text
Integration / QA / Demo / README
```

У каждого должны быть реальные commits.

---

# 39. Порядок реализации MVP

Работу лучше строить по этапам, не привязывая продукт к жёсткому таймингу.

## Этап 1 — Основа проекта

- получить командный репозиторий;
- создать `frontend` и `backend`;
- сразу создать `docker-compose.yml`;
- поднять PostgreSQL 16 в Docker;
- подключить async SQLAlchemy + asyncpg;
- инициализировать Alembic;
- добавить `.gitignore`;
- создать `.env.example`;
- поднять `/api/v1/health`;
- убедиться, что frontend открывается.

Результат этапа:

```text
docker compose up
↓
PostgreSQL healthy
↓
FastAPI /api/v1/health = 200
↓
Frontend открывается
```

## Этап 2 — AI-анализ бизнес-задачи

Реализовать:

```text
Raw business idea
↓
FastAPI
↓
OpenAI
↓
Structured JSON
↓
Quality Score
↓
UI feedback
```

На этом этапе уже должен работать главный AI-анализ.

## Этап 3 — AI Interview + Task Builder

Добавить:

- уточняющие вопросы;
- ответы пользователя;
- повторный анализ;
- пересчёт рейтинга;
- финальную структурированную карточку.

## Этап 4 — Publish + Catalog

Добавить:

- сохранение задачи;
- публикацию;
- открытый каталог;
- сортировку по Quality Score;
- страницу подробной задачи.

## Этап 5 — Student Apply

Добавить:

- просмотр задачи;
- форму предложения;
- сохранение proposal;
- статус отклика.

## Этап 6 — Business Selection

Добавить:

- список предложений;
- просмотр команды;
- выбор команды;
- транзакционное обновление статусов.

После этого обязательный end-to-end MVP уже готов.

## Этап 7 — NVIDIA Matching

Если основной flow работает стабильно, добавить:

- embeddings;
- task ↔ team similarity;
- match score;
- причины рекомендации.

## Этап 8 — UI polish

Добавить:

- score animation;
- loading states;
- badges;
- empty states;
- task evolution;
- аккуратные transition-анимации.

## Этап 9 — Deployment и проверка

- задеплоить frontend;
- задеплоить backend;
- подключить PostgreSQL;
- проверить env variables;
- проверить production URL;
- пройти demo-сценарий несколько раз;
- обновить README;
- сделать финальный push.


# 40. P0 / P1 / P2

## P0 — обязательно

- Create draft
- AI Analyze
- Quality Score
- Improve
- Publish
- Catalog
- Apply
- Select Team

## P1 — после P0

- NVIDIA matching
- animations
- badges
- task evolution
- AI student simulator

## P2 — только если осталось время

- filters
- search
- portfolio links
- extra dashboard metrics

---

# 41. Demo Data

Заранее придумать 3–5 синтетических задач.

## Task 1

```text
AI-классификация заявок
Score: 92
```

## Task 2

```text
Система прогнозирования спроса
Score: 85
```

## Task 3

```text
Cybersecurity awareness assistant
Score: 78
```

## Task 4

```text
Computer Vision для контроля склада
Score: 88
```

---

# 42. Seed Team

```text
Team Alpha

Skills:
Python
FastAPI
React
LLM
PostgreSQL
Docker
```

Это позволит показать matching.

---

# 43. Демонстрационный сценарий

# Шаг 1 — плохая задача

Ввод:

> Хотим автоматизировать обработку заявок.

Нажать:

```text
Analyze with AI
```

---

# Шаг 2 — показать низкий score

```text
Quality Score
29/100
```

Сказать:

> "Система не просто проверяет, заполнены ли поля. Она анализирует, достаточно ли информации студенту для начала работы."

---

# Шаг 3 — ответить на вопросы

AI:

> Сколько заявок поступает ежедневно?

Ответ:

> Около 500.

AI:

> Какой результат будет считаться успешным?

Ответ:

> Автоматически обрабатывать не менее 60%.

AI:

> Какие данные доступны?

Ответ:

> Обезличенные примеры обращений.

---

# Шаг 4 — рост рейтинга

Показать:

```text
29 → 51 → 73 → 91
```

Сказать:

> "Это и есть основная геймификация: бизнес видит, как качество задачи растёт."

---

# Шаг 5 — Publish

Показать финальную карточку.

Нажать:

```text
Publish Challenge
```

---

# Шаг 6 — Student Mode

Переключиться.

Показать, что задача появилась в каталоге.

---

# Шаг 7 — Recommendation

```text
Recommended for Team Alpha
90%
```

Сказать:

> "Система только рекомендует. Решение остаётся за студентом."

---

# Шаг 8 — Apply

Заполнить короткое предложение.

Нажать:

```text
Submit Proposal
```

---

# Шаг 9 — Business Mode

Открыть proposals.

Показать Team Alpha.

---

# Шаг 10 — Select

Нажать:

```text
Select Team
```

Финал:

```text
Challenge matched successfully
```

---

# 44. Короткий demo pitch


> "Сегодня бизнес часто формулирует задачи слишком общо. Студенты получают непонятные требования и тратят время на уточнения."


> "SanaChallenge AI превращает сырую бизнес-потребность в student-ready challenge."


Показать:

```text
raw idea
→ analyze
→ 29/100
→ AI questions
→ 91/100
```


Показать publish.


Student mode + catalog + recommendation.


Apply.


Business selects team.


> "AI improves quality and recommendations, but humans keep the final choice."

---

# 45. Ключевые фразы для жюри

> "Мы не оцениваем наличие текста — мы оцениваем его полезность для выполнения."

> "Score объясним: каждый балл связан с конкретным критерием."

> "AI не назначает студентам проекты, а только помогает найти релевантные."

> "Бизнес получает мотивацию улучшать качество постановки задачи."

> "Чем выше качество задачи, тем выше её позиция в каталоге."

> "Мы сокращаем разрыв между языком бизнеса и языком команды-разработчика."

---

# 46. README — обязательная структура

```markdown
# SanaChallenge AI

## 1. О проекте

## 2. Проблема

## 3. Решение

## 4. Основные функции

## 5. Пользовательский сценарий

## 6. Quality Score

## 7. AI Architecture

## 8. NVIDIA Integration

## 9. Технологии

## 10. Архитектура

## 11. Структура проекта

## 12. Установка

## 13. Environment Variables

## 14. Запуск

## 15. Как проверить решение

## 16. Demo Scenario

## 17. Данные и внешние сервисы

## 18. Ограничения

## 19. Deployment
```

---

# 47. Установка и запуск — Docker First

Основной способ запуска проекта:

```bash
git clone <team-repository>
cd sana-challenge-ai

cp .env.example .env

docker compose up --build
```

После запуска:

```text
Frontend    → http://localhost:5173
Backend API → http://localhost:8000
Swagger     → http://localhost:8000/docs
PostgreSQL  → internal Docker network
```

## docker-compose должен поднимать

```text
postgres
backend
frontend
```

Опционально:

```text
nvidia-matching-service
```

## Миграции

После старта PostgreSQL:

```bash
docker compose exec backend alembic upgrade head
```

## Seed demo data

```bash
docker compose exec backend python scripts/seed_demo_data.py
```

Локальный запуск без Docker допускается только для разработки/отладки отдельного участника, но **официальный reproducible запуск проекта должен быть через Docker Compose**.

---

# 48. Health endpoint

Обязательно:

```text
GET /api/health
```

Ответ:

```json
{
  "status": "ok"
}
```

Это сильно помогает во время deploy/debug.

---

# 49. Error Handling

Если OpenAI недоступен:

```text
AI service is temporarily unavailable.
You can continue editing the task manually.
```

Не делать весь продукт полностью зависимым от AI.

---

# 50. Local fallback

Нужно иметь возможность запустить:

```text
frontend → localhost
backend → localhost
database → local
```

Если облако временно недоступно, demo всё равно можно открыть локально.

---

# 51. Network / оборудование

До хакатона проверить:

```bash
git --version
node --version
npm --version
python --version
docker --version
docker compose version
```

Также заранее проверить:

- GitHub access;
- OpenAI Platform;
- NVIDIA account;
- Brev;
- NVIDIA Build;
- Vercel;
- IDE;
- Ethernet adapter.

---

# 52. OpenAI Credits

OpenAI credits использовать прежде всего для:

- analyze task;
- generate questions;
- improve task;
- validate measurable criteria.

Не нужно делать десятки AI-запросов на каждый экран.

---

# 53. Экономия API

На один challenge достаточно:

```text
1 × initial analysis
1–3 × question/answer refresh
1 × final rewrite
```

То есть примерно 3–5 вызовов.

---

# 54. NVIDIA Credits

Brev использовать как:

```text
GPU recommendation service
```

а не как обязательный backend всего приложения.

Почему:

- если Brev падает, основной MVP продолжает работать;
- matching — полезная, но не критическая P0-функция;
- проще объяснить архитектуру.

---

# 55. UI стиль

Рекомендуемый стиль:

- очень чистый;
- светлый;
- dark navy / graphite;
- glass cards;
- большие числа score;
- минимум визуального шума;
- мягкие animations;
- цвет score меняется по уровню.

Пример:

```text
0–39   red
40–59  orange
60–79  yellow
80–89  blue
90–100 green
```

---

# 56. Самый важный экран

Экран улучшения задачи должен быть лучшим в продукте.

Макет:

```text
┌──────────────────────────────────────────────┐
│ Challenge Builder                  74/100    │
├──────────────────────┬───────────────────────┤
│                      │                       │
│ AI Interview         │ Live Task Preview     │
│                      │                       │
│ Question 2 of 3      │ Problem       12/15   │
│                      │ Goal          13/15   │
│ [ answer... ]        │ Metrics        7/15   │
│                      │ Timeline       5/10   │
│ [ Continue ]         │                       │
│                      │ +18 available         │
└──────────────────────┴───────────────────────┘
```

---

# 57. Task Evolution

Добавить при наличии времени:

```text
Task Evolution

29  Initial draft
│
51  Business problem clarified
│
73  Success metrics added
│
91  Scope and constraints completed
```

Очень хороший visual storytelling.

---

# 58. Metrics dashboard — опционально

Для бизнеса:

```text
Quality Score        91
Views                28
Proposals              5
Recommended matches   12
```

Не обязательно.

---

# 59. Проверка готовности

Перед сдачей пройти этот чеклист.

## Core

- [ ] Сырая идея создаётся
- [ ] OpenAI анализирует
- [ ] Score отображается
- [ ] Reasons отображаются
- [ ] Questions работают
- [ ] Score меняется
- [ ] Final brief генерируется
- [ ] Publish работает
- [ ] Task виден в catalog
- [ ] Student apply работает
- [ ] Business видит proposal
- [ ] Business select работает

## Technical

- [ ] `.env` не в Git
- [ ] API keys не в frontend
- [ ] PostgreSQL используется как основная БД
- [ ] Alembic migrations проходят с нуля
- [ ] Backend использует async SQLAlchemy + asyncpg
- [ ] OpenAI вызывается асинхронно
- [ ] Docker Compose поднимает frontend/backend/postgres
- [ ] Clean Architecture соблюдена
- [ ] Production URL работает
- [ ] `/api/v1/health` работает
- [ ] README актуален
- [ ] Demo data есть
- [ ] Нет console errors
- [ ] Нет broken buttons

## Demo

- [ ] Demo account / mode работает
- [ ] Demo challenge заранее подготовлен
- [ ] Demo проходит быстро и без лишних шагов
- [ ] Все участники знают свои 20–30 секунд выступления
- [ ] Есть backup local version

---

# 60. Что можно убрать, если нужно упростить MVP

Удалять в таком порядке:

1. animations;
2. badges;
3. advanced filters;
4. Task Simulator;
5. NVIDIA semantic matching;
6. user profiles.

Никогда не удалять:

```text
Draft
→ Analyze
→ Score
→ Improve
→ Publish
→ Catalog
→ Apply
→ Select
```

Это ядро кейса.

---

# 61. Финальная архитектурная стратегия

## P0 — профессиональное ядро

```text
React + TypeScript
+
FastAPI async
+
PostgreSQL
+
SQLAlchemy Async
+
asyncpg
+
Alembic
+
OpenAI Async API
+
Docker Compose
+
Clean Architecture
```

Это не optional. Это базовый стандарт проекта.

## P1

```text
NVIDIA Brev
+
Embeddings
+
Matching
+
optional NVIDIA NIM
```

## P2

```text
Animations
+
badges
+
task evolution
+
advanced filters
```

---

# 61.1. Engineering Standards — обязательные требования

Платформа должна создаваться как **маленький профессиональный продукт**, а не набор несвязанных экранов.

## Async-first backend

Обязательно:

```python
async def create_task(...):
    ...

result = await service.analyze(...)
```

Использовать:

```text
FastAPI async endpoints
SQLAlchemy AsyncSession
asyncpg
httpx.AsyncClient
AsyncOpenAI
asyncio.gather() там, где запросы независимы
```

### Где полезен `asyncio.gather`

Например после публикации задачи можно параллельно:

```text
generate embedding
+
calculate recommendations
+
save score history
```

Но не нужно делать параллельность там, где операции зависят друг от друга.

## Performance

Требования:

- не выполнять blocking I/O внутри async endpoint;
- переиспользовать HTTP clients;
- использовать connection pooling PostgreSQL;
- добавлять DB indexes;
- ограничивать количество AI-запросов;
- не пересчитывать embeddings без необходимости;
- использовать pagination для каталога;
- возвращать только необходимые поля.

## Clean Code

Обязательно:

- type hints;
- небольшие функции;
- понятные имена;
- никакого дублирования scoring logic;
- единая обработка ошибок;
- logging вместо `print`;
- конфигурация только через environment variables;
- Pydantic Settings для config;
- единый API response/error style.

## Repository pattern

API router не должен работать с SQLAlchemy напрямую.

Правильно:

```text
Router
 ↓
Use Case
 ↓
Repository Interface
 ↓
PostgreSQL Repository
```

## Dependency Injection

FastAPI dependencies использовать для:

- DB session;
- services;
- repositories;
- current role/demo user;
- external clients.

## Transactions

Критичные операции должны быть транзакционными:

```text
Publish Challenge
Select Team
Create Proposal
Update Score History
```

## PostgreSQL indexes

Минимум:

```text
tasks(status)
tasks(quality_score DESC)
tasks(published_at DESC)
tasks(business_id)
proposals(task_id)
proposals(team_id)
matches(task_id, final_score DESC)
```

## Logging

Минимум логировать:

```text
request errors
OpenAI errors
NVIDIA errors
DB transaction errors
publish/select actions
```

Но никогда не логировать:

```text
API keys
tokens
passwords
confidential business text if not needed
```

## Tests

Даже в рамках MVP желательно иметь минимум:

```text
test_quality_score
test_publish_task
test_submit_proposal
test_select_team
```

Особенно проверить scoring engine, потому что это ядро продукта.

## API design

Использовать versioning:

```text
/api/v1/...
```

Например:

```text
POST /api/v1/tasks
POST /api/v1/tasks/{id}/analyze
POST /api/v1/tasks/{id}/publish
GET  /api/v1/tasks
POST /api/v1/tasks/{id}/proposals
POST /api/v1/proposals/{id}/select
```

## Docker requirements

Нужны минимум:

```text
frontend/Dockerfile
backend/Dockerfile
docker-compose.yml
```

Контейнеры должны общаться через Docker network.

PostgreSQL:

```text
postgres:16-alpine
```

Backend не должен ждать БД "наугад". Добавить healthcheck для PostgreSQL и `depends_on` с health condition, если это поддерживается используемой Compose-схемой.

## Production readiness

Даже в hackathon MVP:

- `/api/v1/health`;
- `.env.example`;
- migrations;
- structured logging;
- CORS config;
- graceful error handling;
- Dockerized start;
- README commands;
- seed data;
- никакого hardcode секретов.

---

# 62. Почему это сильное решение

Оно:

1. напрямую соответствует кейсу;
2. показывает настоящую геймификацию бизнеса;
3. использует AI не декоративно;
4. имеет прозрачный рейтинг;
5. не нарушает принцип самостоятельного выбора студентами;
6. даёт ценность и бизнесу, и студентам;
7. реально собирается как компактный профессиональный MVP;
8. позволяет показать OpenAI и NVIDIA;
9. имеет понятный wow-effect;
10. легко легко демонстрируется.

---

# 63. Главная формулировка проекта

> **SanaChallenge AI — это AI-платформа, которая помогает бизнесу превратить сырую потребность в качественную, измеримую и понятную студентам задачу, оценивает её готовность, публикует в открытом каталоге и помогает релевантным студенческим командам найти её, сохраняя финальный выбор за людьми.**

---

# 64. Самый короткий MVP

Минимальная версия MVP должна обязательно содержать:

```text
Business enters text
↓
OpenAI analyses it
↓
Score appears
↓
Business improves it
↓
Publish
↓
Student sees it
↓
Student applies
↓
Business selects
```

Даже такой вариант уже является полноценным работающим решением кейса.

---

# 65. Официальные организационные ограничения, которые нужно учитывать

На основе предоставленных инструкций HackAlem:

- итоговый код должен быть отправлен в командный GitHub-репозиторий;
- AI-агент должен реально использоваться в процессе разработки;
- README должен описывать только реально реализованные функции;
- проект должен быть создан в рамках хакатона;
- каждый участник должен внести личный вклад;
- нельзя публиковать API-ключи, токены и пароли;
- нельзя загружать конфиденциальные или реальные персональные данные в сторонние сервисы без разрешения;
- необходимо самостоятельно проверять AI-generated результаты;
- лучше заранее подготовить IDE, Git, SDK, Docker и сетевой адаптер;
- нужно иметь локальный fallback на случай проблем с внешним доступом.

---

# 66. Итоговый порядок действий команды

```text
1. Получить repo
2. Создать skeleton
3. Поднять backend
4. Поднять frontend
5. Подключить OpenAI
6. Сделать Quality Score
7. Сделать AI Interview
8. Сделать publish
9. Сделать catalog
10. Сделать proposal
11. Сделать select team
12. Добавить NVIDIA matching
13. Задеплоить
14. Пройти demo
15. Дополнить README
16. Final push
17. Сдать решение
```

---

# 67. Критическое правило хакатона

> **Не делайте много функций. Сделайте один обязательный end-to-end сценарий настолько хорошо, чтобы его невозможно было сломать во время демонстрации.**

Главный сценарий:

```text
Raw Business Need
        ↓
AI Challenge Builder
        ↓
Quality Score
        ↓
Improve
        ↓
Publish
        ↓
Open Catalog
        ↓
Student Choice
        ↓
Proposal
        ↓
Business Decision
```

Это и есть ядро SanaChallenge AI.
