import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Login from "./Login";
import { AuthProvider } from "../context/Auth";
import { clearAuthSession } from "../services/api";

const json = (body) => ({ ok: true, json: async () => body });

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/admin" element={<div>Admin Home</div>} />
          <Route path="/" element={<div>User Home</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

function authFetch(role, username) {
  return vi.fn((url, options = {}) => {
    if (url.endsWith("/api/login")) {
      return Promise.resolve(json({ token: `${role}token`, username, role }));
    }
    if (url.endsWith("/api/session")) {
      const hasBearer = (options.headers || {}).Authorization?.startsWith("Bearer ");
      return Promise.resolve(json({
        authenticated: hasBearer,
        username,
        role,
      }));
    }
    return Promise.resolve(json({}));
  });
}

async function submitCredentials(username, password) {
  fireEvent.change(screen.getByLabelText("Username"), { target: { value: username } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: password } });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
}

describe("Login flow", () => {
  beforeEach(() => {
    clearAuthSession();
  });

  it("lands an admin on the admin console", async () => {
    vi.stubGlobal("fetch", authFetch("admin", "shalini"));
    renderLogin();
    submitCredentials("shalini", "shalini02");
    expect(await screen.findByText("Admin Home")).toBeInTheDocument();
    expect(localStorage.getItem("tce_auth_role")).toBe("admin");
  });

  it("lands a regular user on the public dashboard", async () => {
    vi.stubGlobal("fetch", authFetch("user", "tce_user"));
    renderLogin();
    submitCredentials("tce_user", "tce2026");
    expect(await screen.findByText("User Home")).toBeInTheDocument();
    expect(localStorage.getItem("tce_auth_role")).toBe("user");
  });

  it("signs in any other username/password combination as a standard user", async () => {
    const fetchMock = authFetch("user", "someone_else");
    vi.stubGlobal("fetch", fetchMock);
    renderLogin();
    submitCredentials("someone_else", "their_password");
    expect(await screen.findByText("User Home")).toBeInTheDocument();
    expect(localStorage.getItem("tce_auth_role")).toBe("user");
    const loginCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith("/api/login"));
    expect(JSON.parse(loginCall[1].body)).toEqual({
      username: "someone_else",
      password: "their_password",
    });
  });

  it("does not expose any demo account buttons", async () => {
    vi.stubGlobal("fetch", authFetch("user", "tce_user"));
    renderLogin();
    expect(screen.queryByRole("button", { name: "Continue as Demo User" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Continue as Demo Admin" })).not.toBeInTheDocument();
    expect(screen.queryByText("Try the demo accounts")).not.toBeInTheDocument();
  });

  it("shows a friendly error when the server rejects the request", async () => {
    vi.stubGlobal("fetch", vi.fn(() =>
      Promise.resolve({ ok: false, status: 500, json: async () => ({ error: "Service unavailable" }) }),
    ));

    renderLogin();
    submitCredentials("tce_user", "nope");
    expect(await screen.findByRole("alert")).toHaveTextContent("Service unavailable");
    expect(screen.queryByText("User Home")).not.toBeInTheDocument();
    expect(screen.queryByText("Admin Home")).not.toBeInTheDocument();
  });

  it("the session check always presents the stored bearer token", async () => {
    const fetchMock = authFetch("user", "tce_user");
    vi.stubGlobal("fetch", fetchMock);
    renderLogin();
    submitCredentials("tce_user", "tce2026");
    await screen.findByText("User Home");
    await waitFor(() => {
      const sessionCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith("/api/session"));
      expect(sessionCall).toBeTruthy();
      expect((sessionCall[1].headers || {}).Authorization).toMatch(/^Bearer usertoken$/);
    });
  });
});