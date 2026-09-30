import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/Auth";

const ADMIN_NAV = [
  { to: "/admin", label: "Overview", end: true },
  { to: "/admin/activities", label: "Manage Activities" },
  { to: "/admin/activities/new", label: "Add Activity" },
];

const LINKEDIN_NAV = [
  { to: "/admin/linkedin", label: "LinkedIn Overview", end: true },
  { to: "/admin/linkedin/records", label: "LinkedIn Records" },
  { to: "/admin/linkedin/review", label: "Review Queue" },
];

export default function AdminLayout() {
  const { username, roleLabel, logout } = useAuth();

  async function onLogout() {
    await logout();
    window.location.href = "/login";
  }

  return (
    <div className="app-shell admin-shell">
      <header className="site-header admin-header">
        <div className="site-header-inner">
          <div className="brand-mark admin-mark" aria-hidden="true">ADM</div>
          <h1 className="brand">TCE Admin</h1>
          <nav className="nav-menu admin-nav" aria-label="Admin navigation">
            <span className="nav-group-label">Database</span>
            <ul>
              {ADMIN_NAV.map((item) => (
                <li key={item.to}>
                  <NavLink to={item.to} end={item.end}
                    className={({ isActive }) => (isActive ? "active" : "")}>
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
            <span className="nav-group-label">LinkedIn Validator</span>
            <ul>
              {LINKEDIN_NAV.map((item) => (
                <li key={item.to}>
                  <NavLink to={item.to} end={item.end}
                    className={({ isActive }) => (isActive ? "active" : "")}>
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
          <div className="admin-user">
            <span className="muted">{username} &middot; {roleLabel}</span>
            <button type="button" className="ghost" onClick={onLogout}>Logout</button>
          </div>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}