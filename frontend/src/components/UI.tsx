import {
  cloneElement,
  isValidElement,
  useId,
  type ReactElement,
  type ReactNode,
} from "react";
import { Link } from "react-router-dom";
import {
  ArrowUpRight,
  Clock3,
  AlertCircle,
  SearchX,
  ChevronLeft,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import type { Task } from "../api/types";
import { statusLabels } from "../api/types";
export function ErrorBox({ message }: { message: string }) {
  return message ? (
    <div className="alert error" role="alert">
      <AlertCircle size={18} />
      <span>{message}</span>
    </div>
  ) : null;
}
export function Loading() {
  return (
    <div className="loading" role="status">
      <span className="spinner" />
      Загружаем…
    </div>
  );
}
export function Empty({
  title,
  text,
  action,
}: {
  title: string;
  text: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty">
      <div className="empty-icon">
        <SearchX size={28} />
      </div>
      <h3>{title}</h3>
      <p>{text}</p>
      {action}
    </div>
  );
}
export function Heading({
  eyebrow,
  title,
  subtitle,
  action,
}: {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
export function Score({ value }: { value: number }) {
  return (
    <span className={"score " + (value >= 60 ? "good" : "")}>
      <Sparkles size={13} />
      {value}
      <small>/100</small>
    </span>
  );
}
export function TaskCard({
  task,
  owned = false,
}: {
  task: Task;
  owned?: boolean;
}) {
  return (
    <Link
      className="task-card"
      to={
        owned && task.status === "draft"
          ? `/tasks/${task.id}/edit`
          : `/tasks/${task.id}`
      }
    >
      <div className="card-top">
        <span className="task-icon">
          {task.skill_slugs.includes("llm")
            ? "AI"
            : task.skill_slugs.includes("computer-vision")
              ? "CV"
              : "↗"}
        </span>
        <Score value={task.quality_score} />
      </div>
      <div className="card-status">
        <i />
        {statusLabels[task.status]}
      </div>
      <h3>{task.brief.title || "Новая бизнес-идея"}</h3>
      <p className="clamp">
        {task.brief.problem || task.raw_text || "Уточните описание задачи"}
      </p>
      <div className="tags">
        {task.skill_slugs.slice(0, 4).map((s) => (
          <span key={s}>{s}</span>
        ))}
      </div>
      <div className="card-bottom">
        <span>
          <Clock3 size={14} />
          {task.brief.timeline || "Срок уточняется"}
        </span>
        <ArrowUpRight size={20} />
      </div>
    </Link>
  );
}
export function Pagination({
  total,
  offset,
  limit,
  onChange,
}: {
  total: number;
  offset: number;
  limit: number;
  onChange: (o: number) => void;
}) {
  if (total <= limit) return null;
  return (
    <div className="pagination">
      <span>
        {offset + 1}–{Math.min(total, offset + limit)} из {total}
      </span>
      <button
        className="btn secondary small"
        disabled={offset === 0}
        onClick={() => onChange(Math.max(0, offset - limit))}
      >
        <ChevronLeft size={16} />
        Назад
      </button>
      <button
        className="btn secondary small"
        disabled={offset + limit >= total}
        onClick={() => onChange(offset + limit)}
      >
        Далее
        <ChevronRight size={16} />
      </button>
    </div>
  );
}
export function FormField({
  label,
  children,
  hint,
}: {
  label: string;
  children: ReactNode;
  hint?: string;
}) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {isValidElement(children)
        ? cloneElement(children as ReactElement<Record<string, unknown>>, {
            id,
            "aria-describedby": hint ? id + "-hint" : undefined,
          })
        : children}
      {hint && <small id={id + "-hint"}>{hint}</small>}
    </div>
  );
}
