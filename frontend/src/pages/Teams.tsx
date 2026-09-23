import { TeamSuggestions } from "./Student";
import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  Users,
  Plus,
  ArrowUpRight,
  ArrowLeft,
  Link2,
  Copy,
  Check,
  Crown,
} from "lucide-react";
import { api, patch, post } from "../api/client";
import type { Team, TeamDetail, Skill } from "../api/types";
import { useAuth } from "../app/Auth";
import { useLoad } from "../hooks/useLoad";
import { Empty, ErrorBox, FormField, Heading, Loading } from "../components/UI";
function TeamForm({
  team,
  onSaved,
}: {
  team?: TeamDetail;
  onSaved: (id: string) => void;
}) {
  const skills = useLoad(() => api<Skill[]>("/skills"));
  const [slugs, setSlugs] = useState(team?.skill_slugs || []);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setBusy(true);
    setError("");
    try {
      const payload = {
        name: form.get("name"),
        description: form.get("description"),
        skill_slugs: slugs,
      };
      const t = team
        ? await patch<Team>(`/teams/${team.id}`, payload)
        : await post<Team>("/teams", payload);
      onSaved(t.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <form onSubmit={submit}>
      <ErrorBox message={error || skills.error} />
      <FormField label="Название команды">
        <input
          name="name"
          defaultValue={team?.name}
          required
          maxLength={120}
          placeholder="Например, Team Horizon"
        />
      </FormField>
      <FormField label="О команде">
        <textarea
          name="description"
          defaultValue={team?.description}
          maxLength={3000}
          rows={3}
          placeholder="Расскажите об опыте, интересах и проектах"
        />
      </FormField>
      <div className="field">
        <span>Навыки команды</span>
        <div className="skill-picker">
          {skills.data?.map((s) => (
            <label key={s.slug}>
              <input
                type="checkbox"
                checked={slugs.includes(s.slug)}
                onChange={(e) =>
                  setSlugs(
                    e.target.checked
                      ? [...slugs, s.slug]
                      : slugs.filter((v) => v !== s.slug),
                  )
                }
              />
              {s.name}
            </label>
          ))}
        </div>
      </div>
      <button className="btn" disabled={busy}>
        {busy ? "Сохраняем…" : team ? "Сохранить команду" : "Создать команду"}
      </button>
    </form>
  );
}
export function Teams() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [creating, setCreating] = useState(false);
  const data = useLoad(() => api<Team[]>("/teams/me"));
  if (user?.role !== "student")
    return <ErrorBox message="Управление командами доступно студентам." />;
  return (
    <>
      <Heading
        eyebrow="СИЛЬНЕЕ ВМЕСТЕ"
        title="Мои команды"
        subtitle="Объединяйте навыки, приглашайте участников и беритесь за интересные задачи."
        action={
          <button className="btn" onClick={() => setCreating(!creating)}>
            <Plus size={18} />
            {creating ? "Закрыть форму" : "Новая команда"}
          </button>
        }
      />
      <TeamSuggestions onJoined={data.refresh} />
      <ErrorBox message={data.error} />
      {creating && (
        <section className="panel create-team">
          <h2>Соберите свою команду</h2>
          <TeamForm onSaved={(id) => nav(`/teams/${id}`)} />
        </section>
      )}
      {data.loading ? (
        <Loading />
      ) : data.data?.length ? (
        <div className="task-grid">
          {data.data.map((t) => (
            <Link className="panel team-card" key={t.id} to={`/teams/${t.id}`}>
              <div className="proposal-top">
                <div className="team-avatar">{t.name.slice(0, 1)}</div>
                <ArrowUpRight size={22} />
              </div>
              <h2>{t.name}</h2>
              <p className="clamp">
                {t.description || "Добавьте описание и расскажите о команде."}
              </p>
              <div className="tags">
                {t.skill_slugs.map((s) => (
                  <span key={s}>{s}</span>
                ))}
              </div>
              <div className="muted small-text">
                <Users size={16} />
                Участников: {t.member_ids.length}
              </div>
            </Link>
          ))}
        </div>
      ) : (
        !creating && (
          <Empty
            title="Ваша команда начинается с вас"
            text="Создайте команду и пригласите других студентов по ссылке. Или откройте приглашение от капитана."
            action={
              <button className="btn" onClick={() => setCreating(true)}>
                Создать команду
              </button>
            }
          />
        )
      )}
    </>
  );
}
export function TeamPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const nav = useNavigate();
  const load = useLoad(() => api<TeamDetail>(`/teams/${id}`), [id]);
  const [invite, setInvite] = useState("");
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [edit, setEdit] = useState(false);
  const action = async (path: string, method = "POST") => {
    setBusy(true);
    setError("");
    try {
      await api(path, { method });
      load.refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const makeInvite = async () => {
    setBusy(true);
    setError("");
    try {
      const res = await post<{ url: string }>(`/teams/${id}/invite`);
      setInvite(res.url);
      setCopied(false);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  if (load.loading) return <Loading />;
  if (!load.data) return <ErrorBox message={load.error} />;
  const team = load.data;
  const owner = team.owner_id === user?.id;
  return (
    <>
      <Link to="/teams" className="back-link">
        <ArrowLeft size={16} />
        Мои команды
      </Link>
      <Heading
        eyebrow={owner ? "ВЫ — КАПИТАН КОМАНДЫ" : "ВАША КОМАНДА"}
        title={team.name}
        subtitle={team.description}
        action={
          owner ? (
            <button className="btn secondary" onClick={() => setEdit(!edit)}>
              {edit ? "Закрыть" : "Редактировать"}
            </button>
          ) : undefined
        }
      />
      <ErrorBox message={error} />
      {edit && (
        <section className="panel create-team">
          <TeamForm
            team={team}
            onSaved={() => {
              setEdit(false);
              load.refresh();
            }}
          />
        </section>
      )}
      <div className="two-columns">
        <section className="panel">
          <h2>
            Участники <span className="count">{team.members.length}</span>
          </h2>
          <div className="member-list">
            {team.members.map((m) => (
              <div key={m.id}>
                <span className="avatar">{m.name.slice(0, 1)}</span>
                <span className="member-name">
                  {m.name}
                  {m.id === team.owner_id && (
                    <small>
                      <Crown size={12} />
                      Капитан
                    </small>
                  )}
                </span>
                {owner && m.id !== user?.id && (
                  <div className="member-actions">
                    <button
                      disabled={busy}
                      className="text-link"
                      onClick={() => {
                        if (
                          confirm(
                            `Передать управление командой участнику ${m.name}?`,
                          )
                        )
                          action(`/teams/${id}/captain/${m.id}`);
                      }}
                    >
                      Назначить капитаном
                    </button>
                    <button
                      disabled={busy}
                      className="text-link danger"
                      onClick={() => {
                        if (confirm(`Убрать ${m.name} из команды?`))
                          action(`/teams/${id}/members/${m.id}`, "DELETE");
                      }}
                    >
                      Удалить
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
          {!owner && (
            <button
              className="btn secondary"
              disabled={busy}
              onClick={async () => {
                if (!confirm("Покинуть команду?")) return;
                try {
                  await api(`/teams/${id}/members/${user?.id}`, {
                    method: "DELETE",
                  });
                  nav("/teams");
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            >
              Покинуть команду
            </button>
          )}
        </section>
        <section className="panel">
          <h2>Навыки и возможности</h2>
          <div className="tags large">
            {team.skill_slugs.length ? (
              team.skill_slugs.map((s) => <span key={s}>{s}</span>)
            ) : (
              <p className="muted">
                Капитан может добавить навыки в настройках команды.
              </p>
            )}
          </div>
          <p className="muted">
            Расскажите о сильных сторонах команды, чтобы бизнесу было проще
            оценить ваше предложение.
          </p>
          <Link to="/" className="btn secondary">
            Найти задачу <ArrowUpRight size={18} />
          </Link>
          {owner && (
            <div className="invite-section">
              <h3>Набор в команду</h3>
              <p>
                При открытом наборе студенты увидят команду в рекомендациях и
                смогут вступить без приглашения.
              </p>
              <label className="skill-picker">
                <input
                  type="checkbox"
                  checked={team.open_to_join}
                  disabled={busy}
                  onChange={async (e) => {
                    setBusy(true);
                    setError("");
                    try {
                      await api(`/students/teams/${id}/recruitment`, {
                        method: "PUT",
                        body: JSON.stringify({
                          open_to_join: e.target.checked,
                        }),
                      });
                      load.refresh();
                    } catch (e) {
                      setError((e as Error).message);
                    } finally {
                      setBusy(false);
                    }
                  }}
                />
                Открытый набор
              </label>
              <h3>Пригласить участника</h3>
              <p className="muted small-text">
                Одноразовая ссылка действует 7 дней. При создании новой
                предыдущая перестаёт работать.
              </p>
              <button className="btn" disabled={busy} onClick={makeInvite}>
                <Link2 size={17} />
                Создать приглашение
              </button>
              {invite && (
                <>
                  <input
                    className="invite-url"
                    value={invite}
                    readOnly
                    aria-label="Ссылка приглашения"
                    onFocus={(e) => e.target.select()}
                  />
                  <button
                    className="btn secondary small"
                    onClick={async () => {
                      try {
                        await navigator.clipboard.writeText(invite);
                        setCopied(true);
                      } catch {
                        setError("Выделите и скопируйте ссылку вручную.");
                      }
                    }}
                  >
                    {copied ? <Check size={15} /> : <Copy size={15} />}{" "}
                    {copied ? "Скопировано" : "Копировать ссылку"}
                  </button>
                </>
              )}
            </div>
          )}
        </section>
      </div>
    </>
  );
}
export function Join() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const token = window.location.hash.slice(1);
  const join = async () => {
    setBusy(true);
    setError("");
    try {
      const t = await post<TeamDetail>("/teams/join", { token });
      nav(`/teams/${t.id}`, { replace: true });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="panel narrow">
      <div className="empty-icon">
        <Users size={28} />
      </div>
      <h1>Вас пригласили в команду</h1>
      <p className="muted">
        Присоединитесь, чтобы вместе выбирать проекты и отправлять предложения
        бизнесу.
      </p>
      <ErrorBox message={error} />
      {user?.role !== "student" ? (
        <ErrorBox message="Приглашение предназначено для студенческого аккаунта." />
      ) : !token ? (
        <ErrorBox message="В ссылке отсутствует код приглашения." />
      ) : (
        <button className="btn full" disabled={busy} onClick={join}>
          {busy ? "Присоединяемся…" : "Принять приглашение"}
        </button>
      )}
    </section>
  );
}
