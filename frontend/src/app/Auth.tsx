import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { Navigate, useLocation } from "react-router-dom";
import { api, post } from "../api/client";
import type { User } from "../api/types";
const Context = createContext<{
  user: User | null;
  loading: boolean;
  setUser: (u: User | null) => void;
  logout: () => Promise<void>;
}>({ user: null, loading: true, setUser: () => {}, logout: async () => {} });
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => {})
      .finally(() => setLoading(false));
    const clear = () => setUser(null);
    window.addEventListener("sana:unauthorized", clear);
    return () => window.removeEventListener("sana:unauthorized", clear);
  }, []);
  const logout = async () => {
    await post("/auth/logout");
    setUser(null);
  };
  return (
    <Context.Provider value={{ user, loading, setUser, logout }}>
      {children}
    </Context.Provider>
  );
}
export const useAuth = () => useContext(Context);
export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="loading">Загружаем аккаунт…</div>;
  return user ? (
    children
  ) : (
    <Navigate
      to="/login"
      replace
      state={{ from: location.pathname + location.search + location.hash }}
    />
  );
}
