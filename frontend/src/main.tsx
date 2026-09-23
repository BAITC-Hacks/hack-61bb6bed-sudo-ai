import { StudentSetup } from "./pages/Student";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { AuthProvider, RequireAuth } from "./app/Auth";
import { Layout } from "./app/Layout";
import { AuthPage, Profile } from "./pages/Accounts";
import { Explore, Dashboard } from "./pages/Explore";
import { Builder, NewTask } from "./pages/Builder";
import { TaskDetail, MyProposals } from "./pages/TaskDetail";
import { Teams, TeamPage, Join } from "./pages/Teams";
import { Welcome } from "./pages/Welcome";
import "./styles.css";
import "./liquid.css";
const protectedPage = (page: React.ReactNode) => (
  <RequireAuth>{page}</RequireAuth>
);
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Welcome />} />
          <Route path="login" element={<AuthPage key="login" />} />
          <Route
            path="register"
            element={<AuthPage key="register" register />}
          />
          <Route path="tasks/:id/edit" element={protectedPage(<Builder />)} />
          <Route element={<Layout />}>
            <Route path="catalog" element={<Explore />} />
            <Route
              path="student/profile"
              element={protectedPage(<StudentSetup />)}
            />
            <Route path="dashboard" element={protectedPage(<Dashboard />)} />
            <Route path="profile" element={protectedPage(<Profile />)} />
            <Route path="tasks/new" element={protectedPage(<NewTask />)} />
            <Route path="tasks/:id" element={<TaskDetail />} />
            <Route path="teams" element={protectedPage(<Teams />)} />
            <Route path="teams/:id" element={protectedPage(<TeamPage />)} />
            <Route path="join" element={protectedPage(<Join />)} />
            <Route path="proposals" element={protectedPage(<MyProposals />)} />
            <Route
              path="*"
              element={
                <div className="empty">
                  <h1>Страница не найдена</h1>
                  <Link className="btn" to="/">
                    Вернуться в каталог
                  </Link>
                </div>
              }
            />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
