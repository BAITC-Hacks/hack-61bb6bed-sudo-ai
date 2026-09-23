import {
  interviewRequest,
  type InterviewPlan,
  type CoachReply,
} from "../api/interview";
import { useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, Check, Sparkles } from "lucide-react";
import { labels, type Brief, type BriefField, type Skill } from "../api/types";
import { ErrorBox, FormField } from "./UI";
export const deckFields: BriefField[] = [
  "problem", "target_users", "goal", "deliverable", "success_criteria",
  "constraints", "resources", "timeline", "risk_context", "title",
];
const requiredFields = [
  "title",
  "problem",
  "goal",
  "deliverable",
  "success_criteria",
  "timeline",
];
const questions: Record<BriefField, string> = {
  title: "Как назовём вашу задачу?",
  problem: "Какую проблему нужно решить?",
  goal: "Что должно измениться?",
  deliverable: "Что команда должна создать?",
  success_criteria: "Как вы поймёте, что всё получилось?",
  target_users: "Кто будет пользоваться решением?",
  constraints: "Какие ограничения нужно учесть?",
  timeline: "Сколько времени есть на проект?",
  resources: "Какие данные и ресурсы доступны?",
  risk_context: "Какие риски важно учесть?",
};
const hints: Record<BriefField, string> = {
  title: "Короткое и понятное название.",
  problem: "Что сейчас не работает? Опишите ситуацию и её масштаб.",
  goal: "Какого результата ждёт бизнес?",
  deliverable: "Например: прототип, API или аналитический отчёт.",
  success_criteria: "Укажите измеримый результат: точность, время или объём.",
  target_users: "Для кого вы создаёте решение?",
  constraints: "Бюджет, технологии, доступы или другие условия.",
  timeline: "Укажите срок и объём первой версии.",
  resources: "Данные, эксперты, оборудование или готовые материалы.",
  risk_context: "Персональные данные, безопасность и возможные сложности.",
};
export function TaskDeck({
  taskId,
  revision,
  brief,
  slugs,
  skills,
  skillsError,
  busy,
  step,
  onStep,
  onBrief,
  onSkills,
  onSave,
}: {
  taskId: string;
  revision: number;
  brief: Brief;
  slugs: string[];
  skills?: Skill[];
  skillsError: string;
  busy: boolean;
  step: number;
  onStep: (step: number) => void;
  onBrief: (brief: Brief) => void;
  onSkills: (slugs: string[]) => void;
  onSave: () => Promise<unknown>;
}) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [direction, setDirection] = useState(1);
  const heading = useRef<HTMLHeadingElement>(null);
  const field = deckFields[step];
  const isSkills = step === deckFields.length;
  const locked = busy || saving;
  const [plan, setPlan] = useState<InterviewPlan>();
  const [planError, setPlanError] = useState("");
  const [manual, setManual] = useState(false);
  const ready = plan?.source === "openai" && deckFields.every(
    (f) => plan.questions.some((q) => q.field === f && q.question.trim()),
  );
  useEffect(() => {
    heading.current?.focus({ preventScroll: true });
  }, [step, ready, manual]);
  const [coach, setCoach] = useState<{
    reply: CoachReply;
    answer: string;
    extra: string;
  }>();
  const [coaching, setCoaching] = useState(false);
  const [coachError, setCoachError] = useState("");
  const [clarification, setClarification] = useState("");
  const [round, setRound] = useState(0);
  const requestSequence = useRef(0);
  const live = useRef({
    answer: field ? brief[field] : "",
    field,
    revision,
    clarification,
  });
  live.current = {
    answer: field ? brief[field] : "",
    field,
    revision,
    clarification,
  };
  useEffect(() => {
    let active = true;
    setManual(false);
    setPlan(undefined);
    setPlanError("");
    interviewRequest<InterviewPlan>(`/tasks/${taskId}/interview`)
      .then((p) => {
        if (active) setPlan(p);
      })
      .catch((e) => {
        if (active) setPlanError(e.message);
      });
    return () => {
      active = false;
    };
  }, [taskId, round]);
  useEffect(() => {
    const sequence = ++requestSequence.current;
    setCoach(undefined);
    setCoachError("");
    setClarification("");
    setCoaching(false);
    if (isSkills || !plan || plan.source !== "openai") return;
    const answer = live.current.answer;
    setCoaching(true);
    interviewRequest<CoachReply>(`/tasks/${taskId}/coach`, {
      field,
      answer,
      expected_revision: revision,
    })
      .then((reply) => {
        if (sequence === requestSequence.current)
          setCoach({ reply, answer, extra: "" });
      })
      .catch((e) => {
        if (sequence === requestSequence.current) setCoachError(e.message);
      })
      .finally(() => {
        if (sequence === requestSequence.current) setCoaching(false);
      });
    return () => {
      requestSequence.current++;
    };
  }, [taskId, field, revision, plan, isSkills]);
  const question = plan?.questions.find((q) => q.field === field);
  const fresh =
    coach &&
    coach.answer === brief[field] &&
    coach.extra === clarification &&
    coach.reply.revision === revision;
  async function help() {
    const sequence = ++requestSequence.current;
    const answer = brief[field];
    const extra = clarification;
    setCoaching(true);
    setCoachError("");
    try {
      const reply = await interviewRequest<CoachReply>(
        `/tasks/${taskId}/coach`,
        { field, answer, clarification: extra, expected_revision: revision },
      );
      if (sequence === requestSequence.current)
        setCoach({ reply, answer, extra });
    } catch (e) {
      if (sequence === requestSequence.current)
        setCoachError((e as Error).message);
    } finally {
      if (sequence === requestSequence.current) setCoaching(false);
    }
  }
  async function move(target: number) {
    if (locked) return;
    setSaving(true);
    setError("");
    try {
      await onSave();
      setDirection(target > step ? 1 : -1);
      onStep(target);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }
  function retry() {
    setManual(false);
    setPlan(undefined);
    setPlanError("");
    setRound((r) => r + 1);
  }
  if (!ready && !manual && !isSkills) {
    const failed = Boolean(plan || planError);
    return (
      <section className="deck-preparation" aria-busy={!failed}>
        <div className={`deck-preparation-icon ${failed ? "" : "is-pending"}`} aria-hidden="true">
          <Sparkles size={32} />
        </div>
        <h1>{failed ? "Не удалось подготовить вопросы" : "Готовим вопросы по вашей идее"}</h1>
        <p role="status">{failed
          ? "Попробуйте ещё раз или заполните задачу с обычными вопросами."
          : "AI изучает вашу потребность. Карточки появятся, когда вопросы будут готовы."}</p>
        {failed && <div className="deck-preparation-actions">
          <button className="btn" type="button" onClick={retry}>Попробовать ещё раз</button>
          <button className="btn secondary" type="button" onClick={() => setManual(true)}>Продолжить без AI</button>
        </div>}
      </section>
    );
  }
  return (
    <div className="task-deck">
      {manual && <div className="ai-deck-status">Обычные вопросы · AI недоступен
        <button type="button" onClick={retry}>Повторить запрос AI</button>
      </div>}
      {plan?.source === "openai" && (
        <div className="ai-deck-status">
          <Sparkles size={17} />
          Вопросы по вашей идее
        </div>
      )}
      <div className="deck-progress">
        <span>
          Карточка {step + 1} из {deckFields.length + 1}
        </span>
        <span>
          {isSkills
            ? "Навыки команды"
            : requiredFields.includes(field)
              ? "Обязательно для публикации"
              : "Необязательно"}
        </span>
      </div>
      <div
        className="deck-meter"
        role="progressbar"
        aria-label="Заполнение карточек"
        aria-valuemin={0}
        aria-valuemax={deckFields.length + 1}
        aria-valuenow={step + 1}
      >
        <span
          style={{ width: `${((step + 1) / (deckFields.length + 1)) * 100}%` }}
        />
      </div>
      <div className="deck-stack">
        <span className="deck-under second" aria-hidden="true" />
        <span className="deck-under first" aria-hidden="true" />
        <form
          key={step}
          className={`deck-card ${direction < 0 ? "reverse" : ""}`}
          onSubmit={(e) => {
            e.preventDefault();
            void move(step + 1);
          }}
        >
          <div className="deck-card-top">
            <span>SANA / ЗАДАЧА</span>
            <strong>{String(step + 1).padStart(2, "0")}</strong>
          </div>
          <h1 ref={heading} tabIndex={-1}>
            {isSkills
              ? "Какие навыки нужны команде?"
              : question?.question || questions[field]}
          </h1>
          <p>
            {isSkills
              ? "Выберите подходящие навыки. Это можно уточнить позже."
              : question?.hint || hints[field]}
          </p>
          {isSkills ? (
            <>
              <ErrorBox message={skillsError} />
              <div className="deck-skills">
                {skills?.map((skill) => (
                  <label
                    key={skill.slug}
                    className={slugs.includes(skill.slug) ? "selected" : ""}
                  >
                    <input
                      type="checkbox"
                      checked={slugs.includes(skill.slug)}
                      disabled={locked}
                      onChange={(e) =>
                        onSkills(
                          e.target.checked
                            ? [...slugs, skill.slug]
                            : slugs.filter((s) => s !== skill.slug),
                        )
                      }
                    />
                    {skill.name}
                    {slugs.includes(skill.slug) && <Check size={16} />}
                  </label>
                ))}
              </div>
            </>
          ) : (
            <FormField
              label={
                labels[field] + (requiredFields.includes(field) ? " *" : "")
              }
            >
              {field === "title" ? (
                <input
                  disabled={locked}
                  value={brief[field]}
                  maxLength={200}
                  onChange={(e) =>
                    onBrief({ ...brief, [field]: e.target.value })
                  }
                  placeholder="Название вашего проекта"
                />
              ) : (
                <textarea
                  disabled={locked}
                  rows={5}
                  value={brief[field]}
                  maxLength={8000}
                  onChange={(e) =>
                    onBrief({ ...brief, [field]: e.target.value })
                  }
                  placeholder="Ваш ответ…"
                />
              )}
            </FormField>
          )}
          {!isSkills && (
            <section className="card-coach" aria-label="Помощник AI">
              <div className="coach-top">
                <strong>
                  <Sparkles size={18} />
                  Помощник AI
                </strong>
                <button
                  type="button"
                  className="btn secondary small"
                  disabled={locked || coaching}
                  onClick={() => void help()}
                >
                  {coaching ? "Думает…" : "Помочь с ответом"}
                </button>
              </div>
              {coaching && (
                <p role="status">Учитываю вашу идею и предыдущие ответы…</p>
              )}
              <ErrorBox message={coachError} />
              {coach?.reply.warning && <p>{coach.reply.warning}</p>}
              {!!coach?.reply.followups.length && (
                <>
                  <ul>
                    {coach.reply.followups.map((q) => (
                      <li key={q}>{q}</li>
                    ))}
                  </ul>
                  <label className="coach-extra">
                    Уточните детали
                    <textarea
                      value={clarification}
                      onChange={(e) => setClarification(e.target.value)}
                      maxLength={8000}
                      rows={2}
                      placeholder="Ответьте на уточнения здесь…"
                      disabled={locked || coaching}
                    />
                  </label>
                  <button
                    type="button"
                    className="btn secondary small"
                    disabled={locked || coaching || !clarification.trim()}
                    onClick={() => void help()}
                  >
                    Учесть уточнение
                  </button>
                </>
              )}
              {fresh && coach.reply.suggestion && (
                <div className="coach-suggestion">
                  <span>Вариант формулировки</span>
                  <p>{coach.reply.suggestion}</p>
                  <button
                    type="button"
                    className="btn secondary"
                    disabled={locked || coaching}
                    onClick={() => {
                      onBrief({ ...brief, [field]: coach.reply.suggestion });
                      setClarification("");
                      setCoach(undefined);
                    }}
                  >
                    Использовать этот ответ
                  </button>
                </div>
              )}
              <small>
                AI предлагает — вы подтверждаете. Проверьте факты перед
                применением.
              </small>
            </section>
          )}
          <ErrorBox message={error} />
          <div className="deck-controls">
            <button
              type="button"
              className="btn secondary"
              disabled={locked || step === 0}
              onClick={() => void move(step - 1)}
            >
              <ArrowLeft size={17} />
              Назад
            </button>
            <span>
              {saving ? "Сохраняем…" : "Ответы сохраняются при переходе"}
            </span>
            <button className="btn" disabled={locked}>
              {isSkills ? "К проверке" : "Далее"}
              <ArrowRight size={17} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
