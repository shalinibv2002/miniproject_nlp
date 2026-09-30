import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { api, adminApi, getAuthSession, setAuthSession, clearAuthSession } from "../services/api";

const AuthContext = createContext(null);
const ROLE_LABELS = { admin: "Admin", user: "User" };

export function AuthProvider({ children }) {
  const initial = getAuthSession();
  const [token, setToken] = useState(initial.token);
  const [username, setUsername] = useState(initial.username);
  const [role, setRole] = useState(initial.role);
  const [checking, setChecking] = useState(Boolean(initial.token));

  useEffect(() => {
    if (!token) return undefined;
    let active = true;
    const checkedToken = token;
    setChecking(true);
    adminApi.get("/api/session")
      .then((body) => {
        if (!active) return;
        if (getAuthSession().token !== checkedToken) return;
        if (body.authenticated) {
          setUsername(body.username);
          setRole(body.role);
          setAuthSession(token, body.username, body.role);
        } else {
          clearAuthSession();
          setToken(null);
          setUsername("");
          setRole("");
        }
      })
      .catch(() => {
        if (!active) return;
        if (getAuthSession().token !== checkedToken) return;
        clearAuthSession();
        setToken(null);
        setUsername("");
        setRole("");
      })
      .finally(() => { if (active) setChecking(false); });
    return () => { active = false; };
  }, [token]);

  const login = useCallback(async (name, password) => {
    const body = await api.post("/api/login", { username: name, password });
    setAuthSession(body.token, body.username, body.role);
    setToken(body.token);
    setUsername(body.username);
    setRole(body.role);
    return body;
  }, []);

  const logout = useCallback(async () => {
    try { await adminApi.post("/api/logout"); } catch { /* best effort */ }
    clearAuthSession();
    setToken(null);
    setUsername("");
    setRole("");
  }, []);

  const value = useMemo(
    () => ({
      token, username, role, checking, login, logout,
      isAuthenticated: Boolean(token),
      isAdmin: role === "admin",
      roleLabel: ROLE_LABELS[role] || role,
    }),
    [token, username, role, checking, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function useAdminAuth() {
  return useAuth();
}

export function RequireAuth({ children }) {
  const { token, checking } = useAuth();
  const location = useLocation();
  if (checking) return <p className="muted state">Checking session...</p>;
  if (!token) return <Navigate to="/login" replace state={{ from: location }} />;
  return children;
}

export function RequireAdmin({ children }) {
  const { token, role, checking } = useAuth();
  const location = useLocation();
  if (checking) return <p className="muted state">Checking session...</p>;
  if (!token) return <Navigate to="/login" replace state={{ from: location }} />;
  if (role !== "admin") return <Navigate to="/" replace />;
  return children;
}