import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { api, post } from "../api/client";
import type { Task, Skill } from "../api/types";
import { useAuth } from "../app/Auth";
import { useLoad } from "../hooks/useLoad";
import { ErrorBox, Loading, Heading, TaskCard } from "../components/UI";

type Profile = {
  direction: string;
  skill_slugs: string[];
  experience: string;
  interests: string;
};
type Matches = {
  profile: Profile | null;
  tasks: {
    task: Task;
    matched_skills: string[];
    missing_skills: string[];
    coverage: number;
  }[];
  teams: {
    id: string;
    name: string;
    description: string;
    members: string[];
    added_by_team: string[];
    added_by_you: string[];
  }[];
};
const directions = [
  ["frontend", "Фронтенд"],
  ["backend", "Бэкенд"],
  ["fullstack", "Фулстек"],
  ["data", "Данные и AI"],
  ["design", "Дизайн"],
  ["security", "Безопасность"],
];
export function StudentSetup() {
  const { user } = useAuth();
  const load = useLoad(async () => ({
    profile: await api<Profile | null>("/students/profile"),
    skills: await api<Skill[]>("/skills"),
  }));
  if (user?.role !== "student") return <Navigate to="/dashboard" replace />;
  if (load.loading) return <Loading />;
  if (!load.data) return <ErrorBox message={load.error} />;
  return <SetupForm initial={load.data.profile} skills={load.data.skills} />;
}
function SetupForm({
  initial,
  skills,
}: {
  initial: Profile | null;
  skills: Skill[];
}) {
  const nav = useNavigate();
  const [step, setStep] = useState(0);
  const [value, setValue] = useState<Profile>(
    initial || {
      direction: "",
      skill_slugs: [],
      experience: "",
      interests: "",
    },
  );
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const titles = [
    "Что вам ближе?",
    "С каким стеком вы работаете?",
    "Какой у вас опыт?",
  ];
  const valid =
    step === 0
      ? !!value.direction
      : step === 1
        ? value.skill_slugs.length > 0
        : !!value.experience;
  return (
    <section className="panel student-setup">
      <p className="student-step">Знакомство · {step + 1} из 3</p>
      <h1>{titles[step]}</h1>
      <p>Подберём задачи по вашим навыкам и команды, которые вас дополнят.</p>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          if (!valid) return;
          if (step < 2) {
            setStep(step + 1);
            return;
          }
          setBusy(true);
          setError("");
          try {
            await api("/students/profile", {
              method: "PUT",
              body: JSON.stringify(value),
            });
            nav("/dashboard", { replace: true });
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        {step === 0 && (
          <div className="student-options">
            {directions.map(([id, label]) => (
              <label
                key={id}
                className={value.direction === id ? "selected" : ""}
              >
                <input
                  type="radio"
                  name="direction"
                  checked={value.direction === id}
                  onChange={() => setValue({ ...value, direction: id })}
                />
                {label}
              </label>
            ))}
          </div>
        )}
        {step === 1 && (
          <div className="student-options">
            {skills.map((skill) => (
              <label
                key={skill.slug}
                className={
                  value.skill_slugs.includes(skill.slug) ? "selected" : ""
                }
              >
                <input
                  type="checkbox"
                  checked={value.skill_slugs.includes(skill.slug)}
                  onChange={(e) =>
                    setValue({
                      ...value,
                      skill_slugs: e.target.checked
                        ? [...value.skill_slugs, skill.slug]
                        : value.skill_slugs.filter((s) => s !== skill.slug),
                    })
                  }
                />
                {skill.name}
              </label>
            ))}
          </div>
        )}
        {step === 2 && (
          <>
            <div className="student-options">
              {[
                ["beginner", "Учусь — ищу первый проект"],
                ["practice", "Есть учебные или личные проекты"],
                ["experienced", "Есть опыт работы с заказчиками"],
              ].map(([id, label]) => (
                <label
                  key={id}
                  className={value.experience === id ? "selected" : ""}
                >
                  <input
                    type="radio"
                    name="experience"
                    checked={value.experience === id}
                    onChange={() => setValue({ ...value, experience: id })}
                  />
                  {label}
                </label>
              ))}
            </div>
            <label className="field">
              Что хотите попробовать?{" "}
              <textarea
                value={value.interests}
                maxLength={500}
                onChange={(e) =>
                  setValue({ ...value, interests: e.target.value })
                }
                placeholder="Необязательно: например, интернет-магазин или AI-сервис"
              />
            </label>
          </>
        )}
        <ErrorBox message={error} />
        <div className="student-controls">
          {step > 0 && (
            <button
              type="button"
              className="btn secondary"
              disabled={busy}
              onClick={() => setStep(step - 1)}
            >
              Назад
            </button>
          )}
          <button className="btn" disabled={!valid || busy}>
            {busy
              ? "Сохраняем…"
              : step === 2
                ? "Показать подходящие задачи"
                : "Далее"}
          </button>
        </div>
      </form>
    </section>
  );
}
export function StudentHome() {
  const load = useLoad(() => api<Matches>("/students/matches"));
  if (load.loading) return <Loading />;
  if (!load.data) return <ErrorBox message={load.error} />;
  if (!load.data.profile) return <Navigate to="/student/profile" replace />;
  return (
    <>
      <Heading
        title="Задачи для вас"
        subtitle="Открытые проекты с совпадениями по вашим навыкам."
        action={
          <Link className="btn secondary" to="/student/profile">
            Мои навыки
          </Link>
        }
      />
      <div className="student-controls">
        <Link className="btn" to="/teams">
          Найти команду
        </Link>
        <Link className="btn secondary" to="/catalog">
          Все задачи
        </Link>
      </div>
      {load.data.tasks.length ? (
        <div className="task-grid">
          {load.data.tasks.map((item) => (
            <div key={item.task.id}>
              <p className="match-reason">
                Ваши навыки: {item.matched_skills.join(", ")}
              </p>
              <TaskCard task={item.task} />
              {item.missing_skills.length > 0 && (
                <p className="match-reason">
                  Нужны в команде: {item.missing_skills.join(", ")}
                </p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <section className="panel">
          <h2>Совпадений пока нет</h2>
          <p>
            Посмотрите общий каталог или обновите навыки. Здесь появятся
            подходящие опубликованные задачи.
          </p>
        </section>
      )}
    </>
  );
}
export function TeamSuggestions({ onJoined }: { onJoined: () => void }) {
  const load = useLoad(() => api<Matches>("/students/matches"));
  const [busy, setBusy] = useState(""),
    [error, setError] = useState("");
  if (load.loading) return <Loading />;
  return (
    <section className="student-suggestions">
      <Heading
        title="Дополнят ваши навыки"
        subtitle="Команды с открытым набором и навыками, которых нет в вашем профиле."
      />
      <ErrorBox message={load.error || error} />
      {!load.data?.profile ? (
        <Link className="btn" to="/student/profile">
          Рассказать о навыках
        </Link>
      ) : !load.data.teams.length ? (
        <p>
          Сейчас нет команд с взаимно дополняющими навыками. Можно создать свою
          команду.
        </p>
      ) : (
        <div className="task-grid">
          {load.data.teams.map((team) => (
            <article className="panel" key={team.id}>
              <h2>{team.name}</h2>
              <p>{team.description}</p>
              <p>{team.members.join(" · ")}</p>
              <p>
                <strong>Команда добавит:</strong>{" "}
                {team.added_by_team.join(", ")}
              </p>
              <p>
                <strong>Вы добавите:</strong> {team.added_by_you.join(", ")}
              </p>
              <button
                className="btn"
                disabled={!!busy}
                onClick={async () => {
                  setBusy(team.id);
                  setError("");
                  try {
                    await post(`/students/teams/${team.id}/join`);
                    load.refresh();
                    onJoined();
                  } catch (e) {
                    setError((e as Error).message);
                  } finally {
                    setBusy("");
                  }
                }}
              >
                {busy === team.id ? "Присоединяемся…" : "Вступить в команду"}
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
