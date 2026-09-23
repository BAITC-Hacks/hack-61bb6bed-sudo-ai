import { useEffect, useRef, useState } from "react";
import { Bell, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api, post } from "../api/client";
import { ErrorBox } from "./UI";
type Notice = {
  id: string;
  task_id: string;
  task_title: string;
  team_name: string;
  created_at: string;
  read: boolean;
};
type Feed = { items: Notice[]; total: number; unread_count: number };
export function Notifications() {
  const [feed, setFeed] = useState<Feed>();
  const [open, setOpen] = useState(false),
    [offset, setOffset] = useState(0),
    [error, setError] = useState(""),
    [busy, setBusy] = useState("");
  const nav = useNavigate();
  const root = useRef<HTMLDivElement>(null);
  const sequence = useRef(0);
  useEffect(() => {
    let active = true;
    async function refresh() {
      const request = ++sequence.current;
      try {
        const data = await api<Feed>(
          `/business/notifications?offset=${offset}&limit=20`,
        );
        if (active && request === sequence.current) {
          setFeed(data);
          setError("");
        }
      } catch (e) {
        if (active && request === sequence.current)
          setError((e as Error).message);
      }
    }
    void refresh();
    const onVisible = () => {
      if (!document.hidden) void refresh();
    };
    const timer = setInterval(onVisible, 30000);
    window.addEventListener("focus", onVisible);
    return () => {
      active = false;
      clearInterval(timer);
      window.removeEventListener("focus", onVisible);
    };
  }, [offset, open]);
  useEffect(() => {
    if (!open) return;
    const close = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", close);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("pointerdown", close);
      document.removeEventListener("keydown", escape);
    };
  }, [open]);
  return (
    <div className="notifications" ref={root}>
      <button
        className="icon-btn notification-trigger"
        aria-label={`Уведомления${feed?.unread_count ? `: ${feed.unread_count} новых` : ""}`}
        aria-expanded={open}
        aria-controls="notification-panel"
        onClick={() => setOpen(!open)}
      >
        <Bell size={21} />
        {!!feed?.unread_count && (
          <span className="notification-count">
            {feed.unread_count > 99 ? "99+" : feed.unread_count}
          </span>
        )}
      </button>
      {open && (
        <section
          id="notification-panel"
          className="notification-panel"
          aria-label="Уведомления об откликах"
        >
          <div className="notification-heading">
            <h2>Отклики команд</h2>
            <button
              className="icon-btn"
              aria-label="Закрыть уведомления"
              onClick={() => setOpen(false)}
            >
              <X size={19} />
            </button>
          </div>
          <ErrorBox message={error} />
          {!feed && !error ? (
            <p role="status">Загружаем уведомления…</p>
          ) : feed?.items.length ? (
            <>
              <div className="notification-list">
                {feed.items.map((item) => (
                  <button
                    key={item.id}
                    disabled={!!busy}
                    className={`notification-item ${item.read ? "" : "unread"}`}
                    onClick={async () => {
                      setBusy(item.id);
                      setError("");
                      try {
                        if (!item.read) {
                          await post(`/business/notifications/${item.id}/read`);
                          sequence.current++;
                          setFeed((current) =>
                            current
                              ? {
                                  ...current,
                                  unread_count: Math.max(
                                    0,
                                    current.unread_count - 1,
                                  ),
                                  items: current.items.map((n) =>
                                    n.id === item.id ? { ...n, read: true } : n,
                                  ),
                                }
                              : current,
                          );
                        }
                        setOpen(false);
                        nav(`/tasks/${item.task_id}#proposals`);
                      } catch (e) {
                        setError((e as Error).message);
                      } finally {
                        setBusy("");
                      }
                    }}
                  >
                    <strong>{item.team_name}</strong>
                    <span>Откликнулась на «{item.task_title}»</span>
                    <small>
                      {new Date(item.created_at).toLocaleString("ru-RU", {
                        day: "numeric",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                      {!item.read ? " · Новое" : ""}
                    </small>
                  </button>
                ))}
              </div>
              <div className="notification-paging">
                {offset > 0 && (
                  <button
                    className="text-link"
                    onClick={() => setOffset(offset - 20)}
                  >
                    Назад
                  </button>
                )}
                {offset + 20 < feed.total && (
                  <button
                    className="text-link"
                    onClick={() => setOffset(offset + 20)}
                  >
                    Следующие
                  </button>
                )}
              </div>
            </>
          ) : (
            !error && (
              <p>
                Пока нет откликов. Когда команда предложит решение вашей задачи,
                уведомление появится здесь.
              </p>
            )
          )}
        </section>
      )}
    </div>
  );
}
