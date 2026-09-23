import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  ArrowUpRight,
  Building2,
  GraduationCap,
  ShieldCheck,
} from "lucide-react";
import { api, patch, post } from "../api/client";
import type { Role, User } from "../api/types";
import { useAuth } from "../app/Auth";
import { ErrorBox, FormField, Heading } from "../components/UI";
export function AuthPage({ register = false }: { register?: boolean }) {
  const { setUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [role, setRole] = useState<Role>(
    new URLSearchParams(location.search).get("role") === "student"
      ? "student"
      : "business",
  );
  const selectedRole = new URLSearchParams(location.search).get("role");
  const demoLogin =
    !register &&
    ["business", "student"].includes(selectedRole || "") &&
    ["localhost", "127.0.0.1"].includes(window.location.hostname);
  const demoAccount = demoLogin
    ? selectedRole === "student"
      ? { email: "student.demo@example.com", password: "Sana-Demo-Student-2026", label: "студента" }
      : { email: "business.demo@example.com", password: "Sana-Demo-Business-2026", label: "бизнеса" }
    : undefined;
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    setBusy(true);
    setError("");
    try {
      const user = await post<User>(
        register ? "/auth/register" : "/auth/login",
        {
          email: data.get("email"),
          password: data.get("password"),
          ...(register ? { name: data.get("name"), role } : {}),
        },
      );
      setUser(user);
      navigate(location.state?.from || "/dashboard", { replace: true });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="auth-entry">
      <Link to="/" className="auth-back">
        ← Выбрать роль
      </Link>
      <section className="auth-form panel">
        <div className="eyebrow">ДОБРО ПОЖАЛОВАТЬ В SANACHALLENGE</div>
        <h2>{register ? "Создайте аккаунт" : "Войти в аккаунт"}</h2>
        <p className="muted">
          {register
            ? "Выберите свою роль и присоединяйтесь к платформе."
            : demoAccount
              ? `Демо-аккаунт ${demoAccount.label}. Данные уже заполнены — можно войти.`
              : "Введите email и пароль, чтобы продолжить."}
        </p>
        <ErrorBox message={error} />
        <form key={`${register}-${selectedRole}`} onSubmit={submit}>
          {register && (
            <>
              <div className="role-picker">
                <button
                  type="button"
                  className={role === "business" ? "active" : ""}
                  onClick={() => setRole("business")}
                >
                  <Building2 size={21} />
                  <strong>Я представляю бизнес</strong>
                  <small>Хочу решить задачу</small>
                </button>
                <button
                  type="button"
                  className={role === "student" ? "active" : ""}
                  onClick={() => setRole("student")}
                >
                  <GraduationCap size={22} />
                  <strong>Я студент</strong>
                  <small>Хочу работать над проектом</small>
                </button>
              </div>
              <FormField label="Ваше имя">
                <input
                  name="name"
                  autoComplete="name"
                  required
                  maxLength={120}
                  placeholder="Как к вам обращаться"
                />
              </FormField>
            </>
          )}
          <FormField label="Email">
            <input
              name="email"
              defaultValue={demoAccount?.email || ""}
              type="email"
              autoComplete="email"
              required
              maxLength={254}
              placeholder="you@example.com"
            />
          </FormField>
          <FormField
            label="Пароль"
            hint={
              register
                ? "От 12 символов. Можно использовать длинную фразу."
                : undefined
            }
          >
            <input
              name="password"
              defaultValue={demoAccount?.password || ""}
              type="password"
              autoComplete={register ? "new-password" : "current-password"}
              required
              minLength={register ? 12 : 1}
              maxLength={128}
              placeholder={
                register ? "Придумайте надёжный пароль" : "Введите пароль"
              }
            />
          </FormField>
          <button className="btn full" disabled={busy}>
            {busy
              ? "Подождите…"
              : register
                ? "Создать аккаунт"
                : "Войти в аккаунт"}
            <ArrowUpRight size={18} />
          </button>
        </form>
        <p className="auth-switch">
          {register ? "Уже есть аккаунт?" : "Впервые здесь?"}{" "}
          <Link
            to={(register ? "/login" : "/register") + location.search}
            state={location.state}
          >
            {register ? "Войти" : "Зарегистрироваться"}
          </Link>
        </p>
        <div className="secure-note">
          <ShieldCheck size={16} />
          Защищённый вход в ваше рабочее пространство.
        </div>
      </section>
    </div>
  );
}
export function Profile() {
  const { user, setUser } = useAuth();
  const nav = useNavigate();
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    setBusy(true);
    setError("");
    setMessage("");
    try {
      setUser(await patch<User>("/auth/profile", { name: data.get("name") }));
      setMessage("Профиль сохранён.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function password(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    setError("");
    if (data.get("new") !== data.get("confirm")) {
      setError("Новые пароли не совпадают.");
      return;
    }
    setBusy(true);
    try {
      await post("/auth/password", {
        current_password: data.get("current"),
        new_password: data.get("new"),
      });
      setUser(null);
      nav("/login");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Heading title="Настройки профиля" />
      <ErrorBox message={error} />
      {message && (
        <div role="status" className="alert success">
          {message}
        </div>
      )}
      <div className="two-columns">
        <section className="panel">
          <h2>Личные данные</h2>
          <form onSubmit={save}>
            <FormField label="Имя">
              <input
                name="name"
                defaultValue={user?.name}
                required
                maxLength={120}
              />
            </FormField>
            <FormField label="Email">
              <input value={user?.email || ""} disabled />
            </FormField>
            <FormField label="Тип аккаунта">
              <input
                value={
                  user?.role === "business"
                    ? "Представитель бизнеса"
                    : "Студент"
                }
                disabled
              />
            </FormField>
            <button className="btn" disabled={busy}>
              Сохранить изменения
            </button>
          </form>
        </section>
        <section className="panel">
          <h2>Сменить пароль</h2>
          <p className="muted">
            После смены пароля все сессии завершатся. Потребуется войти снова.
          </p>
          <form onSubmit={password}>
            <FormField label="Текущий пароль">
              <input
                type="password"
                name="current"
                autoComplete="current-password"
                required
              />
            </FormField>
            <FormField label="Новый пароль">
              <input
                type="password"
                name="new"
                autoComplete="new-password"
                required
                minLength={12}
                maxLength={128}
              />
            </FormField>
            <FormField label="Повторите новый пароль">
              <input
                type="password"
                name="confirm"
                autoComplete="new-password"
                required
                minLength={12}
                maxLength={128}
              />
            </FormField>
            <button className="btn secondary" disabled={busy}>
              Обновить пароль
            </button>
          </form>
        </section>
      </div>
    </>
  );
}
