import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Clock3,
  Send,
  CheckCircle2,
  Users,
  ArrowUpRight,
} from "lucide-react";
import { api, post } from "../api/client";
import {
  labels,
  statusLabels,
  type Task,
  type Team,
  type Proposal,
  type Page,
  type BriefField,
} from "../api/types";
import { useAuth } from "../app/Auth";
import { useLoad } from "../hooks/useLoad";
import {
  Empty,
  ErrorBox,
  FormField,
  Heading,
  Loading,
  Score,
  Pagination,
} from "../components/UI";
export function TaskDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const data = useLoad(() => api<Task>(`/tasks/${id}`), [id, user?.id]);
  const teams = useLoad(
    () =>
      user?.role === "student" ? api<Team[]>("/teams/me") : Promise.resolve([]),
    [user?.id],
  );
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  async function apply(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setBusy(true);
    setError("");
    try {
      await post(`/tasks/${id}/apply`, Object.fromEntries(form));
      setSent(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (data.loading) return <Loading />;
  if (!data.data) return <ErrorBox message={data.error} />;
  const task = data.data;
  const owner = user?.id === task.business_id;
  return (
    <>
      <Link to={owner ? "/dashboard" : "/"} className="back-link">
        <ArrowLeft size={16} />
        {owner ? "Мои задачи" : "Все задачи"}
      </Link>
      <Heading
        eyebrow={statusLabels[task.status]}
        title={task.brief.title || "Новая задача"}
        subtitle="Реальная бизнес-потребность. Пространство для вашего решения."
        action={<Score value={task.quality_score} />}
      />
      <div className="tags large">
        {task.skill_slugs.map((s) => (
          <span key={s}>{s}</span>
        ))}
      </div>
      <div className="builder-grid">
        <article className="panel brief-content">
          {(Object.keys(labels) as BriefField[])
            .filter((f) => f !== "title")
            .map((field) =>
              task.brief[field] ? (
                <section key={field}>
                  <h3>{labels[field]}</h3>
                  <p>{task.brief[field]}</p>
                </section>
              ) : null,
            )}
        </article>
        <aside>
          <section className="panel">
            <div className="eyebrow">О ПРОЕКТЕ</div>
            <h3>
              <Clock3 size={18} /> {task.brief.timeline || "Срок уточняется"}
            </h3>
            <p className="muted">{statusLabels[task.status]}</p>
            {owner ? (
              <>
                <p>Выберите команду по её опыту и предложенному подходу.</p>
                {task.status === "draft" && (
                  <Link className="btn full" to={`/tasks/${id}/edit`}>
                    Продолжить редактирование
                  </Link>
                )}
              </>
            ) : task.status !== "published" ? (
              <div className="alert success">
                <CheckCircle2 size={18} />
                Приём предложений завершён.
              </div>
            ) : !user ? (
              <>
                <p>
                  Войдите как студент, чтобы подать предложение от своей
                  команды.
                </p>
                <Link
                  className="btn full"
                  to="/login"
                  state={{ from: `/tasks/${id}` }}
                >
                  Войти и откликнуться <ArrowUpRight size={17} />
                </Link>
              </>
            ) : user.role === "business" ? (
              <p>Предложения отправляют студенческие команды.</p>
            ) : sent ? (
              <div className="alert success" role="status">
                <CheckCircle2 size={19} />
                <div>
                  Предложение отправлено.
                  <br />
                  <Link to="/proposals">Посмотреть статус</Link>
                </div>
              </div>
            ) : teams.loading ? (
              <Loading />
            ) : teams.error ? (
              <ErrorBox message={teams.error} />
            ) : !teams.data?.length ? (
              <>
                <p>
                  Для отклика создайте команду или присоединитесь к существующей
                  по приглашению.
                </p>
                <Link className="btn full" to="/teams">
                  <Users size={18} />
                  Создать команду
                </Link>
              </>
            ) : (
              <form onSubmit={apply}>
                <h2>Ваше предложение</h2>
                <ErrorBox message={error} />
                <FormField label="Команда">
                  <select name="team_id" required>
                    {teams.data.map((t) => (
                      <option value={t.id} key={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </FormField>
                <FormField label="Почему ваша команда?">
                  <textarea
                    name="pitch"
                    required
                    maxLength={8000}
                    rows={3}
                    placeholder="Опыт и сильные стороны команды"
                  />
                </FormField>
                <FormField label="Как вы решите задачу?">
                  <textarea
                    name="approach"
                    required
                    maxLength={8000}
                    rows={4}
                    placeholder="Предложите первые шаги и подход"
                  />
                </FormField>
                <FormField label="Предлагаемый срок">
                  <input
                    name="timeline"
                    required
                    maxLength={300}
                    placeholder="Например, 3 недели"
                  />
                </FormField>
                <button disabled={busy} className="btn full">
                  <Send size={17} />
                  {busy ? "Отправляем…" : "Подать предложение"}
                </button>
                <small className="muted">
                  Один отклик от команды на каждую задачу.
                </small>
              </form>
            )}
          </section>
        </aside>
      </div>
      {owner && task.status !== "draft" && (
        <BusinessProposals task={task} onSelected={data.refresh} />
      )}
    </>
  );
}
function BusinessProposals({
  task,
  onSelected,
}: {
  task: Task;
  onSelected: () => void;
}) {
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [confirm, setConfirm] = useState<string | null>(null);
  const load = useLoad(async () => {
    const page = await api<Page<Proposal>>(
      `/business/tasks/${task.id}/proposals?limit=10&offset=${offset}`,
    );
    const teams = await Promise.all(
      page.items.map((p) => api<Team>(`/business/proposals/${p.id}/team`)),
    );
    return { ...page, teams };
  }, [task.id, task.status, offset]);
  const select = async (id: string) => {
    setBusy(id);
    setError("");
    try {
      await post(`/proposals/${id}/select`);
      setConfirm(null);
      onSelected();
      load.refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  };
  return (
    <section className="proposals-section">
      <Heading
        title="Предложения команд"
        subtitle="Познакомьтесь с подходами и выберите команду для сотрудничества."
      />
      <ErrorBox message={error || load.error} />
      {load.loading ? (
        <Loading />
      ) : load.data?.items.length ? (
        <>
          <div className="proposal-grid">
            {load.data.items.map((p, i) => {
              const team = load.data!.teams[i];
              return (
                <article className="panel" key={p.id}>
                  <div className="proposal-top">
                    <div className="team-avatar">{team.name.slice(0, 1)}</div>
                    <div>
                      <h3>{team.name}</h3>
                      <span className={"badge " + p.status}>
                        {statusLabels[p.status]}
                      </span>
                    </div>
                  </div>
                  <p>{team.description}</p>
                  <div className="tags">
                    {team.skill_slugs.map((s) => (
                      <span key={s}>{s}</span>
                    ))}
                  </div>
                  <h4>Почему мы</h4>
                  <p className="pre-wrap">{p.pitch}</p>
                  <h4>Наш подход</h4>
                  <p className="pre-wrap">{p.approach}</p>
                  <p className="muted">
                    <Clock3 size={14} /> {p.timeline}
                  </p>
                  {task.status === "published" &&
                    (confirm === p.id ? (
                      <div className="confirm-box">
                        <p>
                          Выбрать {team.name}? Другие предложения будут
                          отклонены.
                        </p>
                        <button
                          className="btn"
                          disabled={!!busy}
                          onClick={() => select(p.id)}
                        >
                          Подтвердить выбор
                        </button>
                        <button
                          className="btn secondary"
                          disabled={!!busy}
                          onClick={() => setConfirm(null)}
                        >
                          Отмена
                        </button>
                      </div>
                    ) : (
                      <button
                        className="btn full"
                        onClick={() => setConfirm(p.id)}
                      >
                        Выбрать команду
                      </button>
                    ))}
                </article>
              );
            })}
          </div>
          <Pagination
            total={load.data.total}
            offset={offset}
            limit={10}
            onChange={setOffset}
          />
        </>
      ) : (
        <Empty
          title="Откликов пока нет"
          text="Задача опубликована. Поделитесь ссылкой на карточку со студенческими командами."
        />
      )}
    </section>
  );
}
export function MyProposals() {
  const [offset, setOffset] = useState(0);
  const load = useLoad(async () => {
    const page = await api<Page<Proposal>>(
      `/my-proposals?limit=10&offset=${offset}`,
    );
    const tasks = await Promise.all(
      page.items.map((p) => api<Task>(`/tasks/${p.task_id}`)),
    );
    return { ...page, tasks };
  }, [offset]);
  return (
    <>
      <Heading
        eyebrow="ВАШИ ВОЗМОЖНОСТИ"
        title="Мои отклики"
        subtitle="Все предложения ваших команд и решения бизнеса в одном месте."
      />
      <ErrorBox message={load.error} />
      {load.loading ? (
        <Loading />
      ) : load.data?.items.length ? (
        <>
          <div className="proposal-list">
            {load.data.items.map((p, i) => (
              <Link
                className="panel proposal-row"
                key={p.id}
                to={`/tasks/${p.task_id}`}
              >
                <div>
                  <span className={"badge " + p.status}>
                    {statusLabels[p.status]}
                  </span>
                  <h3>{load.data!.tasks[i].brief.title}</h3>
                  <p className="clamp">{p.pitch}</p>
                  <small className="muted">
                    Предлагаемый срок: {p.timeline}
                  </small>
                </div>
                <ArrowUpRight size={24} />
              </Link>
            ))}
          </div>
          <Pagination
            total={load.data.total}
            offset={offset}
            limit={10}
            onChange={setOffset}
          />
        </>
      ) : (
        <Empty
          title="Пока ни одного отклика"
          text="Найдите интересную задачу и предложите решение от своей команды."
          action={
            <Link to="/catalog" className="btn">
              Перейти в каталог
            </Link>
          }
        />
      )}
    </>
  );
}
