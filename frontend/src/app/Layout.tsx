import { NavLink, Link, Outlet, useNavigate } from "react-router-dom";
import {
  Compass,
  LayoutDashboard,
  Users,
  Send,
  Settings,
  ArrowUpRight,
  LogOut,
  Plus,
  Sparkles,
  Menu,
  X,
} from "lucide-react";
import { useState } from "react";
import { useAuth } from "./Auth";
import { ErrorBox } from "../components/UI";
export function Layout() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const nav = useNavigate();
  const signout = async () => {
    try {
      await logout();
      nav("/");
    } catch (e) {
      setError((e as Error).message);
    }
  };
  return (
    <div className="shell">
      <aside className={"sidebar " + (open ? "open" : "")}>
        <Link to="/" className="brand" onClick={() => setOpen(false)}>
          <span className="brand-mark">
            S<span>✦</span>
          </span>
          <span>
            Sana<span className="brand-light">Challenge</span>
          </span>
        </Link>
        <button
          className="close-nav icon-btn"
          aria-label="Закрыть меню"
          onClick={() => setOpen(false)}
        >
          <X />
        </button>

        <nav onClick={() => setOpen(false)}>
          <NavLink to="/catalog" end>
            <Compass size={19} />
            Каталог задач
            <span className="nav-dot" />
          </NavLink>
          {user && (
            <>
              <NavLink to="/dashboard">
                <LayoutDashboard size={19} />
                Мой кабинет
              </NavLink>
              {user.role === "student" && (
                <>
                  <NavLink to="/teams">
                    <Users size={19} />
                    Мои команды
                  </NavLink>
                  <NavLink to="/proposals">
                    <Send size={19} />
                    Мои отклики
                  </NavLink>
                </>
              )}
              <NavLink to="/profile">
                <Settings size={19} />
                Настройки аккаунта
              </NavLink>
            </>
          )}
        </nav>
        <div className="sidebar-promo">
          <div className="promo-icon">
            <Sparkles size={21} />
          </div>
          <h3>
            Большие идеи.
            <br />
            Реальные результаты.
          </h3>
          <p>
            Бизнес ставит задачу.
            <br />
            Команды находят решение.
          </p>
          <Link
            to={
              user
                ? user.role === "business"
                  ? "/tasks/new"
                  : "/teams"
                : "/register"
            }
          >
            Начать проект <ArrowUpRight size={17} />
          </Link>
        </div>
      </aside>
      {open && <div className="nav-scrim" onClick={() => setOpen(false)} />}
      <div className="workspace">
        <header className="topbar">
          <button
            className="mobile-menu icon-btn"
            aria-label="Открыть меню"
            onClick={() => setOpen(true)}
          >
            <Menu />
          </button>
          <div className="breadcrumb">
            Платформа <span>/</span>{" "}
            {user
              ? user.role === "business"
                ? "Для бизнеса"
                : "Для студентов"
              : "Открытые возможности"}
          </div>
          <div className="top-actions">
            {user ? (
              <>
                <Link className="account-chip" to="/profile">
                  <span className="avatar">
                    {user.name.slice(0, 1).toUpperCase()}
                  </span>
                  <span>
                    {user.name}
                    <small>
                      {user.role === "business" ? "Бизнес" : "Студент"}
                    </small>
                  </span>
                </Link>
                <button
                  className="icon-btn"
                  aria-label="Выйти"
                  title="Выйти"
                  onClick={signout}
                >
                  <LogOut size={18} />
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-link">
                  Войти
                </Link>
                <Link className="btn small" to="/register">
                  Создать аккаунт
                  <ArrowUpRight size={16} />
                </Link>
              </>
            )}
          </div>
        </header>
        <main className="main">
          <ErrorBox message={error} />
          <Outlet />
        </main>
        <footer className="footer">
          <span>© 2026 SanaChallenge</span>
        </footer>
      </div>
    </div>
  );
}
