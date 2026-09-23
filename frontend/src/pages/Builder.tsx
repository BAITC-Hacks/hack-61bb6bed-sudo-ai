import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  ArrowUpRight,
  Save,
  Sparkles,
  Send,
  Check,
  Lightbulb,
} from "lucide-react";
import { api, patch, post } from "../api/client";
import {
  labels,
  type Brief,
  type BriefField,
  type Task,
  type Skill,
} from "../api/types";
import { useLoad } from "../hooks/useLoad";
import { useAuth } from "../app/Auth";
import { ErrorBox, FormField, Heading, Loading } from "../components/UI";
export function NewTask() {
  const nav = useNavigate();
  const { user } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function create(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(e.currentTarget);
    try {
      const task = await post<Task>("/tasks/draft", {
        raw_text: data.get("idea"),
      });
      nav(`/tasks/${task.id}/edit`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (user?.role !== "business")
    return <ErrorBox message="Создавать задачи могут представители бизнеса." />;
  return (
    <>
      <Link to="/dashboard" className="back-link">
        <ArrowLeft size={16} />
        Мои задачи
      </Link>
      <Heading
        eyebrow="ШАГ 01 / ВАША ИДЕЯ"
        title="Какой вызов стоит перед бизнесом?"
        subtitle="Начните своими словами. Мы поможем превратить идею в понятную задачу."
      />
      <div className="builder-grid">
        <section className="panel">
          <ErrorBox message={error} />
          <form onSubmit={create}>
            <FormField
              label="Расскажите о вашей потребности"
              hint="Не обязательно знать техническое решение. Опишите проблему и желаемые изменения."
            >
              <textarea
                autoFocus
                name="idea"
                required
                minLength={3}
                maxLength={8000}
                rows={10}
                placeholder="Например: наша команда вручную обрабатывает 500 обращений в день. Хотим автоматизировать сортировку, чтобы операторы отвечали быстрее…"
              />
            </FormField>
            <button disabled={busy} className="btn">
              {busy ? "Создаём черновик…" : "Создать черновик"}
              <ArrowUpRight size={18} />
            </button>
          </form>
        </section>
        <aside className="guide-card">
          <Lightbulb size={26} />
          <h2>С чего начать?</h2>
          <p>Хорошее описание отвечает на три простых вопроса:</p>
          <ol>
            <li>Что сейчас не работает или отнимает время?</li>
            <li>На кого это влияет?</li>
            <li>Какой результат вы хотите получить?</li>
          </ol>
          <p className="small-text">
            Черновик виден только вам. Задача появится в каталоге после
            публикации.
          </p>
        </aside>
      </div>
    </>
  );
}
export function Builder() {
  const { id } = useParams();
  const nav = useNavigate();
  const { user } = useAuth();
  const load = useLoad(() => api<Task>(`/tasks/${id}`), [id]);
  const skills = useLoad(() => api<Skill[]>("/skills"));
  const [brief, setBrief] = useState<Brief>();
  const [slugs, setSlugs] = useState<string[]>([]);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  useEffect(() => {
    if (load.data) {
      setBrief(load.data.brief);
      setSlugs(load.data.skill_slugs);
      setDirty(false);
    }
  }, [load.data]);
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty]);
  const history = useLoad(
    () =>
      api<{ revision: number; score: number; reason: string }[]>(
        `/tasks/${id}/score-history`,
      ),
    [id, load.data?.revision],
  );
  if (load.loading || !brief)
    return load.error ? <ErrorBox message={load.error} /> : <Loading />;
  const task = load.data!;
  if (task.business_id !== user?.id)
    return (
      <ErrorBox message="Эту карточку может редактировать только её автор." />
    );
  if (task.status !== "draft")
    return (
      <section className="panel">
        <h2>Задача уже опубликована</h2>
        <Link className="btn" to={`/tasks/${id}`}>
          Открыть карточку
        </Link>
      </section>
    );
  async function save() {
    if (!dirty) return task;
    const result = await patch<Task>(`/tasks/${id}`, {
      ...brief,
      skill_slugs: slugs,
      expected_revision: task.revision,
    });
    load.setData(result);
    setDirty(false);
    return result;
  }
  async function action(kind: string, field?: BriefField) {
    setBusy(kind);
    setError("");
    setMessage("");
    try {
      await save();
      if (kind === "save") {
        setMessage("Черновик сохранён.");
        return;
      }
      if (kind === "publish") {
        await post(`/tasks/${id}/publish`);
        nav(`/tasks/${id}`);
        return;
      }
      const result = await post<Task>(
        `/tasks/${id}/${kind}`,
        kind === "answer" ? { field, answer: answers[field!] } : undefined,
      );
      load.setData(result);
      if (field) setAnswers((a) => ({ ...a, [field]: "" }));
      setMessage("Карточка обновлена.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  const assessment = dirty ? null : task.assessment;
  return (
    <>
      <Link className="back-link" to="/dashboard">
        <ArrowLeft size={16} />
        Мои задачи
      </Link>
      <Heading
        eyebrow="КОНСТРУКТОР ЗАДАЧИ"
        title={brief.title || "Сделаем вашу идею понятной"}
        subtitle="Уточните детали, оцените готовность и опубликуйте задачу."
        action={
          <span className="badge">
            {dirty
              ? "Есть несохранённые изменения"
              : "Черновик · виден только вам"}
          </span>
        }
      />
      <ErrorBox message={error} />
      {message && (
        <div className="alert success" role="status">
          <Check size={17} />
          {message}
        </div>
      )}
      <div className="builder-toolbar">
        <button
          className="btn secondary"
          disabled={!!busy}
          onClick={() => action("save")}
        >
          <Save size={17} />
          {busy === "save" ? "Сохраняем…" : "Сохранить"}
        </button>
        <button
          className="btn secondary"
          disabled={!!busy}
          onClick={() => action("analyze")}
        >
          <Sparkles size={17} />
          {busy === "analyze" ? "Анализируем…" : "Оценить задачу"}
        </button>
        <button
          className="btn secondary"
          disabled={!!busy}
          onClick={() => action("improve")}
        >
          <Sparkles size={17} />
          {busy === "improve" ? "Улучшаем…" : "Улучшить с AI"}
        </button>
        <button
          className="btn"
          disabled={!!busy || !assessment}
          onClick={() => action("publish")}
        >
          <Send size={17} />
          {busy === "publish" ? "Публикуем…" : "Опубликовать"}
        </button>
      </div>
      <div className="builder-grid">
        <section className="panel">
          <h2>Карточка задачи</h2>
          <p className="muted small-text">
            Опишите только известные факты. Поля можно заполнить постепенно.
          </p>
          {(Object.keys(labels) as BriefField[]).map((field) => (
            <FormField
              key={field}
              label={
                labels[field] +
                ([
                  "title",
                  "problem",
                  "goal",
                  "deliverable",
                  "success_criteria",
                  "timeline",
                ].includes(field)
                  ? " *"
                  : "")
              }
            >
              {field === "title" ? (
                <input
                  disabled={!!busy}
                  value={brief[field]}
                  maxLength={200}
                  onChange={(e) => {
                    setBrief({ ...brief, [field]: e.target.value });
                    setDirty(true);
                  }}
                />
              ) : (
                <textarea
                  disabled={!!busy}
                  rows={field === "problem" ? 4 : 2}
                  maxLength={8000}
                  value={brief[field]}
                  onChange={(e) => {
                    setBrief({ ...brief, [field]: e.target.value });
                    setDirty(true);
                  }}
                />
              )}
            </FormField>
          ))}
          <div className="field">
            <span>Какие навыки нужны команде?</span>
            <div className="skill-picker">
              {skills.data?.map((s) => (
                <label key={s.slug}>
                  <input
                    type="checkbox"
                    disabled={!!busy}
                    checked={slugs.includes(s.slug)}
                    onChange={(e) => {
                      setSlugs(
                        e.target.checked
                          ? [...slugs, s.slug]
                          : slugs.filter((x) => x !== s.slug),
                      );
                      setDirty(true);
                    }}
                  />
                  {s.name}
                </label>
              ))}
            </div>
          </div>
          <p className="muted small-text">
            * Обязательно для публикации. После изменений оцените карточку ещё
            раз.
          </p>
        </section>
        <aside className="builder-aside">
          <section className="panel score-panel">
            <div className="eyebrow">ГОТОВНОСТЬ ЗАДАЧИ</div>
            <div className="big-score">
              {assessment?.total ?? "—"}
              <small>/ 100</small>
            </div>
            <span className="badge">{assessment?.level || "Нужна оценка"}</span>
            <p className="muted small-text">
              Чем понятнее задача, тем легче команде предложить решение.
            </p>
            {assessment?.warning && (
              <div className="alert info">{assessment.warning}</div>
            )}
            {assessment && (
              <div className="criteria">
                {Object.entries(assessment.scores).map(([key, score]) => (
                  <div key={key} title={score.reason}>
                    <div>
                      <span>{labels[key as BriefField]}</span>
                      <strong>
                        {score.score}/{score.maximum}
                      </strong>
                    </div>
                    <div className="meter">
                      <span
                        style={{
                          width: `${(score.score / score.maximum) * 100}%`,
                        }}
                      />
                    </div>
                    <small>{score.reason}</small>
                  </div>
                ))}
              </div>
            )}
          </section>
          {assessment?.next_questions.length ? (
            <section className="panel">
              <h3>Уточним детали</h3>
              <p className="muted small-text">
                Ответьте на вопросы с наибольшим влиянием на качество.
              </p>
              {assessment.next_questions.map((q) => (
                <form
                  key={q.field}
                  onSubmit={(e) => {
                    e.preventDefault();
                    action("answer", q.field);
                  }}
                >
                  <FormField label={q.question}>
                    <textarea
                      required
                      rows={3}
                      value={answers[q.field] || ""}
                      onChange={(e) =>
                        setAnswers({ ...answers, [q.field]: e.target.value })
                      }
                      maxLength={8000}
                    />
                  </FormField>
                  <button disabled={!!busy} className="btn secondary small">
                    Сохранить ответ
                  </button>
                </form>
              ))}
            </section>
          ) : null}
          {!!history.data?.length && (
            <section className="panel">
              <h3>История улучшений</h3>
              <div className="history">
                {history.data.map((h) => (
                  <div key={h.revision}>
                    <span>Версия {h.revision}</span>
                    <strong>
                      {h.score}
                      <small>/100</small>
                    </strong>
                  </div>
                ))}
              </div>
            </section>
          )}
        </aside>
      </div>
    </>
  );
}
