import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, RequireAuth, RequireAdmin, useAuth } from "./Auth";
import { clearAuthSession } from "../services/api";
import Login from "../pages/Login";

const Home = () => <div>Protected Home</div>;
const LoginPage = () => <div>Login Page</div>;
const Admin = () => <div>Admin Console</div>;

function LogoutButton() {
  const { logout } = useAuth();
  return <button onClick={() => logout()}>Logout</button>;
}

const json = (body) => ({ ok: true, json: async () => body });

function sessionFetch(role, username) {
  return vi.fn(() =>
    Promise.resolve(json({ authenticated: true, username, role })),
  );
}

function renderGuarded() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<RequireAuth><Home /></RequireAuth>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe("auth guards", () => {
  beforeEach(() => clearAuthSession());

  it("redirects unauthenticated visitors from a protected page to Login", async () => {
    vi.stubGlobal("fetch", vi.fn(() =>
      Promise.resolve(json({ authenticated: false })),
    ));
    renderGuarded();
    expect(await screen.findByText("Login Page")).toBeInTheDocument();
    expect(screen.queryByText("Protected Home")).not.toBeInTheDocument();
  });

  it("sends unauthenticated direct access to /admin to Login without a redirect loop", async () => {
    vi.stubGlobal("fetch", vi.fn(() =>
      Promise.resolve(json({ authenticated: false })),
    ));
    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/admin" element={<RequireAdmin><Admin /></RequireAdmin>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );
    expect(await screen.findByText("Login Page")).toBeInTheDocument();
    expect(screen.queryByText("Admin Console")).not.toBeInTheDocument();
  });

  it("lets an admin user through RequireAdmin", async () => {
    localStorage.setItem("tce_auth_token", "admintoken");
    localStorage.setItem("tce_auth_username", "shalini");
    localStorage.setItem("tce_auth_role", "admin");
    vi.stubGlobal("fetch", sessionFetch("admin", "shalini"));
    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <AuthProvider>
          <Routes>
            <Route path="/admin" element={<RequireAdmin><Admin /></RequireAdmin>} />
            <Route path="/login" element={<LoginPage />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );
    expect(await screen.findByText("Admin Console")).toBeInTheDocument();
  });

  it("redirects a non-admin user away from the admin console", async () => {
    localStorage.setItem("tce_auth_token", "usertoken");
    localStorage.setItem("tce_auth_username", "tce_user");
    localStorage.setItem("tce_auth_role", "user");
    vi.stubGlobal("fetch", sessionFetch("user", "tce_user"));
    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<RequireAuth><Home /></RequireAuth>} />
            <Route path="/admin" element={<RequireAdmin><Admin /></RequireAdmin>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );
    expect(await screen.findByText("Protected Home")).toBeInTheDocument();
    expect(screen.queryByText("Admin Console")).not.toBeInTheDocument();
  });

  it("logs an authenticated user out back to the Login page", async () => {
    localStorage.setItem("tce_auth_token", "usertoken");
    localStorage.setItem("tce_auth_username", "tce_user");
    localStorage.setItem("tce_auth_role", "user");
    vi.stubGlobal("fetch", vi.fn((url) =>
      Promise.resolve(json(url.endsWith("/api/logout")
        ? { status: "logged out" }
        : { authenticated: true, username: "tce_user", role: "user" })),
    ));
    render(
      <MemoryRouter initialEntries={["/"]}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<RequireAuth><div>Protected Home<LogoutButton /></div></RequireAuth>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );
    fireEvent.click(await screen.findByRole("button", { name: "Logout" }));
    expect(await screen.findByText("Login Page")).toBeInTheDocument();
    expect(localStorage.getItem("tce_auth_token")).toBeNull();
  });

  it("a stale/revoked stored token is cleared and redirected to Login", async () => {
    localStorage.setItem("tce_auth_token", "stale");
    localStorage.setItem("tce_auth_username", "shalini");
    localStorage.setItem("tce_auth_role", "admin");
    vi.stubGlobal("fetch", vi.fn(() =>
      Promise.resolve(json({ authenticated: false })),
    ));
    renderGuarded();
    expect(await screen.findByText("Login Page")).toBeInTheDocument();
    expect(localStorage.getItem("tce_auth_token")).toBeNull();
  });

  it("RequireAuth shows a checking state while the session is validated", async () => {
    localStorage.setItem("tce_auth_token", "pending");
    vi.stubGlobal("fetch", () => new Promise(() => {}));
    renderGuarded();
    expect(await screen.findByText("Checking session...")).toBeInTheDocument();
  });

  it("a stale session check cannot clobber a freshly issued login token", async () => {
    localStorage.setItem("tce_auth_token", "stale");
    localStorage.setItem("tce_auth_username", "shalini");
    localStorage.setItem("tce_auth_role", "admin");

    let resolveStale;
    const staleSession = new Promise((resolve) => { resolveStale = resolve; });

    vi.stubGlobal("fetch", vi.fn((url, options = {}) => {
      const auth = (options.headers || {}).Authorization || "";
      if (String(url).endsWith("/api/session")) {
        if (auth.includes("stale")) return staleSession;
        return Promise.resolve(json({ authenticated: true, username: "tce_user", role: "user" }));
      }
      if (String(url).endsWith("/api/login")) {
        return Promise.resolve(json({ token: "newtoken", username: "tce_user", role: "user" }));
      }
      return Promise.resolve(json({}));
    }));

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<RequireAuth><Home /></RequireAuth>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText("Username"), { target: { value: "tce_user" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "tce2026" } });
    fireEvent.click(await screen.findByRole("button", { name: "Sign in" }));
    expect(await screen.findByText("Protected Home")).toBeInTheDocument();

    resolveStale(json({ authenticated: false }));
    await screen.findByText("Protected Home");
    expect(localStorage.getItem("tce_auth_token")).toBe("newtoken");
    expect(localStorage.getItem("tce_auth_role")).toBe("user");
  });
});