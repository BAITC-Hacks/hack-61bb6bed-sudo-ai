import { Link, Navigate } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  Building2,
  GraduationCap,
  Sparkles,
} from "lucide-react";
import { useAuth } from "../app/Auth";
export function Welcome() {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading">Загружаем…</div>;
  if (user) return <Navigate to="/dashboard" replace />;
  return (
    <div className="welcome">
      <header className="welcome-header">
        <Link to="/" className="welcome-brand">
          <span className="liquid-mark">S</span>SanaChallenge
          <span className="brand-ai">AI</span>
        </Link>
        <div>
          <span className="welcome-login-note">Уже с нами?</span>
          <Link className="btn secondary small" to="/login">
            Войти <ArrowUpRight size={16} />
          </Link>
        </div>
      </header>
      <main className="welcome-main">
        <div className="welcome-intro">
          <span className="welcome-kicker">
            <span /> ИДЕИ ВСТРЕЧАЮТ ВОЗМОЖНОСТИ
          </span>
          <h1>
            Большие дела
            <br />
            начинаются <em>с вас.</em>
          </h1>
          <p>
            Реальные задачи бизнеса. Свежий взгляд студентов.
            <br />
            Выберите свою роль — и создадим что-то вместе.
          </p>
        </div>
        <div className="role-choices">
          <Link
            to="/login?role=business"
            className="role-choice business-choice"
          >
            <div className="choice-top">
              <span className="choice-icon">
                <Building2 size={30} strokeWidth={1.4} />
              </span>
              <span className="choice-number">01 / БИЗНЕС</span>
            </div>
            <h2>У меня есть задача</h2>
            <span className="choice-cta">
              Я представляю бизнес <ArrowRight size={20} />
            </span>
          </Link>
          <Link
            to="/login?role=student"
            className="role-choice student-choice"
          >
            <div className="choice-top">
              <span className="choice-icon">
                <GraduationCap size={32} strokeWidth={1.4} />
              </span>
              <span className="choice-number">02 / СТУДЕНТЫ</span>
            </div>
            <h2>Хочу создавать решения</h2>
            <span className="choice-cta">
              Я студент <ArrowRight size={20} />
            </span>
          </Link>
        </div>
        <div className="welcome-bottom">
          <span>
            <Sparkles size={16} /> Разные роли. Общий результат.
          </span>
          <Link to="/catalog">
            Сначала посмотреть задачи <ArrowUpRight size={16} />
          </Link>
        </div>
      </main>
      <footer className="welcome-footer">
        <span>© 2026 SanaChallenge AI</span>
        <span>От идеи — к реальному опыту.</span>
      </footer>
    </div>
  );
}
