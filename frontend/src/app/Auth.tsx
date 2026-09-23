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
  signedOut: boolean;
  setUser: (u: User | null) => void;
  logout: () => Promise<void>;
}>({ user: null, loading: true, signedOut: false, setUser: () => {}, logout: async () => {} });
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, updateUser] = useState<User | null>(null);
  const [signedOut, setSignedOut] = useState(false);
  const setUser = (u: User | null) => {
    if (u) setSignedOut(false);
    updateUser(u);
  };
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
    setSignedOut(true);
    setUser(null);
  };
  return (
    <Context.Provider value={{ user, loading, signedOut, setUser, logout }}>
      {children}
    </Context.Provider>
  );
}
export const useAuth = () => useContext(Context);
export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading, signedOut } = useAuth();
  const location = useLocation();
  if (loading) return <div className="loading">Загружаем аккаунт…</div>;
  return user ? (
    children
  ) : (
    <Navigate
      to={signedOut ? "/" : "/login"}
      replace
      state={{ from: location.pathname + location.search + location.hash }}
    />
  );
}
