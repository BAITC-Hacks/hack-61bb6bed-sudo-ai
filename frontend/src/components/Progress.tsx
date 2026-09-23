import { Trophy, Check, LockKeyhole } from "lucide-react";
import { api } from "../api/client";
import { useLoad } from "../hooks/useLoad";
import { ErrorBox } from "./UI";
type ProgressData = {
  xp: number;
  level: number;
  title: string;
  level_start: number;
  next_level_xp: number | null;
  achievements: {
    id: string;
    title: string;
    description: string;
    xp: number;
    unlocked: boolean;
  }[];
};
export function Progress() {
  const { data, error, loading } = useLoad(() =>
    api<ProgressData>("/me/progress"),
  );
  if (loading)
    return (
      <div className="progress-panel" role="status">
        Загружаем достижения…
      </div>
    );
  if (!data) return <ErrorBox message={error} />;
  const next = data.achievements.find((a) => !a.unlocked);
  const percent =
    data.next_level_xp === null
      ? 100
      : Math.round(
          ((data.xp - data.level_start) /
            (data.next_level_xp - data.level_start)) *
            100,
        );
  return (
    <section className="progress-panel" aria-label="Ваш прогресс">
      <div className="progress-heading">
        <div>
          <Trophy size={23} />
          <h2>
            {data.title}
            <small>Уровень {data.level}</small>
          </h2>
        </div>
        <strong>{data.xp} XP</strong>
      </div>
      <div
        className="xp-track"
        role="progressbar"
        aria-label="Прогресс уровня"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <span style={{ width: `${percent}%` }} />
      </div>
      <p>
        {data.next_level_xp === null
          ? "Все этапы пройдены!"
          : `${data.next_level_xp - data.xp} XP до следующего уровня`}
      </p>
      <div className="achievement-list">
        {data.achievements.map((a) => (
          <div
            key={a.id}
            className={a.unlocked ? "achievement earned" : "achievement"}
            title={a.description}
          >
            {a.unlocked ? <Check size={17} /> : <LockKeyhole size={16} />}
            <span>
              {a.title}
              <small>{a.unlocked ? "Получено" : a.description}</small>
            </span>
            <strong>+{a.xp}</strong>
          </div>
        ))}
      </div>
      {next && (
        <p className="next-milestone">
          Следующий шаг: {next.description.toLowerCase()}.
        </p>
      )}
      <small className="progress-note">
        Каждое достижение учитывается один раз. XP не влияет на оценку задачи.
        {data.achievements.some((a) => a.id === "team") &&
          " Командные достижения учитываются по текущему составу."}
      </small>
    </section>
  );
}
