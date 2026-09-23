import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowUpRight, Search, SlidersHorizontal, Plus } from "lucide-react";
import { api, post } from "../api/client";
import type { Page, Task, Skill, Proposal, Team } from "../api/types";
import { statusLabels } from "../api/types";
import { useAuth } from "../app/Auth";
import { useLoad } from "../hooks/useLoad";
import {
  Empty,
  ErrorBox,
  Heading,
  Loading,
  Pagination,
  TaskCard,
} from "../components/UI";
export function Explore() {
  const { user } = useAuth();
  const [text, setText] = useState("");
  const [q, setQ] = useState("");
  const [skill, setSkill] = useState("");
  const [sort, setSort] = useState("quality");
  const [offset, setOffset] = useState(0);
  useEffect(() => {
    const id = setTimeout(() => {
      setQ(text);
      setOffset(0);
    }, 300);
    return () => clearTimeout(id);
  }, [text]);
  const list = useLoad(
    () =>
      api<Page<Task>>(
        `/tasks?limit=9&offset=${offset}&sort=${sort}&skill=${skill}&q=${encodeURIComponent(q)}`,
      ),
    [offset, sort, skill, q],
  );
  const skills = useLoad(() => api<Skill[]>("/skills"));
  return (
    <>
      <Heading
        title="Каталог задач"
        action={
          <Link
            className="btn"
            to={
              user?.role === "business"
                ? "/tasks/new"
                : user
                  ? "/teams"
                  : "/register"
            }
          >
            {user?.role === "business" ? (
              <Plus size={18} />
            ) : (
              <ArrowUpRight size={18} />
            )}{" "}
            {user?.role === "business"
              ? "Создать задачу"
              : "Найти свою команду"}
          </Link>
        }
      />
      <div className="section-title">
        <h2>
          Открытые задачи{" "}
          <span className="count">{list.data?.total ?? "—"}</span>
        </h2>
      </div>
      <div className="filter-bar">
        <label className="search-input">
          <Search size={18} />
          <input
            aria-label="Поиск задач"
            placeholder="Поиск по названию или описанию"
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={200}
          />
        </label>
        <select
          aria-label="Навык"
          value={skill}
          onChange={(e) => {
            setSkill(e.target.value);
            setOffset(0);
          }}
        >
          <option value="">Все направления</option>
          {skills.data?.map((s) => (
            <option key={s.slug} value={s.slug}>
              {s.name}
            </option>
          ))}
        </select>
        <label className="sort">
          <SlidersHorizontal size={16} />
          <select
            aria-label="Сортировка"
            value={sort}
            onChange={(e) => {
              setSort(e.target.value);
              setOffset(0);
            }}
          >
            <option value="quality">Сначала качественные</option>
            <option value="newest">Сначала новые</option>
          </select>
        </label>
      </div>
      <div className="filter-chips">
        {[
          ["", "Все задачи"],
          ["llm", "AI & LLM"],
          ["data-analysis", "Аналитика данных"],
          ["computer-vision", "Computer Vision"],
          ["react", "Web-разработка"],
          ["cybersecurity", "Кибербезопасность"],
        ].map(([slug, title]) => (
          <button
            key={slug}
            className={skill === slug ? "active" : ""}
            onClick={() => {
              setSkill(slug);
              setOffset(0);
            }}
          >
            {title}
          </button>
        ))}
      </div>
      <ErrorBox message={list.error} />
      {list.loading ? (
        <Loading />
      ) : list.data?.items.length ? (
        <>
          <div className="task-grid">
            {list.data.items.map((task) => (
              <TaskCard key={task.id} task={task} />
            ))}
          </div>
          <Pagination
            total={list.data.total}
            limit={9}
            offset={offset}
            onChange={setOffset}
          />
        </>
      ) : (
        <Empty
          title="Пока нет подходящих задач"
          text={
            q || skill
              ? "Попробуйте другой запрос или направление."
              : "Опубликованные задачи появятся здесь. Создайте первую!"
          }
          action={
            <button
              className="btn secondary"
              onClick={() => {
                setText("");
                setSkill("");
              }}
            >
              Сбросить фильтры
            </button>
          }
        />
      )}
    </>
  );
}
function BusinessStart() {
  const navigate = useNavigate();
  const [idea, setIdea] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return (
    <div className="business-start">
      <section className="project-composer">
        <h2>Новая задача</h2>
        <p>Опишите идею — AI поможет уточнить детали.</p>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            try {
              const task = await post<Task>("/tasks/draft", { raw_text: idea });
              navigate(`/tasks/${task.id}/edit`);
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <label htmlFor="quick-idea">В чём ваша задача?</label>
          <textarea
            id="quick-idea"
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            required
            minLength={10}
            maxLength={10000}
            placeholder="Например, автоматизировать обработку обращений клиентов."
            rows={4}
          />
          <ErrorBox message={error} />
          <div className="composer-bottom">
            <button className="btn" disabled={busy}>
              <Plus size={18} />
              {busy ? "Создаём…" : "Создать черновик"}
            </button>
          </div>
        </form>
      </section>
      <aside className="journey-panel">
        <h3>Три шага к команде</h3>
        <ol>
          {[
            ["Опишите задачу", "Укажите цель и результат."],
            ["Получите отклики", "Опубликуйте задачу."],
            ["Выберите команду", "Сравните предложения."],
          ].map(([title, text], i) => (
            <li key={title}>
              <span>{i + 1}</span>
              <div>
                <strong>{title}</strong>
                <p>{text}</p>
              </div>
            </li>
          ))}
        </ol>
      </aside>
    </div>
  );
}
export function Dashboard() {
  const { user } = useAuth();
  const business = user?.role === "business";
  const [offset, setOffset] = useState(0);
  const data = useLoad(
    async () =>
      business
        ? {
            tasks: await api<Page<Task>>(
              `/business/tasks?limit=9&offset=${offset}`,
            ),
          }
        : {
            proposals: await api<Page<Proposal>>("/my-proposals?limit=100"),
            teams: await api<Team[]>("/teams/me"),
          },
    [business, offset],
  );
  return (
    <>
      <Heading
        eyebrow={business ? "КАБИНЕТ БИЗНЕСА" : "КАБИНЕТ СТУДЕНТА"}
        title={`Здравствуйте, ${user?.name.split(" ")[0]}.`}
        action={
          <Link className="btn" to={business ? "/tasks/new" : "/catalog"}>
            <Plus size={18} />
            {business ? "Создать задачу" : "Найти проект"}
          </Link>
        }
      />
      <ErrorBox message={data.error} />
      {data.loading ? (
        <Loading />
      ) : business ? (
        <>
          <BusinessStart />
          <div className="section-title">
            <h2>Мои задачи</h2>
          </div>
          {data.data?.tasks?.items.length ? (
            <>
              <div className="task-grid">
                {data.data.tasks.items.map((t) => (
                  <TaskCard key={t.id} task={t} owned />
                ))}
              </div>
              <Pagination
                total={data.data.tasks.total}
                offset={offset}
                limit={9}
                onChange={setOffset}
              />
            </>
          ) : (
            <Empty
              title="Пока нет задач"
              text="Создайте черновик в форме выше."
              action={
                <Link className="btn" to="/tasks/new">
                  Создать первую задачу
                </Link>
              }
            />
          )}
        </>
      ) : (
        <>
          <div className="stat-grid">
            <Link to="/teams" className="stat">
              <small>Мои команды</small>
              <strong>{data.data?.teams?.length ?? 0}</strong>
              <span>Сильнее вместе ↗</span>
            </Link>
            <Link to="/proposals" className="stat">
              <small>Отправлено откликов</small>
              <strong>{data.data?.proposals?.total ?? 0}</strong>
              <span>Следите за решениями бизнеса ↗</span>
            </Link>
          </div>
          <section className="panel">
            <h2>Готовы к следующему вызову?</h2>
            <p className="muted">
              Соберите команду, расскажите о своих навыках и выберите задачу,
              которая вам интересна.
            </p>
            <Link className="btn" to="/catalog">
              Открыть каталог <ArrowUpRight size={18} />
            </Link>
          </section>
        </>
      )}
    </>
  );
}
