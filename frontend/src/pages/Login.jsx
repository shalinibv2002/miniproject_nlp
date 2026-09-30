import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Card } from "../components/ui";
import { useAuth } from "../context/Auth";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function authenticate(credentials) {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const body = await login(credentials.username, credentials.password);
      const from = location.state?.from?.pathname || (body.role === "admin" ? "/admin" : "/");
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || "Invalid username or password.");
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(event) {
    event.preventDefault();
    authenticate({ username, password });
  }

  return (
    <div className="page admin-login-page">
      <div className="admin-login-wrap">
        <Card title="Sign in to TCE Activity Intelligence">
          <p className="muted">Use your TCE account to explore institution activities.</p>
          <form onSubmit={onSubmit} className="admin-form">
            <label className="field">
              <span className="field-label">Username</span>
              <input
                autoFocus
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                autoComplete="username"
                aria-label="Username"
                required
              />
            </label>
            <label className="field">
              <span className="field-label">Password</span>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                aria-label="Password"
                required
              />
            </label>
            {error && <p className="error state" role="alert">{error}</p>}
            <button type="submit" className="primary" disabled={busy || !username.trim() || !password}>
              {busy ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </Card>
      </div>
    </div>
  );
}